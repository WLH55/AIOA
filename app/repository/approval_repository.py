"""
审批数据访问层

提供审批相关的数据库操作方法
"""
import logging
from typing import Optional, List

from beanie import PydanticObjectId
from app.models.approval import Approval

logger = logging.getLogger(__name__)


class ApprovalRepository:
    """
    审批数据访问层

    封装所有审批相关的数据库操作
    """

    @staticmethod
    async def create(approval: Approval) -> Approval:
        """
        创建审批记录

        Args:
            approval: Approval 实体对象

        Returns:
            创建后的 Approval 对象
        """
        await approval.insert()
        logger.info(f"审批记录创建成功: {approval.no} (id={approval.id})")
        return approval

    @staticmethod
    async def find_by_id(approval_id: str) -> Optional[Approval]:
        """
        根据 ID 查询审批记录

        Args:
            approval_id: 审批 ID

        Returns:
            Approval 对象或 None
        """
        return await Approval.get(PydanticObjectId(approval_id))

    @staticmethod
    async def update(approval: Approval) -> Approval:
        """
        更新审批记录

        Args:
            approval: Approval 实体对象

        Returns:
            更新后的 Approval 对象
        """
        approval.update_timestamp()
        await approval.save()
        logger.info(f"审批记录更新成功: {approval.no} (id={approval.id})")
        return approval

    @staticmethod
    async def delete(approval_id: str) -> bool:
        """
        删除审批记录

        Args:
            approval_id: 审批 ID

        Returns:
            是否删除成功
        """
        approval = await ApprovalRepository.find_by_id(approval_id)
        if not approval:
            return False
        await approval.delete()
        logger.info(f"审批记录删除成功: id={approval_id}")
        return True

    @staticmethod
    async def find_by_user_id(
        user_id: str,
        page: int = 1,
        page_size: int = 10
    ) -> tuple[List[Approval], int]:
        """
        根据申请人ID分页查询审批列表

        Args:
            user_id: 申请人ID
            page: 页码
            page_size: 每页数量

        Returns:
            (审批列表, 总数)
        """
        skip = (page - 1) * page_size
        query = Approval.find(Approval.userId == user_id)
        total = await query.count()
        approvals = await query.skip(skip).limit(page_size).sort("-createAt").to_list()
        return approvals, total

    @staticmethod
    async def find_by_approval_id_and_status(
        approval_id: str,
        status: int,
        page: int = 1,
        page_size: int = 10
    ) -> tuple[List[Approval], int]:
        """
        根据当前审批人ID和状态分页查询审批列表

        Args:
            approval_id: 当前审批人ID
            status: 审批状态
            page: 页码
            page_size: 每页数量

        Returns:
            (审批列表, 总数)
        """
        skip = (page - 1) * page_size
        query = Approval.find(
            Approval.approvalId == approval_id,
            Approval.status == status
        )
        total = await query.count()
        approvals = await query.skip(skip).limit(page_size).sort("-createAt").to_list()
        return approvals, total

    @staticmethod
    async def find_by_participation_containing(
        user_id: str,
        page: int = 1,
        page_size: int = 10
    ) -> tuple[List[Approval], int]:
        """
        根据参与人员包含指定用户分页查询审批列表

        Args:
            user_id: 参与人员ID
            page: 页码
            page_size: 每页数量

        Returns:
            (审批列表, 总数)
        """
        skip = (page - 1) * page_size
        query = Approval.find({"participation": {"$in": [user_id]}})
        total = await query.count()
        approvals = await query.skip(skip).limit(page_size).sort("-createAt").to_list()
        return approvals, total

    @staticmethod
    async def find_by_ids(ids: List[str]) -> List[Approval]:
        """
        根据ID列表查询审批记录

        Args:
            ids: 审批ID列表

        Returns:
            审批列表
        """
        if not ids:
            return []
        object_ids = [PydanticObjectId(id) for id in ids if id]
        return await Approval.find({"_id": {"$in": object_ids}}).to_list()