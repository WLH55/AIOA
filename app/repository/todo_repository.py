"""
待办事项数据访问层

提供待办事项相关的数据库操作方法
"""
import logging
from typing import Optional, List

from beanie import PydanticObjectId
from app.models.todo import Todo, UserTodo

logger = logging.getLogger(__name__)


class TodoRepository:
    """
    待办事项数据访问层

    封装所有待办事项相关的数据库操作
    """

    @staticmethod
    async def create(todo: Todo) -> Todo:
        """
        创建待办事项

        Args:
            todo: Todo 实体对象

        Returns:
            创建后的 Todo 对象
        """
        await todo.insert()
        logger.info(f"待办事项创建成功: {todo.title} (id={todo.id})")
        return todo

    @staticmethod
    async def find_by_id(todo_id: str) -> Optional[Todo]:
        """
        根据 ID 查询待办事项

        Args:
            todo_id: 待办事项 ID

        Returns:
            Todo 对象或 None
        """
        return await Todo.get(PydanticObjectId(todo_id))

    @staticmethod
    async def update(todo: Todo) -> Todo:
        """
        更新待办事项

        Args:
            todo: Todo 实体对象

        Returns:
            更新后的 Todo 对象
        """
        todo.update_timestamp()
        await todo.save()
        logger.info(f"待办事项更新成功: {todo.title} (id={todo.id})")
        return todo

    @staticmethod
    async def delete(todo_id: str) -> bool:
        """
        删除待办事项

        Args:
            todo_id: 待办事项 ID

        Returns:
            是否删除成功
        """
        todo = await TodoRepository.find_by_id(todo_id)
        if not todo:
            return False
        await todo.delete()
        logger.info(f"待办事项删除成功: id={todo_id}")
        return True

    @staticmethod
    async def find_by_creator_id(
        creator_id: str,
        page: int = 1,
        page_size: int = 10
    ) -> tuple[List[Todo], int]:
        """
        根据创建者ID分页查询待办事项

        Args:
            creator_id: 创建者ID
            page: 页码
            page_size: 每页数量

        Returns:
            (待办列表, 总数)
        """
        skip = (page - 1) * page_size
        query = Todo.find(Todo.creatorId == creator_id)
        total = await query.count()
        todos = await query.skip(skip).limit(page_size).sort("-createAt").to_list()
        return todos, total

    @staticmethod
    async def find_by_execute_user_id(
        user_id: str,
        page: int = 1,
        page_size: int = 10
    ) -> tuple[List[Todo], int]:
        """
        根据执行人ID分页查询待办事项

        Args:
            user_id: 执行人ID
            page: 页码
            page_size: 每页数量

        Returns:
            (待办列表, 总数)
        """
        skip = (page - 1) * page_size
        # 查询 executes 数组中包含指定用户ID的待办
        query = Todo.find(Todo.executes.userId == user_id)
        total = await query.count()
        todos = await query.skip(skip).limit(page_size).sort("-createAt").to_list()
        return todos, total

    @staticmethod
    async def find_by_execute_user_id_and_time_range(
        user_id: str,
        start_time: int,
        end_time: int,
        page: int = 1,
        page_size: int = 10
    ) -> tuple[List[Todo], int]:
        """
        根据执行人ID和时间范围分页查询待办事项

        Args:
            user_id: 执行人ID
            start_time: 开始时间戳(毫秒)
            end_time: 结束时间戳(毫秒)
            page: 页码
            page_size: 每页数量

        Returns:
            (待办列表, 总数)
        """
        skip = (page - 1) * page_size
        # 查询 executes 数组中包含指定用户ID且在时间范围内的待办
        query = Todo.find(
            Todo.executes.userId == user_id,
            Todo.createAt >= start_time,
            Todo.createAt <= end_time
        )
        total = await query.count()
        todos = await query.skip(skip).limit(page_size).sort("-createAt").to_list()
        return todos, total