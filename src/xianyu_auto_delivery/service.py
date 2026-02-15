from __future__ import annotations

from .card_store import CardStore
from .delivery_client import DeliveryClient
from .order_provider import OrderProvider
from .product_matcher import ProductMatcher


class AutoDeliveryService:
    """闲鱼支付订单自动发货核心编排。"""

    def __init__(
        self,
        order_provider: OrderProvider,
        card_store: CardStore,
        product_matcher: ProductMatcher,
        delivery_client: DeliveryClient,
    ) -> None:
        self.order_provider = order_provider
        self.card_store = card_store
        self.product_matcher = product_matcher
        self.delivery_client = delivery_client

    def run_once(self) -> dict[str, int]:
        metrics = {
            "fetched": 0,
            "delivered": 0,
            "failed": 0,
            "insufficient_cards": 0,
            "unmatched_product": 0,
            "skipped": 0,
        }

        orders = self.order_provider.fetch_paid_pending_orders()
        metrics["fetched"] = len(orders)

        for order in orders:
            if self.card_store.is_delivered(order.order_id):
                metrics["skipped"] += 1
                continue

            product_key = self.product_matcher.match(order.item_title)
            if not product_key:
                metrics["unmatched_product"] += 1
                continue

            cards = self.card_store.allocate_cards(product_key, order.order_id, order.quantity)
            if len(cards) < order.quantity:
                metrics["insufficient_cards"] += 1
                continue

            message = self._build_message(order.order_id, order.buyer_nick, [c.code for c in cards])

            try:
                self.delivery_client.deliver_card_codes(order.order_id, message)
                self.card_store.mark_delivered(order.order_id)
                self.order_provider.mark_delivered(order.order_id)
                metrics["delivered"] += 1
            except Exception:
                self.card_store.rollback_cards(order.order_id)
                metrics["failed"] += 1

        return metrics

    @staticmethod
    def _build_message(order_id: str, buyer_nick: str, codes: list[str]) -> str:
        lines = [f"买家 {buyer_nick} 您好，订单 {order_id} 的卡密如下："]
        lines.extend(f"{i}. {code}" for i, code in enumerate(codes, 1))
        lines.append("请妥善保管卡密，祝您使用愉快。")
        return "\n".join(lines)
