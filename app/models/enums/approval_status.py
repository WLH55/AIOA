"""
审批状态枚举

0-未开始, 1-处理中, 2-通过, 3-拒绝, 4-撤销, 5-自动通过
"""
from enum import IntEnum


class ApprovalStatus(IntEnum):
    """审批状态枚举"""
    NOT_STARTED = 0  # 未开始
    PROCESSED = 1    # 处理中
    PASS = 2         # 通过
    REFUSE = 3       # 拒绝
    CANCEL = 4       # 撤销
    AUTO_PASS = 5    # 自动通过

    @classmethod
    def from_value(cls, value: int) -> "ApprovalStatus":
        """
        根据整数值获取枚举实例

        Args:
            value: 整数值

        Returns:
            ApprovalStatus 枚举实例，未找到时返回 NOT_STARTED
        """
        for status in cls:
            if status.value == value:
                return status
        return cls.NOT_STARTED