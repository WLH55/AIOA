"""
审批服务层

处理审批相关的业务逻辑
"""
import logging
import random
import time
from datetime import datetime
from typing import List, Set

from app.config.exceptions import BusinessValidationException, ResourceNotFoundException
from app.models.approval import Approval, Approver, Leave, GoOut, MakeCard
from app.models.department import Department
from app.models.department_user import DepartmentUser
from app.models.user import User
from app.models.enums.approval_status import ApprovalStatus
from app.models.enums.approval_type import ApprovalType
from app.models.enums.leave_type import LeaveType
from app.repository.approval_repository import ApprovalRepository
from app.repository.user_repository import UserRepository
from app.repository.department_repository import DepartmentRepository
from app.repository.department_user_repository import DepartmentUserRepository
from app.dto.approval.approval_request import (
    ApprovalRequest,
    ApprovalListRequest,
    DisposeRequest,
    LeaveRequest,
    GoOutRequest,
    MakeCardRequest,
)
from app.dto.approval.approval_response import (
    ApprovalResponse,
    ApprovalListResponse,
    ApprovalListItemResponse,
    ApproverResponse,
    LeaveResponse,
    GoOutResponse,
    MakeCardResponse,
)

logger = logging.getLogger(__name__)


class ApprovalService:
    """
    审批服务类

    提供审批 CRUD、处理等业务逻辑
    """

    @staticmethod
    async def info(approval_id: str) -> ApprovalResponse:
        """
        获取审批详情

        Args:
            approval_id: 审批ID

        Returns:
            审批详情响应 DTO

        Raises:
            ResourceNotFoundException: 审批记录不存在
        """
        approval = await ApprovalRepository.find_by_id(approval_id)
        if not approval:
            raise ResourceNotFoundException("审批记录不存在")

        # 查询所有参与人员信息
        users = await UserRepository.find_by_ids(approval.participation)
        user_map = {str(user.id): user for user in users}

        # 获取申请人信息
        applicant = user_map.get(approval.userId)
        if not applicant:
            raise ResourceNotFoundException("申请人信息不存在")

        user_info = ApproverResponse(
            user_id=applicant.id,
            user_name=applicant.name,
        )

        # 获取当前审批人信息
        approver_info = None
        if approval.approvalId:
            current_approver = user_map.get(approval.approvalId)
            if current_approver:
                approver_info = ApproverResponse(
                    user_id=current_approver.id,
                    user_name=current_approver.name,
                )

        # 构建审批人列表
        approvers: List[ApproverResponse] = []
        if approval.approvers:
            for approver in approval.approvers:
                user = user_map.get(approver.userId)
                approvers.append(ApproverResponse(
                    user_id=approver.userId,
                    user_name=user.name if user else "",
                    status=approver.status,
                    reason=approver.reason,
                ))

        # 构建抄送人列表
        copy_persons: List[ApproverResponse] = []
        if approval.copyPersons:
            for copy_person in approval.copyPersons:
                user = user_map.get(copy_person.userId)
                copy_persons.append(ApproverResponse(
                    user_id=copy_person.userId,
                    user_name=user.name if user else "",
                ))

        # 构建多态详情
        leave_resp = None
        if approval.leave:
            leave_resp = LeaveResponse(
                type=approval.leave.type,
                start_time=approval.leave.startTime,
                end_time=approval.leave.endTime,
                reason=approval.leave.reason,
                time_type=approval.leave.timeType,
                duration=approval.leave.duration,
            )

        go_out_resp = None
        if approval.goOut:
            go_out_resp = GoOutResponse(
                start_time=approval.goOut.startTime,
                end_time=approval.goOut.endTime,
                duration=approval.goOut.duration,
                reason=approval.goOut.reason,
            )

        make_card_resp = None
        if approval.makeCard:
            make_card_resp = MakeCardResponse(
                date=approval.makeCard.date,
                reason=approval.makeCard.reason,
                day=approval.makeCard.day,
                check_type=approval.makeCard.checkType,
            )

        return ApprovalResponse(
            id=str(approval.id),
            user=user_info,
            no=approval.no,
            type=approval.type,
            status=approval.status,
            title=approval.title,
            abstract=approval.abstract,
            reason=approval.reason,
            approver=approver_info,
            approvers=approvers,
            copy_persons=copy_persons,
            finish_at=approval.finishAt,
            finish_day=approval.finishDay,
            finish_month=approval.finishMonth,
            finish_year=approval.finishYeas,
            leave=leave_resp,
            go_out=go_out_resp,
            make_card=make_card_resp,
            update_at=approval.updateAt,
            create_at=approval.createAt,
        )

    @staticmethod
    async def create(request: ApprovalRequest, current_user: User) -> str:
        """
        创建审批申请

        Args:
            request: 审批请求 DTO
            current_user: 当前用户

        Returns:
            创建的审批ID
        """
        logger.info(f"创建审批: type={request.type}")

        current_user_id = str(current_user.id)
        current_time = int(time.time() * 1000)

        # 创建审批记录
        approval = Approval(
            userId=current_user_id,
            no=ApprovalService._generate_random_no(11),
            type=request.type,
            status=ApprovalStatus.PROCESSED.value,
            reason=request.reason,
        )

        # 根据审批类型处理不同的审批内容
        abstract = await ApprovalService._process_approval_content(approval, request)

        # 生成审批标题和摘要
        approval_type = ApprovalType(request.type)
        approval.title = f"{current_user.name} 提交的 {approval_type.description}"
        approval.abstract = abstract

        # 构建审批流程：根据部门层级确定审批人
        await ApprovalService._build_approval_process(approval, current_user_id)

        # 保存审批记录
        saved = await ApprovalRepository.create(approval)
        logger.info(f"创建审批成功: id={saved.id}")

        return str(saved.id)

    @staticmethod
    async def dispose(request: DisposeRequest, current_user: User) -> None:
        """
        处理审批（通过/拒绝/撤销）

        Args:
            request: 处理请求 DTO
            current_user: 当前用户

        Raises:
            ResourceNotFoundException: 审批记录不存在
            BusinessValidationException: 权限错误
        """
        logger.info(f"处理审批: approval_id={request.approval_id}, status={request.status}")

        current_user_id = str(current_user.id)

        # 查询审批记录
        approval = await ApprovalRepository.find_by_id(request.approval_id)
        if not approval:
            raise ResourceNotFoundException("审批记录不存在")

        # 处理撤销操作
        if request.status == ApprovalStatus.CANCEL.value:
            # 只有申请人才能撤销
            if current_user_id != approval.userId:
                raise BusinessValidationException("只有申请人才能撤销审批")
            approval.status = ApprovalStatus.CANCEL.value
            await ApprovalRepository.update(approval)
            logger.info(f"撤销审批成功: id={request.approval_id}")
            return

        # 验证当前用户是否为当前审批人
        if current_user_id != approval.approvalId:
            raise BusinessValidationException("您不是当前审批人")

        # 检查审批状态
        if approval.status == ApprovalStatus.CANCEL.value:
            raise BusinessValidationException("该审批已撤销")
        if approval.status == ApprovalStatus.PASS.value:
            raise BusinessValidationException("该审批已通过")
        if approval.status == ApprovalStatus.REFUSE.value:
            raise BusinessValidationException("该审批已拒绝")

        # 处理拒绝操作
        if request.status == ApprovalStatus.REFUSE.value:
            # 记录当前审批人的拒绝状态和原因
            if approval.approvers and approval.approvalIdx < len(approval.approvers):
                approval.approvers[approval.approvalIdx].status = ApprovalStatus.REFUSE.value
                approval.approvers[approval.approvalIdx].reason = request.reason
            approval.status = ApprovalStatus.REFUSE.value

        # 处理通过操作
        elif request.status == ApprovalStatus.PASS.value:
            # 记录当前审批人的通过状态和原因
            if approval.approvers and approval.approvalIdx < len(approval.approvers):
                approval.approvers[approval.approvalIdx].status = ApprovalStatus.PASS.value
                approval.approvers[approval.approvalIdx].reason = request.reason

                # 如果还有下一级审批人，则流转到下一级
                if len(approval.approvers) - 1 > approval.approvalIdx:
                    approval.approvalIdx += 1
                    approval.approvalId = approval.approvers[approval.approvalIdx].userId
                else:
                    # 检查是否所有审批人都已通过
                    all_passed = all(
                        a.status == ApprovalStatus.PASS.value
                        for a in approval.approvers
                    )
                    if all_passed:
                        approval.status = ApprovalStatus.PASS.value
                        # 设置完成时间戳
                        finish_time = int(time.time() * 1000)
                        approval.finishAt = finish_time
                        dt = datetime.now()
                        approval.finishDay = int(dt.strftime("%Y%m%d"))
                        approval.finishMonth = int(dt.strftime("%Y%m"))
                        approval.finishYeas = dt.year

        await ApprovalRepository.update(approval)
        logger.info(f"处理审批成功: id={request.approval_id}, status={request.status}")

    @staticmethod
    async def list(request: ApprovalListRequest, current_user: User) -> ApprovalListResponse:
        """
        审批列表查询

        Args:
            request: 审批列表请求 DTO
            current_user: 当前用户

        Returns:
            审批列表响应 DTO
        """
        logger.info(f"审批列表查询: page={request.page}, count={request.count}, type={request.type}")

        current_user_id = str(current_user.id)

        # 根据操作类型查询审批列表
        if request.type == 1:  # 我提交的
            approvals, total = await ApprovalRepository.find_by_user_id(
                current_user_id, request.page, request.count
            )
        elif request.type == 2:  # 待我审批的
            approvals, total = await ApprovalRepository.find_by_approval_id_and_status(
                current_user_id, ApprovalStatus.PROCESSED.value, request.page, request.count
            )
        else:  # 与我相关的所有审批
            approvals, total = await ApprovalRepository.find_by_participation_containing(
                current_user_id, request.page, request.count
            )

        # 构建响应列表
        data: List[ApprovalListItemResponse] = []
        for approval in approvals:
            leave_resp = None
            if approval.leave:
                leave_resp = LeaveResponse(
                    type=approval.leave.type,
                    start_time=approval.leave.startTime,
                    end_time=approval.leave.endTime,
                    reason=approval.leave.reason,
                    time_type=approval.leave.timeType,
                    duration=approval.leave.duration,
                )

            go_out_resp = None
            if approval.goOut:
                go_out_resp = GoOutResponse(
                    start_time=approval.goOut.startTime,
                    end_time=approval.goOut.endTime,
                    duration=approval.goOut.duration,
                    reason=approval.goOut.reason,
                )

            make_card_resp = None
            if approval.makeCard:
                make_card_resp = MakeCardResponse(
                    date=approval.makeCard.date,
                    reason=approval.makeCard.reason,
                    day=approval.makeCard.day,
                    check_type=approval.makeCard.checkType,
                )

            data.append(ApprovalListItemResponse(
                id=str(approval.id),
                no=approval.no,
                type=approval.type,
                status=approval.status,
                title=approval.title,
                abstract=approval.abstract,
                create_id=approval.userId,
                participating_id=approval.approvalId,
                create_at=approval.createAt,
                leave=leave_resp,
                go_out=go_out_resp,
                make_card=make_card_resp,
            ))

        return ApprovalListResponse(count=total, data=data)

    @staticmethod
    async def _process_approval_content(approval: Approval, request: ApprovalRequest) -> str:
        """
        处理审批内容并生成摘要
        """
        abstract = ""
        approval_type = ApprovalType(request.type)

        if approval_type == ApprovalType.LEAVE and request.leave:
            leave = request.leave
            # 计算时长
            if leave.time_type == 1:  # 小时
                duration = (leave.end_time - leave.start_time) / 3600.0
            else:  # 天
                duration = (leave.end_time - leave.start_time) / 86400.0

            approval.leave = Leave(
                type=leave.type,
                startTime=leave.start_time,
                endTime=leave.end_time,
                reason=leave.reason,
                timeType=leave.time_type,
                duration=duration,
            )

            leave_type = LeaveType(leave.type)
            abstract = f"【{leave_type.description}】: 【{ApprovalService._format_timestamp(leave.start_time)}】-【{ApprovalService._format_timestamp(leave.end_time)}】"
            approval.reason = leave.reason

        elif approval_type == ApprovalType.GO_OUT and request.go_out:
            go_out = request.go_out
            duration = (go_out.end_time - go_out.start_time) / 3600.0

            approval.goOut = GoOut(
                startTime=go_out.start_time,
                endTime=go_out.end_time,
                duration=duration,
                reason=go_out.reason,
            )

            abstract = f"【{ApprovalService._format_timestamp(go_out.start_time)}】-【{ApprovalService._format_timestamp(go_out.end_time)}】"
            approval.reason = go_out.reason

        elif approval_type == ApprovalType.MAKE_CARD and request.make_card:
            make_card = request.make_card
            approval.makeCard = MakeCard(
                date=make_card.date,
                reason=make_card.reason,
                day=make_card.day,
                checkType=make_card.check_type,
            )

            abstract = f"【{ApprovalService._format_timestamp(make_card.date)}】【{make_card.reason}】"
            approval.reason = make_card.reason

        else:
            approval.reason = request.reason
            abstract = request.abstract or ""

        return abstract

    @staticmethod
    async def _build_approval_process(approval: Approval, user_id: str) -> None:
        """
        构建审批流程：根据部门层级确定审批人
        """
        # 获取申请人所有关联的部门
        dep_users = await DepartmentUserRepository.find_by_user_id(user_id)
        if not dep_users:
            raise BusinessValidationException("用户未分配部门")

        # 获取所有这些部门的ID
        user_dep_ids = [du.depId for du in dep_users]

        # 查询所有这些部门的详细信息
        user_deps = await DepartmentRepository.find_by_ids(user_dep_ids)
        if not user_deps:
            raise BusinessValidationException("用户关联的部门不存在")

        # 找出层级最深的部门
        department = max(user_deps, key=lambda d: len(d.parentPath) if d.parentPath else 0)

        logger.info(f"用户 {user_id} 所属部门: {department.name}, ParentPath: {department.parentPath}")

        # 解析父级路径
        parent_ids = ApprovalService._parse_parent_path(department.parentPath)
        logger.info(f"解析的父级部门ID列表: {parent_ids}")

        # 查询所有父级部门
        parent_departments = await DepartmentRepository.find_by_ids(parent_ids)
        dep_map = {str(d.id): d for d in parent_departments}

        # 收集所有审批人用户ID
        leader_ids = [department.leaderId] if department.leaderId else []
        for parent_id in parent_ids[1:]:
            parent_dep = dep_map.get(parent_id)
            if parent_dep and parent_dep.leaderId:
                leader_ids.append(parent_dep.leaderId)

        # 查询所有审批人用户信息
        leaders = await UserRepository.find_by_ids(leader_ids)
        leader_map = {str(user.id): user for user in leaders}

        approvers: List[Approver] = []
        participations: List[str] = []

        # 添加直属部门负责人作为第一级审批人
        if department.leaderId:
            leader = leader_map.get(department.leaderId)
            first_approver = Approver(
                userId=department.leaderId,
                userName=leader.name if leader else "",
                status=ApprovalStatus.PROCESSED.value,
            )
            approvers.append(first_approver)
            participations.append(department.leaderId)
            logger.info(f"添加第一级审批人（直属部门负责人）: {department.leaderId}")

        participations.append(user_id)

        # 按部门层级从下到上添加审批人
        for i in range(len(parent_ids) - 1, 0, -1):
            parent_id = parent_ids[i]
            parent_dep = dep_map.get(parent_id)
            if parent_dep and parent_dep.leaderId:
                leader = leader_map.get(parent_dep.leaderId)
                approver = Approver(
                    userId=parent_dep.leaderId,
                    userName=leader.name if leader else "",
                    status=ApprovalStatus.NOT_STARTED.value,
                )
                approvers.append(approver)
                participations.append(parent_dep.leaderId)
                logger.info(f"添加上级审批人: 部门={parent_dep.name}, 领导={parent_dep.leaderId}")

        approval.approvers = approvers
        approval.participation = participations
        if approvers:
            approval.approvalId = approvers[0].userId
            approval.approvalIdx = 0

    @staticmethod
    def _parse_parent_path(parent_path: str) -> List[str]:
        """
        解析父级路径

        例如: ":root:dep1:dep2:" -> ["root", "dep1", "dep2"]
        """
        if not parent_path:
            return []
        return [p for p in parent_path.split(":") if p]

    @staticmethod
    def _format_timestamp(timestamp: int) -> str:
        """
        格式化时间戳为字符串
        """
        if not timestamp:
            return "未设置"
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime("%Y-%m-%d %H:%M")

    @staticmethod
    def _generate_random_no(width: int) -> str:
        """
        生成唯一审批编号

        格式：时间戳后8位 + 随机数，确保唯一性
        """
        timestamp_suffix = str(int(time.time() * 1000))[-8:]
        random_suffix = "".join(str(random.randint(0, 9)) for _ in range(width - 8))
        return timestamp_suffix + random_suffix