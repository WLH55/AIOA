"""
审批类型枚举

1-通用, 2-请假, 3-补卡, 4-外出, 5-报销, 6-付款, 7-采购, 8-收款, 9-转正, 10-离职, 11-加班, 12-合同
"""
from enum import IntEnum


class ApprovalType(IntEnum):
    """审批类型枚举"""
    UNIVERSAL = 1       # 通用审批
    LEAVE = 2           # 请假审批
    MAKE_CARD = 3       # 补卡审批
    GO_OUT = 4          # 外出审批
    REIMBURSE = 5       # 报销审批
    PAYMENT = 6         # 付款审批
    BUYER = 7           # 采购审批
    PROCEEDS = 8        # 收款审批
    POSITIVE = 9        # 转正审批
    DIMISSION = 10      # 离职审批
    OVERTIME = 11       # 加班审批
    BUYER_CONTRACT = 12 # 采购合同审批

    @classmethod
    def from_value(cls, value: int) -> "ApprovalType":
        """
        根据整数值获取枚举实例

        Args:
            value: 整数值

        Returns:
            ApprovalType 枚举实例，未找到时返回 UNIVERSAL
        """
        for atype in cls:
            if atype.value == value:
                return atype
        return cls.UNIVERSAL