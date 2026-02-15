#!/usr/bin/env python3
"""示例发货脚本。

请替换为你自己的 Playwright/Selenium 自动化逻辑：
1. 打开闲鱼卖家后台订单页
2. 定位对应 order_id
3. 粘贴 message
4. 点击发货
"""

from __future__ import annotations

import argparse


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--order-id", required=True)
    parser.add_argument("--message", required=True)
    args = parser.parse_args()

    # TODO: 在这里接入你的浏览器自动化代码
    # 这里先打印，作为可运行占位。
    print(f"[DRY-RUN] deliver order={args.order_id}")
    print(args.message)


if __name__ == "__main__":
    main()
