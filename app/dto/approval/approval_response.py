"""
审批响应 DTO 模块

定义审批相关的响应数据结构
"""
from typing import Optional, List
from pydantic import BaseModel, Field


class ApproverResponse(BaseModel):
    """
    审批人响应 DTO
    """

    userId: str = Field(..., description="用户ID")
    userName: str = Field(..., description="用户姓名")
    status: int = Field(default=0, description="审批状态")
    reason: Optional[str] = Field(None, description="审批理由")


class LeaveResponse(BaseModel):
    """
    请假信息响应 DTO
    """

    type: int = Field(..., description="请假类型")
    startTime: int = Field(..., description="开始时间戳")
    endTime: int = Field(..., description="结束时间戳")
    reason: str = Field(..., description="请假原因")
    timeType: int = Field(default=1, description="时长类型")
    duration: float = Field(..., description="请假时长")


class GoOutResponse(BaseModel):
    """
    外出信息响应 DTO
    """

    startTime: int = Field(..., description="开始时间戳")
    endTime: int = Field(..., description="结束时间戳")
    duration: float = Field(..., description="时长(小时)")
    reason: str = Field(..., description="外出原因")


class MakeCardResponse(BaseModel):
    """
    补卡信息响应 DTO
    """

    date: int = Field(..., description="补卡时间戳")
    reason: str = Field(..., description="补卡理由")
    day: int = Field(..., description="补卡日期")
    checkType: int = Field(..., description="补卡类型")


class ApprovalResponse(BaseModel):
    """
    审批详情响应 DTO
    """

    id: str = Field(..., description="审批ID")
    user: Optional[ApproverResponse] = Field(None, description="申请人信息")
    no: str = Field(..., description="审批编号")
    type: int = Field(..., description="审批类型")
    status: int = Field(default=0, description="审批状态")
    title: Optional[str] = Field(None, description="标题")
    abstract: Optional[str] = Field(None, description="摘要")
    reason: Optional[str] = Field(None, description="原因")
    approver: Optional[ApproverResponse] = Field(None, description="当前审批人")
    approvers: List[ApproverResponse] = Field(default_factory=list, description="所有审批人列表")
    copyPersons: List[ApproverResponse] = Field(default_factory=list, description="抄送人列表")
    finishAt: Optional[int] = Field(None, description="完成时间戳")
    finishDay: Optional[int] = Field(None, description="完成日期")
    finishMonth: Optional[int] = Field(None, description="完成月份")
    finishYear: Optional[int] = Field(None, description="完成年份")
    makeCard: Optional[MakeCardResponse] = Field(None, description="补卡信息")
    leave: Optional[LeaveResponse] = Field(None, description="请假信息")
    goOut: Optional[GoOutResponse] = Field(None, description="外出信息")
    updateAt: Optional[int] = Field(None, description="更新时间戳")
    createAt: Optional[int] = Field(None, description="创建时间戳")


class ApprovalListItemResponse(BaseModel):
    """
    审批列表项响应 DTO
    """

    id: str = Field(..., description="审批ID")
    no: str = Field(..., description="审批编号")
    type: int = Field(..., description="审批类型")
    status: int = Field(default=0, description="审批状态")
    title: Optional[str] = Field(None, description="标题")
    abstract: Optional[str] = Field(None, description="摘要")
    createId: Optional[str] = Field(None, description="创建人ID")
    participatingId: Optional[str] = Field(None, description="参与人ID")
    createAt: Optional[int] = Field(None, description="创建时间戳")
    leave: Optional[LeaveResponse] = Field(None, description="请假信息")
    makeCard: Optional[MakeCardResponse] = Field(None, description="补卡信息")
    goOut: Optional[GoOutResponse] = Field(None, description="外出信息")


class ApprovalListResponse(BaseModel):
    """
    审批列表响应 DTO
    """

    count: int = Field(..., description="总记录数")
    data: List[ApprovalListItemResponse] = Field(default_factory=list, description="审批列表")