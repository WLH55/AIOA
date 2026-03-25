"""
群组数据访问层

提供群组相关的数据库操作方法
"""
import logging
from typing import Optional, List

from beanie import PydanticObjectId
from app.models.group import Group

logger = logging.getLogger(__name__)


class GroupRepository:
    """
    群组数据访问层

    封装所有群组相关的数据库操作
    """

    @staticmethod
    async def create(group: Group) -> Group:
        """
        创建群组

        Args:
            group: Group 实体对象

        Returns:
            创建后的 Group 对象
        """
        await group.insert()
        logger.info(f"群组创建成功: id={group.id}, name={group.name}")
        return group

    @staticmethod
    async def find_by_id(group_id: str) -> Optional[Group]:
        """
        根据 ID 查询群组

        Args:
            group_id: 群组 ID

        Returns:
            Group 对象或 None
        """
        return await Group.get(group_id)

    @staticmethod
    async def find_by_member_id(
        member_id: str,
        status: Optional[int] = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[Group], int]:
        """
        根据成员ID分页查询群组列表

        Args:
            member_id: 成员ID
            status: 状态筛选（可选）
            page: 页码
            page_size: 每页数量

        Returns:
            (群组列表, 总数)
        """
        skip = (page - 1) * page_size
        conditions = [Group.memberIds == member_id]
        if status is not None:
            conditions.append(Group.status == status)

        query = Group.find(*conditions)
        total = await query.count()
        groups = await query.skip(skip).limit(page_size).sort("-createAt").to_list()
        return groups, total

    @staticmethod
    async def update(group: Group) -> Group:
        """
        更新群组

        Args:
            group: Group 实体对象

        Returns:
            更新后的 Group 对象
        """
        await group.save()
        logger.info(f"群组更新成功: id={group.id}")
        return group

    @staticmethod
    async def delete(group_id: str) -> bool:
        """
        删除群组

        Args:
            group_id: 群组 ID

        Returns:
            是否删除成功
        """
        group = await GroupRepository.find_by_id(group_id)
        if not group:
            return False
        await group.delete()
        logger.info(f"群组删除成功: id={group_id}")
        return True
