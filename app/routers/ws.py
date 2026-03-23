"""
WebSocket 路由模块

提供 WebSocket 端点，处理实时通信
"""
import asyncio
import logging
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from app.dto.ws.message import (
    MessageType,
    ChatMessage,
    PongMessage,
    CloseMessage,
)
from app.dto.ws.response import ErrorResponse
from app.models.user import User
from app.repository.user_repository import UserRepository
from app.security.jwt import decode_jwt
from app.security.dependencies import extract_token_from_header
from app.services.ws_manager import ws_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["WebSocket"])


# WebSocket 错误码
class WSErrorCode:
    """WebSocket 错误码"""
    AUTH_REQUIRED = 4001       # 需要认证
    INVALID_TOKEN = 4002       # Token 无效
    EXPIRED_TOKEN = 4003       # Token 过期
    USER_NOT_FOUND = 4004      # 用户不存在
    USER_INACTIVE = 4005       # 用户被禁用
    UNKNOWN_MESSAGE = 6001     # 未知消息类型
    INVALID_MESSAGE = 6002     # 消息格式错误


async def authenticate_websocket(websocket: WebSocket) -> Optional[User]:
    """
    认证 WebSocket 连接

    Args:
        websocket: WebSocket 连接对象

    Returns:
        User 对象或 None
    """
    # 从 Header 获取 Authorization
    authorization = websocket.headers.get("Authorization")

    if not authorization:
        # 尝试从 Query 参数获取 token
        token = websocket.query_params.get("token")
    else:
        token = extract_token_from_header(authorization)

    if not token:
        await websocket.close(code=WSErrorCode.AUTH_REQUIRED, reason="Authentication required")
        return None

    # 解码 JWT
    payload = decode_jwt(token)

    if payload is None:
        await websocket.close(code=WSErrorCode.INVALID_TOKEN, reason="Invalid token")
        return None

    # 验证 Token 类型
    token_type = payload.get("type")
    if token_type != "access":
        await websocket.close(code=WSErrorCode.INVALID_TOKEN, reason="Invalid token type")
        return None

    # 获取用户 ID
    user_id = payload.get("sub")
    if not user_id:
        await websocket.close(code=WSErrorCode.INVALID_TOKEN, reason="Invalid token payload")
        return None

    # 查询用户
    user = await UserRepository.find_by_id(user_id)

    if user is None:
        await websocket.close(code=WSErrorCode.USER_NOT_FOUND, reason="User not found")
        return None

    # 验证用户状态
    if user.status != "active":
        await websocket.close(code=WSErrorCode.USER_INACTIVE, reason="User is inactive")
        return None

    return user


@router.websocket("/chat")
async def websocket_chat(websocket: WebSocket):
    """
    WebSocket 聊天端点

    连接流程：
    1. 客户端携带 Token 连接
    2. 服务端验证 Token
    3. 验证成功后建立连接，发送 connected 消息
    4. 客户端可以发送 chat/pong/close 消息
    5. 服务端响应消息或关闭连接

    消息类型：
    - chat: 聊天消息
    - pong: 心跳响应
    - close: 关闭连接
    """
    # 认证
    user = await authenticate_websocket(websocket)

    if user is None:
        return

    # 建立连接
    session_id = await ws_manager.connect(websocket, str(user.id), user.username)

    try:
        # 消息循环
        while True:
            # 接收消息
            try:
                data = await websocket.receive_json()
            except Exception as e:
                logger.warning(f"接收消息失败: {e}")
                continue

            # 解析消息类型
            msg_type = data.get("type")

            if not msg_type:
                await _send_error(websocket, WSErrorCode.INVALID_MESSAGE, "Missing message type")
                continue

            # 处理不同类型的消息
            try:
                if msg_type == MessageType.CHAT:
                    await _handle_chat(websocket, session_id, user, data)

                elif msg_type == MessageType.PONG:
                    await _handle_pong(websocket, session_id, data)

                elif msg_type == MessageType.CLOSE:
                    await _handle_close(websocket, session_id, user, data)
                    break

                else:
                    await _send_error(
                        websocket,
                        WSErrorCode.UNKNOWN_MESSAGE,
                        f"Unknown message type: {msg_type}"
                    )

            except Exception as e:
                logger.error(f"处理消息异常: {e}")
                await _send_error(websocket, 5000, f"Internal error: {str(e)}")

    except WebSocketDisconnect:
        logger.info(f"WebSocket 断开: user_id={user.id}, session_id={session_id}")

    except Exception as e:
        logger.error(f"WebSocket 异常: user_id={user.id}, error={e}")

    finally:
        # 清理连接
        await ws_manager.disconnect(websocket)


async def _handle_chat(
    websocket: WebSocket,
    session_id: str,
    user: User,
    data: dict
) -> None:
    """
    处理聊天消息

    Args:
        websocket: WebSocket 连接对象
        session_id: 会话 ID
        user: 用户对象
        data: 消息数据
    """
    try:
        message = ChatMessage(**data)
    except Exception as e:
        await _send_error(websocket, WSErrorCode.INVALID_MESSAGE, f"Invalid chat message: {e}")
        return

    conversation_id = message.get_or_create_conversation_id()

    logger.info(
        f"收到聊天消息: user_id={user.id}, "
        f"conversation_id={conversation_id}, content_length={len(message.content)}"
    )

    # TODO: 调用 AI 服务处理消息
    # 当前返回模拟响应
    await ws_manager.send_to_user(str(user.id), {
        "type": MessageType.MESSAGE,
        "content": f"收到您的消息：{message.content}",
        "conversation_id": conversation_id,
        "message_id": f"msg_{session_id[:8]}",
        "is_final": True,
    })


async def _handle_pong(
    websocket: WebSocket,
    session_id: str,
    data: dict
) -> None:
    """
    处理心跳响应

    Args:
        websocket: WebSocket 连接对象
        session_id: 会话 ID
        data: 消息数据
    """
    await ws_manager.handle_pong(session_id)


async def _handle_close(
    websocket: WebSocket,
    session_id: str,
    user: User,
    data: dict
) -> None:
    """
    处理关闭连接请求

    Args:
        websocket: WebSocket 连接对象
        session_id: 会话 ID
        user: 用户对象
        data: 消息数据
    """
    reason = data.get("reason", "user_close")

    logger.info(f"用户主动关闭连接: user_id={user.id}, reason={reason}")

    try:
        await websocket.close(code=1000, reason=reason)
    except Exception:
        pass


async def _send_error(websocket: WebSocket, code: int, message: str) -> None:
    """
    发送错误消息

    Args:
        websocket: WebSocket 连接对象
        code: 错误码
        message: 错误消息
    """
    try:
        error = ErrorResponse(code=code, message=message)
        await websocket.send_json(error.model_dump())
    except Exception:
        pass