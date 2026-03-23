"""
用户数据访问层

提供用户相关的数据库操作方法
"""
import logging
from typing import Optional

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