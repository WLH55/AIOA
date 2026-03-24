"""
部门用户关联数据访问层

提供部门用户关联相关的数据库操作方法
"""
import logging
from typing import Optional, List

from beanie import PydanticObjectId
from app.models.department_user import DepartmentUser

logger = logging.getLogger(__name__)


class DepartmentUserRepository:
    """
    部门用户关联数据访问层

    封装所有部门用户关联相关的数据库操作
    """

    @staticmethod
    async def create(department_user: DepartmentUser) -> DepartmentUser:
        """
        创建部门用户关联

        Args:
            department_user: DepartmentUser 实体对象

        Returns:
            创建后的 DepartmentUser 对象
        """
        await department_user.insert()
        logger.info(f"部门用户关联创建成功: depId={department_user.depId}, userId={department_user.userId}")
        return department_user

    @staticmethod
    async def find_by_id(du_id: str) -> Optional[DepartmentUser]:
        """
        根据 ID 查询部门用户关联

        Args:
            du_id: 关联 ID

        Returns:
            DepartmentUser 对象或 None
        """
        return await DepartmentUser.get(PydanticObjectId(du_id))

    @staticmethod
    async def delete(du_id: str) -> bool:
        """
        删除部门用户关联

        Args:
            du_id: 关联 ID

        Returns:
            是否删除成功
        """
        du = await DepartmentUserRepository.find_by_id(du_id)
        if not du:
            return False
        await du.delete()
        logger.info(f"部门用户关联删除成功: id={du_id}")
        return True

    @staticmethod
    async def find_by_dep_id(dep_id: str) -> List[DepartmentUser]:
        """
        根据部门ID查询所有用户关联

        Args:
            dep_id: 部门ID

        Returns:
            部门用户关联列表
        """
        return await DepartmentUser.find(DepartmentUser.depId == dep_id).to_list()

    @staticmethod
    async def find_by_user_id(user_id: str) -> List[DepartmentUser]:
        """
        根据用户ID查询所有部门关联

        Args:
            user_id: 用户ID

        Returns:
            部门用户关联列表
        """
        return await DepartmentUser.find(DepartmentUser.userId == user_id).to_list()

    @staticmethod
    async def find_all() -> List[DepartmentUser]:
        """
        查询所有部门用户关联

        Returns:
            部门用户关联列表
        """
        return await DepartmentUser.find().to_list()

    @staticmethod
    async def exists_by_dep_and_user(dep_id: str, user_id: str) -> bool:
        """
        检查部门用户关联是否存在

        Args:
            dep_id: 部门ID
            user_id: 用户ID

        Returns:
            是否存在
        """
        return await DepartmentUser.find_one(
            DepartmentUser.depId == dep_id,
            DepartmentUser.userId == user_id
        ) is not None