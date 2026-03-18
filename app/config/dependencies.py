"""
依赖注入模块
"""
from typing import Annotated, Optional
from fastapi import Depends


# 示例：获取当前用户
async def get_current_user():
    """获取当前登录用户（示例）"""
    # TODO: 实现用户认证逻辑
    return None


# 类型别名（简化使用）
CurrentUserDep = Annotated[Optional[str], Depends(get_current_user)]
