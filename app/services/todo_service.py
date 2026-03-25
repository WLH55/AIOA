"""
待办事项服务层

处理待办事项相关的业务逻辑
"""
import logging
import time
import uuid
from typing import List, Set

from app.config.exceptions import BusinessValidationException, ResourceNotFoundException
from app.models.todo import Todo, UserTodo, TodoRecord
from app.models.user import User
from app.models.enums.todo_status import TodoStatus
from app.repository.todo_repository import TodoRepository
from app.repository.user_repository import UserRepository
from app.dto.todo.todo_request import TodoRequest, TodoListRequest, FinishTodoRequest, TodoRecordRequest
from app.dto.todo.todo_response import (
    TodoResponse,
    TodoListResponse,
    TodoInfoResponse,
    TodoRecordResponse,
    UserTodoResponse,
)

logger = logging.getLogger(__name__)


class TodoService:
    """
    待办事项服务类

    提供待办事项 CRUD、完成、创建记录等业务逻辑
    """

    @staticmethod
    async def info(todo_id: str) -> TodoInfoResponse:
        """
        获取待办详情

        Args:
            todo_id: 待办ID

        Returns:
            待办详情响应 DTO

        Raises:
            ResourceNotFoundException: 待办事项不存在
        """
        todo = await TodoRepository.find_by_id(todo_id)
        if not todo:
            raise ResourceNotFoundException("待办事项不存在")

        # 收集所有用户ID（执行人 + 创建人）
        user_ids: Set[str] = {todo.creatorId}
        if todo.executes:
            for exec_item in todo.executes:
                user_ids.add(exec_item.userId)

        # 批量查询用户信息
        users = await UserRepository.find_by_ids(list(user_ids))
        user_map = {str(user.id): user for user in users}

        # 检查是否超时
        current_time = int(time.time() * 1000)
        todo_status = todo.todoStatus
        if todo.deadlineAt and current_time > todo.deadlineAt:
            todo_status = TodoStatus.TIMEOUT.value

        # 获取创建人信息
        creator = user_map.get(todo.creatorId)
        if not creator:
            raise ResourceNotFoundException("用户信息查询失败")

        # 构建执行人详细信息列表
        execute_ids_response: List[UserTodoResponse] = []
        if todo.executes:
            for exec_item in todo.executes:
                user = user_map.get(exec_item.userId)
                user_name = user.name if user else ""
                execute_ids_response.append(
                    UserTodoResponse(
                        id=exec_item.id,
                        userId=exec_item.userId,
                        userName=user_name,
                        todoId=todo_id,
                        todoStatus=exec_item.todoStatus,
                    )
                )

        # 构建操作记录列表
        records_response: List[TodoRecordResponse] = []
        if todo.records:
            for record in todo.records:
                record_user = user_map.get(record.userId)
                user_name = record_user.name if record_user else ""
                records_response.append(
                    TodoRecordResponse(
                        todoId=todo_id,
                        userId=record.userId,
                        userName=user_name,
                        content=record.content,
                        image=record.image,
                        createAt=record.createAt,
                    )
                )

        return TodoInfoResponse(
            id=str(todo.id),
            creatorId=todo.creatorId,
            creatorName=creator.name,
            title=todo.title,
            deadlineAt=todo.deadlineAt,
            desc=todo.desc,
            status=todo_status,
            todoStatus=todo_status,
            executeIds=execute_ids_response,
            records=records_response,
        )

    @staticmethod
    async def create(request: TodoRequest, current_user: User) -> str:
        """
        创建待办

        Args:
            request: 待办请求 DTO
            current_user: 当前用户

        Returns:
            创建的待办ID
        """
        logger.info(f"创建待办: {request.title}")

        current_user_id = str(current_user.id)

        # 查询执行人信息
        execute_user_ids = request.executeIds if request.executeIds else [current_user_id]
        users = await UserRepository.find_by_ids(execute_user_ids)
        user_map = {str(user.id): user for user in users}

        # 创建执行人列表（先不设置 todoId，等 todo 创建后再更新）
        executes: List[UserTodo] = []
        for execute_id in execute_user_ids:
            user = user_map.get(execute_id)
            user_todo = UserTodo(
                id=str(uuid.uuid4()),
                userId=execute_id,
                userName=user.name if user else "",
                todoId="",  # 先设置为空，等创建 todo 后再更新
                todoStatus=TodoStatus.PENDING.value,
            )
            executes.append(user_todo)

        # 创建待办记录列表
        records: List[TodoRecord] = []
        if request.records:
            for record_req in request.records:
                record_user = user_map.get(record_req.userId)
                record = TodoRecord(
                    userId=record_req.userId,
                    userName=record_user.name if record_user else "",
                    content=record_req.content,
                    image=record_req.image,
                    createAt=int(time.time() * 1000),
                )
                records.append(record)

        # 创建待办事项
        todo = Todo(
            creatorId=current_user_id,
            title=request.title,
            deadlineAt=request.deadlineAt,
            desc=request.desc,
            records=records,
            executes=executes,
            todoStatus=TodoStatus.PENDING.value,
        )

        saved = await TodoRepository.create(todo)
        todo_id = str(saved.id)

        # 更新执行人的 todoId
        for exec_item in saved.executes:
            exec_item.todoId = todo_id

        await saved.save()

        logger.info(f"创建待办成功: id={todo_id}")

        return todo_id

    @staticmethod
    async def edit(request: TodoRequest) -> None:
        """
        编辑待办

        Args:
            request: 待办请求 DTO

        Raises:
            BusinessValidationException: 待办ID不能为空
            ResourceNotFoundException: 待办事项不存在
        """
        if not request.id:
            raise BusinessValidationException("待办事项ID不能为空")

        todo = await TodoRepository.find_by_id(request.id)
        if not todo:
            raise ResourceNotFoundException("待办事项不存在")

        # 更新字段
        todo.title = request.title
        todo.desc = request.desc
        todo.deadlineAt = request.deadlineAt
        if request.status is not None:
            todo.todoStatus = request.status

        await TodoRepository.update(todo)
        logger.info(f"编辑待办成功: id={request.id}")

    @staticmethod
    async def delete(todo_id: str, current_user: User) -> None:
        """
        删除待办

        Args:
            todo_id: 待办ID
            current_user: 当前用户

        Raises:
            ResourceNotFoundException: 待办事项不存在
            BusinessValidationException: 您不能删除该待办事项
        """
        todo = await TodoRepository.find_by_id(todo_id)
        if not todo:
            raise ResourceNotFoundException("待办事项不存在")

        # 只有创建人可以删除
        if todo.creatorId != str(current_user.id):
            raise BusinessValidationException("您不能删除该待办事项")

        await TodoRepository.delete(todo_id)
        logger.info(f"删除待办成功: id={todo_id}")

    @staticmethod
    async def finish(request: FinishTodoRequest, current_user: User) -> None:
        """
        完成待办

        Args:
            request: 完成待办请求 DTO
            current_user: 当前用户

        Raises:
            ResourceNotFoundException: 待办事项不存在
            BusinessValidationException: 用户不在待办执行人列表中或无权限
        """
        todo = await TodoRepository.find_by_id(request.todoId)
        if not todo:
            raise ResourceNotFoundException("待办事项不存在")

        # 验证权限：只能完成自己的待办，请求的 userId 必须是当前用户
        current_user_id = str(current_user.id)
        if request.userId != current_user_id:
            raise BusinessValidationException("只能完成自己的待办事项")

        # 标记指定用户的待办状态为完成
        user_found = False
        if todo.executes:
            for exec_item in todo.executes:
                if exec_item.userId == current_user_id:
                    exec_item.todoStatus = TodoStatus.FINISHED.value
                    user_found = True
                    break

        if not user_found:
            raise BusinessValidationException("您不在待办执行人列表中")

        # 检查是否所有执行人都完成了
        all_finished = True
        if todo.executes:
            for exec_item in todo.executes:
                if exec_item.todoStatus != TodoStatus.FINISHED.value:
                    all_finished = False
                    break

        # 如果所有执行人都完成，更新整体状态为完成
        if all_finished:
            todo.todoStatus = TodoStatus.FINISHED.value

        await TodoRepository.update(todo)
        logger.info(f"完成待办成功: todoId={request.todoId}, userId={current_user_id}")

    @staticmethod
    async def create_record(request: TodoRecordRequest, current_user: User) -> None:
        """
        创建操作记录

        Args:
            request: 操作记录请求 DTO
            current_user: 当前用户

        Raises:
            ResourceNotFoundException: 待办事项不存在
        """
        todo = await TodoRepository.find_by_id(request.todoId)
        if not todo:
            raise ResourceNotFoundException("待办事项不存在")

        # 创建新记录
        record = TodoRecord(
            userId=str(current_user.id),
            userName=current_user.name,
            content=request.content,
            image=request.image,
            createAt=int(time.time() * 1000),
        )

        # 添加记录到待办事项
        if not todo.records:
            todo.records = []
        todo.records.append(record)

        await TodoRepository.update(todo)
        logger.info(f"创建待办记录成功: todoId={request.todoId}")

    @staticmethod
    async def list(request: TodoListRequest, current_user: User) -> TodoListResponse:
        """
        待办列表查询

        Args:
            request: 待办列表请求 DTO
            current_user: 当前用户

        Returns:
            待办列表响应 DTO
        """
        logger.info(f"待办列表查询: page={request.page}, count={request.count}")

        current_user_id = str(current_user.id)

        # 查询待办列表
        if request.startTime and request.endTime:
            todos, total = await TodoRepository.find_by_execute_user_id_and_time_range(
                current_user_id,
                request.startTime,
                request.endTime,
                request.page,
                request.count,
            )
        else:
            todos, total = await TodoRepository.find_by_execute_user_id(
                current_user_id,
                request.page,
                request.count,
            )

        # 收集所有用户ID（包括创建人和执行人）
        user_ids: Set[str] = set()
        for todo in todos:
            user_ids.add(todo.creatorId)
            if todo.executes:
                for exec_item in todo.executes:
                    user_ids.add(exec_item.userId)

        # 批量查询用户信息
        users = await UserRepository.find_by_ids(list(user_ids))
        user_map = {str(user.id): user for user in users}

        # 构建响应列表
        current_time = int(time.time() * 1000)
        data: List[TodoResponse] = []

        for todo in todos:
            # 检查是否超时
            todo_status = todo.todoStatus
            if todo.deadlineAt and current_time > todo.deadlineAt:
                todo_status = TodoStatus.TIMEOUT.value

            # 获取创建人名称
            creator = user_map.get(todo.creatorId)
            creator_name = creator.name if creator else ""

            # 获取执行人名称列表
            execute_names: List[str] = []
            if todo.executes:
                for exec_item in todo.executes:
                    exec_user = user_map.get(exec_item.userId)
                    if exec_user:
                        execute_names.append(exec_user.name)

            todo_response = TodoResponse(
                id=str(todo.id),
                creatorId=todo.creatorId,
                creatorName=creator_name,
                title=todo.title,
                deadlineAt=todo.deadlineAt,
                desc=todo.desc,
                status=todo_status,
                todoStatus=todo_status,
                executeIds=execute_names,
                createAt=todo.createAt,
                updateAt=todo.updateAt,
            )
            data.append(todo_response)

        return TodoListResponse(count=total, data=data)