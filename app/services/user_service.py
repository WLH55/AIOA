"""
用户服务层

处理用户相关的业务逻辑
"""
import logging
from typing import Optional

from app.config.exceptions import BusinessValidationException, ResourceNotFoundException
from app.config.settings import settings
from app.models.user import User
from app.repository.user_repository import UserRepository
from app.security.password import hash_password, verify_password
from app.security.jwt import create_access_token, create_refresh_token
from app.dto.user.user_request import UserRequest, UserListRequest, UpdatePasswordRequest
from app.dto.user.user_response import UserResponse, UserListResponse

logger = logging.getLogger(__name__)


class UserService:
    """
    用户服务类

    提供用户 CRUD、登录、修改密码等业务逻辑
    """

    @staticmethod
    async def info(user_id: str) -> UserResponse:
        """
        获取用户信息

        Args:
            user_id: 用户ID

        Returns:
            用户响应 DTO

        Raises:
            ResourceNotFoundException: 用户不存在
        """
        user = await UserRepository.find_by_id(user_id)
        if not user:
            raise ResourceNotFoundException("用户不存在")

        return UserResponse.from_user(user)

    @staticmethod
    async def create(request: UserRequest, current_user: User) -> None:
        """
        创建用户

        Args:
            request: 用户请求 DTO
            current_user: 当前操作用户

        Raises:
            BusinessValidationException: 用户名已存在
        """
        # 检查用户名是否已存在
        if await UserRepository.exists_by_name(request.name):
            raise BusinessValidationException("已存在该用户")

        # 设置默认密码
        password = request.password or "123456"

        # 创建用户实体
        user = User(
            name=request.name,
            password=hash_password(password),
            status=request.status if request.status is not None else 0,  # 默认正常状态
            isAdmin=False,
        )

        await UserRepository.create(user)
        logger.info(f"创建用户成功: {user.name}")

    @staticmethod
    async def edit(request: UserRequest, current_user: User) -> None:
        """
        编辑用户

        Args:
            request: 用户请求 DTO
            current_user: 当前操作用户

        Raises:
            ResourceNotFoundException: 用户不存在
            BusinessValidationException: 用户名已被占用或无权限
        """
        if not request.id:
            raise BusinessValidationException("用户ID不能为空")

        # 权限校验：管理员可编辑任意用户，普通用户只能编辑自己
        if not current_user.isAdmin and str(current_user.id) != request.id:
            raise BusinessValidationException("无权限操作该用户")

        user = await UserRepository.find_by_id(request.id)
        if not user:
            raise ResourceNotFoundException("用户不存在")

        # 如果用户名有变化，检查新用户名是否已被使用
        if request.name and request.name != user.name:
            existing_user = await UserRepository.find_by_name(request.name)
            if existing_user and str(existing_user.id) != request.id:
                raise BusinessValidationException("用户名已被占用")
            user.name = request.name

        # 更新密码
        if request.password:
            user.password = hash_password(request.password)

        # 更新状态（仅管理员可修改）
        if request.status is not None:
            if not current_user.isAdmin:
                raise BusinessValidationException("无权限修改用户状态")
            user.status = request.status

        await UserRepository.update(user)
        logger.info(f"编辑用户成功: {user.name}")

    @staticmethod
    async def delete(user_id: str, current_user: User) -> None:
        """
        删除用户

        Args:
            user_id: 用户ID
            current_user: 当前操作用户

        Raises:
            ResourceNotFoundException: 用户不存在
            BusinessValidationException: 无权限或不能删除自己
        """
        # 权限校验：仅管理员可删除用户
        if not current_user.isAdmin:
            raise BusinessValidationException("无权限删除用户")

        # 不能删除自己
        if str(current_user.id) == user_id:
            raise BusinessValidationException("不能删除自己的账户")

        user = await UserRepository.find_by_id(user_id)
        if not user:
            raise ResourceNotFoundException("用户不存在")

        await UserRepository.delete(user_id)
        logger.info(f"删除用户成功: {user.name}")

    @staticmethod
    async def list(request: UserListRequest) -> UserListResponse:
        """
        用户列表查询

        Args:
            request: 用户列表请求 DTO

        Returns:
            用户列表响应 DTO
        """
        users = []
        count = 0

        # 根据条件查询
        if request.ids:
            # 按ID列表查询
            users = await UserRepository.find_by_ids(request.ids)
            count = len(users)
        elif request.name:
            # 按用户名查询
            user = await UserRepository.find_by_name(request.name)
            if user:
                users = [user]
                count = 1
        else:
            # 分页查询所有用户
            users, count = await UserRepository.find_all(request.page, request.count)

        # 转换为响应对象
        user_responses = [UserResponse.from_user(user) for user in users]

        return UserListResponse(
            count=count,
            data=user_responses,
        )

    @staticmethod
    async def update_password(request: UpdatePasswordRequest, current_user: User) -> None:
        """
        修改密码

        Args:
            request: 修改密码请求 DTO
            current_user: 当前操作用户

        Raises:
            ResourceNotFoundException: 用户不存在
            BusinessValidationException: 原密码错误或无权限
        """
        # 权限校验：管理员可修改任意用户密码，普通用户只能修改自己密码
        if not current_user.isAdmin and str(current_user.id) != request.id:
            raise BusinessValidationException("无权限修改该用户密码")

        user = await UserRepository.find_by_id(request.id)
        if not user:
            raise ResourceNotFoundException("用户不存在")

        # 验证原密码（管理员修改他人密码时无需验证原密码）
        if str(current_user.id) == request.id:
            if not verify_password(request.old_pwd, user.password):
                raise BusinessValidationException("原密码错误")

        # 更新密码
        user.password = hash_password(request.new_pwd)
        await UserRepository.update(user)
        logger.info(f"修改密码成功: {user.name}")

    @staticmethod
    async def init_admin_user() -> None:
        """
        初始化系统管理员用户

        如果不存在管理员用户，则创建默认管理员
        """
        # 检查是否已存在管理员用户
        admin = await UserRepository.find_admin()
        if admin:
            logger.info("管理员用户已存在")
            return

        # 创建默认管理员用户
        admin = User(
            name="root",
            password=hash_password("123456"),
            status=0,
            isAdmin=True,
        )

        await UserRepository.create(admin)
        logger.info("初始化管理员用户成功")

    @staticmethod
    async def get_user_id_by_name(name: str) -> Optional[str]:
        """
        根据用户名获取用户ID

        Args:
            name: 用户名

        Returns:
            用户ID，如果找不到返回 None
        """
        if not name or not name.strip():
            return None

        user = await UserRepository.find_by_name(name.strip())
        if user:
            logger.debug(f"找到用户: name={name}, id={user.id}")
            return str(user.id)

        logger.debug(f"未找到用户: name={name}")
        return None