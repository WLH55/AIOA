"""
WebSocket 连接管理器

管理 WebSocket 连接的生命周期、心跳检测和消息分发
"""
import asyncio
import logging
import uuid
from datetime import datetime
from typing import Dict, Optional, Set

from fastapi import WebSocket

logger = logging.getLogger(__name__)


# WebSocket 关闭码（4000-4999 为应用自定义码）
class WSCloseCode:
    """WebSocket 关闭码"""
    # 正常关闭
    NORMAL = 1000
    # 端点离开
    GOING_AWAY = 1001
    # 被新登录踢掉
    KICKED_BY_NEW_LOGIN = 4100
    # 被管理员踢掉
    KICKED_BY_ADMIN = 4102
    # 心跳超时
    HEARTBEAT_TIMEOUT = 4101


class WebSocketConnectionManager:
    """
    WebSocket 连接管理器

    功能：
    - 连接注册与注销
    - 单用户单连接限制（踢掉旧连接）
    - 心跳检测
    - 消息广播

    映射关系：
    - session_id → user_id
    - user_id → WebSocket
    - WebSocket → session_id
    """

    def __init__(
        self,
        heartbeat_interval: int = 30,
        heartbeat_timeout: int = 60,
    ):
        """
        初始化连接管理器

        Args:
            heartbeat_interval: 心跳发送间隔（秒）
            heartbeat_timeout: 心跳超时时间（秒）
        """
        # 连接映射
        self._session_to_user: Dict[str, str] = {}
        self._user_to_ws: Dict[str, WebSocket] = {}
        self._ws_to_session: Dict[WebSocket, str] = {}

        # 心跳相关
        self._last_pong_time: Dict[str, datetime] = {}
        self._heartbeat_interval = heartbeat_interval
        self._heartbeat_timeout = heartbeat_timeout

        # 心跳任务
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._running = False

        # 锁，防止并发问题
        self._lock = asyncio.Lock()

    async def connect(
        self,
        websocket: WebSocket,
        user_id: str,
        username: str,
    ) -> str:
        """
        建立连接

        如果用户已有连接，会踢掉旧连接

        Args:
            websocket: WebSocket 连接对象
            user_id: 用户 ID
            username: 用户名

        Returns:
            str: session_id
        """
        async with self._lock:
            # 生成 session_id
            session_id = self._generate_session_id()

            # 先建立新连接（避免旧连接的关闭消息影响新连接）
            await websocket.accept()

            # 检查是否已有旧连接，需要清理
            if user_id in self._user_to_ws:
                old_ws = self._user_to_ws[user_id]
                # 只有当旧连接不是当前连接时才踢掉
                if old_ws != websocket:
                    await self._kick_old_connection(old_ws, user_id, username)

            # 记录映射
            self._session_to_user[session_id] = user_id
            self._user_to_ws[user_id] = websocket
            self._ws_to_session[websocket] = session_id
            self._last_pong_time[session_id] = datetime.utcnow()

            logger.info(
                f"WebSocket 连接建立: user_id={user_id}, "
                f"username={username}, session_id={session_id}"
            )

            # 发送连接成功消息
            await self._send_to_websocket(websocket, {
                "type": "connected",
                "user_id": user_id,
                "username": username,
                "session_id": session_id,
                "timestamp": datetime.utcnow().isoformat(),
            })

            return session_id

    async def disconnect(self, websocket: WebSocket) -> None:
        """
        断开连接，清理映射

        Args:
            websocket: WebSocket 连接对象
        """
        async with self._lock:
            session_id = self._ws_to_session.pop(websocket, None)

            if session_id:
                user_id = self._session_to_user.pop(session_id, None)
                self._last_pong_time.pop(session_id, None)

                if user_id:
                    # 确保移除的是当前 websocket（防止移除新连接）
                    if self._user_to_ws.get(user_id) == websocket:
                        self._user_to_ws.pop(user_id, None)

                    logger.info(
                        f"WebSocket 连接断开: user_id={user_id}, session_id={session_id}"
                    )

    async def kick_user(self, user_id: str, reason: str = "kicked") -> bool:
        """
        踢掉用户的连接

        Args:
            user_id: 用户 ID
            reason: 原因

        Returns:
            bool: 是否成功踢掉
        """
        async with self._lock:
            if user_id not in self._user_to_ws:
                return False

            websocket = self._user_to_ws[user_id]
            session_id = self._ws_to_session.get(websocket)

            if session_id:
                logger.info(f"踢掉用户连接: user_id={user_id}, reason={reason}")

                # 发送踢出消息
                try:
                    await self._send_to_websocket(websocket, {
                        "type": "kicked",
                        "reason": reason,
                        "message": "您的连接已被断开",
                        "timestamp": datetime.utcnow().isoformat(),
                    })
                except Exception:
                    pass

                # 关闭连接（使用特定关闭码，客户端可识别）
                try:
                    await websocket.close(code=WSCloseCode.KICKED_BY_ADMIN, reason=reason)
                except Exception:
                    pass

                # 清理映射
                self._session_to_user.pop(session_id, None)
                self._user_to_ws.pop(user_id, None)
                self._ws_to_session.pop(websocket, None)
                self._last_pong_time.pop(session_id, None)

                return True

            return False

    async def send_to_user(self, user_id: str, message: dict) -> bool:
        """
        向指定用户发送消息

        Args:
            user_id: 用户 ID
            message: 消息内容

        Returns:
            bool: 是否发送成功
        """
        websocket = self._user_to_ws.get(user_id)

        if not websocket:
            logger.warning(f"用户不在线，无法发送消息: user_id={user_id}")
            return False

        return await self._send_to_websocket(websocket, message)

    async def broadcast(self, message: dict, exclude: Optional[Set[str]] = None) -> int:
        """
        广播消息给所有在线用户

        Args:
            message: 消息内容
            exclude: 排除的用户 ID 集合

        Returns:
            int: 发送成功的数量
        """
        exclude = exclude or set()
        success_count = 0

        for user_id, websocket in list(self._user_to_ws.items()):
            if user_id in exclude:
                continue

            if await self._send_to_websocket(websocket, message):
                success_count += 1

        return success_count

    def get_user_by_session(self, session_id: str) -> Optional[str]:
        """
        根据 session_id 获取用户 ID

        Args:
            session_id: 会话 ID

        Returns:
            Optional[str]: 用户 ID 或 None
        """
        return self._session_to_user.get(session_id)

    def get_session_by_websocket(self, websocket: WebSocket) -> Optional[str]:
        """
        根据 WebSocket 获取 session_id

        Args:
            websocket: WebSocket 连接对象

        Returns:
            Optional[str]: session_id 或 None
        """
        return self._ws_to_session.get(websocket)

    def get_online_users(self) -> Set[str]:
        """
        获取所有在线用户 ID

        Returns:
            Set[str]: 在线用户 ID 集合
        """
        return set(self._user_to_ws.keys())

    def get_online_count(self) -> int:
        """
        获取在线用户数量

        Returns:
            int: 在线用户数量
        """
        return len(self._user_to_ws)

    def is_user_online(self, user_id: str) -> bool:
        """
        检查用户是否在线

        Args:
            user_id: 用户 ID

        Returns:
            bool: 是否在线
        """
        return user_id in self._user_to_ws

    async def handle_pong(self, session_id: str) -> None:
        """
        处理心跳响应

        Args:
            session_id: 会话 ID
        """
        if session_id in self._session_to_user:
            self._last_pong_time[session_id] = datetime.utcnow()
            logger.debug(f"收到心跳响应: session_id={session_id}")

    async def start_heartbeat(self) -> None:
        """
        启动心跳检测任务（只检测超时，不主动发送心跳）
        """
        if self._running:
            logger.warning("心跳检测任务已在运行")
            return

        self._running = True
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        logger.info(
            f"心跳检测任务启动: interval={self._heartbeat_interval}s, "
            f"timeout={self._heartbeat_timeout}s（被动接收客户端心跳）"
        )

    async def stop_heartbeat(self) -> None:
        """
        停止心跳检测任务
        """
        self._running = False

        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
            self._heartbeat_task = None

        logger.info("心跳检测任务已停止")

    # ==================== 私有方法 ====================

    def _generate_session_id(self) -> str:
        """
        生成唯一的 session_id

        Returns:
            str: session_id
        """
        return f"sess_{uuid.uuid4().hex[:16]}"

    async def _kick_old_connection(
        self,
        old_ws: WebSocket,
        user_id: str,
        username: str,
    ) -> None:
        """
        踢掉旧连接

        Args:
            old_ws: 旧的 WebSocket 连接
            user_id: 用户 ID
            username: 用户名
        """
        old_session_id = self._ws_to_session.get(old_ws)

        if old_session_id:
            logger.info(
                f"用户重新登录，踢掉旧连接: user_id={user_id}, "
                f"old_session_id={old_session_id}"
            )

            # 发送被踢消息（如果连接仍然有效）
            try:
                await self._send_to_websocket(old_ws, {
                    "type": "kicked",
                    "reason": "new_login",
                    "message": "您的账号在其他设备登录，当前连接已断开",
                    "timestamp": datetime.utcnow().isoformat(),
                })
            except Exception:
                # 旧连接可能已经自然断开，忽略发送失败
                logger.debug(f"旧连接已断开，无法发送踢人消息: session_id={old_session_id}")

            # 关闭旧连接（使用特定关闭码，客户端可识别并决定是否重连）
            try:
                await old_ws.close(code=WSCloseCode.KICKED_BY_NEW_LOGIN, reason="new_login")
            except Exception:
                pass

            # 清理旧映射（注意：不清理 _user_to_ws，因为新连接会覆盖）
            self._session_to_user.pop(old_session_id, None)
            self._ws_to_session.pop(old_ws, None)
            self._last_pong_time.pop(old_session_id, None)

    async def _send_to_websocket(self, websocket: WebSocket, message: dict) -> bool:
        """
        发送消息到 WebSocket

        Args:
            websocket: WebSocket 连接对象
            message: 消息内容

        Returns:
            bool: 是否发送成功
        """
        try:
            await websocket.send_json(message)
            return True
        except Exception as e:
            logger.warning(f"发送消息失败: {e}")
            return False

    async def _heartbeat_loop(self) -> None:
        """
        心跳检测循环（只检测超时，不主动发送心跳）
        """
        while self._running:
            try:
                await asyncio.sleep(self._heartbeat_interval)

                # 检查超时连接
                await self._check_timeout_connections()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"心跳检测异常: {e}")

    async def _check_timeout_connections(self) -> None:
        """
        检查并清理超时连接
        """
        now = datetime.utcnow()
        timeout_seconds = self._heartbeat_timeout

        # 找出超时的 session
        timeout_sessions = []

        for session_id, last_pong in list(self._last_pong_time.items()):
            elapsed = (now - last_pong).total_seconds()
            if elapsed > timeout_seconds:
                timeout_sessions.append(session_id)

        # 清理超时连接
        for session_id in timeout_sessions:
            user_id = self._session_to_user.get(session_id)

            if user_id:
                logger.warning(
                    f"心跳超时，断开连接: user_id={user_id}, "
                    f"session_id={session_id}, elapsed={elapsed:.1f}s"
                )

                websocket = self._user_to_ws.get(user_id)

                if websocket:
                    try:
                        await websocket.close(code=1001, reason="heartbeat_timeout")
                    except Exception:
                        pass

                # 清理映射
                self._session_to_user.pop(session_id, None)
                self._user_to_ws.pop(user_id, None)
                self._ws_to_session.pop(websocket, None)
                self._last_pong_time.pop(session_id, None)


# 全局单例
ws_manager = WebSocketConnectionManager()