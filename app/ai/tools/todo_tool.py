"""
待办管理工具

提供创建待办和查询待办的能力，通过闭包注入当前用户上下文
"""
import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any

from langchain_core.tools import StructuredTool, BaseTool
from pydantic import BaseModel, Field

from app.ai.tools.base import ToolProvider
from app.models.todo import Todo, UserTodo
from app.models.enums.todo_status import TodoStatus
from app.repository.todo_repository import TodoRepository
from app.repository.user_repository import UserRepository

logger = logging.getLogger(__name__)


_CST = timezone(timedelta(hours=8))


class CreateTodoInput(BaseModel):
    """创建待办输入"""
    title: str = Field(..., description="待办标题")
    desc: str = Field(default="", description="待办描述")
    deadline: str = Field(default="", description="截止时间戳（毫秒字符串），为空则无截止时间")
    executorNames: List[str] = Field(default_factory=list, description="执行人列表，可以是用户名或用户ID")


class FindTodosInput(BaseModel):
    """查询待办输入"""
    startTime: str = Field(default="", description="开始时间戳（毫秒字符串），为空则不限")
    endTime: str = Field(default="", description="结束时间戳（毫秒字符串），为空则不限")


def _make_create_todo(userId: str, userName: str):
    """
    创建待办工具的工厂函数

    Args:
        userId: 当前用户 ID
        userName: 当前用户名
    """
    async def _create_todo(
        title: str,
        desc: str = "",
        deadline: str = "",
        executorNames: Optional[List[str]] = None,
    ) -> str:
        """
        创建待办事项

        Args:
            title: 待办标题
            desc: 待办描述
            deadline: 截止时间戳（毫秒字符串）
            executorNames: 执行人列表（用户名或用户ID）

        Returns:
            格式化的创建结果
        """
        if executorNames is None:
            executorNames = []
        executeUserIds = []
        executeUserNames = []
        for nameOrId in executorNames:
            if len(nameOrId) == 24 and nameOrId.isalnum():
                executeUserIds.append(nameOrId)
            else:
                user = await UserRepository.find_by_name(nameOrId)
                if user:
                    executeUserIds.append(str(user.id))
                    executeUserNames.append(user.name)
                else:
                    return f"未找到用户：{nameOrId}"
        if not executeUserIds:
            executeUserIds = [userId]
            executeUserNames = [userName]
        if len(executeUserNames) < len(executeUserIds):
            users = await UserRepository.find_by_ids(executeUserIds)
            userMap = {str(u.id): u.name for u in users}
            executeUserNames = [userMap.get(uid, uid) for uid in executeUserIds]
        executes = []
        for uid, uname in zip(executeUserIds, executeUserNames):
            executes.append(UserTodo(
                id=str(uuid.uuid4()),
                userId=uid,
                userName=uname,
                todoId="",
                todoStatus=TodoStatus.PENDING.value,
            ))
        deadlineAt = int(deadline) if deadline and deadline.isdigit() else None
        todo = Todo(
            creatorId=userId,
            title=title,
            desc=desc or None,
            deadlineAt=deadlineAt,
            executes=executes,
            todoStatus=TodoStatus.PENDING.value,
        )
        saved = await TodoRepository.create(todo)
        todoId = str(saved.id)
        for execItem in saved.executes:
            execItem.todoId = todoId
        await saved.save()
        executorStr = "、".join(executeUserNames)
        result = f"待办创建成功！标题：{title}"
        if deadlineAt:
            dt = datetime.fromtimestamp(deadlineAt / 1000, tz=_CST)
            result += f"，截止时间：{dt.strftime('%Y-%m-%d %H:%M')}"
        result += f"，执行人：{executorStr}，待办ID：{todoId[:12]}..."
        return result
    return _create_todo


def _make_find_todos(userId: str, userName: str):
    """
    查询待办工具的工厂函数

    Args:
        userId: 当前用户 ID
        userName: 当前用户名
    """
    async def _find_todos(startTime: str = "", endTime: str = "") -> str:
        """
        查询当前用户的待办列表

        Args:
            startTime: 开始时间戳（毫秒字符串）
            endTime: 结束时间戳（毫秒字符串）

        Returns:
            格式化的待办列表
        """
        start = int(startTime) if startTime and startTime.isdigit() else None
        end = int(endTime) if endTime and endTime.isdigit() else None
        if start and end:
            todos, total = await TodoRepository.find_by_execute_user_id_and_time_range(
                userId, start, end,
            )
        else:
            todos, total = await TodoRepository.find_by_execute_user_id(userId)
        if not todos:
            return "暂无待办事项"
        statusMap = {1: "待处理", 2: "进行中", 3: "已完成", 4: "已取消", 5: "已超时"}
        lines = [f"找到 {total} 条待办："]
        for i, todo in enumerate(todos[:10], 1):
            statusText = statusMap.get(todo.todoStatus, "未知")
            line = f"{i}. {todo.title} - {statusText}"
            if todo.deadlineAt:
                dt = datetime.fromtimestamp(todo.deadlineAt / 1000, tz=_CST)
                line += f" - 截止：{dt.strftime('%Y-%m-%d %H:%M')}"
            lines.append(line)
        return "\n".join(lines)
    return _find_todos


class TodoToolProvider(ToolProvider):
    """待办管理工具提供者"""

    name = "todo"
    description = "待办管理工具"
    requires_context = True
    category = "business"

    def get_tools(
        self,
        user_id: str = None,
        user_name: str = None,
        context: Dict[str, Any] = None,
    ) -> List[BaseTool]:
        """
        获取待办管理工具列表

        Args:
            user_id: 当前用户 ID
            user_name: 当前用户名
            context: 额外上下文信息（未使用）

        Returns:
            工具列表
        """
        if not user_id or not user_name:
            return []
        return [
            StructuredTool.from_function(
                coroutine=_make_create_todo(user_id, user_name),
                name="createTodo",
                description=(
                    "创建待办事项。支持指定标题、描述、截止时间和执行人。"
                    "执行人可以是用户名（如'张三'）或用户ID。"
                    "未指定执行人时默认为当前用户。"
                ),
                args_schema=CreateTodoInput,
            ),
            StructuredTool.from_function(
                coroutine=_make_find_todos(user_id, user_name),
                name="findTodos",
                description="查询当前用户的待办事项列表。可选按时间范围过滤。",
                args_schema=FindTodosInput,
            ),
        ]


# 模块导入时自动注册
TodoToolProvider().register()