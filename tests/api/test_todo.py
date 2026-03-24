"""
Todo 模块集成测试

测试待办 CRUD、完成待办等 API 端点
"""
import pytest
from httpx import AsyncClient

from app.models.user import User
from app.models.todo import Todo, UserTodo
from app.security.password import hash_password
from app.security.jwt import create_access_token
import time


class TestTodoAPI:
    """待办 API 测试类"""

    @pytest.mark.asyncio
    async def test_create_todo_success(self, client: AsyncClient, test_user: User):
        """TODO-001: 正常创建待办"""
        token = create_access_token(str(test_user.id), test_user.name)
        response = await client.post(
            "/api/v1/todo",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "title": "测试待办",
                "deadline_at": int(time.time() * 1000) + 86400000,
                "desc": "这是一个测试待办",
                "execute_ids": [str(test_user.id)]
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["code"] == 200
        assert "data" in data  # 返回待办ID

    @pytest.mark.asyncio
    async def test_create_todo_without_executor(self, client: AsyncClient, test_user: User):
        """TODO-003: 未指定执行人时默认为创建人"""
        token = create_access_token(str(test_user.id), test_user.name)
        response = await client.post(
            "/api/v1/todo",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "title": "无执行人待办",
                "deadline_at": int(time.time() * 1000) + 86400000,
            }
        )

        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_get_todo_info(self, client: AsyncClient, test_user: User, test_todo: Todo):
        """TODO-获取详情: 正常获取待办详情"""
        token = create_access_token(str(test_user.id), test_user.name)
        response = await client.get(
            f"/api/v1/todo/{test_todo.id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["id"] == str(test_todo.id)
        assert data["data"]["title"] == test_todo.title

    @pytest.mark.asyncio
    async def test_edit_todo_success(self, client: AsyncClient, test_user: User, test_todo: Todo):
        """TODO-编辑: 正常编辑待办"""
        token = create_access_token(str(test_user.id), test_user.name)
        response = await client.put(
            "/api/v1/todo",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "id": str(test_todo.id),
                "title": "更新后的标题",
                "desc": "更新后的描述",
            }
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_delete_todo_by_creator(self, client: AsyncClient, test_user: User, test_todo: Todo):
        """TODO-007: 创建人删除待办"""
        token = create_access_token(str(test_user.id), test_user.name)
        response = await client.delete(
            f"/api/v1/todo/{test_todo.id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_delete_todo_by_non_creator_forbidden(self, client: AsyncClient, test_todo: Todo):
        """TODO-008: 非创建人删除待办被拒绝"""
        # 创建另一个用户
        other_user = User(
            name="other_user_todo",
            password=hash_password("Password123"),
            status=0,
            isAdmin=False,
        )
        await other_user.insert()

        token = create_access_token(str(other_user.id), other_user.name)
        response = await client.delete(
            f"/api/v1/todo/{test_todo.id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_finish_todo_success(self, client: AsyncClient, test_user: User, test_todo: Todo):
        """TODO-004: 正常完成待办"""
        token = create_access_token(str(test_user.id), test_user.name)
        response = await client.post(
            "/api/v1/todo/finish",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "todo_id": str(test_todo.id),
                "user_id": str(test_user.id),
            }
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_finish_todo_other_user_forbidden(self, client: AsyncClient, test_user: User, test_todo: Todo):
        """TODO-伪造身份: 不能代替他人完成待办"""
        # 创建另一个用户
        other_user = User(
            name="other_finish_user",
            password=hash_password("Password123"),
            status=0,
            isAdmin=False,
        )
        await other_user.insert()

        token = create_access_token(str(other_user.id), other_user.name)
        response = await client.post(
            "/api/v1/todo/finish",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "todo_id": str(test_todo.id),
                "user_id": str(test_user.id),  # 尝试伪造身份
            }
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_create_todo_record(self, client: AsyncClient, test_user: User, test_todo: Todo):
        """TODO-记录: 创建操作记录"""
        token = create_access_token(str(test_user.id), test_user.name)
        response = await client.post(
            "/api/v1/todo/record",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "todo_id": str(test_todo.id),
                "content": "这是一条操作记录",
            }
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_todo_list(self, client: AsyncClient, test_user: User, test_todo: Todo):
        """TODO-列表: 查询待办列表"""
        token = create_access_token(str(test_user.id), test_user.name)
        response = await client.get(
            "/api/v1/todo/list?page=1&count=10",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "count" in data["data"]
        assert "data" in data["data"]