"""
审批实体模型

使用 Beanie ODM 定义 MongoDB Document
包含内嵌文档：Approver（审批人）、MakeCard（补卡）、Leave（请假）、GoOut（外出）
"""
import time
from typing import List, Optional
from pydantic import BaseModel, Field
from beanie import Document


# ==================== 内嵌文档 ====================

class Approver(BaseModel):
    """
    审批人（内嵌文档）

    用于 Approval 实体中的 approvers 和 copyPersons 字段
    """

    userId: str = Field(..., description="用户ID")
    userName: str = Field(..., description="用户姓名")
    status: int = Field(default=0, description="审批状态")
    reason: Optional[str] = Field(None, description="审批理由")


class MakeCard(BaseModel):
    """
    补卡信息（内嵌文档）

    用于 Approval 实体中的 makeCard 字段
    """

    date: int = Field(..., description="补卡时间戳")
    reason: str = Field(..., description="补卡理由")
    day: int = Field(..., description="补卡日期(格式20221011)")
    checkType: int = Field(..., description="补卡类型(1-上班卡, 2-下班卡)")


class Leave(BaseModel):
    """
    请假信息（内嵌文档）

    用于 Approval 实体中的 leave 字段
    """

    type: int = Field(..., description="请假类型(1-事假, 2-调休, 3-病假, 4-年假, 5-产假, 6-陪产假, 7-婚假, 8-丧假, 9-哺乳假)")
    startTime: int = Field(..., description="开始时间戳")
    endTime: int = Field(..., description="结束时间戳")
    reason: str = Field(..., description="请假原因")
    timeType: int = Field(default=1, description="时长类型(1-小时, 2-天)")
    duration: float = Field(..., description="请假时长")


class GoOut(BaseModel):
    """
    外出信息（内嵌文档）

    用于 Approval 实体中的 goOut 字段
    """

    startTime: int = Field(..., description="开始时间戳")
    endTime: int = Field(..., description="结束时间戳")
    duration: float = Field(..., description="时长(小时)")
    reason: str = Field(..., description="外出原因")


# ==================== 主文档 ====================

class Approval(Document):
    """
    审批文档模型

    Attributes:
        userId: 申请人用户ID
        no: 审批编号
        type: 审批类型
        status: 审批状态
        title: 审批标题
        abstract: 审批摘要
        reason: 申请理由
        approvalId: 当前审批人ID
        approvalIdx: 当前审批人索引
        approvers: 审批人列表
        copyPersons: 抄送人列表
        participation: 参与人员ID列表
        finishAt: 完成时间戳
        finishDay: 完成日期
        finishMonth: 完成月份
        finishYeas: 完成年份
        makeCard: 补卡申请详情
        leave: 请假申请详情
        goOut: 外出申请详情
        createAt: 创建时间戳
        updateAt: 更新时间戳
    """

    # 基本信息
    userId: str = Field(..., description="申请人用户ID")
    no: str = Field(..., description="审批编号")
    type: int = Field(..., description="审批类型")
    status: int = Field(default=0, description="审批状态")

    # 详情信息
    title: Optional[str] = Field(None, description="审批标题")
    abstract: Optional[str] = Field(None, description="审批摘要")
    reason: Optional[str] = Field(None, description="申请理由")

    # 审批流程
    approvalId: Optional[str] = Field(None, description="当前审批人ID")
    approvalIdx: Optional[int] = Field(None, description="当前审批人索引")
    approvers: List[Approver] = Field(default_factory=list, description="审批人列表")
    copyPersons: List[Approver] = Field(default_factory=list, description="抄送人列表")
    participation: List[str] = Field(default_factory=list, description="参与人员ID列表")

    # 完成信息
    finishAt: Optional[int] = Field(None, description="完成时间戳")
    finishDay: Optional[int] = Field(None, description="完成日期")
    finishMonth: Optional[int] = Field(None, description="完成月份")
    finishYeas: Optional[int] = Field(None, description="完成年份")

    # 多态详情（可选）
    makeCard: Optional[MakeCard] = Field(None, description="补卡申请详情")
    leave: Optional[Leave] = Field(None, description="请假申请详情")
    goOut: Optional[GoOut] = Field(None, description="外出申请详情")

    # 时间戳
    createAt: int = Field(default_factory=lambda: int(time.time() * 1000), description="创建时间戳")
    updateAt: int = Field(default_factory=lambda: int(time.time() * 1000), description="更新时间戳")

    class Settings:
        """Beanie 设置"""
        name = "approval"

    class Config:
        """Pydantic 配置"""
        json_schema_extra = {
            "example": {
                "userId": "user123",
                "no": "AP20240101001",
                "type": 2,
                "status": 1,
                "title": "请假申请",
                "reason": "身体不适",
                "approvers": [],
                "leave": {
                    "type": 3,
                    "startTime": 1704067200000,
                    "endTime": 1704153600000,
                    "reason": "身体不适",
                    "timeType": 2,
                    "duration": 1.0
                }
            }
        }

    def update_timestamp(self) -> None:
        """更新时间戳"""
        self.updateAt = int(time.time() * 1000)

    @staticmethod
    def get_current_timestamp() -> int:
        """获取当前时间戳（毫秒）"""
        return int(time.time() * 1000)