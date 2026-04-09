"""
Redis 客户端全局访问

提供 Redis 客户端的全局引用，供工具层等非请求上下文模块访问。
在应用启动时由 main.py 设置。
"""
import redis.asyncio as redis

# 全局 Redis 客户端引用
_redis_client: redis.Redis = None


def set_redis_client(client: redis.Redis) -> None:
    """
    设置全局 Redis 客户端（应用启动时调用）

    Args:
        client: Redis 异步客户端
    """
    global _redis_client
    _redis_client = client


async def get_redis_client() -> redis.Redis:
    """
    获取全局 Redis 客户端

    Returns:
        Redis 异步客户端，未初始化时返回 None
    """
    return _redis_client
