from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(slots=True)
class Settings:
    """仅保留自动发货闭环配置，不依赖 team-helper API。"""

    sqlite_path: str
    orders_json_path: str
    product_mapping_path: str
    delivery_command: str
    poll_interval_seconds: int = 15

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            sqlite_path=os.environ.get("SQLITE_PATH", "./data/cards.db"),
            orders_json_path=os.environ.get("ORDERS_JSON_PATH", "./data/orders.json"),
            product_mapping_path=os.environ.get("PRODUCT_MAPPING_PATH", "./data/product_mapping.json"),
            delivery_command=os.environ.get("DELIVERY_COMMAND", ""),
            poll_interval_seconds=int(os.environ.get("POLL_INTERVAL_SECONDS", "15")),
        )

    def validate(self) -> None:
        required = {
            "DELIVERY_COMMAND": self.delivery_command,
        }
        missing = [key for key, value in required.items() if not value]
        if missing:
            raise ValueError(f"缺少必要环境变量: {', '.join(missing)}")
