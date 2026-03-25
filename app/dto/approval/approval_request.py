"""
审批请求 DTO 模块

定义审批相关的请求参数
"""
from typing import Optional, List
from pydantic import BaseModel, Field


class LeaveRequest(BaseModel):
    """
    请假信息请求 DTO
    """

    type: int = Field(..., description="请假类型(1-事假, 2-调休, 3-病假, 4-年假, 5-产假, 6-陪产假, 7-婚假, 8-丧假, 9-哺乳假)")
    startTime: int = Field(..., description="开始时间戳(秒)")
    endTime: int = Field(..., description="结束时间戳(秒)")
    reason: str = Field(..., description="请假原因")
    timeType: int = Field(default=1, description="时长类型(1-小时, 2-天)")
    duration: Optional[float] = Field(None, description="请假时长")


class GoOutRequest(BaseModel):
    """
    外出信息请求 DTO
    """

    startTime: int = Field(..., description="开始时间戳(秒)")
    endTime: int = Field(..., description="结束时间戳(秒)")
    duration: Optional[float] = Field(None, description="时长(小时)")
    reason: str = Field(..., description="外出原因")


class MakeCardRequest(BaseModel):
    """
    补卡信息请求 DTO
    """

    date: int = Field(..., description="补卡时间戳(秒)")
    reason: str = Field(..., description="补卡理由")
    day: int = Field(..., description="补卡日期(格式20221011)")
    checkType: int = Field(..., description="补卡类型(1-上班卡, 2-下班卡)")


class ApprovalRequest(BaseModel):
    """
    审批请求 DTO

    用于创建审批申请
    """

    id: Optional[str] = Field(None, description="审批ID(编辑时需要)")
    type: int = Field(..., description="审批类型(1-请假, 2-外出, 3-补卡)")
    title: Optional[str] = Field(None, description="标题")
    abstract: Optional[str] = Field(None, description="摘要")
    reason: Optional[str] = Field(None, description="原因")
    approverIds: Optional[List[str]] = Field(None, description="审批人ID列表")
    copyPersonIds: Optional[List[str]] = Field(None, description="抄送人ID列表")
    makeCard: Optional[MakeCardRequest] = Field(None, description="补卡信息")
    leave: Optional[LeaveRequest] = Field(None, description="请假信息")
    goOut: Optional[GoOutRequest] = Field(None, description="外出信息")


class ApprovalListRequest(BaseModel):
    """
    审批列表请求 DTO
    """

    page: int = Field(default=1, ge=1, description="页码")
    count: int = Field(default=10, ge=1, le=100, description="每页数量")
    type: int = Field(default=1, description="操作类型(1-我提交的, 2-待我审批的)")


class DisposeRequest(BaseModel):
    """
    审批处理请求 DTO

    用于处理审批(通过/拒绝/撤销)
    """

    approvalId: str = Field(..., description="审批ID")
    status: int = Field(..., description="处理状态(2-通过, 3-拒绝, 4-取消)")
    reason: Optional[str] = Field(None, description="处理原因/备注")