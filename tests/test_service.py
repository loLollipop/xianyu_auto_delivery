from __future__ import annotations

import json

from xianyu_auto_delivery.card_store import CardStore
from xianyu_auto_delivery.models import Order
from xianyu_auto_delivery.order_provider import JsonOrderProvider
from xianyu_auto_delivery.product_matcher import ProductMatcher
from xianyu_auto_delivery.service import AutoDeliveryService


class FakeDeliveryClient:
    def __init__(self, fail: bool = False):
        self.fail = fail
        self.calls: list[tuple[str, str]] = []

    def deliver_card_codes(self, order_id: str, message: str) -> None:
        if self.fail:
            raise RuntimeError("delivery failed")
        self.calls.append((order_id, message))


def _write_orders(path, rows):
    path.write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")


def test_run_once_success(tmp_path):
    db_path = tmp_path / "cards.db"
    orders_path = tmp_path / "orders.json"
    mapping = ProductMatcher({"gpt": "GPT"})
    _write_orders(
        orders_path,
        [{"order_id": "A1", "item_title": "GPT Plus 月卡", "buyer_nick": "bob", "quantity": 2, "paid": True, "delivered": False}],
    )

    provider = JsonOrderProvider(str(orders_path))
    store = CardStore(str(db_path))
    cards_file = tmp_path / "cards.txt"
    cards_file.write_text("C1\nC2\n", encoding="utf-8")
    assert store.import_cards_from_file("GPT", str(cards_file)) == 2

    delivery = FakeDeliveryClient()
    service = AutoDeliveryService(provider, store, mapping, delivery)
    metrics = service.run_once()

    assert metrics["delivered"] == 1
    assert len(delivery.calls) == 1
    assert store.is_delivered("A1") is True


def test_unmatched_product(tmp_path):
    orders_path = tmp_path / "orders.json"
    _write_orders(
        orders_path,
        [{"order_id": "A2", "item_title": "Netflix", "buyer_nick": "alice", "quantity": 1, "paid": True, "delivered": False}],
    )

    provider = JsonOrderProvider(str(orders_path))
    store = CardStore(str(tmp_path / "cards.db"))
    delivery = FakeDeliveryClient()
    service = AutoDeliveryService(provider, store, ProductMatcher({"gpt": "GPT"}), delivery)

    metrics = service.run_once()
    assert metrics["unmatched_product"] == 1


def test_delivery_failure_rolls_back(tmp_path):
    db_path = tmp_path / "cards.db"
    orders_path = tmp_path / "orders.json"
    _write_orders(
        orders_path,
        [{"order_id": "A3", "item_title": "GPT", "buyer_nick": "tom", "quantity": 1, "paid": True, "delivered": False}],
    )

    provider = JsonOrderProvider(str(orders_path))
    store = CardStore(str(db_path))
    cards_file = tmp_path / "cards.txt"
    cards_file.write_text("ROLLBACK1\n", encoding="utf-8")
    store.import_cards_from_file("GPT", str(cards_file))

    service = AutoDeliveryService(provider, store, ProductMatcher({"gpt": "GPT"}), FakeDeliveryClient(fail=True))
    metrics = service.run_once()
    assert metrics["failed"] == 1

    orders = provider.fetch_paid_pending_orders()
    assert len(orders) == 1
