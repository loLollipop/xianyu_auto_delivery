from __future__ import annotations

from abc import ABC, abstractmethod
import json
from urllib import request


class DeliveryClient(ABC):
    """发货动作抽象层。"""

    @abstractmethod
    def deliver_card_codes(self, order_id: str, message: str) -> None:
        raise NotImplementedError


class XianyuDeliveryClient(DeliveryClient):
    """对接 chatgpt-team-helper 中的闲鱼自动发货接口。"""

    def __init__(self, base_url: str, token: str, timeout: int = 15) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    def deliver_card_codes(self, order_id: str, message: str) -> None:
        req = request.Request(
            f"{self.base_url}/api/xianyu/orders/{order_id}/deliver",
            headers=self.headers,
            data=json.dumps({"message": message}).encode("utf-8"),
            method="POST",
        )
        with request.urlopen(req, timeout=self.timeout):
            return
