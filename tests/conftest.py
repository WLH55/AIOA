"""
pytest 配置和测试 fixtures

提供测试所需的共享配置和测试数据
"""
import asyncio
import os
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

# 设置测试环境变量
os.environ["ENVIRONMENT"] = "test"
os.environ["DEBUG"] = "true"
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"
os.environ["MONGODB_URI"] = "mongodb://admin:admin123@118.145.107.158:27017/aiworkhelper_test?authSource=admin"
os.environ["MONGODB_DATABASE"] = "aiworkhelper_test"
os.environ["REDIS_URI"] = "redis://:redis123@118.145.107.158:6379/1"

from app.main import app
from app.models.user import User
from app.models.todo import Todo, UserTodo
from app.models.approval import Approval, Approver
from app.models.department import Department
from app.models.department_user import DepartmentUser
from app.models.chat_log import ChatLog
from app.security.password import hash_password
from app.security.jwt import create_access_token, create_refresh_token


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """
    创建事件循环

    pytest-asyncio 需要一个事件循环来运行异步测试
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def db():
    """
    初始化测试数据库连接

    使用独立的测试数据库，保留数据以便观察
    """
    # 连接测试数据库
    client = AsyncIOMotorClient(os.environ["MONGODB_URI"])
    database = client[os.environ["MONGODB_DATABASE"]]

    # 初始化 Beanie
    await init_beanie(
        database=database,
        document_models=[
            User,
            Todo,
            Approval,
            Department,
            DepartmentUser,
            ChatLog,
        ],
    )

    yield database

    # 关闭连接（保留测试数据）
    client.close()


@pytest_asyncio.fixture
async def client(db) -> AsyncGenerator[AsyncClient, None]:
    """
    创建测试客户端

    使用 httpx.AsyncClient 测试 FastAPI 应用
    保留测试数据以便观察
    """
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac


@pytest_asyncio.fixture
async def test_user(db) -> User:
    """
    创建测试用户

    Returns:
        User: 测试用户对象
    """
    user = User(
        name="testuser1",
        password=hash_password("Password123"),
        status=0,
        isAdmin=False,
    )
    await user.insert()
    return user


@pytest_asyncio.fixture
async def admin_user(db) -> User:
    """
    创建管理员测试用户

    Returns:
        User: 管理员用户对象
    """
    user = User(
        name="admin",
        password=hash_password("Password123"),
        status=0,
        isAdmin=True,
    )
    await user.insert()
    return user


@pytest_asyncio.fixture
async def suspended_user(db) -> User:
    """
    创建被禁用的测试用户

    Returns:
        User: 被禁用的测试用户对象
    """
    user = User(
        name="suspended_user",
        password=hash_password("Password123"),
        status=1,  # 1-禁用
        isAdmin=False,
    )
    await user.insert()
    return user


@pytest_asyncio.fixture
async def test_department(db, test_user: User) -> Department:
    """
    创建测试部门

    Returns:
        Department: 测试部门对象
    """
    department = Department(
        name="技术部",
        parentId=None,
        parentPath=None,
        level=1,
        leaderId=str(test_user.id),
        userCount=1,
    )
    await department.insert()
    return department


@pytest_asyncio.fixture
async def test_todo(db, test_user: User) -> Todo:
    """
    创建测试待办

    Returns:
        Todo: 测试待办对象
    """
    import time
    todo = Todo(
        creatorId=str(test_user.id),
        title="测试待办",
        deadlineAt=int(time.time() * 1000) + 86400000,  # 1天后
        desc="这是一个测试待办",
        executes=[
            UserTodo(
                id="test-exec-id",
                userId=str(test_user.id),
                userName=test_user.name,
                todoId="",  # 在插入后更新
                todoStatus=1,
            )
        ],
        todoStatus=1,
    )
    await todo.insert()
    # 更新 todoId
    todo.executes[0].todoId = str(todo.id)
    await todo.save()
    return todo


@pytest_asyncio.fixture
def auth_headers(test_user: User) -> dict:
    """
    生成认证请求头

    Args:
        test_user: 测试用户

    Returns:
        dict: 包含 Authorization 的请求头
    """
    token = create_access_token(str(test_user.id), test_user.name)
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
def refresh_token(test_user: User) -> str:
    """
    生成刷新令牌

    Args:
        test_user: 测试用户

    Returns:
        str: refresh_token
    """
    return create_refresh_token(str(test_user.id))


# 测试数据常量
TEST_USER_DATA = {
    "name": "newuser",
    "password": "Password123",
}

TEST_LOGIN_DATA = {
    "name": "testuser1",
    "password": "Password123",
}

WEAK_PASSWORD_DATA = {
    "name": "weakpass",
    "password": "123456",
}