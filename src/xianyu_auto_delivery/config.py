from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(slots=True)
class Settings:
    """运行配置。

    通过环境变量读取，便于容器化部署。
    """

    helper_api_base: str
    helper_api_token: str
    xianyu_delivery_api_base: str
    xianyu_delivery_token: str
    sqlite_path: str = "./data/cards.db"
    poll_interval_seconds: int = 15

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            helper_api_base=os.environ.get("HELPER_API_BASE", "").rstrip("/"),
            helper_api_token=os.environ.get("HELPER_API_TOKEN", ""),
            xianyu_delivery_api_base=os.environ.get("XIANYU_DELIVERY_API_BASE", "").rstrip("/"),
            xianyu_delivery_token=os.environ.get("XIANYU_DELIVERY_TOKEN", ""),
            sqlite_path=os.environ.get("SQLITE_PATH", "./data/cards.db"),
            poll_interval_seconds=int(os.environ.get("POLL_INTERVAL_SECONDS", "15")),
        )

    def validate(self) -> None:
        required = {
            "HELPER_API_BASE": self.helper_api_base,
            "HELPER_API_TOKEN": self.helper_api_token,
            "XIANYU_DELIVERY_API_BASE": self.xianyu_delivery_api_base,
            "XIANYU_DELIVERY_TOKEN": self.xianyu_delivery_token,
        }
        missing = [key for key, value in required.items() if not value]
        if missing:
            joined = ", ".join(missing)
            raise ValueError(f"缺少必要环境变量: {joined}")
