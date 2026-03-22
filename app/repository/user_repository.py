"""
用户数据访问层

提供用户相关的数据库操作方法
"""
import logging
from typing import Optional
from bson import ObjectId

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
        logger.info(f"用户创建成功: {user.username} (id={user.id})")
        return user

    @staticmethod
    async def find_by_id(user_id: str) -> Optional[User]:
        """
        根据 ID 查询用户

        Args:
            user_id: 用户 ID（字符串形式的 ObjectId）

        Returns:
            User 对象或 None
        """
        if not ObjectId.is_valid(user_id):
            return None
        return await User.find_one(User.id == ObjectId(user_id))

    @staticmethod
    async def find_by_username(username: str) -> Optional[User]:
        """
        根据用户名查询用户

        Args:
            username: 用户名

        Returns:
            User 对象或 None
        """
        return await User.find_one(User.username == username)

    @staticmethod
    async def find_by_email(email: str) -> Optional[User]:
        """
        根据邮箱查询用户

        Args:
            email: 邮箱地址

        Returns:
            User 对象或 None
        """
        return await User.find_one(User.email == email)

    @staticmethod
    async def find_by_username_or_email(identifier: str) -> Optional[User]:
        """
        根据用户名或邮箱查询用户

        用于支持用户名/邮箱登录

        Args:
            identifier: 用户名或邮箱

        Returns:
            User 对象或 None
        """
        # 先尝试用户名查询
        user = await UserRepository.find_by_username(identifier)
        if user:
            return user
        # 再尝试邮箱查询
        return await UserRepository.find_by_email(identifier)

    @staticmethod
    async def find_by_employee_id(employee_id: str) -> Optional[User]:
        """
        根据工号查询用户

        Args:
            employee_id: 工号

        Returns:
            User 对象或 None
        """
        return await User.find_one(User.employee_id == employee_id)

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
        logger.info(f"用户更新成功: {user.username} (id={user.id})")
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
        logger.info(f"用户删除成功: {user.username} (id={user_id})")
        return True

    @staticmethod
    async def exists_by_username(username: str) -> bool:
        """
        检查用户名是否已存在

        Args:
            username: 用户名

        Returns:
            是否存在
        """
        return await User.find_one(User.username == username) is not None

    @staticmethod
    async def exists_by_email(email: str) -> bool:
        """
        检查邮箱是否已存在

        Args:
            email: 邮箱地址

        Returns:
            是否存在
        """
        return await User.find_one(User.email == email) is not None