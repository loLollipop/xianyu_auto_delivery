from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Order:
    """闲鱼已支付待发货订单。"""

    order_id: str
    item_title: str
    buyer_nick: str
    quantity: int = 1
    paid: bool = True


@dataclass(slots=True)
class CardCode:
    code: str
