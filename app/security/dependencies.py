"""
认证依赖模块

提供 FastAPI 依赖注入函数，用于获取当前认证用户
"""
import logging
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.requests import Request

from app.models.user import User
from app.repository.user_repository import UserRepository
from app.security.jwt import decode_jwt

logger = logging.getLogger(__name__)

# HTTP Bearer 认证方案
security = HTTPBearer(auto_error=False)


class AuthError(Exception):
    """认证异常基类"""

    def __init__(self, message: str, code: int = 401):
        self.message = message
        self.code = code
        super().__init__(self.message)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> User:
    """
    获取当前认证用户

    从 Authorization Header 中提取 Bearer Token，验证并返回用户对象

    Args:
        credentials: HTTP Bearer 凭证

    Returns:
        当前认证的 User 对象

    Raises:
        HTTPException: 未认证或 Token 无效
    """
    # 检查是否提供了凭证
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    # 解码 JWT
    payload = decode_jwt(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 验证 Token 类型
    token_type = payload.get("type")
    if token_type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 获取用户 ID
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 查询用户
    user = await UserRepository.find_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 验证用户状态
    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is inactive or suspended",
        )

    return user


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[User]:
    """
    获取当前认证用户（可选）

    与 get_current_user 类似，但不强制要求认证

    Returns:
        当前认证的 User 对象或 None
    """
    if credentials is None:
        return None

    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None


def extract_token_from_header(authorization: Optional[str]) -> Optional[str]:
    """
    从 Authorization Header 提取 Token

    用于 WebSocket 连接等场景

    Args:
        authorization: Authorization Header 值

    Returns:
        Token 字符串或 None
    """
    if not authorization:
        return None

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None

    return parts[1]