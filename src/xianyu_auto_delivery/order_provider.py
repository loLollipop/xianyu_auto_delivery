from __future__ import annotations

from abc import ABC, abstractmethod
import json
from pathlib import Path

from .models import Order


class OrderProvider(ABC):
    @abstractmethod
    def fetch_paid_pending_orders(self) -> list[Order]:
        raise NotImplementedError

    @abstractmethod
    def mark_delivered(self, order_id: str) -> None:
        raise NotImplementedError


class JsonOrderProvider(OrderProvider):
    """从本地 JSON 读取闲鱼订单（可由你的抓单脚本实时刷新）。"""

    def __init__(self, orders_json_path: str) -> None:
        self.orders_json_path = orders_json_path
        Path(orders_json_path).parent.mkdir(parents=True, exist_ok=True)
        if not Path(orders_json_path).exists():
            Path(orders_json_path).write_text("[]", encoding="utf-8")

    def _read(self) -> list[dict]:
        with open(self.orders_json_path, "r", encoding="utf-8") as file:
            data = json.load(file)
        if not isinstance(data, list):
            raise ValueError("orders.json 必须是数组")
        return data

    def _write(self, rows: list[dict]) -> None:
        with open(self.orders_json_path, "w", encoding="utf-8") as file:
            json.dump(rows, file, ensure_ascii=False, indent=2)

    def fetch_paid_pending_orders(self) -> list[Order]:
        rows = self._read()
        orders: list[Order] = []
        for row in rows:
            paid = bool(row.get("paid", False))
            delivered = bool(row.get("delivered", False))
            if not paid or delivered:
                continue
            orders.append(
                Order(
                    order_id=str(row["order_id"]),
                    item_title=str(row["item_title"]),
                    buyer_nick=str(row.get("buyer_nick", "买家")),
                    quantity=max(int(row.get("quantity", 1)), 1),
                    paid=True,
                )
            )
        return orders

    def mark_delivered(self, order_id: str) -> None:
        rows = self._read()
        for row in rows:
            if str(row.get("order_id")) == order_id:
                row["delivered"] = True
        self._write(rows)
