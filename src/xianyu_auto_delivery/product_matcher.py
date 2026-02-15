from __future__ import annotations

import json


class ProductMatcher:
    """将闲鱼商品标题映射到卡池 product_key。"""

    def __init__(self, mapping: dict[str, str]) -> None:
        self.mapping = mapping

    @classmethod
    def from_json(cls, file_path: str) -> "ProductMatcher":
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)
        if not isinstance(data, dict):
            raise ValueError("product mapping 文件必须是 JSON 对象")
        return cls({str(k): str(v) for k, v in data.items()})

    def match(self, item_title: str) -> str | None:
        text = item_title.lower()
        for keyword, product_key in self.mapping.items():
            if keyword.lower() in text:
                return product_key
        return None
