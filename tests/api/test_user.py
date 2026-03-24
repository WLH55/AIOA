"""
User 模块集成测试

测试用户 CRUD、权限校验等 API 端点
"""
import pytest
from httpx import AsyncClient

from app.models.user import User
from app.security.password import hash_password
from app.security.jwt import create_access_token


class TestUserAPI:
    """用户 API 测试类"""

    @pytest.mark.asyncio
    async def test_get_user_info_success(self, client: AsyncClient, test_user: User):
        """USER-001: 正常获取用户信息"""
        token = create_access_token(str(test_user.id), test_user.name)
        response = await client.get(
            f"/api/v1/user/{test_user.id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["user_id"] == str(test_user.id)
        assert data["data"]["name"] == test_user.name

    @pytest.mark.asyncio
    async def test_get_user_not_found(self, client: AsyncClient, test_user: User):
        """USER-002: 获取不存在的用户"""
        token = create_access_token(str(test_user.id), test_user.name)
        response = await client.get(
            "/api/v1/user/507f1f77bcf86cd799439011",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_create_user_success(self, client: AsyncClient, admin_user: User):
        """USER-005: 正常创建用户"""
        token = create_access_token(str(admin_user.id), admin_user.name)
        response = await client.post(
            "/api/v1/user",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "newuser",
                "password": "Password123",
                "status": 0
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["code"] == 200

    @pytest.mark.asyncio
    async def test_create_user_duplicate_name(self, client: AsyncClient, test_user: User, admin_user: User):
        """USER-006: 用户名重复"""
        token = create_access_token(str(admin_user.id), admin_user.name)
        response = await client.post(
            "/api/v1/user",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": test_user.name,
                "password": "Password123",
            }
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_create_user_default_status(self, client: AsyncClient, admin_user: User):
        """USER-007: 创建用户默认状态为正常"""
        token = create_access_token(str(admin_user.id), admin_user.name)
        response = await client.post(
            "/api/v1/user",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "default_status_user",
                "password": "Password123",
            }
        )

        assert response.status_code == 201
        # 验证用户状态
        user = await User.find_one(User.name == "default_status_user")
        assert user.status == 0  # 默认正常状态

    @pytest.mark.asyncio
    async def test_edit_user_by_admin(self, client: AsyncClient, test_user: User, admin_user: User):
        """USER-编辑: 管理员编辑用户"""
        token = create_access_token(str(admin_user.id), admin_user.name)
        response = await client.put(
            "/api/v1/user",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "id": str(test_user.id),
                "name": "updated_name",
            }
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_edit_user_by_self(self, client: AsyncClient, test_user: User):
        """USER-编辑: 用户编辑自己"""
        token = create_access_token(str(test_user.id), test_user.name)
        response = await client.put(
            "/api/v1/user",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "id": str(test_user.id),
                "name": "self_updated_name",
            }
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_edit_user_by_other_forbidden(self, client: AsyncClient, test_user: User):
        """USER-编辑: 普通用户编辑他人被拒绝"""
        # 创建另一个用户
        other_user = User(
            name="other_user",
            password=hash_password("Password123"),
            status=0,
            isAdmin=False,
        )
        await other_user.insert()

        token = create_access_token(str(other_user.id), other_user.name)
        response = await client.put(
            "/api/v1/user",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "id": str(test_user.id),
                "name": "hacked_name",
            }
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_delete_user_by_admin(self, client: AsyncClient, test_user: User, admin_user: User):
        """USER-删除: 管理员删除用户"""
        # 创建一个新用户用于删除
        user_to_delete = User(
            name="user_to_delete",
            password=hash_password("Password123"),
            status=0,
            isAdmin=False,
        )
        await user_to_delete.insert()

        token = create_access_token(str(admin_user.id), admin_user.name)
        response = await client.delete(
            f"/api/v1/user/{user_to_delete.id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_delete_user_by_normal_forbidden(self, client: AsyncClient, test_user: User):
        """USER-删除: 普通用户无权删除"""
        token = create_access_token(str(test_user.id), test_user.name)
        response = await client.delete(
            f"/api/v1/user/{test_user.id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_delete_self_forbidden(self, client: AsyncClient, admin_user: User):
        """USER-删除: 不能删除自己"""
        token = create_access_token(str(admin_user.id), admin_user.name)
        response = await client.delete(
            f"/api/v1/user/{admin_user.id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_user_list(self, client: AsyncClient, test_user: User):
        """USER-列表: 分页查询用户列表"""
        token = create_access_token(str(test_user.id), test_user.name)
        response = await client.get(
            "/api/v1/user/list?page=1&count=10",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "count" in data["data"]
        assert "data" in data["data"]

    @pytest.mark.asyncio
    async def test_update_password_by_self(self, client: AsyncClient, test_user: User):
        """USER-密码: 用户修改自己密码"""
        token = create_access_token(str(test_user.id), test_user.name)
        response = await client.post(
            "/api/v1/user/password",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "id": str(test_user.id),
                "old_pwd": "Password123",
                "new_pwd": "NewPassword123",
            }
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_update_password_wrong_old(self, client: AsyncClient, test_user: User):
        """USER-密码: 原密码错误"""
        token = create_access_token(str(test_user.id), test_user.name)
        response = await client.post(
            "/api/v1/user/password",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "id": str(test_user.id),
                "old_pwd": "WrongPassword",
                "new_pwd": "NewPassword123",
            }
        )

        assert response.status_code == 400