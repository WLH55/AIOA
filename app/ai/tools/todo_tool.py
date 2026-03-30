"""
待办管理工具

提供创建待办和查询待办的能力，通过闭包注入当前用户上下文
"""
import logging
import uuid
from typing import List, Optional

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from app.models.todo import Todo, UserTodo
from app.models.enums.todo_status import TodoStatus
from app.repository.todo_repository import TodoRepository
from app.repository.user_repository import UserRepository

logger = logging.getLogger(__name__)


class CreateTodoInput(BaseModel):
    """创建待办输入"""
    title: str = Field(..., description="待办标题")
    desc: str = Field(default="", description="待办描述")
    deadline: str = Field(default="", description="截止时间戳（毫秒字符串），为空则无截止时间")
    executorNames: List[str] = Field(default_factory=list, description="执行人，可以是用户名或用户ID列表，为空则为当前用户")


class FindTodosInput(BaseModel):
    """查询待办输入"""
    startTime: str = Field(default="", description="开始时间戳（毫秒字符串），为空则不限")
    endTime: str = Field(default="", description="结束时间戳（毫秒字符串），为空则不限")


def _make_create_todo(user_id: str, user_name: str):
    """
    创建待办工具的工厂函数

    Args:
        user_id: 当前用户 ID
        user_name: 当前用户名
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
        # 解析执行人：区分用户名和用户ID
        execute_user_ids = []
        execute_user_names = []
        for name_or_id in executorNames:
            if len(name_or_id) == 24 and name_or_id.isalnum():
                # 视为用户 ID
                execute_user_ids.append(name_or_id)
            else:
                # 视为用户名，查找用户 ID
                user = await UserRepository.find_by_name(name_or_id)
                if user:
                    execute_user_ids.append(str(user.id))
                    execute_user_names.append(user.name)
                else:
                    return f"未找到用户：{name_or_id}"
        # 默认执行人为当前用户
        if not execute_user_ids:
            execute_user_ids = [user_id]
            execute_user_names = [user_name]
        # 如果有未获取名字的用户，批量查询
        if len(execute_user_names) < len(execute_user_ids):
            users = await UserRepository.find_by_ids(execute_user_ids)
            user_map = {str(u.id): u.name for u in users}
            execute_user_names = [user_map.get(uid, uid) for uid in execute_user_ids]
        # 创建执行人列表
        executes = []
        for uid, uname in zip(execute_user_ids, execute_user_names):
            executes.append(UserTodo(
                id=str(uuid.uuid4()),
                userId=uid,
                userName=uname,
                todoId="",
                todoStatus=TodoStatus.PENDING.value,
            ))
        # 解析截止时间
        deadline_at = int(deadline) if deadline and deadline.isdigit() else None
        # 创建待办
        todo = Todo(
            creatorId=user_id,
            title=title,
            desc=desc or None,
            deadlineAt=deadline_at,
            executes=executes,
            todoStatus=TodoStatus.PENDING.value,
        )
        saved = await TodoRepository.create(todo)
        todo_id = str(saved.id)
        # 更新执行人的 todoId
        for exec_item in saved.executes:
            exec_item.todoId = todo_id
        await saved.save()
        # 格式化结果
        executor_str = "、".join(execute_user_names)
        result = f"待办创建成功！标题：{title}"
        if deadline_at:
            from datetime import datetime, timezone, timedelta
            cst = timezone(timedelta(hours=8))
            dt = datetime.fromtimestamp(deadline_at / 1000, tz=cst)
            result += f"，截止时间：{dt.strftime('%Y-%m-%d %H:%M')}"
        result += f"，执行人：{executor_str}，待办ID：{todo_id[:12]}..."
        return result
    return _create_todo


def _make_find_todos(user_id: str, _user_name: str):
    """
    查询待办工具的工厂函数

    Args:
        user_id: 当前用户 ID
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
                user_id, start, end,
            )
        else:
            todos, total = await TodoRepository.find_by_execute_user_id(user_id)
        if not todos:
            return "暂无待办事项"
        status_map = {1: "待处理", 2: "进行中", 3: "已完成", 4: "已取消", 5: "已超时"}
        lines = [f"找到 {total} 条待办："]
        for i, todo in enumerate(todos[:10], 1):
            status_text = status_map.get(todo.todoStatus, "未知")
            line = f"{i}. {todo.title} - {status_text}"
            if todo.deadlineAt:
                from datetime import datetime, timezone, timedelta
                cst = timezone(timedelta(hours=8))
                dt = datetime.fromtimestamp(todo.deadlineAt / 1000, tz=cst)
                line += f" - 截止：{dt.strftime('%Y-%m-%d %H:%M')}"
            lines.append(line)
        return "\n".join(lines)
    return _find_todos


def get_todo_tools(user_id: str, user_name: str) -> List[StructuredTool]:
    """
    获取待办管理工具列表

    Args:
        user_id: 当前用户 ID
        user_name: 当前用户名

    Returns:
        工具列表
    """
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
