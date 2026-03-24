"""
ChatLog 模块集成测试

测试聊天记录 CRUD 等 API 端点
"""
import pytest
from httpx import AsyncClient

from app.models.user import User
from app.models.chat_log import ChatLog
from app.security.password import hash_password
from app.security.jwt import create_access_token
import time


class TestChatLogAPI:
    """聊天记录 API 测试类"""

    @pytest.mark.asyncio
    async def test_create_private_chat(self, client: AsyncClient, test_user: User):
        """CHAT-001: 创建私聊消息"""
        # 创建接收者
        receiver = User(
            name="chat_receiver",
            password=hash_password("Password123"),
            status=0,
            isAdmin=False,
        )
        await receiver.insert()

        token = create_access_token(str(test_user.id), test_user.name)
        response = await client.post(
            "/api/v1/chat",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "conversation_id": f"conv-{test_user.id}-{receiver.id}",
                "send_id": str(test_user.id),
                "recv_id": str(receiver.id),
                "chat_type": 2,  # 私聊
                "msg_content": "你好，这是一条测试消息"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["code"] == 200
        assert "data" in data  # 返回记录ID

    @pytest.mark.asyncio
    async def test_create_group_chat(self, client: AsyncClient, test_user: User):
        """CHAT-002: 创建群聊消息"""
        token = create_access_token(str(test_user.id), test_user.name)
        response = await client.post(
            "/api/v1/chat",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "conversation_id": "group-123",
                "send_id": str(test_user.id),
                "recv_id": None,  # 群聊无接收者
                "chat_type": 1,  # 群聊
                "msg_content": "大家好，这是一条群消息"
            }
        )

        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_get_chat_log_info(self, client: AsyncClient, test_user: User):
        """CHAT-详情: 获取聊天记录详情"""
        # 创建一条记录
        chat_log = ChatLog(
            conversationId="conv-test",
            sendId=str(test_user.id),
            recvId=None,
            chatType=1,
            msgContent="测试消息",
            sendTime=int(time.time() * 1000),
        )
        await chat_log.insert()

        token = create_access_token(str(test_user.id), test_user.name)
        response = await client.get(
            f"/api/v1/chat/{chat_log.id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["id"] == str(chat_log.id)
        assert data["data"]["msg_content"] == chat_log.msgContent

    @pytest.mark.asyncio
    async def test_list_chat_logs(self, client: AsyncClient, test_user: User):
        """CHAT-005: 分页查询聊天记录"""
        # 创建几条记录
        for i in range(3):
            chat_log = ChatLog(
                conversationId=f"conv-list-{i}",
                sendId=str(test_user.id),
                recvId=None,
                chatType=1,
                msgContent=f"消息{i}",
                sendTime=int(time.time() * 1000) + i,
            )
            await chat_log.insert()

        token = create_access_token(str(test_user.id), test_user.name)
        response = await client.get(
            "/api/v1/chat/list?page=1&count=10",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "count" in data["data"]
        assert "data" in data["data"]

    @pytest.mark.asyncio
    async def test_list_chat_logs_by_conversation(self, client: AsyncClient, test_user: User):
        """CHAT-003: 按会话查询聊天记录"""
        conversation_id = "conv-filter-test"

        # 创建几条记录
        for i in range(3):
            chat_log = ChatLog(
                conversationId=conversation_id,
                sendId=str(test_user.id),
                recvId=None,
                chatType=1,
                msgContent=f"消息{i}",
                sendTime=int(time.time() * 1000) + i,
            )
            await chat_log.insert()

        token = create_access_token(str(test_user.id), test_user.name)
        response = await client.get(
            f"/api/v1/chat/conversation/{conversation_id}?page=1&count=10",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        # 验证所有记录都属于该会话
        for item in data["data"]["data"]:
            assert item["conversation_id"] == conversation_id

    @pytest.mark.asyncio
    async def test_list_chat_logs_filter_by_type(self, client: AsyncClient, test_user: User):
        """CHAT-按类型筛选: 按聊天类型查询"""
        # 创建私聊和群聊记录
        private_log = ChatLog(
            conversationId="conv-private",
            sendId=str(test_user.id),
            recvId="receiver-id",
            chatType=2,  # 私聊
            msgContent="私聊消息",
            sendTime=int(time.time() * 1000),
        )
        await private_log.insert()

        group_log = ChatLog(
            conversationId="conv-group",
            sendId=str(test_user.id),
            recvId=None,
            chatType=1,  # 群聊
            msgContent="群聊消息",
            sendTime=int(time.time() * 1000),
        )
        await group_log.insert()

        token = create_access_token(str(test_user.id), test_user.name)
        response = await client.get(
            "/api/v1/chat/list?chat_type=1",  # 只查群聊
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        # 验证返回的都是群聊
        for item in data["data"]["data"]:
            assert item["chat_type"] == 1