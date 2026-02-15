# claw.cloud 部署说明

本文提供 `xianyu_auto_delivery` 在 claw.cloud 上的最小可用部署步骤。

## 1. 前置条件

- 你已有抓单程序，会持续写入 `orders.json`。
- 你已有自动发货脚本（Playwright/Selenium），可通过命令行执行。
- 已准备商品映射 `product_mapping.json` 与卡密库文件（后续导入 SQLite）。

## 2. 创建持久化目录/卷

至少持久化 `/app/data`，避免重启后丢失：
- `cards.db`
- `orders.json`
- `product_mapping.json`

## 3. 环境变量

参考 `.env.example`：

- `SQLITE_PATH=/app/data/cards.db`
- `ORDERS_JSON_PATH=/app/data/orders.json`
- `PRODUCT_MAPPING_PATH=/app/data/product_mapping.json`
- `DELIVERY_COMMAND=python /app/scripts/xianyu_deliver.py --order-id {order_id} --message {message}`
- `POLL_INTERVAL_SECONDS=15`

## 4. 构建与启动

使用仓库内 `Dockerfile` 构建镜像后启动，默认命令是：

```bash
xianyu-auto-delivery
```

如果只想跑一轮用于检查，可以在平台里将启动命令改为：

```bash
xianyu-auto-delivery --once
```

## 5. 首次数据准备

1. 准备 `/app/data/product_mapping.json`。
2. 准备 `/app/data/orders.json`（至少为空数组 `[]`）。
3. 用一次性命令导入卡密：

```bash
python -c "from xianyu_auto_delivery.card_store import CardStore; s=CardStore('/app/data/cards.db'); print(s.import_cards_from_file('GPT','/app/data/cards_gpt.txt'))"
```

## 6. 发货脚本接入

仓库提供了占位脚本 `scripts/xianyu_deliver.py`。请将其替换为你的真实自动化逻辑（登录、定位订单、填入卡密、点击发货）。

> 服务只负责编排，不负责浏览器登录态管理；建议你把登录态目录也放持久卷。
