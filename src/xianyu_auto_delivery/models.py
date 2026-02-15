from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class Order:
    """闲鱼订单核心信息。"""

    order_id: str
    item_title: str
    buyer_nick: str
    quantity: int = 1
    status: str = "pending"


@dataclass(slots=True)
class Card:
    """卡密实体。"""

    card_id: int
    product_name: str
    card_code: str
    created_at: datetime
