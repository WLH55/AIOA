# AIWorkHelper WebSocket 聊天系统设计文档

---

## 文档信息

| 项目 | 内容 |
|------|------|
| 文档名称 | WebSocket 聊天系统设计文档 |
| 版本 | v1.0 |
| 日期 | 2026-03-25 |
| 项目 | AIWorkHelper 智能办公系统 |

---

## 目录

- [1. 概述](#1-概述)
- [2. 系统架构](#2-系统架构)
- [3. 核心模块设计](#3-核心模块设计)
- [4. 连接管理](#4-连接管理)
- [5. 消息机制](#5-消息机制)
- [6. 心跳保活](#6-心跳保活)
- [7. 数据持久化](#7-数据持久化)
- [8. 未读消息机制](#8-未读消息机制)
- [9. 单设备登录](#9-单设备登录)
- [10. 前端实现](#10-前端实现)
- [11. 错误处理](#11-错误处理)
- [12. 安全设计](#12-安全设计)
- [13. 性能优化](#13-性能优化)
- [14. 关键设计决策](#14-关键设计决策)
- [15. 附录](#15-附录)

---

## 1. 概述

### 1.1 设计目标

本系统旨在为 AIWorkHelper 智能办公平台提供实时通信能力，支持：

- **私聊**: 用户之间的一对一实时消息传递
- **群聊**: 多人协作的群组消息广播
- **单设备登录**: 确保同一账号仅有一个活跃连接
- **消息持久化**: 所有消息可靠存储，支持历史查询
- **离线消息**: 通过未读计数机制处理离线用户

### 1.2 技术选型

| 组件 | 技术选型 | 说明 |
|------|---------|------|
| 后端框架 | FastAPI | 高性能异步 Web 框架 |
| 协议 | WebSocket | 全双工实时通信协议 |
| 数据库 | MongoDB | 高性能文档数据库 |
| 前端框架 | Vue 3 | 渐进式 JavaScript 框架 |
| 状态管理 | Pinia | Vue 官方状态管理库 |
| 认证方式 | JWT | 无状态的 Token 认证 |

### 1.3 核心特性

- **连接管理**: 单用户单连接，自动踢掉旧连接
- **心跳保活**: 30秒心跳间隔，60秒超时检测
- **全局单例**: 前端使用引用计数管理连接复用
- **自动重连**: 连接断开后自动尝试重连（最多5次）
- **优雅降级**: 离线用户通过未读计数机制接收消息

---

## 2. 系统架构

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                         客户端层 (Vue 3)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │  Login.vue   │  │Dashboard.vue │  │  Chat.vue    │           │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘           │
│         │                 │                  │                    │
│         └─────────────────┼──────────────────┘                    │
│                           │                                       │
│                   ┌───────▼────────┐                             │
│                   │ WebSocketClient │                             │
│                   │  (全局单例)     │                             │
│                   └───────┬────────┘                             │
└───────────────────────────┼─────────────────────────────────────┘
                            │
                            │ WebSocket (ws://)
                            │
┌───────────────────────────┼─────────────────────────────────────┐
│                           ▼                                       │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                   FastAPI 应用层                        │    │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐         │    │
│  │  │ ws_router  │  │  user_rtr  │  │ group_rtr  │         │    │
│  │  └─────┬──────┘  └────────────┘  └────────────┘         │    │
│  │        │                                               │    │
│  │  ┌─────▼────────────────────────────────────┐          │    │
│  │  │      ws_manager (连接管理器)              │          │    │
│  │  │  - session_to_user 映射                   │          │    │
│  │  │  - user_to_ws 映射                         │          │    │
│  │  │  - 心跳检测任务                            │          │    │
│  │  └─────┬────────────────────────────────────┘          │    │
│  │        │                                               │    │
│  │  ┌─────▼──────┐  ┌────────────┐  ┌────────────┐      │    │
│  │  │chat_service│  │unread_svr  │  │auth_service│      │    │
│  │  └─────┬──────┘  └────────────┘  └────────────┘      │    │
│  └────────┼──────────────────────────────────────────────┘    │
│           │                                                    │
│  ┌────────▼────────────────────────────────────────────┐     │
│  │                   数据访问层 (Repository)           │     │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐          │     │
│  │  │user_repo │  │chat_repo │  │group_repo│          │     │
│  │  └──────────┘  └──────────┘  └──────────┘          │     │
│  └────────┬────────────────────────────────────────────┘     │
│           │                                                    │
│  ┌────────▼────────────────────────────────────────────┐     │
│  │                   数据持久层 (MongoDB)               │     │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐          │     │
│  │  │ user     │  │ chat_log │  │  group   │          │     │
│  │  └──────────┘  └──────────┘  └──────────┘          │     │
│  │  ┌──────────┐                                        │     │
│  │  │ unread   │                                        │     │
│  │  └──────────┘                                        │     │
│  └────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 消息流转架构

```
                    ┌─────────────┐
                    │  发送者 A   │
                    └──────┬──────┘
                           │
                    1. 发送消息
                           │
                    ┌──────▼──────────┐
                    │  WebSocket      │
                    │  (ws_manager)   │
                    └──────┬──────────┘
                           │
                    2. 路由分发
                           │
              ┌────────────┼────────────┐
              │            │            │
         ┌────▼─────┐  ┌───▼──────┐  ┌▼────────┐
         │私聊处理  │  │群聊处理  │  │认证失败  │
         └────┬─────┘  └───┬──────┘  └─────────┘
              │            │
         3.保存消息     3.保存消息
              │            │
         4.更新未读     4.批量更新未读
              │            │
         5.点对点发送   5.群组广播
              │            │
              └────┬───────┘
                   │
            6. 返回确认
                   │
              ┌────▼──────┐
              │ 发送者 A  │
              └───────────┘

                   │
            ┌──────▼──────┐
            │ 接收者 B/C  │
            │ (在线)      │
            └─────────────┘
```

---

## 3. 核心模块设计

### 3.1 模块职责划分

| 模块 | 文件路径 | 职责 |
|------|---------|------|
| WebSocket 路由 | `app/routers/ws.py` | WebSocket 端点定义、连接认证、消息路由 |
| 连接管理器 | `app/services/ws_manager.py` | 连接生命周期管理、心跳检测、消息分发 |
| 聊天服务 | `app/services/chat_service.py` | 聊天业务逻辑、消息处理、消息保存 |
| 未读服务 | `app/services/unread_service.py` | 未读计数管理、未读消息查询 |
| 用户仓库 | `app/repository/user_repository.py` | 用户数据访问 |
| 聊天日志仓库 | `app/repository/chat_log_repository.py` | 聊天记录数据访问 |
| 消息 DTO | `app/dto/ws/message.py` | WebSocket 消息数据结构定义 |
| 响应 DTO | `app/dto/ws/response.py` | WebSocket 响应数据结构定义 |

### 3.2 数据模型设计

#### 3.2.1 ChatLog (聊天记录)

```python
class ChatLog(Document):
    """聊天记录文档模型"""

    # 会话信息
    conversationId: Indexed(str)  # 会话ID
    sendId: str                   # 发送者用户ID
    recvId: Optional[str]         # 接收者用户ID（群聊时为空）

    # 消息信息
    chatType: int                 # 聊天类型（1=群聊, 2=私聊）
    msgContent: str               # 消息内容
    sendTime: int                 # 发送时间戳（毫秒）

    # 时间戳
    createAt: int                 # 创建时间戳
    updateAt: int                 # 更新时间戳

    class Settings:
        name = "chat_log"
        indexes = [
            "conversationId",  # 会话ID索引
        ]
```

#### 3.2.2 UnreadMessage (未读消息)

```python
class UnreadMessage(BaseDocument):
    """未读消息计数模型"""

    userId: str                   # 用户ID
    conversationId: str           # 会话ID
    conversationType: int         # 会话类型（1=群组, 2=私聊）
    unreadCount: int              # 未读消息数量
    lastReadTime: Optional[int]   # 最后阅读时间戳

    class Settings:
        name = "unread_message"
        indexes = [
            [("userId", 1), ("conversationId", 1)],  # 复合唯一索引
            [("userId", 1), ("unreadCount", 1)],     # 查询索引
        ]
```

---

## 4. 连接管理

### 4.1 连接建立流程

```
客户端                          服务端
  │                               │
  │  1. WebSocket 握手请求        │
  │  (携带 Token)                 │
  │─────────────────────────────>│
  │                               │
  │                       2. 验证 Token
  │                       (JWT 解码)
  │                               │
  │                       3. 查询用户
  │                       (状态验证)
  │                               │
  │                    4. 检查旧连接
  │                    (有则踢掉)
  │                               │
  │  5. 连接建立成功               │
  │<─────────────────────────────│
  │  (connected 消息)             │
  │                               │
  │  6. 进入消息循环               │
  │<─────────────────────────────│
  │  (ping 心跳)                  │
  │─────────────────────────────>│
  │  7. 心跳响应                  │
  │<─────────────────────────────│
```

### 4.2 连接认证

**认证方式**: 支持两种方式传递 Token

1. **Header 方式**:
   ```
   Authorization: Bearer <token>
   ```

2. **Query 参数方式**:
   ```
   ws://host/ws/chat?token=<token>
   ```

**认证流程** (`app/routers/ws.py:43-97`):

```python
async def authenticate_websocket(websocket: WebSocket) -> Optional[User]:
    # 1. 获取 Token
    authorization = websocket.headers.get("Authorization")
    if not authorization:
        token = websocket.query_params.get("token")
    else:
        token = extract_token_from_header(authorization)

    if not token:
        await websocket.close(code=4001, reason="Authentication required")
        return None

    # 2. 解码 JWT
    payload = decode_jwt(token)
    if payload is None:
        await websocket.close(code=4002, reason="Invalid token")
        return None

    # 3. 验证 Token 类型
    if payload.get("type") != "access":
        await websocket.close(code=4002, reason="Invalid token type")
        return None

    # 4. 获取并验证用户
    user_id = payload.get("sub")
    user = await UserRepository.find_by_id(user_id)
    if not user:
        await websocket.close(code=4004, reason="User not found")
        return None

    if user.status == 0:
        await websocket.close(code=4005, reason="User is inactive")
        return None

    return user
```

### 4.3 连接映射关系

**核心数据结构** (`app/services/ws_manager.py:61-66`):

```python
class WebSocketConnectionManager:
    # 连接映射
    _session_to_user: Dict[str, str]           # session_id → user_id
    _user_to_ws: Dict[str, WebSocket]           # user_id → WebSocket
    _ws_to_session: Dict[WebSocket, str]        # WebSocket → session_id
    _last_pong_time: Dict[str, datetime]        # session_id → 最后pong时间
```

**映射关系图**:

```
┌─────────────────────────────────────────────────────────┐
│                    ws_manager 内存结构                   │
│                                                          │
│  ┌─────────────────┐  ┌─────────────────┐              │
│  │ _session_to_user │  │  _user_to_ws    │              │
│  ├─────────────────┤  ├─────────────────┤              │
│  │ sess_xxx1 → u1  │  │  u1 → ws_obj1   │              │
│  │ sess_xxx2 → u2  │  │  u2 → ws_obj2   │              │
│  └─────────────────┘  └─────────────────┘              │
│                                                          │
│  ┌─────────────────┐  ┌─────────────────┐              │
│  │ _ws_to_session  │  │ _last_pong_time │              │
│  ├─────────────────┤  ├─────────────────┤              │
│  │ ws_obj1 → sess1 │  │ sess1 → time1   │              │
│  │ ws_obj2 → sess2 │  │ sess2 → time2   │              │
│  └─────────────────┘  └─────────────────┘              │
└─────────────────────────────────────────────────────────┘
```

**为什么需要三个映射？**

| 映射 | 用途 | 查询场景 |
|------|------|---------|
| `_session_to_user` | 根据 session 查询用户 | 心跳超时清理时 |
| `_user_to_ws` | 根据 user 快速发送消息 | 消息转发时 |
| `_ws_to_session` | 根据 WebSocket 查询 session | 连接断开时清理 |

### 4.4 连接断开场景

| 场景 | 关闭码 | 说明 | 处理逻辑 |
|------|--------|------|---------|
| 正常关闭 | 1000 | 客户端主动发送 close 消息 | 清理映射，释放资源 |
| 端点离开 | 1001 | 页面关闭、网络断开 | 清理映射，释放资源 |
| 心跳超时 | 1001 | 60秒未收到 pong | 主动关闭，清理映射 |
| 新登录踢人 | 4100 | 同账号新连接建立 | 发送 kicked 消息后关闭 |
| 管理员踢人 | 4102 | 后台强制踢出 | 发送 kicked 消息后关闭 |

---

## 5. 消息机制

### 5.1 消息类型定义

#### 5.1.1 客户端可发送的消息

```typescript
enum MessageType {
  CHAT = "chat",       // 聊天消息
  PONG = "pong",       // 心跳响应
  CLOSE = "close"      // 关闭连接
}
```

#### 5.1.2 服务端可发送的消息

```typescript
enum MessageType {
  CONNECTED = "connected",  // 连接成功
  PING = "ping",           // 心跳检测
  MESSAGE = "message",     // 消息内容
  KICKED = "kicked",       // 被踢出
  ERROR = "error"          // 错误消息
}
```

### 5.2 ChatMessage 数据结构

```typescript
interface ChatMessage {
  type: "chat"                                    // 消息类型
  conversationId: string                          // 会话ID
  recvId?: string                                 // 接收者ID（群聊为空）
  sendId: string                                  // 发送者ID
  chatType: 1 | 2                                // 1=群聊, 2=私聊
  content: string                                 // 消息内容
  contentType: 1 | 2 | 3                         // 1=文字, 2=图片, 3=表情包
  systemType?: string                             // 系统消息类型
  groupInfo?: GroupInfo                           // 群组信息
}
```

### 5.3 消息路由判断逻辑

```
收到消息
    │
    ▼
┌───────────────────────┐
│  解析消息类型 (type)   │
└───────────┬───────────┘
            │
            ▼
    ┌───────────────┐
    │ type == chat? │
    └───────┬───────┘
            │
    ┌───────┴───────┐
    │Yes           No│
    ▼               ▼
┌─────────┐    ┌─────────┐
│解析chat │    │ 其他处理 │
│message  │    └─────────┘
└────┬────┘
     │
     ▼
┌─────────────────────┐
│ 判断 chatType       │
└──────┬──────┬──────┘
       │      │
   ┌───▼──┐ ┌▼──────┐
   │ = 1  │ │ = 2   │
   │群聊  │ │私聊   │
   └───┬──┘ └───┬───┘
       │        │
       ▼        ▼
  ┌────────┐ ┌──────────┐
  │广播消息│ │点对点发送│
  └────────┘ └──────────┘
```

### 5.4 私聊消息处理流程

```
用户 A 发送私聊消息给 B
         │
         ▼
  ┌──────────────┐
  │ 1. 验证消息  │
  │    - 内容非空│
  │    - B 存在  │
  └──────┬───────┘
         │
         ▼
  ┌──────────────┐
  │ 2. 生成会话ID│
  │ private_min │
  │ _max(u1,u2)  │
  └──────┬───────┘
         │
         ▼
  ┌──────────────┐
  │ 3. 检查 B    │
  │    是否在线  │
  └──────┬───────┘
         │
         ▼
  ┌──────────────┐
  │ 4. 保存到    │
  │    MongoDB   │
  └──────┬───────┘
         │
         ▼
  ┌──────────────┐
  │ 5. 增加 B 的 │
  │    未读计数  │
  └──────┬───────┘
         │
    ┌────┴────┐
    │         │
   在线       离线
    │         │
    ▼         ▼
┌─────────┐ ┌─────────┐
│6. 转发给│ │status=  │
│   B     │ │"offline"│
└─────────┘ └─────────┘
```

### 5.5 群聊消息处理流程

```
用户 A 发送群聊消息到群组 G
         │
         ▼
  ┌──────────────┐
  │ 1. 验证消息  │
  │    - 内容非空│
  │    - G 存在  │
  │    - A 是成员│
  └──────┬───────┘
         │
         ▼
  ┌──────────────┐
  │ 2. 保存到    │
  │    MongoDB   │
  │  (recvId为空)│
  └──────┬───────┘
         │
         ▼
  ┌──────────────┐
  │ 3. 获取群成员│
  │    [A,B,C,D] │
  └──────┬───────┘
         │
         ▼
  ┌──────────────┐
  │ 4. 排除发送者│
  │    [B,C,D]   │
  └──────┬───────┘
         │
         ▼
  ┌──────────────┐
  │ 5. 批量增加  │
  │    未读计数  │
  └──────┬───────┘
         │
         ▼
  ┌──────────────┐
  │ 6. 广播给    │
  │    [B,C,D]   │
  └──────────────┘
```

---

## 6. 心跳保活

### 6.1 为什么需要心跳

1. **检测静默断开**: 网络断开、路由器故障、NAT 超时等情况下 TCP 层不会立即感知
2. **防止资源泄漏**: 僵尸连接占用内存、文件描述符等有限资源
3. **确保在线状态准确**: 影响消息推送和未读计数的准确性
4. **支持单设备登录**: 准确判断旧连接是否真正活跃

### 6.2 心跳参数配置

| 参数 | 默认值 | 说明 |
|------|--------|------|
| heartbeat_interval | 30 秒 | 服务端发送 ping 的间隔时间 |
| heartbeat_timeout | 60 秒 | 超时判定阈值（2 个间隔） |

**为什么超时是间隔的 2 倍？**

- 允许网络偶尔出现延迟
- 避免短暂网络波动导致误判超时
- 平衡响应速度和连接稳定性

### 6.3 心跳机制流程图

```
服务端                           客户端
  │                               │
  │                               │
  │  每 30 秒                     │
  │                               │
  │ ──────────────────────────>  │
  │  { type: "ping" }             │
  │                               │
  │                         [处理 ping]
  │                               │
  │  <────────────────────────── │
  │  { type: "pong" }             │
  │                               │
  [更新 last_pong_time]           │
  │                               │
  │  每 30 秒检查超时              │
  │                               │
  [当前时间 - last_pong_time]     │
  │                               │
  [ > 60 秒?]                     │
  │                               │
  ┌───Yes─────────────────────┐   │
  │                            │   │
  │ [判定为超时]                │   │
  │                            │   │
  │ ──────────────────────────> │   │
  │ (关闭连接，code=1001)       │   │
  │                            │   │
  └────────────────────────────┘   │
                                    │
                               [连接关闭]
```

### 6.4 心跳实现代码

**服务端发送心跳** (`app/services/ws_manager.py:434-446`):

```python
async def _send_heartbeat(self) -> None:
    """向所有连接发送心跳"""
    for user_id, websocket in list(self._user_to_ws.items()):
        try:
            await self._send_to_websocket(websocket, {
                "type": "ping",
                "timestamp": datetime.utcnow().isoformat(),
            })
        except Exception:
            pass  # 发送失败，连接可能已断开
```

**客户端响应心跳** (`app/routers/ws.py:227-240`):

```python
async def _handle_pong(
    websocket: WebSocket,
    session_id: str,
    data: dict
) -> None:
    """处理心跳响应"""
    await ws_manager.handle_pong(session_id)
```

**超时检测** (`app/services/ws_manager.py:448-485`):

```python
async def _check_timeout_connections(self) -> None:
    """检查并清理超时连接"""
    now = datetime.utcnow()
    timeout_seconds = self._heartbeat_timeout  # 60秒

    for session_id, last_pong in list(self._last_pong_time.items()):
        elapsed = (now - last_pong).total_seconds()
        if elapsed > timeout_seconds:
            user_id = self._session_to_user.get(session_id)
            if user_id:
                logger.warning(
                    f"心跳超时，断开连接: user_id={user_id}, "
                    f"session_id={session_id}, elapsed={elapsed:.1f}s"
                )

                websocket = self._user_to_ws.get(user_id)
                if websocket:
                    await websocket.close(code=1001, reason="heartbeat_timeout")

                # 清理映射
                self._session_to_user.pop(session_id, None)
                self._user_to_ws.pop(user_id, None)
                self._ws_to_session.pop(websocket, None)
                self._last_pong_time.pop(session_id, None)
```

### 6.5 为什么服务端主动发 ping

| 对比项 | 服务端主动 ping | 客户端主动 ping |
|--------|----------------|----------------|
| 控制权 | 服务端统一控制 | 各客户端独立控制 |
| 客户端逻辑 | 简单（只响应） | 复杂（需定时器、状态管理） |
| 流量控制 | 服务端统一控制 | 无法控制无效流量 |
| 状态同步 | 一致 | 可能不一致 |
| 适用场景 | 服务主导、检测连接状态 | 客户主导、防止 NAT 超时 |

---

## 7. 数据持久化

### 7.1 消息存储设计

**存储位置**: MongoDB `chat_log` 集合

**存储时机**: 消息接收后立即保存，确保不丢失

### 7.2 消息保存流程

```
收到消息
    │
    ▼
┌──────────────┐
│ 1. 数据验证  │
│   - 格式正确 │
│   - 内容非空 │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ 2. 业务验证  │
│   - 用户存在 │
│   - 群组存在 │
│   - 权限验证 │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ 3. 生成/获取 │
│    会话ID    │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ 4. 创建      │
│    ChatLog   │
│    对象      │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ 5. 保存到    │
│    MongoDB   │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ 6. 后续处理  │
│   - 更新未读 │
│   - 转发消息 │
└──────────────┘
```

### 7.3 会话ID 生成规则

#### 私聊会话ID

**格式**: `private_min(userId1,userId2)_max(userId1,userId2)`

**示例**:
- user1 = "abc", user2 = "xyz"
- conversationId = "private_abc_xyz"

**设计目的**:
- 确保同一对用户的会话ID唯一
- 方便查询双方的历史消息
- 避免会话ID重复

**生成代码** (`app/services/chat_service.py:86-108`):

```python
@staticmethod
def generate_conversation_id(user1_id: str, user2_id: str) -> str:
    """
    生成私聊会话ID
    规则：private_{min(userId1, userId2)}_{max(userId1, userId2)}
    """
    if user1_id == user2_id:
        raise BusinessValidationException("不能给自己发消息")

    # 按 ID 字典序排序，确保唯一性
    sorted_ids = sorted([user1_id, user2_id])
    return f"private_{sorted_ids[0]}_{sorted_ids[1]}"
```

#### 群聊会话ID

**格式**: 直接使用群组ID

**设计目的**:
- 简化设计，群组ID已保证唯一性
- 便于通过群组ID关联群成员信息

---

## 8. 未读消息机制

### 8.1 设计目的

1. **离线消息处理**: 用户离线时的消息通过未读计数标记
2. **消息提醒**: 清晰展示用户有多少未读消息
3. **会话级别统计**: 按会话（群组/私聊）分别统计未读数量

### 8.2 未读计数模型

```python
class UnreadMessage(BaseDocument):
    """未读消息计数模型"""

    userId: str                   # 用户ID
    conversationId: str           # 会话ID
    conversationType: int         # 1=群组, 2=私聊
    unreadCount: int              # 未读消息数量
    lastReadTime: Optional[int]   # 最后阅读时间戳
```

### 8.3 未读计数更新流程

```
新消息到达
    │
    ▼
┌──────────────┐
│ 判断消息类型 │
└──────┬───────┘
       │
  ┌────┴────┐
  │         │
  ▼         ▼
私聊      群聊
  │         │
  ▼         ▼
┌──────┐ ┌──────────────┐
│增加  │ │获取群成员列表 │
│接收者│ │排除发送者    │
│未读  │ └──────┬───────┘
└──────┘        │
                ▼
         ┌──────────────┐
         │为每个成员    │
         │增加未读计数  │
         └──────────────┘
```

### 8.4 未读计数 API

| 方法 | 说明 |
|------|------|
| `get_list(userId, conversationType)` | 获取用户的未读消息列表 |
| `clear(userId, conversationId)` | 清除指定会话的未读计数 |
| `increment(userId, conversationId, type, delta)` | 增加未读计数 |
| `increment_for_conversation(...)` | 为会话中所有接收者增加未读 |

---

## 9. 单设备登录

### 9.1 设计目标

确保同一用户账号在同一时间只有一个活跃的 WebSocket 连接，新登录会踢掉旧连接。

### 9.2 实现原理

**核心机制**: 在连接建立时检查用户是否已有连接，有则踢掉旧连接。

### 9.3 踢掉旧连接流程

```
用户尝试建立新连接
         │
         ▼
┌──────────────┐
│ 1. 验证用户  │
│    通过认证  │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ 2. 检查是否  │
│    已有连接  │
└──────┬───────┘
       │
   ┌───┴───┐
   │       │
  有       无
   │       │
   ▼       ▼
┌──────┐ ┌──────┐
│3. 踢 │ │直接  │
│  掉  │ │建立  │
│旧连接│ │新连接│
└───┬──┘ └──────┘
    │
    ▼
┌──────────────┐
│ 3.1 发送     │
│     kicked   │
│     消息     │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ 3.2 关闭连接│
│     (code=   │
│     4100)    │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ 3.3 清理     │
│     映射     │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ 4. 建立新连接│
└──────────────┘
```

### 9.4 踢掉旧连接代码

**连接时检查** (`app/services/ws_manager.py:103-109`):

```python
# 检查是否已有旧连接，需要清理
if user_id in self._user_to_ws:
    old_ws = self._user_to_ws[user_id]
    # 只有当旧连接不是当前连接时才踢掉
    if old_ws != websocket:
        await self._kick_old_connection(old_ws, user_id, username)
```

**踢掉实现** (`app/services/ws_manager.py:352-395`):

```python
async def _kick_old_connection(
    self,
    old_ws: WebSocket,
    user_id: str,
    username: str,
) -> None:
    """踢掉旧连接"""
    old_session_id = self._ws_to_session.get(old_ws)

    if old_session_id:
        # 发送被踢消息
        try:
            await self._send_to_websocket(old_ws, {
                "type": "kicked",
                "reason": "new_login",
                "message": "您的账号在其他设备登录，当前连接已断开",
                "timestamp": datetime.utcnow().isoformat(),
            })
        except Exception:
            pass

        # 关闭旧连接
        try:
            await old_ws.close(code=WSCloseCode.KICKED_BY_NEW_LOGIN, reason="new_login")
        except Exception:
            pass

        # 清理旧映射
        self._session_to_user.pop(old_session_id, None)
        self._ws_to_session.pop(old_ws, None)
        self._last_pong_time.pop(old_session_id, None)
```

---

## 10. 前端实现

### 10.1 WebSocketClient 类设计

```typescript
class WebSocketClient {
  private ws: WebSocket | null = null
  private url: string
  private token: string
  private reconnectTimer: NodeJS.Timeout | null = null
  private heartbeatTimer: NodeJS.Timeout | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private messageHandlers: ((message: WsMessage) => void)[] = []
  private savedHandlers: ((message: WsMessage) => void)[] = []

  // 连接、发送、关闭、重连等方法
}
```

### 10.2 全局单例管理

**引用计数机制**:

```typescript
interface WsInstance {
  client: WebSocketClient
  token: string
  refCount: number  // 引用计数
}

const globalWsMap = new Map<string, WsInstance>()
```

**获取连接**:

```typescript
export function getWebSocket(token: string): WebSocketClient {
  let instance = globalWsMap.get(token)

  if (!instance) {
    // 创建新连接
    const client = new WebSocketClient(fullUrl, token)
    instance = { client, token, refCount: 0 }
    globalWsMap.set(token, instance)
  }

  // 增加引用计数
  instance.refCount++
  return instance.client
}
```

**释放连接**:

```typescript
export function releaseWebSocket(token: string, client: WebSocketClient): void {
  const instance = globalWsMap.get(token)
  if (instance && instance.client === client) {
    instance.refCount--

    // 只有当引用计数为 0 时才关闭连接
    if (instance.refCount <= 0) {
      client.close()
      globalWsMap.delete(token)
    }
  }
}
```

### 10.3 自动重连机制

**重连配置**:
- 最大重连次数: 5 次
- 重连间隔: 3秒 × 重连次数（递增）

**重连逻辑** (`src/utils/websocket.ts:138-156`):

```typescript
private attemptReconnect(): void {
  if (this.reconnectAttempts < this.maxReconnectAttempts) {
    this.reconnectAttempts++
    console.log(`尝试重连WebSocket (${this.reconnectAttempts}/${this.maxReconnectAttempts})`)

    this.reconnectTimer = setTimeout(() => {
      this.connect().then(() => {
        // 重连成功后，重新注册所有保存的处理器
        this.messageHandlers = [...this.savedHandlers]
        console.log(`[WebSocket] 重连成功，重新注册了${this.messageHandlers.length}个处理器`)
      }).catch(error => {
        console.error('重连失败:', error)
      })
    }, 3000 * this.reconnectAttempts)
  } else {
    console.error('WebSocket重连失败，已达到最大重连次数')
  }
}
```

**被踢不重连**:

```typescript
this.ws.onclose = (event: CloseEvent) => {
  // 如果是被踢掉（4100 或 4102），不自动重连
  if (NO_RECONNECT_CODES.includes(event.code)) {
    console.log('被踢下线，不自动重连')
    return
  }

  this.attemptReconnect()
}
```

### 10.4 连接生命周期

```
进入聊天页面
    │
    ▼
┌──────────────┐
│ onMounted    │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ initWebSocket│
│              │
│ getWebSocket │
│   (单例)     │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ connect()    │
│              │
│ 建立连接     │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ 添加消息     │
│ 处理器       │
└──────┬───────┘
       │
       ▼
    消息循环
       │
       ▼
离开聊天页面
    │
    ▼
┌──────────────┐
│onBeforeUnmount│
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ 移除消息     │
│ 处理器       │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ release     │
│ WebSocket   │
│              │
│ refCount--  │
└──────┬───────┘
       │
  ┌────┴────┐
  │         │
 refCount   refCount
  > 0       = 0
  │         │
  ▼         ▼
保持     关闭连接
连接
```

### 10.5 不同场景下的连接行为

| 场景 | 连接是否断开 | 是否自动重连 | 说明 |
|------|-------------|-------------|------|
| 离开聊天页面 | 不一定 | - | 引用计数>0 时保持连接 |
| 刷新页面 | 是 | 是（进入聊天页面时） | 页面销毁后重新建立 |
| 重新登录（正常） | 是 | 是 | Token 变化，新连接 |
| 重新登录（其他设备） | 是 | **否** | 被踢掉（4100），需手动重登 |

---

## 11. 错误处理

### 11.1 错误码设计

| 范围 | 用途 | 示例 |
|------|------|------|
| 1000-1999 | WebSocket 标准码 | 1000=正常关闭, 1001=离开 |
| 4000-4999 | 应用层认证错误 | 4001=需认证, 4002=Token无效 |
| 4100-4199 | 业务层踢人 | 4100=新登录, 4102=管理员踢 |
| 6000-6999 | 消息格式错误 | 6001=未知类型, 6002=格式错误 |

### 11.2 认证错误码

```python
class WSErrorCode:
    AUTH_REQUIRED = 4001       # 需要认证
    INVALID_TOKEN = 4002       # Token 无效
    EXPIRED_TOKEN = 4003       # Token 过期
    USER_NOT_FOUND = 4004      # 用户不存在
    USER_INACTIVE = 4005       # 用户被禁用
```

### 11.3 消息错误码

```python
class WSErrorCode:
    UNKNOWN_MESSAGE = 6001     # 未知消息类型
    INVALID_MESSAGE = 6002     # 消息格式错误
```

### 11.4 错误响应格式

```typescript
interface ErrorResponse {
  code: number        // 错误码
  message: string     // 错误消息
}
```

---

## 12. 安全设计

### 12.1 认证机制

**JWT Token 认证**:
- Token 必须是 access 类型
- Token 必须有效且未过期
- 用户必须存在且状态正常（status=1）

### 12.2 防止未授权访问

1. **连接时认证**: 建立 WebSocket 连接前验证 Token
2. **消息验证**: 处理消息时验证用户权限
3. **群组权限**: 发送群聊消息时验证用户是否为群成员

### 12.3 防止消息篡改

1. **服务端验证**: 所有消息参数在服务端重新验证
2. **会话ID生成**: 私聊会话ID由服务端生成，防止伪造
3. **时间戳服务端生成**: 消息时间戳由服务端设置

### 12.4 防止重放攻击

1. **JWT 短期有效**: access token 有效期较短
2. **消息ID唯一**: 可扩展添加消息ID防重放

---

## 13. 性能优化

### 13.1 连接复用

**全局单例 + 引用计数**:
- 同一 token 的多个页面共享一个连接
- 减少连接数量，降低服务器负载

### 13.2 批量操作

**群聊未读计数**:
- 使用 `increment_for_conversation` 批量更新
- 避免多次数据库查询

### 13.3 索引优化

**MongoDB 索引**:
```python
class ChatLog(Document):
    class Settings:
        indexes = [
            "conversationId",  # 会话查询索引
        ]
```

```python
class UnreadMessage(Document):
    class Settings:
        indexes = [
            [("userId", 1), ("conversationId", 1)],  # 复合唯一索引
            [("userId", 1), ("unreadCount", 1)],     # 查询索引
        ]
```

### 13.4 异步处理

- 所有 I/O 操作使用 async/await
- 心跳检测使用后台任务
- 消息发送不阻塞

---

## 14. 关键设计决策

### 14.1 会话ID 生成规则

**决策**: 私聊使用 `private_min_max` 格式

**原因**:
- 保证同一对用户的会话ID唯一
- 方便查询双方历史消息
- 避免会话ID冲突

### 14.2 心跳方向

**决策**: 服务端主动发 ping，客户端响应 pong

**原因**:
- 服务端统一控制连接状态
- 客户端逻辑简单
- 与超时检测机制一致

### 14.3 单设备登录

**决策**: 新连接踢掉旧连接

**原因**:
- 安全性：防止账号被多处使用
- 资源管理：限制连接数量
- 用户体验：清晰的登录状态

### 14.4 引用计数机制

**决策**: 前端使用引用计数管理连接

**原因**:
- 支持多页面共享连接
- 减少重复连接
- 更精确的生命周期管理

### 14.5 未读计数机制

**决策**: 独立的未读消息表

**原因**:
- 支持会话级别的未读统计
- 查询性能优于实时计算
- 灵活的未读清除策略

---

## 15. 附录

### 15.1 相关文件索引

| 功能 | 后端文件 | 前端文件 |
|------|---------|---------|
| WebSocket 路由 | `app/routers/ws.py` | - |
| 连接管理器 | `app/services/ws_manager.py` | - |
| 聊天服务 | `app/services/chat_service.py` | - |
| 未读服务 | `app/services/unread_service.py` | - |
| 消息 DTO | `app/dto/ws/message.py` | - |
| 响应 DTO | `app/dto/ws/response.py` | - |
| WebSocket 客户端 | - | `src/utils/websocket.ts` |
| 聊天页面 | - | `src/views/chat/Index.vue` |
| 用户模型 | `app/models/user.py` | - |
| 聊天日志模型 | `app/models/chat_log.py` | - |
| 未读消息模型 | `app/models/unread_message.py` | - |

### 15.2 WebSocket 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/v1/ws/chat` | WebSocket | 聊天连接端点 |

### 15.3 消息类型参考

| 消息类型 | 方向 | 说明 |
|---------|------|------|
| `chat` | 客户端→服务端 | 聊天消息 |
| `pong` | 客户端→服务端 | 心跳响应 |
| `close` | 客户端→服务端 | 关闭连接请求 |
| `connected` | 服务端→客户端 | 连接成功 |
| `ping` | 服务端→客户端 | 心跳检测 |
| `message` | 服务端→客户端 | 消息内容 |
| `kicked` | 服务端→客户端 | 被踢出 |
| `error` | 服务端→客户端 | 错误消息 |

### 15.4 关闭码参考

| 关闭码 | 名称 | 说明 | 客户端行为 |
|--------|------|------|-----------|
| 1000 | NORMAL | 正常关闭 | - |
| 1001 | GOING_AWAY | 端点离开 | - |
| 4100 | KICKED_BY_NEW_LOGIN | 被新登录踢掉 | 不自动重连 |
| 4101 | HEARTBEAT_TIMEOUT | 心跳超时 | 自动重连 |
| 4102 | KICKED_BY_ADMIN | 被管理员踢掉 | 不自动重连 |

### 15.5 配置参数

| 参数 | 默认值 | 说明 | 位置 |
|------|--------|------|------|
| heartbeat_interval | 30 | 心跳间隔（秒） | `ws_manager.py:50` |
| heartbeat_timeout | 60 | 心跳超时（秒） | `ws_manager.py:51` |
| maxReconnectAttempts | 5 | 最大重连次数 | `websocket.ts:34` |
| reconnectDelay | 3000 | 重连间隔（毫秒） | `websocket.ts:152` |

---

## 版本历史

| 版本 | 日期 | 变更说明 |
|------|------|---------|
| v1.0 | 2026-03-25 | 初始版本 |

---

**文档结束**