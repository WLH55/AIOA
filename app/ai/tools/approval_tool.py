"""
审批管理工具

提供创建请假/补卡/外出审批和查询审批记录的能力，通过闭包注入当前用户上下文
"""
import logging
import time
from datetime import datetime, timezone, timedelta
from typing import List

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from app.models.approval import Approval, Leave, MakeCard, GoOut
from app.models.enums.approval_type import ApprovalType
from app.repository.approval_repository import ApprovalRepository

logger = logging.getLogger(__name__)


# 东八区时区
_CST = timezone(timedelta(hours=8))


# 假期类型映射
_LEAVE_TYPE_MAP = {
    1: "事假", 2: "调休", 3: "病假", 4: "年假", 5: "产假",
    6: "陪产假", 7: "婚假", 8: "丧假", 9: "哺乳假",
}


def _generate_approval_no() -> str:
    """
    生成审批编号

    Returns:
        审批编号，格式 AP + 年月日 + 毫秒后3位
    """
    now_ms = int(time.time() * 1000)
    dt = datetime.fromtimestamp(now_ms / 1000, tz=_CST)
    date_str = dt.strftime("%Y%m%d")
    suffix = str(now_ms)[-3:]
    return f"AP{date_str}{suffix}"


# ==================== 输入模型 ====================


class LeaveApprovalInput(BaseModel):
    """请假审批输入"""
    leaveType: int = Field(
        ..., description="请假类型：1-事假, 2-调休, 3-病假, 4-年假, 5-产假, 6-陪产假, 7-婚假, 8-丧假, 9-哺乳假"
    )
    startTime: str = Field(..., description="开始时间戳（毫秒字符串）")
    endTime: str = Field(..., description="结束时间戳（毫秒字符串）")
    reason: str = Field(..., description="请假原因")


class PunchApprovalInput(BaseModel):
    """补卡审批输入"""
    punchType: int = Field(..., description="补卡类型：1-上班卡, 2-下班卡")
    date: str = Field(..., description="补卡日期时间戳（毫秒字符串）")
    reason: str = Field(..., description="补卡原因")


class GoOutApprovalInput(BaseModel):
    """外出审批输入"""
    startTime: str = Field(..., description="开始时间戳（毫秒字符串）")
    endTime: str = Field(..., description="结束时间戳（毫秒字符串）")
    reason: str = Field(..., description="外出原因")


class FindApprovalsInput(BaseModel):
    """查询审批输入"""
    queryType: str = Field(
        default="mine",
        description="查询类型：'mine'-我提交的, 'pending'-待我审批的",
    )


# ==================== 工厂函数 ====================


def _make_create_leave_approval(user_id: str, user_name: str):
    """
    创建请假审批工具的工厂函数

    Args:
        user_id: 当前用户 ID
        user_name: 当前用户名
    """
    async def _create_leave_approval(
        leaveType: int, startTime: str, endTime: str, reason: str,
    ) -> str:
        type_name = _LEAVE_TYPE_MAP.get(leaveType)
        if not type_name:
            return f"无效的请假类型：{leaveType}，有效值为 1-9"
        start_ts = int(startTime)
        end_ts = int(endTime)
        if end_ts <= start_ts:
            return "结束时间必须大于开始时间"
        duration_hours = (end_ts - start_ts) / (1000 * 3600)
        leave = Leave(
            type=leaveType,
            startTime=start_ts,
            endTime=end_ts,
            reason=reason,
            timeType=2 if duration_hours >= 24 else 1,
            duration=round(duration_hours, 1),
        )
        approval = Approval(
            userId=user_id,
            no=_generate_approval_no(),
            type=ApprovalType.LEAVE.value,
            status=0,
            title=f"{user_name}的{type_name}申请",
            abstract=reason,
            reason=reason,
            leave=leave,
            participation=[user_id],
        )
        saved = await ApprovalRepository.create(approval)
        start_dt = datetime.fromtimestamp(start_ts / 1000, tz=_CST)
        end_dt = datetime.fromtimestamp(end_ts / 1000, tz=_CST)
        return (
            f"请假申请已提交！类型：{type_name}，"
            f"时间：{start_dt.strftime('%Y-%m-%d %H:%M')} ~ {end_dt.strftime('%Y-%m-%d %H:%M')}，"
            f"审批编号：{saved.no}"
        )
    return _create_leave_approval


def _make_create_punch_approval(user_id: str, user_name: str):
    """
    创建补卡审批工具的工厂函数

    Args:
        user_id: 当前用户 ID
        user_name: 当前用户名
    """
    async def _create_punch_approval(
        punchType: int, date: str, reason: str,
    ) -> str:
        if punchType not in (1, 2):
            return "无效的补卡类型：1-上班卡, 2-下班卡"
        date_ts = int(date)
        dt = datetime.fromtimestamp(date_ts / 1000, tz=_CST)
        day_int = int(dt.strftime("%Y%m%d"))
        make_card = MakeCard(
            date=date_ts,
            reason=reason,
            day=day_int,
            checkType=punchType,
        )
        punch_name = "上班卡" if punchType == 1 else "下班卡"
        approval = Approval(
            userId=user_id,
            no=_generate_approval_no(),
            type=ApprovalType.MAKE_CARD.value,
            status=0,
            title=f"{user_name}的补卡申请（{punch_name}）",
            abstract=reason,
            reason=reason,
            makeCard=make_card,
            participation=[user_id],
        )
        saved = await ApprovalRepository.create(approval)
        return (
            f"补卡申请已提交！类型：{punch_name}，"
            f"日期：{dt.strftime('%Y-%m-%d')}，审批编号：{saved.no}"
        )
    return _create_punch_approval


def _make_create_go_out_approval(user_id: str, user_name: str):
    """
    创建外出审批工具的工厂函数

    Args:
        user_id: 当前用户 ID
        user_name: 当前用户名
    """
    async def _create_go_out_approval(
        startTime: str, endTime: str, reason: str,
    ) -> str:
        start_ts = int(startTime)
        end_ts = int(endTime)
        if end_ts <= start_ts:
            return "结束时间必须大于开始时间"
        duration = round((end_ts - start_ts) / (1000 * 3600), 1)
        go_out = GoOut(
            startTime=start_ts,
            endTime=end_ts,
            duration=duration,
            reason=reason,
        )
        approval = Approval(
            userId=user_id,
            no=_generate_approval_no(),
            type=ApprovalType.GO_OUT.value,
            status=0,
            title=f"{user_name}的外出申请",
            abstract=reason,
            reason=reason,
            goOut=go_out,
            participation=[user_id],
        )
        saved = await ApprovalRepository.create(approval)
        start_dt = datetime.fromtimestamp(start_ts / 1000, tz=_CST)
        end_dt = datetime.fromtimestamp(end_ts / 1000, tz=_CST)
        return (
            f"外出申请已提交！"
            f"时间：{start_dt.strftime('%H:%M')} ~ {end_dt.strftime('%H:%M')}（{duration}小时），"
            f"审批编号：{saved.no}"
        )
    return _create_go_out_approval


def _make_find_approvals(user_id: str, _user_name: str):
    """
    查询审批记录工具的工厂函数

    Args:
        user_id: 当前用户 ID
    """
    async def _find_approvals(queryType: str = "mine") -> str:
        if queryType == "pending":
            approvals, total = await ApprovalRepository.find_by_approval_id_and_status(
                user_id, 0,
            )
            prefix = "待我审批"
        else:
            approvals, total = await ApprovalRepository.find_by_user_id(user_id)
            prefix = "我提交的"
        if not approvals:
            return f"暂无{prefix}的审批记录"
        status_map = {0: "审批中", 1: "已通过", 2: "已拒绝", 3: "已撤销"}
        type_map = {2: "请假", 3: "补卡", 4: "外出"}
        lines = [f"找到 {total} 条{prefix}审批："]
        for i, app in enumerate(approvals[:10], 1):
            status_text = status_map.get(app.status, "未知")
            type_text = type_map.get(app.type, "审批")
            line = f"{i}. {type_text} - {status_text} - {app.title or app.no}"
            lines.append(line)
        return "\n".join(lines)
    return _find_approvals


def get_approval_tools(user_id: str, user_name: str) -> List[StructuredTool]:
    """
    获取审批管理工具列表

    Args:
        user_id: 当前用户 ID
        user_name: 当前用户名

    Returns:
        工具列表
    """
    return [
        StructuredTool.from_function(
            coroutine=_make_create_leave_approval(user_id, user_name),
            name="createLeaveApproval",
            description=(
                "创建请假审批。支持9种假期类型：1-事假, 2-调休, 3-病假, 4-年假, 5-产假, 6-陪产假, 7-婚假, 8-丧假, 9-哺乳假。"
                "需要提供请假类型、起止时间和请假原因。"
            ),
            args_schema=LeaveApprovalInput,
        ),
        StructuredTool.from_function(
            coroutine=_make_create_punch_approval(user_id, user_name),
            name="createPunchApproval",
            description="创建补卡审批。支持上班卡(1)和下班卡(2)。需要补卡类型、日期和补卡原因。",
            args_schema=PunchApprovalInput,
        ),
        StructuredTool.from_function(
            coroutine=_make_create_go_out_approval(user_id, user_name),
            name="createGoOutApproval",
            description="创建外出审批。需要起止时间和外出原因。",
            args_schema=GoOutApprovalInput,
        ),
        StructuredTool.from_function(
            coroutine=_make_find_approvals(user_id, user_name),
            name="findApprovals",
            description="查询审批记录。queryType='mine'查询我提交的，queryType='pending'查询待我审批的。",
            args_schema=FindApprovalsInput,
        ),
    ]
