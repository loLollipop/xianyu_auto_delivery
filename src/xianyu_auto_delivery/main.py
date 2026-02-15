from __future__ import annotations

import argparse
import json
import time

from .card_store import CardStore
from .config import Settings
from .delivery_client import CommandDeliveryClient
from .order_provider import JsonOrderProvider
from .product_matcher import ProductMatcher
from .service import AutoDeliveryService


def build_service(settings: Settings) -> AutoDeliveryService:
    order_provider = JsonOrderProvider(settings.orders_json_path)
    card_store = CardStore(settings.sqlite_path)
    product_matcher = ProductMatcher.from_json(settings.product_mapping_path)
    delivery_client = CommandDeliveryClient(settings.delivery_command)
    return AutoDeliveryService(order_provider, card_store, product_matcher, delivery_client)


def main() -> None:
    parser = argparse.ArgumentParser(description="闲鱼自动发货服务")
    parser.add_argument("--once", action="store_true", help="只执行一轮")
    args = parser.parse_args()

    settings = Settings.from_env()
    settings.validate()
    service = build_service(settings)

    if args.once:
        print(json.dumps(service.run_once(), ensure_ascii=False))
        return

    while True:
        print(json.dumps(service.run_once(), ensure_ascii=False))
        time.sleep(settings.poll_interval_seconds)


if __name__ == "__main__":
    main()
