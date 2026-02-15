# xianyu_auto_delivery

这是一个只做 **闲鱼自动发货** 的项目：

- 抓取“已支付、待发货”订单（不包含 team 账号管理）。
- 根据商品标题自动匹配卡池。
- 从本地卡密库提取对应卡密。
- 自动发送卡密并执行“点击发货”。

## 核心设计（无 team-helper API 依赖）

1. `JsonOrderProvider`：读取你抓单脚本写入的 `orders.json`。
2. `ProductMatcher`：按关键字把商品标题映射到卡池 `product_key`。
3. `CardStore`：本地 SQLite 管理卡密库存（导入、分配、失败回滚、发货幂等）。
4. `CommandDeliveryClient`：调用你的浏览器自动化脚本，把卡密发送给买家并点击发货。

## 项目结构

```text
src/xianyu_auto_delivery/
  config.py
  models.py
  order_provider.py    # 已支付订单读取 + 标记已发货
  product_matcher.py   # 商品标题 -> 卡池映射
  card_store.py        # 卡密库存管理（SQLite）
  delivery_client.py   # 调用外部自动化命令发货
  service.py           # 自动发货编排
  main.py
```

## 准备数据

### 1) 订单文件 `orders.json`

由你自己的抓单程序持续更新，例如：

```json
[
  {
    "order_id": "12345",
    "item_title": "GPT Plus 月卡",
    "buyer_nick": "buyer_a",
    "quantity": 1,
    "paid": true,
    "delivered": false
  }
]
```

### 2) 商品映射 `product_mapping.json`

key 是标题关键字，value 是卡池名：

```json
{
  "gpt": "GPT",
  "claude": "CLAUDE"
}
```

### 3) 卡密导入

```python
from xianyu_auto_delivery.card_store import CardStore

store = CardStore("./data/cards.db")
store.import_cards_from_file("GPT", "./cards_gpt.txt")
```

## 环境变量

| 变量名 | 说明 |
|---|---|
| `SQLITE_PATH` | 卡密数据库路径，默认 `./data/cards.db` |
| `ORDERS_JSON_PATH` | 订单文件路径，默认 `./data/orders.json` |
| `PRODUCT_MAPPING_PATH` | 商品映射文件路径，默认 `./data/product_mapping.json` |
| `DELIVERY_COMMAND` | 实际执行发货点击的命令模板（必须） |
| `POLL_INTERVAL_SECONDS` | 轮询秒数，默认 `15` |

`DELIVERY_COMMAND` 支持变量：`{order_id}`、`{message}`。

示例：

```bash
export DELIVERY_COMMAND='python scripts/xianyu_deliver.py --order-id {order_id} --message {message}'
```

> 你只需要把 `scripts/xianyu_deliver.py` 替换成你现有的闲鱼页面自动化脚本（例如 Playwright/Selenium），这个项目就会把订单和卡密拼好后调用它自动点击发货。

## 运行

```bash
xianyu-auto-delivery --once
xianyu-auto-delivery
```

## 测试

```bash
python -m pytest
```
