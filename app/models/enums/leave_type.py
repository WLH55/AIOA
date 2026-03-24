"""
请假类型枚举

1-事假, 2-调休, 3-病假, 4-年假, 5-产假, 6-陪产假, 7-婚假, 8-丧假, 9-哺乳假
"""
from enum import IntEnum


class LeaveType(IntEnum):
    """请假类型枚举"""
    MATTER = 1        # 事假
    REST = 2          # 调休
    FALL = 3          # 病假
    ANNUAL = 4        # 年假
    MATERNITY = 5     # 产假
    PATERNITY = 6     # 陪产假
    MARRIAGE = 7      # 婚假
    FUNERAL = 8       # 丧假
    BREASTFEEDING = 9 # 哺乳假

    @property
    def description(self) -> str:
        """获取请假类型描述"""
        descriptions = {
            1: "事假",
            2: "调休",
            3: "病假",
            4: "年假",
            5: "产假",
            6: "陪产假",
            7: "婚假",
            8: "丧假",
            9: "哺乳假",
        }
        return descriptions.get(self.value, "未知请假类型")

    @classmethod
    def from_value(cls, value: int) -> "LeaveType":
        """
        根据整数值获取枚举实例

        Args:
            value: 整数值

        Returns:
            LeaveType 枚举实例，未找到时返回 MATTER
        """
        for ltype in cls:
            if ltype.value == value:
                return ltype
        return cls.MATTER