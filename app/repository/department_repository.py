"""
部门数据访问层

提供部门相关的数据库操作方法
"""
import logging
from typing import Optional, List

from beanie import PydanticObjectId
from app.models.department import Department

logger = logging.getLogger(__name__)


class DepartmentRepository:
    """
    部门数据访问层

    封装所有部门相关的数据库操作
    """

    @staticmethod
    async def create(department: Department) -> Department:
        """
        创建部门

        Args:
            department: Department 实体对象

        Returns:
            创建后的 Department 对象
        """
        await department.insert()
        logger.info(f"部门创建成功: {department.name} (id={department.id})")
        return department

    @staticmethod
    async def find_by_id(department_id: str) -> Optional[Department]:
        """
        根据 ID 查询部门

        Args:
            department_id: 部门 ID

        Returns:
            Department 对象或 None
        """
        return await Department.get(PydanticObjectId(department_id))

    @staticmethod
    async def update(department: Department) -> Department:
        """
        更新部门

        Args:
            department: Department 实体对象

        Returns:
            更新后的 Department 对象
        """
        department.update_timestamp()
        await department.save()
        logger.info(f"部门更新成功: {department.name} (id={department.id})")
        return department

    @staticmethod
    async def delete(department_id: str) -> bool:
        """
        删除部门

        Args:
            department_id: 部门 ID

        Returns:
            是否删除成功
        """
        department = await DepartmentRepository.find_by_id(department_id)
        if not department:
            return False
        await department.delete()
        logger.info(f"部门删除成功: id={department_id}")
        return True

    @staticmethod
    async def find_all() -> List[Department]:
        """
        查询所有部门

        Returns:
            部门列表
        """
        return await Department.find().to_list()

    @staticmethod
    async def find_by_name(name: str) -> Optional[Department]:
        """
        根据名称查询部门

        Args:
            name: 部门名称

        Returns:
            Department 对象或 None
        """
        return await Department.find_one(Department.name == name)

    @staticmethod
    async def find_by_ids(ids: List[str]) -> List[Department]:
        """
        根据ID列表查询部门

        Args:
            ids: 部门ID列表

        Returns:
            部门列表
        """
        if not ids:
            return []
        object_ids = [PydanticObjectId(id) for id in ids if id]
        return await Department.find({"_id": {"$in": object_ids}}).to_list()

    @staticmethod
    async def find_by_parent_id(parent_id: str) -> List[Department]:
        """
        根据父部门ID查询子部门

        Args:
            parent_id: 父部门ID

        Returns:
            子部门列表
        """
        return await Department.find(Department.parentId == parent_id).to_list()