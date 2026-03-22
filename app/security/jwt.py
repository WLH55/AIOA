"""
JWT Token 编解码模块

使用 HS256 算法生成和验证 JWT Token
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from jose import jwt, JWTError

from app.config.settings import settings

logger = logging.getLogger(__name__)

# JWT 配置常量
ALGORITHM = "HS256"
ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"


def create_access_token(
    user_id: str,
    username: str,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    生成 JWT Access Token

    Args:
        user_id: 用户 ID
        username: 用户名
        expires_delta: 过期时间增量，默认使用配置中的值

    Returns:
        JWT Token 字符串
    """
    if expires_delta is None:
        expires_delta = timedelta(days=settings.ACCESS_TOKEN_EXPIRE_DAYS)

    now = datetime.utcnow()
    expire = now + expires_delta

    payload = {
        "sub": user_id,
        "username": username,
        "type": ACCESS_TOKEN_TYPE,
        "exp": expire,
        "iat": now,
    }

    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)
    logger.debug(f"Access Token 生成成功: user_id={user_id}, expire={expire}")
    return token


def create_refresh_token(
    user_id: str,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    生成 JWT Refresh Token

    Args:
        user_id: 用户 ID
        expires_delta: 过期时间增量，默认使用配置中的值

    Returns:
        JWT Token 字符串
    """
    if expires_delta is None:
        expires_delta = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    now = datetime.utcnow()
    expire = now + expires_delta

    payload = {
        "sub": user_id,
        "type": REFRESH_TOKEN_TYPE,
        "exp": expire,
        "iat": now,
    }

    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)
    logger.debug(f"Refresh Token 生成成功: user_id={user_id}, expire={expire}")
    return token


def decode_jwt(token: str) -> Optional[Dict[str, Any]]:
    """
    解码并验证 JWT Token

    Args:
        token: JWT Token 字符串

    Returns:
        解码后的 payload 字典，验证失败返回 None
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[ALGORITHM]
        )
        return payload
    except JWTError as e:
        logger.warning(f"JWT 解码失败: {e}")
        return None


def get_token_payload(token: str) -> Optional[Dict[str, Any]]:
    """
    获取 Token Payload（不验证过期时间）

    用于调试或特殊场景

    Args:
        token: JWT Token 字符串

    Returns:
        payload 字典
    """
    try:
        # 不验证过期时间
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[ALGORITHM],
            options={"verify_exp": False}
        )
        return payload
    except JWTError as e:
        logger.warning(f"JWT 解码失败: {e}")
        return None