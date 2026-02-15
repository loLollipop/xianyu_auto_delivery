from __future__ import annotations

from .card_store import CardStore
from .delivery_client import DeliveryClient
from .models import Order
from .order_provider import OrderProvider


class AutoDeliveryService:
    """编排订单->卡密分配->闲鱼发货的核心服务。"""

    def __init__(
        self,
        order_provider: OrderProvider,
        card_store: CardStore,
        delivery_client: DeliveryClient,
    ) -> None:
        self.order_provider = order_provider
        self.card_store = card_store
        self.delivery_client = delivery_client

    def run_once(self) -> dict[str, int]:
        metrics = {
            "fetched": 0,
            "skipped": 0,
            "delivered": 0,
            "failed": 0,
            "insufficient_cards": 0,
        }

        orders = self.order_provider.fetch_pending_orders()
        metrics["fetched"] = len(orders)

        for order in orders:
            if self.card_store.is_order_delivered(order.order_id):
                metrics["skipped"] += 1
                continue

            status = self._deliver_single_order(order)
            if status == "delivered":
                metrics["delivered"] += 1
            elif status == "insufficient_cards":
                metrics["insufficient_cards"] += 1
            else:
                metrics["failed"] += 1

        return metrics

    def _deliver_single_order(self, order: Order) -> str:
        cards = self.card_store.allocate_cards(
            product_name=order.item_title,
            order_id=order.order_id,
            quantity=order.quantity,
        )
        if not cards:
            return "insufficient_cards"

        message = self._build_delivery_message(order, [card.card_code for card in cards])

        try:
            self.delivery_client.deliver_card_codes(order.order_id, message)
            self.card_store.mark_delivered(
                order_id=order.order_id,
                card_count=len(cards),
                message=message,
            )
            return "delivered"
        except Exception:
            self.card_store.rollback_cards(order.order_id)
            return "failed"

    @staticmethod
    def _build_delivery_message(order: Order, card_codes: list[str]) -> str:
        lines = [
            f"买家 {order.buyer_nick} 您好，订单 {order.order_id} 的卡密如下：",
        ]
        lines.extend(f"{idx}. {code}" for idx, code in enumerate(card_codes, 1))
        lines.append("请妥善保管卡密，如有问题请及时联系。")
        return "\n".join(lines)
