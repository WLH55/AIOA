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

    user_id: str = Field(..., description="用户ID")
    user_name: str = Field(..., description="用户姓名")
    status: int = Field(default=0, description="审批状态")
    reason: Optional[str] = Field(None, description="审批理由")


class LeaveResponse(BaseModel):
    """
    请假信息响应 DTO
    """

    type: int = Field(..., description="请假类型")
    start_time: int = Field(..., description="开始时间戳")
    end_time: int = Field(..., description="结束时间戳")
    reason: str = Field(..., description="请假原因")
    time_type: int = Field(default=1, description="时长类型")
    duration: float = Field(..., description="请假时长")


class GoOutResponse(BaseModel):
    """
    外出信息响应 DTO
    """

    start_time: int = Field(..., description="开始时间戳")
    end_time: int = Field(..., description="结束时间戳")
    duration: float = Field(..., description="时长(小时)")
    reason: str = Field(..., description="外出原因")


class MakeCardResponse(BaseModel):
    """
    补卡信息响应 DTO
    """

    date: int = Field(..., description="补卡时间戳")
    reason: str = Field(..., description="补卡理由")
    day: int = Field(..., description="补卡日期")
    check_type: int = Field(..., description="补卡类型")


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
    abstract: Optional[str] = Field(None, alias="abstract_", description="摘要")
    reason: Optional[str] = Field(None, description="原因")
    approver: Optional[ApproverResponse] = Field(None, description="当前审批人")
    approvers: List[ApproverResponse] = Field(default_factory=list, description="所有审批人列表")
    copy_persons: List[ApproverResponse] = Field(default_factory=list, description="抄送人列表")
    finish_at: Optional[int] = Field(None, description="完成时间戳")
    finish_day: Optional[int] = Field(None, description="完成日期")
    finish_month: Optional[int] = Field(None, description="完成月份")
    finish_year: Optional[int] = Field(None, description="完成年份")
    make_card: Optional[MakeCardResponse] = Field(None, description="补卡信息")
    leave: Optional[LeaveResponse] = Field(None, description="请假信息")
    go_out: Optional[GoOutResponse] = Field(None, description="外出信息")
    update_at: Optional[int] = Field(None, description="更新时间戳")
    create_at: Optional[int] = Field(None, description="创建时间戳")


class ApprovalListItemResponse(BaseModel):
    """
    审批列表项响应 DTO
    """

    id: str = Field(..., description="审批ID")
    no: str = Field(..., description="审批编号")
    type: int = Field(..., description="审批类型")
    status: int = Field(default=0, description="审批状态")
    title: Optional[str] = Field(None, description="标题")
    abstract: Optional[str] = Field(None, alias="abstract_", description="摘要")
    create_id: Optional[str] = Field(None, description="创建人ID")
    participating_id: Optional[str] = Field(None, description="参与人ID")
    create_at: Optional[int] = Field(None, description="创建时间戳")
    leave: Optional[LeaveResponse] = Field(None, description="请假信息")
    make_card: Optional[MakeCardResponse] = Field(None, description="补卡信息")
    go_out: Optional[GoOutResponse] = Field(None, description="外出信息")


class ApprovalListResponse(BaseModel):
    """
    审批列表响应 DTO
    """

    count: int = Field(..., description="总记录数")
    data: List[ApprovalListItemResponse] = Field(default_factory=list, description="审批列表")