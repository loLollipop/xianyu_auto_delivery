from __future__ import annotations

from xianyu_auto_delivery.card_store import CardStore
from xianyu_auto_delivery.models import Order
from xianyu_auto_delivery.service import AutoDeliveryService


class FakeProvider:
    def __init__(self, orders: list[Order]):
        self._orders = orders

    def fetch_pending_orders(self) -> list[Order]:
        return self._orders


class FakeDeliveryClient:
    def __init__(self, should_fail: bool = False):
        self.should_fail = should_fail
        self.calls: list[tuple[str, str]] = []

    def deliver_card_codes(self, order_id: str, message: str) -> None:
        if self.should_fail:
            raise RuntimeError("deliver failed")
        self.calls.append((order_id, message))


def test_run_once_success(tmp_path):
    db = tmp_path / "cards.db"
    cards_txt = tmp_path / "cards.txt"
    cards_txt.write_text("ABC\nDEF\n", encoding="utf-8")

    store = CardStore(str(db))
    assert store.import_cards_from_file("GPT会员", str(cards_txt)) == 2

    provider = FakeProvider([
        Order(order_id="A1", item_title="GPT会员", buyer_nick="bob", quantity=2),
    ])
    client = FakeDeliveryClient()

    service = AutoDeliveryService(provider, store, client)
    metrics = service.run_once()

    assert metrics == {
        "fetched": 1,
        "skipped": 0,
        "delivered": 1,
        "failed": 0,
        "insufficient_cards": 0,
    }
    assert len(client.calls) == 1
    assert store.is_order_delivered("A1") is True


def test_run_once_delivery_failure_rolls_back(tmp_path):
    db = tmp_path / "cards.db"
    cards_txt = tmp_path / "cards.txt"
    cards_txt.write_text("ABC\n", encoding="utf-8")

    store = CardStore(str(db))
    store.import_cards_from_file("GPT会员", str(cards_txt))

    provider = FakeProvider([
        Order(order_id="A2", item_title="GPT会员", buyer_nick="alice", quantity=1),
    ])
    client = FakeDeliveryClient(should_fail=True)

    service = AutoDeliveryService(provider, store, client)
    metrics = service.run_once()

    assert metrics["failed"] == 1
    assert store.is_order_delivered("A2") is False

    provider_retry = FakeProvider([
        Order(order_id="A3", item_title="GPT会员", buyer_nick="alice", quantity=1),
    ])
    client_retry = FakeDeliveryClient(should_fail=False)
    retry_service = AutoDeliveryService(provider_retry, store, client_retry)
    retry_metrics = retry_service.run_once()

    assert retry_metrics["delivered"] == 1
