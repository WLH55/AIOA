"""
待办事项状态枚举

1-待处理, 2-进行中, 3-已完成, 4-已取消, 5-已超时
"""
from enum import IntEnum


class TodoStatus(IntEnum):
    """待办事项状态枚举"""
    PENDING = 1      # 待处理
    IN_PROGRESS = 2  # 进行中
    FINISHED = 3     # 已完成
    CANCELLED = 4    # 已取消
    TIMEOUT = 5      # 已超时

    @classmethod
    def from_value(cls, value: int) -> "TodoStatus":
        """
        根据整数值获取枚举实例

        Args:
            value: 整数值

        Returns:
            TodoStatus 枚举实例，未找到时返回 PENDING
        """
        for status in cls:
            if status.value == value:
                return status
        return cls.PENDING