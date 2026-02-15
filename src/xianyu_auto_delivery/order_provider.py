from __future__ import annotations

from abc import ABC, abstractmethod
import json
from urllib import request

from .models import Order


class OrderProvider(ABC):
    """订单来源抽象层。"""

    @abstractmethod
    def fetch_pending_orders(self) -> list[Order]:
        raise NotImplementedError


class ChatGPTTeamHelperOrderProvider(OrderProvider):
    """对接 chatgpt-team-helper 的订单抓取接口。"""

    def __init__(self, base_url: str, token: str, timeout: int = 15) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    def fetch_pending_orders(self) -> list[Order]:
        req = request.Request(
            f"{self.base_url}/api/xianyu/orders/pending",
            headers=self.headers,
            method="GET",
        )
        with request.urlopen(req, timeout=self.timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))

        orders: list[Order] = []
        for row in payload.get("orders", []):
            orders.append(
                Order(
                    order_id=str(row["order_id"]),
                    item_title=str(row["item_title"]),
                    buyer_nick=str(row.get("buyer_nick", "未知买家")),
                    quantity=max(int(row.get("quantity", 1)), 1),
                    status=str(row.get("status", "pending")),
                )
            )
        return orders
