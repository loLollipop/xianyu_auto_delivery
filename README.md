# xianyu_auto_delivery

一个将 **闲鱼订单抓取自动化** 与 **卡密库存管理** 结合的自动发货项目。

> 设计目标：参考 `Kylsky/chatgpt-team-helper` 的订单抓取与发货能力，融合 `loLollipop/xianyu_card` 的卡密管理思路，形成“订单 -> 卡密分配 -> 自动回传闲鱼”的闭环。

## 功能特性

- 对接上游订单源（默认：`chatgpt-team-helper` 暴露的 pending 订单接口）。
- 本地 SQLite 卡密仓库：导入卡密、按商品名分配、失败回滚。
- 自动发货：将分配出的卡密拼接为发货消息，回调闲鱼发货接口。
- 幂等保障：已发货订单写入 `delivery_logs`，避免重复发货。

## 项目结构

```text
src/xianyu_auto_delivery/
  config.py          # 环境变量配置
  models.py          # 订单/卡密模型
  order_provider.py  # 订单抓取抽象 + chatgpt-team-helper 适配
  card_store.py      # 卡密库存与发货日志
  delivery_client.py # 发货动作抽象 + 闲鱼发货适配
  service.py         # 编排核心逻辑
  main.py            # CLI 入口
```

## 安装

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## 环境变量

| 变量名 | 说明 |
|---|---|
| `HELPER_API_BASE` | 订单抓取服务地址（如 chatgpt-team-helper API） |
| `HELPER_API_TOKEN` | 订单抓取服务 Token |
| `XIANYU_DELIVERY_API_BASE` | 闲鱼发货服务地址 |
| `XIANYU_DELIVERY_TOKEN` | 闲鱼发货服务 Token |
| `SQLITE_PATH` | 本地卡密数据库路径，默认 `./data/cards.db` |
| `POLL_INTERVAL_SECONDS` | 轮询间隔秒数，默认 `15` |

## 卡密导入示例

可以直接复用 `CardStore.import_cards_from_file`，每行一条卡密：

```python
from xianyu_auto_delivery.card_store import CardStore

store = CardStore("./data/cards.db")
count = store.import_cards_from_file("GPT会员", "./cards.txt")
print("imported", count)
```

## 运行

只跑一轮：

```bash
xianyu-auto-delivery --once
```

持续轮询：

```bash
xianyu-auto-delivery
```

## 可扩展建议（创新点）

1. **商品映射规则**：增加“商品标题 -> 卡池名”的模糊映射，提升实际订单匹配率。
2. **分布式锁/多实例协同**：避免多实例抢同一批卡密。
3. **风控策略**：对高频订单或异常买家加人工审核队列。
4. **可观测性**：接入 Prometheus 指标与告警（库存低水位、发货失败率）。
5. **管理后台**：补充简单 Web 控制台，查看库存、订单与发货日志。

## 测试

```bash
pytest
```

## 合规提示

请确保你的自动化流程符合闲鱼平台规则、商品合规要求及当地法律法规。
