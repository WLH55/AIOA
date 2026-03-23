"""
WebSocket 接口测试

测试 WebSocket 管理器和消息处理功能

注意：WebSocket 端到端测试需要运行应用服务器，可使用以下命令手动测试：
  uvicorn app.main:app --host 0.0.0.0 --port 8000
  然后使用 wscat 或其他 WebSocket 客户端连接测试
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from app.main import app
from app.models.user import User
from app.security.jwt import create_access_token
from app.services.ws_manager import WebSocketConnectionManager
from app.dto.ws.message import MessageType, ChatMessage, PongMessage, CloseMessage
from app.dto.ws.response import ErrorResponse, ConnectedResponse, KickedResponse


class TestWebSocketManager:
    """WebSocket 管理器单元测试类"""

    def test_generate_session_id(self):
        """测试 session_id 生成"""
        manager = WebSocketConnectionManager()
        session_id = manager._generate_session_id()

        assert session_id.startswith("sess_")
        assert len(session_id) == 21  # "sess_" + 16 字符

    def test_session_id_uniqueness(self):
        """测试 session_id 唯一性"""
        manager = WebSocketConnectionManager()
        ids = [manager._generate_session_id() for _ in range(100)]

        assert len(ids) == len(set(ids))

    def test_get_online_users_empty(self):
        """测试获取在线用户（空）"""
        manager = WebSocketConnectionManager()

        users = manager.get_online_users()
        assert len(users) == 0

    def test_get_online_count_empty(self):
        """测试获取在线用户数量（空）"""
        manager = WebSocketConnectionManager()

        count = manager.get_online_count()
        assert count == 0

    def test_is_user_online_false(self):
        """测试用户是否在线（不在线）"""
        manager = WebSocketConnectionManager()

        assert manager.is_user_online("non_existent_user") is False

    @pytest.mark.asyncio
    async def test_connect_registers_user(self):
        """测试连接注册用户"""
        manager = WebSocketConnectionManager()
        mock_ws = MagicMock()
        mock_ws.accept = AsyncMock()
        mock_ws.send_json = AsyncMock()

        session_id = await manager.connect(mock_ws, "user123", "testuser")

        assert session_id is not None
        assert manager.is_user_online("user123")
        assert manager.get_online_count() == 1
        assert manager.get_user_by_session(session_id) == "user123"

    @pytest.mark.asyncio
    async def test_disconnect_removes_user(self):
        """测试断开连接移除用户"""
        manager = WebSocketConnectionManager()
        mock_ws = MagicMock()
        mock_ws.accept = AsyncMock()
        mock_ws.send_json = AsyncMock()

        session_id = await manager.connect(mock_ws, "user123", "testuser")
        assert manager.is_user_online("user123")

        await manager.disconnect(mock_ws)

        assert not manager.is_user_online("user123")
        assert manager.get_online_count() == 0

    @pytest.mark.asyncio
    async def test_single_connection_kicks_old(self):
        """测试单连接踢掉旧连接"""
        manager = WebSocketConnectionManager()

        # 第一个连接
        mock_ws1 = MagicMock()
        mock_ws1.accept = AsyncMock()
        mock_ws1.send_json = AsyncMock()
        mock_ws1.close = AsyncMock()

        session_id1 = await manager.connect(mock_ws1, "user123", "testuser")
        assert manager.is_user_online("user123")

        # 第二个连接（同一用户）
        mock_ws2 = MagicMock()
        mock_ws2.accept = AsyncMock()
        mock_ws2.send_json = AsyncMock()

        session_id2 = await manager.connect(mock_ws2, "user123", "testuser")

        # 验证新连接已注册
        assert manager.is_user_online("user123")
        assert manager.get_session_by_websocket(mock_ws2) == session_id2

        # 验证旧连接被踢（收到了 kicked 消息）
        mock_ws1.send_json.assert_called()
        call_args = mock_ws1.send_json.call_args[0][0]
        assert call_args["type"] == MessageType.KICKED
        assert call_args["reason"] == "new_login"

    @pytest.mark.asyncio
    async def test_send_to_user_success(self):
        """测试向用户发送消息成功"""
        manager = WebSocketConnectionManager()
        mock_ws = MagicMock()
        mock_ws.accept = AsyncMock()
        mock_ws.send_json = AsyncMock()

        await manager.connect(mock_ws, "user123", "testuser")

        message = {"type": "test", "content": "hello"}
        result = await manager.send_to_user("user123", message)

        assert result is True
        mock_ws.send_json.assert_called_with(message)

    @pytest.mark.asyncio
    async def test_send_to_user_offline(self):
        """测试向离线用户发送消息"""
        manager = WebSocketConnectionManager()

        message = {"type": "test", "content": "hello"}
        result = await manager.send_to_user("offline_user", message)

        assert result is False

    @pytest.mark.asyncio
    async def test_kick_user_success(self):
        """测试踢掉用户连接"""
        manager = WebSocketConnectionManager()
        mock_ws = MagicMock()
        mock_ws.accept = AsyncMock()
        mock_ws.send_json = AsyncMock()
        mock_ws.close = AsyncMock()

        await manager.connect(mock_ws, "user123", "testuser")

        result = await manager.kick_user("user123", "test_reason")

        assert result is True
        assert not manager.is_user_online("user123")

    @pytest.mark.asyncio
    async def test_kick_user_offline(self):
        """测试踢掉离线用户"""
        manager = WebSocketConnectionManager()

        result = await manager.kick_user("offline_user", "test_reason")

        assert result is False

    @pytest.mark.asyncio
    async def test_handle_pong(self):
        """测试心跳响应处理"""
        manager = WebSocketConnectionManager()
        mock_ws = MagicMock()
        mock_ws.accept = AsyncMock()
        mock_ws.send_json = AsyncMock()

        session_id = await manager.connect(mock_ws, "user123", "testuser")

        # 更新 pong 时间
        await manager.handle_pong(session_id)

        assert session_id in manager._last_pong_time

    @pytest.mark.asyncio
    async def test_broadcast(self):
        """测试广播消息"""
        manager = WebSocketConnectionManager()

        # 创建多个连接
        connections = []
        for i in range(3):
            mock_ws = MagicMock()
            mock_ws.accept = AsyncMock()
            mock_ws.send_json = AsyncMock()
            await manager.connect(mock_ws, f"user{i}", f"testuser{i}")
            connections.append(mock_ws)

        message = {"type": "broadcast", "content": "hello all"}
        count = await manager.broadcast(message)

        assert count == 3
        for ws in connections:
            ws.send_json.assert_called_with(message)


class TestWebSocketDTO:
    """WebSocket DTO 测试类"""

    def test_chat_message_validation(self):
        """测试聊天消息验证"""
        # 有效消息
        msg = ChatMessage(content="hello", conversation_id="conv_001")
        assert msg.type == MessageType.CHAT
        assert msg.content == "hello"

    def test_chat_message_create_conversation_id(self):
        """测试聊天消息自动创建会话 ID"""
        msg = ChatMessage(content="hello")
        conv_id = msg.get_or_create_conversation_id()

        assert conv_id is not None
        assert conv_id.startswith("conv_")

    def test_pong_message(self):
        """测试心跳响应消息"""
        msg = PongMessage()
        assert msg.type == MessageType.PONG

    def test_close_message(self):
        """测试关闭消息"""
        msg = CloseMessage(reason="user_close")
        assert msg.type == MessageType.CLOSE
        assert msg.reason == "user_close"

    def test_error_response(self):
        """测试错误响应"""
        response = ErrorResponse(code=4001, message="Authentication required")
        assert response.type == MessageType.ERROR
        assert response.code == 4001

    def test_connected_response(self):
        """测试连接成功响应"""
        response = ConnectedResponse(
            user_id="user123",
            username="testuser",
            session_id="sess_abc123"
        )
        assert response.type == MessageType.CONNECTED
        assert response.user_id == "user123"

    def test_kicked_response(self):
        """测试被踢响应"""
        response = KickedResponse(
            reason="new_login",
            message="您的账号在其他设备登录"
        )
        assert response.type == MessageType.KICKED
        assert response.reason == "new_login"


class TestMessageType:
    """消息类型枚举测试类"""

    def test_message_type_values(self):
        """测试消息类型枚举值"""
        assert MessageType.CHAT == "chat"
        assert MessageType.PONG == "pong"
        assert MessageType.CLOSE == "close"
        assert MessageType.CONNECTED == "connected"
        assert MessageType.KICKED == "kicked"
        assert MessageType.PING == "ping"
        assert MessageType.MESSAGE == "message"
        assert MessageType.ERROR == "error"


class TestWebSocketErrorCodes:
    """WebSocket 错误码测试类"""

    def test_error_codes_defined(self):
        """测试错误码定义"""
        from app.routers.ws import WSErrorCode

        assert WSErrorCode.AUTH_REQUIRED == 4001
        assert WSErrorCode.INVALID_TOKEN == 4002
        assert WSErrorCode.EXPIRED_TOKEN == 4003
        assert WSErrorCode.USER_NOT_FOUND == 4004
        assert WSErrorCode.USER_INACTIVE == 4005
        assert WSErrorCode.UNKNOWN_MESSAGE == 6001
        assert WSErrorCode.INVALID_MESSAGE == 6002