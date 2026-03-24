"""
Department 模块集成测试

测试部门 CRUD、用户关联等 API 端点
"""
import pytest
from httpx import AsyncClient

from app.models.user import User
from app.models.department import Department
from app.models.department_user import DepartmentUser
from app.security.password import hash_password
from app.security.jwt import create_access_token


class TestDepartmentAPI:
    """部门 API 测试类"""

    @pytest.mark.asyncio
    async def test_get_department_tree(self, client: AsyncClient, test_user: User, test_department: Department):
        """DEP-001: 获取部门树结构"""
        token = create_access_token(str(test_user.id), test_user.name)
        response = await client.get(
            "/api/v1/dep/soa",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "child" in data["data"]

    @pytest.mark.asyncio
    async def test_create_root_department(self, client: AsyncClient, test_user: User):
        """DEP-003: 创建根部门"""
        token = create_access_token(str(test_user.id), test_user.name)
        response = await client.post(
            "/api/v1/dep",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "总公司",
                "level": 1,
                "leader_id": str(test_user.id)
            }
        )

        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_create_child_department(self, client: AsyncClient, test_user: User, test_department: Department):
        """DEP-004: 创建子部门"""
        token = create_access_token(str(test_user.id), test_user.name)
        response = await client.post(
            "/api/v1/dep",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "技术部子部门",
                "parent_id": str(test_department.id),
                "level": 2,
                "leader_id": str(test_user.id)
            }
        )

        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_create_department_duplicate_name(self, client: AsyncClient, test_user: User, test_department: Department):
        """DEP-005: 部门名重复"""
        token = create_access_token(str(test_user.id), test_user.name)
        response = await client.post(
            "/api/v1/dep",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": test_department.name,
                "level": 1,
                "leader_id": str(test_user.id)
            }
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_create_department_parent_not_found(self, client: AsyncClient, test_user: User):
        """DEP-006: 父部门不存在"""
        token = create_access_token(str(test_user.id), test_user.name)
        response = await client.post(
            "/api/v1/dep",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "新部门",
                "parent_id": "507f1f77bcf86cd799439011",
                "level": 2,
                "leader_id": str(test_user.id)
            }
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_department_info(self, client: AsyncClient, test_user: User, test_department: Department):
        """DEP-获取详情: 获取部门详情"""
        token = create_access_token(str(test_user.id), test_user.name)
        response = await client.get(
            f"/api/v1/dep/{test_department.id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["id"] == str(test_department.id)
        assert data["data"]["name"] == test_department.name

    @pytest.mark.asyncio
    async def test_update_department(self, client: AsyncClient, test_user: User, test_department: Department):
        """DEP-编辑: 更新部门信息"""
        token = create_access_token(str(test_user.id), test_user.name)
        response = await client.put(
            "/api/v1/dep",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "id": str(test_department.id),
                "name": "更新后的部门名",
                "leader_id": str(test_user.id)
            }
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_delete_empty_department(self, client: AsyncClient, test_user: User):
        """DEP-007: 删除空部门"""
        # 创建一个空部门
        empty_dept = Department(
            name="空部门",
            parentId=None,
            parentPath=None,
            level=1,
            leaderId=str(test_user.id),
            count=0,
        )
        await empty_dept.insert()

        token = create_access_token(str(test_user.id), test_user.name)
        response = await client.delete(
            f"/api/v1/dep/{empty_dept.id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_add_department_user(self, client: AsyncClient, test_user: User, test_department: Department):
        """DEP-010: 添加部门用户"""
        # 创建一个新用户
        new_user = User(
            name="new_dept_user",
            password=hash_password("Password123"),
            status=0,
            isAdmin=False,
        )
        await new_user.insert()

        token = create_access_token(str(test_user.id), test_user.name)
        response = await client.post(
            "/api/v1/dep/user/add",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "dep_id": str(test_department.id),
                "user_id": str(new_user.id),
            }
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_add_department_user_duplicate(self, client: AsyncClient, test_user: User, test_department: Department):
        """DEP-011: 重复添加部门用户"""
        # 先添加一次
        dep_user = DepartmentUser(
            depId=str(test_department.id),
            userId=str(test_user.id),
        )
        await dep_user.insert()

        token = create_access_token(str(test_user.id), test_user.name)
        response = await client.post(
            "/api/v1/dep/user/add",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "dep_id": str(test_department.id),
                "user_id": str(test_user.id),
            }
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_remove_department_user_leader_forbidden(self, client: AsyncClient, test_user: User, test_department: Department):
        """DEP-013: 不能删除部门负责人"""
        # 添加部门用户关联
        dep_user = DepartmentUser(
            depId=str(test_department.id),
            userId=str(test_user.id),
        )
        await dep_user.insert()

        token = create_access_token(str(test_user.id), test_user.name)
        response = await client.request(
            "DELETE",
            "/api/v1/dep/user/remove",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "dep_id": str(test_department.id),
                "user_id": str(test_user.id),  # test_user 是部门负责人
            }
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_get_user_department_info(self, client: AsyncClient, test_user: User, test_department: Department):
        """DEP-用户部门信息: 获取用户所属部门"""
        # 添加部门用户关联
        dep_user = DepartmentUser(
            depId=str(test_department.id),
            userId=str(test_user.id),
        )
        await dep_user.insert()

        token = create_access_token(str(test_user.id), test_user.name)
        response = await client.get(
            f"/api/v1/dep/user/{test_user.id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200