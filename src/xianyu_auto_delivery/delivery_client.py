from __future__ import annotations

from abc import ABC, abstractmethod
import shlex
import subprocess


class DeliveryClient(ABC):
    """发货动作抽象：最终应自动把卡密发送给买家并点击发货。"""

    @abstractmethod
    def deliver_card_codes(self, order_id: str, message: str) -> None:
        raise NotImplementedError


class CommandDeliveryClient(DeliveryClient):
    """通过命令行调用浏览器自动化脚本执行“发送卡密并点击发货”。

    DELIVERY_COMMAND 示例：
    python scripts/xianyu_deliver.py --order-id "{order_id}" --message "{message}"
    """

    def __init__(self, command_template: str) -> None:
        self.command_template = command_template

    def deliver_card_codes(self, order_id: str, message: str) -> None:
        command = self.command_template.format(
            order_id=order_id,
            message=message.replace('"', '\\"'),
        )
        completed = subprocess.run(shlex.split(command), check=False, capture_output=True, text=True)
        if completed.returncode != 0:
            raise RuntimeError(f"发货命令执行失败: {completed.stderr.strip()}")
