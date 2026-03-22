"""
密码哈希模块

使用 bcrypt 算法进行密码哈希和验证
"""
import logging
from passlib.context import CryptContext

logger = logging.getLogger(__name__)

# 密码哈希上下文配置
# bcrypt work factor = 12，平衡安全性和性能
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12
)


def hash_password(password: str) -> str:
    """
    生成密码哈希值

    Args:
        password: 明文密码

    Returns:
        密码哈希字符串（格式: $2b$12$...）
    """
    password_hash = pwd_context.hash(password)
    logger.debug("密码哈希生成成功")
    return password_hash


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码

    Args:
        plain_password: 明文密码
        hashed_password: 密码哈希值

    Returns:
        密码是否匹配
    """
    result = pwd_context.verify(plain_password, hashed_password)
    if result:
        logger.debug("密码验证成功")
    else:
        logger.debug("密码验证失败")
    return result