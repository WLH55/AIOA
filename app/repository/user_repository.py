"""
用户数据访问层

提供用户相关的数据库操作方法
"""
import logging
from typing import Optional, List

from beanie import PydanticObjectId
from app.models.user import User

logger = logging.getLogger(__name__)


class UserRepository:
    """
    用户数据访问层

    封装所有用户相关的数据库操作
    """

    @staticmethod
    async def create(user: User) -> User:
        """
        创建用户

        Args:
            user: User 实体对象

        Returns:
            创建后的 User 对象（包含 _id）
        """
        await user.insert()
        logger.info(f"用户创建成功: {user.name} (id={user.id})")
        return user

    @staticmethod
    async def find_by_id(user_id: str) -> Optional[User]:
        """
        根据 ID 查询用户

        Args:
            user_id: 用户 ID

        Returns:
            User 对象或 None
        """
        return await User.get(user_id)

    @staticmethod
    async def find_by_name(name: str) -> Optional[User]:
        """
        根据用户名查询用户

        Args:
            name: 用户名

        Returns:
            User 对象或 None
        """
        return await User.find_one(User.name == name)

    @staticmethod
    async def update(user: User) -> User:
        """
        更新用户

        Args:
            user: User 实体对象

        Returns:
            更新后的 User 对象
        """
        user.update_timestamp()
        await user.save()
        logger.info(f"用户更新成功: {user.name} (id={user.id})")
        return user

    @staticmethod
    async def delete(user_id: str) -> bool:
        """
        删除用户

        Args:
            user_id: 用户 ID

        Returns:
            是否删除成功
        """
        user = await UserRepository.find_by_id(user_id)
        if not user:
            return False
        await user.delete()
        logger.info(f"用户删除成功: {user.name} (id={user_id})")
        return True

    @staticmethod
    async def exists_by_name(name: str) -> bool:
        """
        检查用户名是否已存在

        Args:
            name: 用户名

        Returns:
            是否存在
        """
        return await User.find_one(User.name == name) is not None

    @staticmethod
    async def find_all(page: int = 1, page_size: int = 10) -> tuple[List[User], int]:
        """
        分页查询所有用户

        Args:
            page: 页码（从1开始）
            page_size: 每页数量

        Returns:
            (用户列表, 总数)
        """
        skip = (page - 1) * page_size
        total = await User.find().count()
        users = await User.find().skip(skip).limit(page_size).sort("-createAt").to_list()
        return users, total

    @staticmethod
    async def find_by_ids(ids: List[str]) -> List[User]:
        """
        根据ID列表查询用户

        Args:
            ids: 用户ID列表

        Returns:
            用户列表
        """
        if not ids:
            return []
        object_ids = [PydanticObjectId(id) for id in ids if id]
        return await User.find({"_id": {"$in": object_ids}}).to_list()

    @staticmethod
    async def find_by_names(names: List[str]) -> List[User]:
        """
        根据用户名列表查询用户

        Args:
            names: 用户名列表

        Returns:
            用户列表
        """
        if not names:
            return []
        return await User.find({"name": {"$in": names}}).to_list()

    @staticmethod
    async def find_admin() -> Optional[User]:
        """
        查找管理员用户

        Returns:
            管理员用户或 None
        """
        return await User.find_one(User.isAdmin == True)

    @staticmethod
    async def find_by_status(status: int) -> List[User]:
        """
        根据状态查询用户

        Args:
            status: 状态值

        Returns:
            用户列表
        """
        return await User.find(User.status == status).to_list()