from __future__ import annotations

import argparse
import json
import time

from .card_store import CardStore
from .config import Settings
from .delivery_client import XianyuDeliveryClient
from .order_provider import ChatGPTTeamHelperOrderProvider
from .service import AutoDeliveryService


def build_service() -> AutoDeliveryService:
    settings = Settings.from_env()
    settings.validate()

    provider = ChatGPTTeamHelperOrderProvider(
        base_url=settings.helper_api_base,
        token=settings.helper_api_token,
    )
    delivery_client = XianyuDeliveryClient(
        base_url=settings.xianyu_delivery_api_base,
        token=settings.xianyu_delivery_token,
    )
    card_store = CardStore(settings.sqlite_path)
    return AutoDeliveryService(provider, card_store, delivery_client)


def main() -> None:
    parser = argparse.ArgumentParser(description="闲鱼自动发货服务")
    parser.add_argument("--once", action="store_true", help="只运行一轮")
    args = parser.parse_args()

    settings = Settings.from_env()
    settings.validate()
    service = build_service()

    if args.once:
        metrics = service.run_once()
        print(json.dumps(metrics, ensure_ascii=False))
        return

    while True:
        metrics = service.run_once()
        print(json.dumps(metrics, ensure_ascii=False))
        time.sleep(settings.poll_interval_seconds)


if __name__ == "__main__":
    main()
