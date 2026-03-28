"""
聊天类型枚举

1-群聊, 2-私聊, 3-AI消息
"""
from enum import IntEnum


class ChatType(IntEnum):
    """聊天类型枚举"""
    GROUP = 1   # 群聊
    SINGLE = 2  # 私聊
    AI = 3      # AI消息

    @classmethod
    def from_value(cls, value: int) -> "ChatType":
        """
        根据整数值获取枚举实例

        Args:
            value: 整数值

        Returns:
            ChatType 枚举实例，未找到时返回 GROUP
        """
        for ctype in cls:
            if ctype.value == value:
                return ctype
        return cls.GROUP