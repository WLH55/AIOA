"""
Approval 模块集成测试

测试审批创建、处理等 API 端点
"""
import pytest
from httpx import AsyncClient

from app.models.user import User
from app.models.department import Department
from app.models.department_user import DepartmentUser
from app.security.password import hash_password
from app.security.jwt import create_access_token
import time


class TestApprovalAPI:
    """审批 API 测试类"""

    @pytest.fixture
    async def setup_approval_data(self, db):
        """设置审批测试数据"""
        # 创建申请人
        applicant = User(
            name="applicant",
            password=hash_password("Password123"),
            status=0,
            isAdmin=False,
        )
        await applicant.insert()

        # 创建部门负责人
        leader = User(
            name="leader",
            password=hash_password("Password123"),
            status=0,
            isAdmin=False,
        )
        await leader.insert()

        # 创建部门
        department = Department(
            name="测试部门",
            parentId=None,
            parentPath=None,
            level=1,
            leaderId=str(leader.id),
            count=1,
        )
        await department.insert()

        # 创建部门用户关联
        dep_user = DepartmentUser(
            depId=str(department.id),
            userId=str(applicant.id),
        )
        await dep_user.insert()

        return {"applicant": applicant, "leader": leader, "department": department}

    @pytest.mark.asyncio
    async def test_create_leave_approval(self, client: AsyncClient, setup_approval_data):
        """APR-001: 创建请假审批"""
        data = setup_approval_data
        token = create_access_token(str(data["applicant"].id), data["applicant"].name)

        response = await client.post(
            "/api/v1/approval",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "type": 2,
                "leave": {
                    "type": 3,
                    "start_time": int(time.time()),
                    "end_time": int(time.time()) + 86400,
                    "reason": "身体不适",
                    "time_type": 2
                }
            }
        )

        assert response.status_code == 201
        result = response.json()
        assert result["code"] == 200
        assert "data" in result  # 返回审批ID

    @pytest.mark.asyncio
    async def test_create_goout_approval(self, client: AsyncClient, setup_approval_data):
        """APR-002: 创建外出审批"""
        data = setup_approval_data
        token = create_access_token(str(data["applicant"].id), data["applicant"].name)

        response = await client.post(
            "/api/v1/approval",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "type": 4,
                "go_out": {
                    "start_time": int(time.time()),
                    "end_time": int(time.time()) + 3600,
                    "reason": "外出办事",
                }
            }
        )

        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_create_approval_no_department(self, client: AsyncClient, test_user: User):
        """APR-004: 用户未分配部门时创建审批失败"""
        token = create_access_token(str(test_user.id), test_user.name)

        response = await client.post(
            "/api/v1/approval",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "type": 2,
                "leave": {
                    "type": 3,
                    "start_time": int(time.time()),
                    "end_time": int(time.time()) + 86400,
                    "reason": "身体不适",
                    "time_type": 2
                }
            }
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_approve_pass(self, client: AsyncClient, setup_approval_data):
        """APR-005: 通过审批"""
        data = setup_approval_data
        applicant_token = create_access_token(str(data["applicant"].id), data["applicant"].name)

        # 先创建审批
        create_response = await client.post(
            "/api/v1/approval",
            headers={"Authorization": f"Bearer {applicant_token}"},
            json={
                "type": 2,
                "leave": {
                    "type": 3,
                    "start_time": int(time.time()),
                    "end_time": int(time.time()) + 86400,
                    "reason": "身体不适",
                    "time_type": 2
                }
            }
        )
        approval_id = create_response.json()["data"]

        # 审批人通过
        leader_token = create_access_token(str(data["leader"].id), data["leader"].name)
        response = await client.put(
            "/api/v1/approval/dispose",
            headers={"Authorization": f"Bearer {leader_token}"},
            json={
                "approval_id": approval_id,
                "status": 2,  # 通过
                "reason": "同意",
            }
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_approve_reject(self, client: AsyncClient, setup_approval_data):
        """APR-006: 拒绝审批"""
        data = setup_approval_data
        applicant_token = create_access_token(str(data["applicant"].id), data["applicant"].name)

        # 先创建审批
        create_response = await client.post(
            "/api/v1/approval",
            headers={"Authorization": f"Bearer {applicant_token}"},
            json={
                "type": 2,
                "leave": {
                    "type": 3,
                    "start_time": int(time.time()),
                    "end_time": int(time.time()) + 86400,
                    "reason": "身体不适",
                    "time_type": 2
                }
            }
        )
        approval_id = create_response.json()["data"]

        # 审批人拒绝
        leader_token = create_access_token(str(data["leader"].id), data["leader"].name)
        response = await client.put(
            "/api/v1/approval/dispose",
            headers={"Authorization": f"Bearer {leader_token}"},
            json={
                "approval_id": approval_id,
                "status": 3,  # 拒绝
                "reason": "不同意",
            }
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_approve_cancel_by_applicant(self, client: AsyncClient, setup_approval_data):
        """APR-009: 申请人撤销审批"""
        data = setup_approval_data
        applicant_token = create_access_token(str(data["applicant"].id), data["applicant"].name)

        # 先创建审批
        create_response = await client.post(
            "/api/v1/approval",
            headers={"Authorization": f"Bearer {applicant_token}"},
            json={
                "type": 2,
                "leave": {
                    "type": 3,
                    "start_time": int(time.time()),
                    "end_time": int(time.time()) + 86400,
                    "reason": "身体不适",
                    "time_type": 2
                }
            }
        )
        approval_id = create_response.json()["data"]

        # 申请人撤销
        response = await client.put(
            "/api/v1/approval/dispose",
            headers={"Authorization": f"Bearer {applicant_token}"},
            json={
                "approval_id": approval_id,
                "status": 4,  # 撤销
            }
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_approve_cancel_by_non_applicant_forbidden(self, client: AsyncClient, setup_approval_data):
        """APR-010: 非申请人撤销审批被拒绝"""
        data = setup_approval_data
        applicant_token = create_access_token(str(data["applicant"].id), data["applicant"].name)

        # 先创建审批
        create_response = await client.post(
            "/api/v1/approval",
            headers={"Authorization": f"Bearer {applicant_token}"},
            json={
                "type": 2,
                "leave": {
                    "type": 3,
                    "start_time": int(time.time()),
                    "end_time": int(time.time()) + 86400,
                    "reason": "身体不适",
                    "time_type": 2
                }
            }
        )
        approval_id = create_response.json()["data"]

        # 非申请人尝试撤销
        leader_token = create_access_token(str(data["leader"].id), data["leader"].name)
        response = await client.put(
            "/api/v1/approval/dispose",
            headers={"Authorization": f"Bearer {leader_token}"},
            json={
                "approval_id": approval_id,
                "status": 4,  # 撤销
            }
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_approval_list(self, client: AsyncClient, setup_approval_data):
        """APR-列表: 查询审批列表"""
        data = setup_approval_data
        token = create_access_token(str(data["applicant"].id), data["applicant"].name)

        response = await client.get(
            "/api/v1/approval/list?page=1&count=10&type=1",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        result = response.json()
        assert result["code"] == 200