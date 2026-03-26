# AIWorkHelper 聊天系统与已读回执设计文档

---

## 文档信息

| 项目 | 内容 |
|------|------|
| 文档名称 | 聊天系统与已读回执设计文档 |
| 版本 | v1.0 |
| 日期 | 2026-03-26 |
| 项目 | AIWorkHelper 智能办公系统 |
| 作者 | AIWorkHelper 技术团队 |

---

## 目录

- [1. 系统概述](#1-系统概述)
- [2. 技术选型](#2-技术选型)
- [3. 系统架构](#3-系统架构)
- [4. WebSocket 连接管理](#4-websocket-连接管理)
- [5. 消息机制](#5-消息机制)
- [6. 心跳保活机制](#6-心跳保活机制)
- [7. 已读回执机制](#7-已读回执机制)
- [8. 数据模型设计](#8-数据模型设计)
- [9. API 接口设计](#9-api-接口设计)
- [10. 前端实现](#10-前端实现)
- [11. 安全设计](#11-安全设计)
- [12. 性能优化](#12-性能优化)
- [13. 用例图](#13-用例图)
- [14. 流程图](#14-流程图)
- [15. 部署架构](#15-部署架构)

---

## 1. 系统概述

### 1.1 设计目标

本系统为 AIWorkHelper 智能办公平台提供实时通信能力，支持：

- **私聊**: 用户之间的一对一实时消息传递
- **群聊**: 多人协作的群组消息广播
- **单设备登录**: 确保同一账号仅有一个活跃连接
- **消息持久化**: 所有消息可靠存储，支持历史查询
- **离线消息**: 通过未读计数机制处理离线用户
- **已读回执**: 发送者可获知消息是否已被接收者阅读

### 1.2 核心特性

| 特性 | 描述 |
|------|------|
| 连接管理 | 单用户单连接，自动踢掉旧连接 |
| 心跳保活 | 客户端每30秒发送心跳，服务端60秒超时检测 |
| 消息可靠 | 消息先存储后转发，确保不丢失 |
| 已读状态 | 支持私聊和群聊的已读回执 |
| 全局单例 | 前端使用引用计数管理连接复用 |
| 自动重连 | 连接断开后自动尝试重连（最多5次） |

---

## 2. 技术选型

| 组件 | 技术选型 | 版本 | 说明 |
|------|---------|------|------|
| 后端框架 | FastAPI | 0.104+ | 高性能异步 Web 框架 |
| 通信协议 | WebSocket | RFC 6455 | 全双工实时通信协议 |
| 数据库 | MongoDB | 5.0+ | 高性能文档数据库 |
| 前端框架 | Vue 3 | 3.3+ | 渐进式 JavaScript 框架 |
| 状态管理 | Pinia | 2.1+ | Vue 官方状态管理库 |
| 认证方式 | JWT | - | 无状态的 Token 认证 |
| Python 版本 | Python | 3.10+ | 异步编程支持 |

---

## 3. 系统架构

### 3.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              客户端层 (Vue 3)                             │
│                                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │
│  │  Login.vue   │  │Dashboard.vue │  │  Chat.vue    │                  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘                  │
│         │                 │                  │                          │
│         └─────────────────┼──────────────────┘                          │
│                           │                                             │
│                   ┌───────▼────────┐                                   │
│                   │ WebSocketClient │                                   │
│                   │  (全局单例)     │                                   │
│                   └───────┬────────┘                                   │
└───────────────────────────┼─────────────────────────────────────────────┘
                            │
                            │ WebSocket (ws://)
                            │
┌───────────────────────────▼─────────────────────────────────────────────┐
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                   FastAPI 应用层                                │   │
│  │                                                                  │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐               │   │
│  │  │ ws_router  │  │  user_rtr  │  │ group_rtr  │               │   │
│  │  └─────┬──────┘  └────────────┘  └────────────┘               │   │
│  │        │                                                        │   │
│  │  ┌─────▼────────────────────────────────────┐                  │   │
│  │  │      ws_manager (连接管理器)              │                  │   │
│  │  │  - _session_to_user 映射                  │                  │   │
│  │  │  - _user_to_ws 映射                        │                  │   │
│  │  │  - _ws_to_session 映射                     │                  │   │
│  │  │  - _last_pong_time 映射                    │                  │   │
│  │  └─────┬────────────────────────────────────┘                  │   │
│  │        │                                                        │   │
│  │  ┌─────▼──────┐  ┌────────────┐  ┌────────────┐            │   │
│  │  │chat_service│  │unread_svr  │  │read_receipt│            │   │
│  │  └─────┬──────┘  └────────────┘  └────────────┘            │   │
│  └────────┼───────────────────────────────────────────────────┘   │
│           │                                                         │
│  ┌────────▼─────────────────────────────────────────────────┐     │
│  │                   数据访问层 (Repository)                 │     │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐              │     │
│  │  │user_repo │  │chat_repo │  │group_repo│              │     │
│  └────────┬────────────────────────────────────────────────┘     │
│           │                                                         │
│  ┌────────▼─────────────────────────────────────────────────┐     │
│  │                   数据持久层 (MongoDB)                     │     │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐              │     │
│  │  │ user     │  │ chat_log │  │  group   │              │     │
│  │  └──────────┘  └──────────┘  └──────────┘              │     │
│  │  ┌──────────┐  ┌──────────┐                            │     │
│  │  │ unread   │  │read_receipt│                          │     │
│  │  └──────────┘  └──────────┘                            │     │
│  └──────────────────────────────────────────────────────────┘     │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3.2 模块职责划分

| 模块 | 文件路径 | 职责 |
|------|---------|------|
| WebSocket 路由 | `app/routers/ws.py` | WebSocket 端点定义、连接认证、消息路由 |
| 连接管理器 | `app/services/ws_manager.py` | 连接生命周期管理、心跳检测、消息分发 |
| 聊天服务 | `app/services/chat_service.py` | 聊天业务逻辑、消息处理、消息保存 |
| 未读服务 | `app/services/unread_service.py` | 未读计数管理、未读消息查询 |
| 已读回执服务 | `app/services/read_receipt_service.py` | 已读回执创建、查询、统计 |
| 用户仓库 | `app/repository/user_repository.py` | 用户数据访问 |
| 聊天日志仓库 | `app/repository/chat_log_repository.py` | 聊天记录数据访问 |
| 已读回执仓库 | `app/repository/read_receipt_repository.py` | 已读回执数据访问 |
| 消息 DTO | `app/dto/ws/message.py` | WebSocket 消息数据结构定义 |
| 响应 DTO | `app/dto/ws/response.py` | WebSocket 响应数据结构定义 |

---

## 4. WebSocket 连接管理

### 4.1 连接映射关系

服务端维护四个核心映射：

```python
class WebSocketConnectionManager:
    # 连接映射
    _session_to_user: Dict[str, str]           # session_id → user_id
    _user_to_ws: Dict[str, WebSocket]           # user_id → WebSocket
    _ws_to_session: Dict[WebSocket, str]        # WebSocket → session_id
    _last_pong_time: Dict[str, datetime]        # session_id → 最后pong时间
```

#### 映射关系图

```
┌─────────────────────────────────────────────────────────────────┐
│                    ws_manager 内存结构                          │
│                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐                      │
│  │ _session_to_user│  │  _user_to_ws    │                      │
│  ├─────────────────┤  ├─────────────────┤                      │
│  │ sess_abc1 → u1  │  │  u1 → ws_obj1   │                      │
│  │ sess_def2 → u2  │  │  u2 → ws_obj2   │                      │
│  └─────────────────┘  └─────────────────┘                      │
│                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐                      │
│  │ _ws_to_session  │  │ _last_pong_time │                      │
│  ├─────────────────┤  ├─────────────────┤                      │
│  │ ws_obj1 → sess1 │  │ sess1 → time1   │                      │
│  │ ws_obj2 → sess2 │  │ sess2 → time2   │                      │
│  └─────────────────┘  └─────────────────┘                      │
└─────────────────────────────────────────────────────────────────┘
```

#### 映射用途说明

| 映射 | 用途 | 查询场景 |
|------|------|---------| `_user_to_ws` | 根据用户查找连接 | 发送消息时 |
| `_ws_to_session` | 根据连接查找会话 | 连接断开时清理 |
| `_last_pong_time` | 记录最后活跃时间 | 心跳超时检测 |

### 4.2 连接建立流程

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
  │   {                           │
  │     type: "connected",        │
  │     user_id: "xxx",           │
  │     session_id: "yyy"         │
  │   }                           │
  │                               │
  │  6. 进入消息循环               │
  │<═══════════════════════════════│
  │  { type: "ping" } 每30秒       │
  │══════════════════════════════>│
  │  7. 心跳响应                  │
  │  (更新_last_pong_time)        │
```

### 4.3 单设备登录机制

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

### 4.4 连接断开场景

| 场景 | 关闭码 | 说明 | 处理逻辑 |
|------|--------|------|---------|
| 正常关闭 | 1000 | 客户端主动发送 close 消息 | 清理映射，释放资源 |
| 端点离开 | 1001 | 页面关闭、网络断开 | 清理映射，释放资源 |
| 心跳超时 | 1001 | 60秒未收到心跳 | 主动关闭，清理映射 |
| 新登录踢人 | 4100 | 同账号新连接建立 | 发送 kicked 消息后关闭 |
| 管理员踢人 | 4102 | 后台强制踢出 | 发送 kicked 消息后关闭 |

### 4.5 客户端断开连接行为

#### 4.5.1 三种断开场景

前端采用全局单例 + 引用计数机制管理 WebSocket 连接，不同场景下的断开行为不同：

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      客户端关闭/离开页面的三种场景                         │
└─────────────────────────────────────────────────────────────────────────┘

场景 1: 离开聊天页面（但浏览器还有其他页面在使用 WebSocket）
──────────────────────────────────────────────────────────────────────────
  用户操作：从聊天页面切换到其他页面
  │
  ▼
  ┌─────────────────────────────────────────────────────────────────┐
  │  onBeforeUnmount 触发                                            │
  │                                                                  │
  │  1. offMessage() - 移除消息处理器                                │
  │  2. releaseWebSocket() - refCount--                              │
  │                                                                  │
  │  if (refCount > 0) {                                             │
  │    // 其他页面还在使用，连接保持                                  │
  │    return  // 连接不断开！                                       │
  │  }                                                               │
  └─────────────────────────────────────────────────────────────────┘
  │
  ▼
  [WebSocket 连接保持打开]
  [服务端继续检测心跳]
  [服务端不知道用户离开页面]

场景 2: 关闭浏览器标签页（引用计数为 0）
──────────────────────────────────────────────────────────────────────────
  用户操作：关闭标签页
  │
  ▼
  ┌─────────────────────────────────────────────────────────────────┐
  │  浏览器触发 beforeunload 事件                                    │
  │                                                                  │
  │  onBeforeUnmount 触发                                            │
  │                                                                  │
  │  1. offMessage()                                                 │
  │  2. releaseWebSocket() → refCount = 0                            │
  │                                                                  │
  │  调用 client.close()                                             │
  │    ↓                                                             │
  │  ws.close()  // 尝试主动关闭                                     │
  └─────────────────────────────────────────────────────────────────┘
  │
  ├─────────────────────────────────────────────────────────────────┤
  │                                                                  │
  ▼                                                                  ▼
[成功发送 close 帧给服务端]                                  [浏览器已关闭]
  │                                                        (无法发送)
  ▼
服务端立即收到 close 事件
  │
  ▼
┌─────────────────────────────────────────────────────────────────┐
│  ws.py: websocket_chat()                                        │
│                                                                  │
│  try:                                                           │
│    while True:                                                  │
│      data = await websocket.receive_json()  // 收到 close        │
│  except WebSocketDisconnect:  // 触发异常                        │
│    logger.info("WebSocket 断开")                                 │
│  finally:                                                       │
│    await ws_manager.disconnect(websocket)  // 立即清理！         │
└─────────────────────────────────────────────────────────────────┘
  │
  ▼
[立即清理所有映射，不等超时]

场景 3: 浏览器崩溃/强制关闭/网络断开
──────────────────────────────────────────────────────────────────────────
  用户操作：浏览器崩溃、任务管理器结束进程、网线拔掉
  │
  ▼
  ┌─────────────────────────────────────────────────────────────────┐
  │  客户端无法发送任何通知                                         │
  │                                                                  │
  │  WebSocket 连接处于"僵尸"状态                                    │
  └─────────────────────────────────────────────────────────────────┘
  │
  ▼
[服务端不知道连接已断开]
  │
  ▼
[服务端继续等待心跳]
  │
  ▼
┌─────────────────────────────────────────────────────────────────┐
│  心跳检测任务（每30秒）                                          │
│                                                                  │
│  检查: 当前时间 - last_pong_time > 60秒?                         │
│                                                                  │
│  YES → 超时！                                                   │
│    ↓                                                             │
│  主动关闭连接                                                    │
│  清理所有映射                                                    │
└─────────────────────────────────────────────────────────────────┘
```

#### 4.5.2 场景对比

| 场景 | 客户端行为 | 服务端感知 | 服务端处理 | 清理时间 |
|------|----------|----------|----------|---------|
| **离开聊天页面** | 移除处理器，减少引用计数 | 不知道（连接保持） | 继续正常检测心跳 | N/A（连接保持） |
| **关闭标签页** | 尝试发送 close 帧 | **立即感知** | **立即清理映射** | < 1秒 |
| **浏览器崩溃** | 无法通知 | 不知道 | 等待心跳超时 | 最多 60 秒 |

#### 4.5.3 前端代码实现

```typescript
// 聊天页面组件
onBeforeUnmount(() => {
  // 1. 移除消息处理器
  if (wsClient && messageHandler) {
    wsClient.offMessage(messageHandler)
  }

  // 2. 释放 WebSocket 引用（引用计数-1）
  if (wsClient && userStore.token) {
    releaseWebSocket(userStore.token, wsClient)
  }

  // 只有当引用计数为 0 时，才真正关闭连接
  // refCount = 0 → client.close() → ws.close()
})

// WebSocketClient.close() 方法
close(): void {
  this.stopHeartbeat()
  if (this.ws) {
    this.ws.close()  // 主动发送 close 帧
    this.ws = null
  }
  this.messageHandlers = []
}

// releaseWebSocket() 全局函数
export function releaseWebSocket(token: string, client: WebSocketClient): void {
  const instance = globalWsMap.get(token)
  if (instance && instance.client === client) {
    instance.refCount--

    // 只有当引用计数为 0 时才关闭连接
    if (instance.refCount <= 0) {
      client.close()  // 真正关闭连接
      globalWsMap.delete(token)
    }
  }
}
```

#### 4.5.4 服务端处理代码

```python
# ws.py - WebSocket 路由处理
@router.websocket("/chat")
async def websocket_chat(websocket: WebSocket):
    # ... 认证和连接建立 ...

    try:
        # 消息循环
        while True:
            data = await websocket.receive_json()
            # ... 处理消息 ...

    except WebSocketDisconnect:
        # 客户端主动关闭（关闭标签页等情况）
        logger.info(f"WebSocket 断开: user_id={user.id}, session_id={session_id}")

    except Exception as e:
        logger.error(f"WebSocket 异常: user_id={user.id}, error={e}")

    finally:
        # 无论何种断开，都立即清理映射
        await ws_manager.disconnect(websocket)

# ws_manager.py - 断开连接处理
async def disconnect(self, websocket: WebSocket) -> None:
    """断开连接，清理映射"""
    async with self._lock:
        session_id = self._ws_to_session.pop(websocket, None)

        if session_id:
            user_id = self._session_to_user.pop(session_id, None)
            self._last_pong_time.pop(session_id, None)

            if user_id:
                if self._user_to_ws.get(user_id) == websocket:
                    self._user_to_ws.pop(user_id, None)
```

#### 4.5.5 关键要点

**离开聊天页面 ≠ 断开连接**

```javascript
// 当前设计：离开聊天页面
onBeforeUnmount(() => {
  releaseWebSocket(token, wsClient)  // refCount--
  // 如果 refCount > 0，连接不断开！
})

// 结果：服务端不知道用户离开页面
// 影响：心跳继续正常，连接保持
// 原因：全局单例设计，可能其他页面还在使用
```

**关闭标签页 = 主动断开（最佳情况）**

```javascript
// 当前设计：关闭标签页
client.close() {
  this.ws.close()  // 主动发送 close 帧
}

// 结果：服务端立即收到 close 事件
// 影响：立即清理映射，不等超时
// 清理时间：< 1 秒
```

**浏览器崩溃 = 被动超时断开（最差情况）**

```javascript
// 无法发送任何通知

// 服务端等待心跳超时
// 最多 60 秒后清理
```

---

## 5. 消息机制

### 5.1 消息类型定义

#### 客户端可发送的消息

```typescript
enum ClientMessageType {
  CHAT = "chat",       // 聊天消息
  PING = "ping",       // 心跳请求
  PONG = "pong",       // 心跳响应
  CLOSE = "close",     // 关闭连接
  READ_RECEIPT = "read_receipt"  // 已读回执
}
```

#### 服务端可发送的消息

```typescript
enum ServerMessageType {
  CONNECTED = "connected",  // 连接成功
  MESSAGE = "message",      // 消息内容
  READ_RECEIPT = "read_receipt",  // 已读回执通知
  KICKED = "kicked",        // 被踢出
  ERROR = "error"           // 错误消息
}
```

### 5.2 消息数据结构

#### ChatMessage（聊天消息）

```typescript
interface ChatMessage {
  type: "chat"                                    // 消息类型
  conversationId: string                          // 会话ID
  recvId?: string                                 // 接收者ID（群聊为空）
  sendId: string                                  // 发送者ID
  chatType: 1 | 2                                // 1=群聊, 2=私聊
  content: string                                 // 消息内容
  contentType: 1 | 2 | 3                         // 1=文字, 2=图片, 3=表情包
  msgId?: string                                  // 消息ID（可选）
}
```

#### ReadReceiptMessage（已读回执消息）

```typescript
interface ReadReceiptMessage {
  type: "read_receipt"                            // 消息类型
  msgId: string                                   // 消息ID
  conversationId: string                          // 会话ID
}
```

#### ReadReceiptNotification（已读通知）

```typescript
interface ReadReceiptNotification {
  type: "read_receipt"                            // 通知类型
  msgId: string                                   // 消息ID
  conversationId: string                          // 会话ID
  readerId: string                                // 已读者ID
  readerName: string                              // 已读者名称
  readTime: number                                // 已读时间戳（毫秒）
}
```

### 5.3 私聊消息处理流程

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
  │ 3. 保存到    │
  │    MongoDB   │
  └──────┬───────┘
         │
         ▼
  ┌──────────────┐
  │ 4. 增加 B 的 │
  │    未读计数  │
  └──────┬───────┘
         │
    ┌────┴────┐
    │         │
   在线       离线
    │         │
    ▼         ▼
┌─────────┐ ┌─────────┐
│5. 转发给│ │status=  │
│   B     │ │"offline"│
└─────────┘ └─────────┘
    │
    ▼
┌─────────┐
│6. 返回  │
│  给 A   │
│status=  │
│"sent"  │
└─────────┘
```

### 5.4 群聊消息处理流程

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

## 6. 心跳保活机制

### 6.1 心跳参数配置

| 参数 | 默认值 | 说明 |
|------|--------|------|
| heartbeat_interval | 30 秒 | 客户端发送心跳的间隔时间 |
| heartbeat_timeout | 60 秒 | 超时判定阈值（2 个间隔） |

### 6.2 心跳机制流程图

```
服务端                           客户端
  │                               │
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

                                    │
                                    │ 客户端每 30 秒
                                    │
                                    │ ──────────────────────────>
                                    │  { type: "ping" }
                                    │
                                    │                    [更新 last_pong_time]
                                    │
                                    │  (服务端不回 pong，只更新时间)
```

### 6.3 心跳超时处理

```python
async def _check_timeout_connections(self) -> None:
    """
    检查并清理超时连接
    """
    now = datetime.utcnow()
    timeout_seconds = self._heartbeat_timeout  # 60秒

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

            # 清理所有映射
            self._session_to_user.pop(session_id, None)
            self._user_to_ws.pop(user_id, None)
            self._ws_to_session.pop(websocket, None)
            self._last_pong_time.pop(session_id, None)
```

---

## 7. 已读回执机制

### 7.1 已读回执设计目标

1. **私聊已读**: 发送者可获知接收者是否已阅读消息
2. **群聊已读**: 发送者可查看群组成员的已读状态
3. **已读时间**: 记录消息被阅读的具体时间
4. **隐私保护**: 支持用户选择是否发送已读回执

### 7.2 已读回执触发时机

| 场景 | 是否触发 | 说明 |
|------|---------|------|
| 用户打开聊天会话 | ✅ 是 | 发送会话中最早未读消息的已读回执 |
| 用户在聊天列表滑动 | ❌ 否 | 不触发已读 |
| 消息已存在已读回执 | ❌ 否 | 避免重复通知 |
| 用户禁用已读回执 | ❌ 否 | 隐私保护 |

### 7.3 已读回执数据模型

#### ReadReceipt（已读回执）

```python
class ReadReceipt(BaseDocument):
    """消息已读回执模型"""

    msgId: str                     # 消息ID
    conversationId: str             # 会话ID
    conversationType: int           # 1=群组, 2=私聊
    senderId: str                  # 发送者ID
    readerId: str                  # 已读者ID
    readerName: str                # 已读者名称
    readTime: int                  # 已读时间戳（毫秒）

    class Settings:
        name = "read_receipt"
        indexes = [
            "msgId",               # 消息ID索引
            [("msgId", 1), ("readerId", 1)],  # 复合唯一索引（防止重复）
            [("conversationId", 1), ("senderId", 1)],  # 查询某会话的已读状态
            [("readerId", 1), ("readTime", -1)],  # 查询用户的已读记录
        ]
```

### 7.4 私聊已读回执流程

```
用户 A                              服务端                              用户 B
  │                                  │                                  │
  │  ─────────发送消息─────────────>│                                  │
  │   "你好"                                                          │
  │                                  │ ─────────转发消息─────────────>│
  │                                  │  "你好"                          │
  │                                  │                                  │
  │  <──────确认────────────────     │              [B 收到消息]         │
  │   status: "sent"                 │                   (未读)          │
  │                                  │                                  │
  │                                  │              [B 打开聊天]         │
  │                                  │                                  │
  │                                  │<────── 已读回执 ─────────────────│
  │                                  │  { type: "read_receipt",         │
  │                                  │    msgId: "msg_123" }            │
  │                                  │                                  │
  │  <───────已读通知─────────────────│                                  │
  │   { type: "read_receipt",         │                                  │
  │     msgId: "msg_123",             │                                  │
  │     conversationId: "private_...",│                                  │
  │     readerId: "user_B",           │                                  │
  │     readerName: "张三",            │                                  │
  │     readTime: 1649999999000 }     │                                  │
  │                                  │                                  │
  │  [A 界面显示: "已读 14:59"]       │                                  │
```

### 7.5 群聊已读回执流程

```
用户 A                              服务端                    群成员 B/C/D
  │                                  │                             │
  │  ─────────发送消息─────────────>│                             │
  │   "@所有人 明天开会"                                              │
  │                                  │ ─────────广播消息────────────>
  │                                  │                             │
  │  <──────确认────────────────     │  [B 打开聊天]               │
  │   status: "sent"                 │                             │
  │                                  │<────── 已读回执 ─────────────│
  │                                  │  msgId: "msg_456"            │
  │  <──────已读通知(B)────────────  │  readerId: "user_B"          │
  │   { readerId: "user_B",          │                             │
  │     readerName: "张三" }          │                             │
  │                                  │  [C 打开聊天]               │
  │                                  │<────── 已读回执 ─────────────│
  │  <──────已读通知(C)────────────  │  readerId: "user_C"          │
  │   { readerId: "user_C",          │                             │
  │     readerName: "李四" }          │                             │
  │                                  │                             │
  │  [A 界面显示: "已读 2/4"]         │  [D 未打开聊天]             │
  │   点击查看: [张三, 李四]          │                             │
```

### 7.6 已读回执服务接口

```python
class ReadReceiptService:
    """已读回执服务"""

    @staticmethod
    async def create_read_receipt(
        msg_id: str,
        conversation_id: str,
        reader_id: str,
        reader_name: str
    ) -> ReadReceipt:
        """
        创建已读回执

        1. 检查是否已存在回执（防止重复）
        2. 创建已读回执记录
        3. 通知消息发送者
        """

    @staticmethod
    async def get_msg_read_status(
        msg_id: str
    ) -> dict:
        """
        获取消息的已读状态

        返回：已读人数、未读人数、已读用户列表
        """

    @staticmethod
    async def get_conversation_read_status(
        conversation_id: str,
        sender_id: str
    ) -> list:
        """
        获取会话中发送者的所有消息已读状态
        """
```

---

## 8. 数据模型设计

### 8.1 ChatLog（聊天记录）

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
            "conversationId",     # 会话ID索引
            [("sendId", 1), ("sendTime", -1)],  # 查询用户消息
            [("conversationId", 1), ("sendTime", -1)],  # 查询会话历史
        ]
```

### 8.2 UnreadMessage（未读消息）

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
            [(("userId", 1), ("conversationId", 1)],  # 复合唯一索引
            [("userId", 1), ("unreadCount", 1)],     # 查询索引
        ]
```

### 8.3 ReadReceipt（已读回执）

```python
class ReadReceipt(BaseDocument):
    """消息已读回执模型"""

    msgId: str                     # 消息ID
    conversationId: str             # 会话ID
    conversationType: int           # 1=群组, 2=私聊
    senderId: str                  # 发送者ID
    readerId: str                  # 已读者ID
    readerName: str                # 已读者名称
    readTime: int                  # 已读时间戳（毫秒）

    class Settings:
        name = "read_receipt"
        indexes = [
            "msgId",               # 消息ID索引
            [("msgId", 1), ("readerId", 1)],  # 复合唯一索引
            [("conversationId", 1), ("senderId", 1)],
            [("readerId", 1), ("readTime", -1)],
        ]
```

### 8.4 会话ID 生成规则

#### 私聊会话ID

**格式**: `private_{min(userId1,userId2)}_{max(userId1,userId2)}`

**示例**:
```
user1 = "abc", user2 = "xyz"
conversationId = "private_abc_xyz"
```

**生成代码**:
```python
@staticmethod
def generate_conversation_id(user1_id: str, user2_id: str) -> str:
    """
    生成私聊会话ID
    规则：private_{min(userId1, userId2)}_{max(userId1, userId2)}
    """
    if user1_id == user2_id:
        raise BusinessValidationException("不能给自己发消息")

    sorted_ids = sorted([user1_id, user2_id])
    return f"private_{sorted_ids[0]}_{sorted_ids[1]}"
```

#### 群聊会话ID

**格式**: 直接使用群组ID

---

## 9. API 接口设计

### 9.1 WebSocket 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/v1/ws/chat` | WebSocket | 聊天连接端点 |

### 9.2 HTTP API 端点

#### 未读消息相关

| 端点 | 方法 | 说明 |
|------|------|------|
| `/v1/chat/unread/list` | POST | 获取未读消息列表 |
| `/v1/chat/unread/clear` | POST | 清除会话未读计数 |

#### 已读回执相关

| 端点 | 方法 | 说明 |
|------|------|------|
| `/v1/chat/read/status` | GET | 获取消息已读状态 |
| `/v1/chat/read/conversation` | GET | 获取会话已读状态 |

### 9.3 请求/响应示例

#### 获取未读消息列表

**请求**:
```json
POST /v1/chat/unread/list
{
  "conversationType": 2  // 可选：1=群组, 2=私聊
}
```

**响应**:
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "total": 5,
    "list": [
      {
        "conversationId": "private_abc_def",
        "conversationType": 2,
        "unreadCount": 3,
        "updateAt": 1649999999000
      }
    ]
  }
}
```

#### 获取消息已读状态

**请求**:
```json
GET /v1/chat/read/status?msgId=msg_123
```

**响应**:
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "msgId": "msg_123",
    "readCount": 2,
    "unreadCount": 1,
    "readUsers": [
      {
        "userId": "user_B",
        "userName": "张三",
        "readTime": 1649999999000
      }
    ]
  }
}
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

```typescript
interface WsInstance {
  client: WebSocketClient
  token: string
  refCount: number  // 引用计数
}

const globalWsMap = new Map<string, WsInstance>()

export function getWebSocket(token: string): WebSocketClient {
  let instance = globalWsMap.get(token)

  if (!instance) {
    const client = new WebSocketClient(fullUrl, token)
    instance = { client, token, refCount: 0 }
    globalWsMap.set(token, instance)
  }

  instance.refCount++
  return instance.client
}
```

### 10.3 已读回执发送时机

```typescript
// 打开聊天会话时
async function openChat(conversationId: string) {
  // 1. 加载历史消息
  const messages = await getMessages(conversationId)

  // 2. 获取最早的一条未读消息
  const firstUnreadMsg = messages.find(m => !m.read)

  if (firstUnreadMsg) {
    // 3. 发送已读回执
    ws.send({
      type: 'read_receipt',
      msgId: firstUnreadMsg.msgId,
      conversationId: conversationId
    })
  }

  // 4. 清除未读计数
  await api.clearUnread(conversationId)
}
```

### 10.4 组件生命周期管理

#### 10.4.1 生命周期流程

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      Vue 组件生命周期与 WebSocket                        │
└─────────────────────────────────────────────────────────────────────────┘

用户打开聊天页面
  │
  ▼
┌─────────────────────────────────────────────────────────────────┐
│  onMounted()                                                     │
│                                                                  │
│  1. wsClient = getWebSocket(token)                                │
│     - 检查 globalWsMap 是否已有连接                               │
│     - 有则复用，refCount++                                        │
│     - 无则创建新连接                                              │
│                                                                  │
│  2. wsClient.connect()                                            │
│     - 建立 WebSocket 连接                                          │
│     - 启动心跳定时器                                              │
│                                                                  │
│  3. wsClient.onMessage(messageHandler)                            │
│     - 注册消息处理器                                              │
│                                                                  │
│  4. 加载聊天历史                                                  │
└─────────────────────────────────────────────────────────────────┘
  │
  ▼
  ┌─────────────────────────────────────────────────────────────────┐
  │  运行期                                                          │
  │                                                                  │
  │  - 接收实时消息                                                  │
  │  - 发送聊天消息                                                  │
  │  - 心跳保活                                                      │
  │  - 已读回执                                                      │
  └─────────────────────────────────────────────────────────────────┘
  │
  ▼
用户离开聊天页面 / 关闭浏览器
  │
  ▼
┌─────────────────────────────────────────────────────────────────┐
│  onBeforeUnmount()                                               │
│                                                                  │
│  1. wsClient.offMessage(messageHandler)                          │
│     - 移除消息处理器                                              │
│                                                                  │
│  2. releaseWebSocket(token, wsClient)                            │
│     - refCount--                                                 │
│     - if (refCount <= 0) { wsClient.close() }                     │
│                                                                  │
│  3. wsClient.close() 调用时机：                                    │
│     - refCount = 0 时（没有任何页面使用）                          │
│     - 浏览器触发 beforeunload 事件（关闭标签页）                   │
└─────────────────────────────────────────────────────────────────┘
```

#### 10.4.2 代码实现

```typescript
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { getWebSocket, releaseWebSocket, WebSocketClient } from '@/utils/websocket'
import type { WsMessage } from '@/types'

// WebSocket 客户端实例
const wsClient = ref<WebSocketClient | null>(null)
const wsConnected = ref(false)

// 消息处理器
const messageHandler = (message: WsMessage) => {
  switch (message.type) {
    case 'message':
      // 处理聊天消息
      break
    case 'read_receipt':
      // 处理已读回执
      break
    case 'kicked':
      // 处理被踢下线
      break
  }
}

// 组件挂载
onMounted(async () => {
  // 1. 获取 WebSocket 连接（全局单例）
  const userStore = useUserStore()
  wsClient.value = getWebSocket(userStore.token)

  // 2. 建立连接（如果还未连接）
  if (!wsClient.value.isConnected) {
    await wsClient.value.connect()
  }

  wsConnected.value = true

  // 3. 注册消息处理器
  wsClient.value.onMessage(messageHandler)

  // 4. 加载聊天历史
  await loadChatHistory()
})

// 组件卸载
onBeforeUnmount(() => {
  console.log('[组件销毁] 清理WebSocket资源')

  // 1. 移除消息处理器
  if (wsClient.value && messageHandler) {
    wsClient.value.offMessage(messageHandler)
    console.log('[组件销毁] 消息处理器已移除')
  }

  // 2. 释放 WebSocket 引用（引用计数-1）
  const userStore = useUserStore()
  if (wsClient.value && userStore.token) {
    releaseWebSocket(userStore.token, wsClient.value)
    console.log('[组件销毁] WebSocket 引用已释放')
  }

  wsConnected.value = false
  wsClient.value = null
})
```

#### 10.4.3 releaseWebSocket 实现

```typescript
// 释放 WebSocket 引用
export function releaseWebSocket(token: string, client: WebSocketClient): void {
  const instance = globalWsMap.get(token)

  // 验证是否为同一个实例
  if (instance && instance.client === client) {
    instance.refCount--
    console.log(`[WebSocket] 释放引用，当前引用计数: ${instance.refCount}`)

    // 只有当引用计数为 0 时才关闭连接
    if (instance.refCount <= 0) {
      console.log('[WebSocket] 引用计数为0，关闭连接')
      client.close()  // 真正关闭连接
      globalWsMap.delete(token)
    }
  }
}
```

#### 10.4.4 浏览器事件监听

```typescript
// 监听浏览器关闭事件（可选）
onMounted(() => {
  const handleBeforeUnload = (e: BeforeUnloadEvent) => {
    // 可以在这里做一些清理工作
    // 但浏览器可能会限制异步操作
    console.log('[浏览器] 页面即将卸载')
  }

  window.addEventListener('beforeunload', handleBeforeUnload)

  onBeforeUnmount(() => {
    window.removeEventListener('beforeunload', handleBeforeUnload)
  })
})
```

#### 10.4.5 不同场景下的引用计数变化

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      引用计数变化场景                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  场景 1: 单页面使用                                                    │
│  ─────────────────────────────────────────────────────────────────     │
│  打开聊天页面: refCount = 0 → 1                                         │
│  关闭聊天页面: refCount = 1 → 0 → 关闭连接                              │
│                                                                         │
│  场景 2: 多页面共享                                                    │
│  ─────────────────────────────────────────────────────────────────     │
│  页面A打开聊天: refCount = 0 → 1                                        │
│  页面B打开聊天: refCount = 1 → 2                                        │
│  页面A关闭:     refCount = 2 → 1（连接保持）                            │
│  页面B关闭:     refCount = 1 → 0 → 关闭连接                              │
│                                                                         │
│  场景 3: 标签页关闭                                                    │
│  ─────────────────────────────────────────────────────────────────     │
│  正常运行:     refCount = 1                                            │
│  关闭标签页:   refCount = 1 → 0 → 立即发送 close 帧                     │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 11. 安全设计

### 11.1 认证机制

**JWT Token 认证**:
- Token 必须是 access 类型
- Token 必须有效且未过期
- 用户必须存在且状态正常（status=1）

### 11.2 防止未授权访问

1. **连接时认证**: 建立 WebSocket 连接前验证 Token
2. **消息验证**: 处理消息时验证用户权限
3. **群组权限**: 发送群聊消息时验证用户是否为群成员

### 11.3 防止消息篡改

1. **服务端验证**: 所有消息参数在服务端重新验证
2. **会话ID生成**: 私聊会话ID由服务端生成，防止伪造
3. **时间戳服务端生成**: 消息时间戳由服务端设置

---

## 12. 性能优化

### 12.1 连接复用

**全局单例 + 引用计数**:
- 同一 token 的多个页面共享一个连接
- 减少连接数量，降低服务器负载

### 12.2 批量操作

**群聊未读计数**:
- 使用 `increment_for_conversation` 批量更新
- 避免多次数据库查询

### 12.3 索引优化

**MongoDB 索引**:
```python
class ChatLog(Document):
    class Settings:
        indexes = [
            "conversationId",
            [("sendId", 1), ("sendTime", -1)],
            [("conversationId", 1), ("sendTime", -1)],
        ]
```

---

## 13. 用例图

### 13.1 系统用例图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            AIWorkHelper 聊天系统                         │
│                                                                         │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐        │
│  │  普通用户  │    │  管理员   │    │  系统定时 │    │  WebSocket│        │
│  └─────┬────┘    └─────┬────┘    └─────┬────┘    └─────┬────┘        │
│        │                │                │                │             │
│        │                │                │                │             │
│   ┌────┴────────────────┴────────────────┴────────────────┴─────┐     │
│   │                                                             │     │
│   │  用例：                                                     │     │
│   │  ┌─────────────────────────────────────────────────────────┐│     │
│   │  │  UC01: 发送私聊消息                                     ││     │
│   │  │  UC02: 发送群聊消息                                     ││     │
│   │  │  UC03: 接收实时消息                                     ││     │
│   │  │  UC04: 查看历史消息                                     ││     │
│   │  │  UC05: 查看未读消息                                     ││     │
│   │  │  UC06: 清除未读计数                                     ││     │
│   │  │  UC07: 查看消息已读状态                                 ││     │
│   │  │  UC08: 发送已读回执                                     ││     │
│   │  │  UC09: 接收已读通知                                     ││     │
│   │  │  UC10: 单设备登录（踢掉旧连接）                         ││     │
│   │  │  UC11: 心跳保活                                         ││     │
│   │  │  UC12: 自动重连                                         ││     │
│   │  │  UC13: 踢出用户（管理员）                               ││     │
│   │  │  UC14: 心跳超时检测（系统定时任务）                      ││     │
│   │  └─────────────────────────────────────────────────────────┘│     │
│   │                                                             │     │
│   └─────────────────────────────────────────────────────────────┘     │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 13.2 已读回执用例图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            已读回执功能                                  │
│                                                                         │
│  ┌──────────┐                    ┌──────────┐                          │
│  │  发送者   │                    │  接收者   │                          │
│  └─────┬────┘                    └─────┬────┘                          │
│        │                              │                               │
│        │                              │                               │
│   ┌────┴──────────────────────────────┴─────┐                         │
│   │                                         │                         │
│   │  用例：                                 │                         │
│   │  ┌─────────────────────────────────────┐│                         │
│   │  │  UC_READ_01: 打开聊天会话           ││                         │
│   │  │  UC_READ_02: 发送已读回执           ││                         │
│   │  │  UC_READ_03: 接收已读通知           ││                         │
│   │  │  UC_READ_04: 查看消息已读状态       ││                         │
│   │  │  UC_READ_05: 查看群聊已读成员       ││                         │
│   │  └─────────────────────────────────────┘│                         │
│   │                                         │                         │
│   └─────────────────────────────────────────┘                         │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 14. 流程图

### 14.1 私聊消息完整流程

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        私聊消息发送完整流程                              │
└─────────────────────────────────────────────────────────────────────────┘

 用户 A                          服务端                          用户 B
   │                               │                               │
   │  1. 发送聊天消息               │                               │
   │  ──────────────────────────>  │                               │
   │   { type: "chat",             │                               │
   │     recvId: "user_B",         │                               │
   │     content: "你好" }          │                               │
   │                               │                               │
   │                               │  2. 验证消息                  │
   │                               │  - 内容非空                   │
   │                               │  - B 存在                     │
   │                               │                               │
   │                               │  3. 生成会话ID                │
   │                               │  private_min_max(A,B)         │
   │                               │                               │
   │                               │  4. 保存到 MongoDB            │
   │                               │                               │
   │                               │  5. 增加 B 的未读计数         │
   │                               │                               │
   │                               │  6. 判断 B 是否在线           │
   │                               │                               │
   │  7. 返回确认                  │                               │
   │  <─────────────────────────── │                               │
   │   { type: "message",          │                               │
   │     status: "sent" }          │                               │
   │                               │                               │
   │                               │  8. 转发消息给 B              │
   │                               │  ──────────────────────────> │
   │                               │   { type: "message",         │
   │                               │     content: "你好" }         │
   │                               │                               │
   │                               │                        9. B 打开聊天
   │                               │                               │
   │                               │  10. 已读回执                │
   │                               │  <────────────────────────── │
   │                               │   { type: "read_receipt",    │
   │                               │     msgId: "xxx" }           │
   │                               │                               │
   │  11. 已读通知                  │                               │
   │  <─────────────────────────── │                               │
   │   { type: "read_receipt",      │                               │
   │     readerId: "user_B",        │                               │
   │     readTime: 1649999999000 }  │                               │
   │                               │                               │
   │  12. A 显示 "已读"             │                               │
   │   [界面更新]                   │                               │
```

### 14.2 群聊消息完整流程

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        群聊消息发送完整流程                              │
└─────────────────────────────────────────────────────────────────────────┘

 用户 A                          服务端               群成员 B/C/D
   │                               │                      │
   │  1. 发送群聊消息               │                      │
   │  ──────────────────────────>  │                      │
   │   { type: "chat",             │                      │
   │     conversationId: "group_1", │                      │
   │     content: "开会" }          │                      │
   │                               │                      │
   │                               │  2. 验证消息          │
   │                               │  - 内容非空           │
   │                               │  - 群组存在           │
   │                               │  - A 是成员           │
   │                               │                      │
   │                               │  3. 保存到 MongoDB   │
   │                               │                      │
   │                               │  4. 获取群成员        │
   │                               │  [A,B,C,D]            │
   │                               │                      │
   │                               │  5. 排除发送者 A      │
   │                               │  [B,C,D]              │
   │                               │                      │
   │                               │  6. 批量增加未读      │
   │                               │                      │
   │  7. 返回确认                  │                      │
   │  <─────────────────────────── │                      │
   │   { type: "message",          │                      │
   │     status: "sent" }          │                      │
   │                               │                      │
   │                               │  8. 广播给 B/C/D      │
   │                               │  ─┬─────────────────> │
   │                               │   │ ─────────────────>│
   │                               │   └─────────────────>│
   │                               │                      │
   │                               │            9. B 打开聊天
   │                               │  <───────────────────│
   │                               │   已读回执            │
   │                               │                      │
   │  10. B 已读通知               │                      │
   │  <─────────────────────────── │                      │
   │   { readerId: "user_B" }      │                      │
   │                               │                      │
   │                               │           10. C 打开聊天
   │                               │  <───────────────────│
   │                               │   已读回执            │
   │                               │                      │
   │  11. C 已读通知               │                      │
   │  <─────────────────────────── │                      │
   │   { readerId: "user_C" }      │                      │
   │                               │                      │
   │  12. A 显示 "已读 2/3"        │  D 未打开             │
   │   点击查看: [张三, 李四]       │                      │
```

### 14.3 连接断开重连流程

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        连接断开与重连流程                                │
└─────────────────────────────────────────────────────────────────────────┘

 客户端                          服务端
   │                               │
   │  1. 连接已建立                 │
   │  ──────────────────────────>  │
   │                               │
   │  <─────────────────────────── │
   │   { type: "connected" }       │
   │                               │
   │  [心跳: 每30秒发送 ping]       │
   │  ──────────────────────────>  │
   │                               │
   │                               │  [心跳检测: 每30秒]
   │                               │  检查: 当前时间 - last_pong > 60s?
   │                               │
   │                               │  2. 检测到超时
   │                               │  ──────────────────────────>
   │   关闭连接 (code=1001)         │
   │  <─────────────────────────── │
   │                               │
   │  3. onclose 触发               │
   │  [event.code = 1001]           │
   │  [event.reason = "heartbeat_timeout"]                             │
   │                               │
   │  4. 判断是否可以重连            │
   │  - 非被踢 (4100/4102)          │
   │  - 未达到最大重连次数          │
   │                               │
   │  5. 延迟 3 秒 × 重连次数         │
   │  等待...                       │
   │                               │
   │  6. 尝试重新连接               │
   │  ──────────────────────────>  │
   │   (携带 Token)                 │
   │                               │
   │                               │  7. 验证 Token
   │                               │  建立新连接
   │                               │
   │  8. 重连成功                   │
   │  <─────────────────────────── │
   │   { type: "connected" }       │
   │                               │
   │  9. 重新注册消息处理器          │
   │  [恢复监听消息]                │
```

### 14.4 已读回执处理流程

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        已读回执处理流程                                  │
└─────────────────────────────────────────────────────────────────────────┘

 接收者 B                        服务端                        发送者 A
    │                               │                               │
    │  1. 打开聊天会话               │                               │
    │  ─── 加载历史消息 ──────────>  │                               │
    │                               │                               │
    │  2. 获取最早未读消息           │                               │
    │  <─────────────────────────── │                               │
    │   messages[0]                 │                               │
    │    .msgId = "msg_123"         │                               │
    │                               │                               │
    │  3. 发送已读回执               │                               │
    │  ──────────────────────────>  │                               │
    │   { type: "read_receipt",     │                               │
    │     msgId: "msg_123" }        │                               │
    │                               │                               │
    │                               │  4. 检查是否已存在回执         │
    │                               │  SELECT * FROM read_receipt    │
    │                               │  WHERE msgId="msg_123"         │
    │                               │    AND readerId="user_B"        │
    │                               │                               │
    │                               │  5. 不存在，创建回执           │
    │                               │  INSERT INTO read_receipt       │
    │                               │  (msgId, readerId, readTime)    │
    │                               │                               │
    │                               │  6. 查询消息发送者             │
    │                               │  SELECT sendId FROM chat_log   │
    │                               │  WHERE msgId="msg_123"         │
    │                               │  → senderId = "user_A"         │
    │                               │                               │
    │                               │  7. 通知发送者 A              │
    │                               │  ──────────────────────────>  │
    │                               │   { type: "read_receipt",      │
    │                               │     msgId: "msg_123",          │
    │                               │     readerId: "user_B",        │
    │                               │     readerName: "张三",         │
    │                               │     readTime: 1649999999000 }  │
    │                               │                               │
    │  8. 清除未读计数               │                               │
    │  ───────── HTTP POST ────────>│                               │
    │   /chat/unread/clear          │                               │
    │                               │                               │
    │                               │  9. 更新未读计数               │
    │                               │  UPDATE unread_message         │
    │                               │  SET unreadCount = 0           │
    │                               │  WHERE userId="user_B"         │
    │                               │                               │
    │  10. 响应成功                  │                               │
    │  <─────────────────────────── │                               │
    │   { "message": "清除成功" }    │                               │
    │                               │                          11. A 收到已读通知
    │                               │                               │
    │                               │                          12. A 显示 "已读"
    │                               │                             [界面更新]
```

---

## 15. 部署架构

### 15.1 单机部署架构

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              负载均衡                                  │
│                           (Nginx / Traefik)                            │
│                                                                         │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │
                                │ WebSocket 转发
                                │ HTTP(S) 代理
                ┌───────────────┴───────────────┐
                │                               │
┌───────────────▼──────────────┐  ┌─────────────▼──────────────┐
│     FastAPI 服务实例 1       │  │    FastAPI 服务实例 2     │
│  ┌─────────────────────────┐ │  │ ┌─────────────────────────┐│
│  │   WebSocket 连接池       │ │  │ │   WebSocket 连接池      ││
│  │   (内存中维护)           │ │  │ │   (内存中维护)          ││
│  └─────────────────────────┘ │  │ └─────────────────────────┘│
│  ┌─────────────────────────┐ │  │ ┌─────────────────────────┐│
│  │   业务逻辑处理          │ │  │ │   业务逻辑处理          ││
│  └─────────────────────────┘ │  │ └─────────────────────────┘│
└───────────────┬──────────────┘  └─────────────┬──────────────┘
                │                               │
                └───────────────┬───────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────────────┐
│                              MongoDB 副本集                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                │
│  │   Primary    │  │  Secondary 1 │  │  Secondary 2 │                │
│  │   (主节点)    │  │   (从节点)    │  │   (从节点)    │                │
│  └──────────────┘  └──────────────┘  └──────────────┘                │
└─────────────────────────────────────────────────────────────────────────┘
```

### 15.2 会话亲和性（Session Affinity）

由于 WebSocket 是有状态连接，需要确保同一用户的请求路由到同一服务实例：

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      WebSocket 连接路由                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  用户 A 首次连接                                                        │
│  │                                                                     │
│  │  负载均衡器（IP Hash / Cookie）                                     │
│  │  ────────────────────────────────────────────────────────>          │
│  │                                                   实例 1           │
│  │                                                   (建立连接)       │
│  │                                                                     │
│  │  后续请求（同一用户）                                              │
│  │  ────────────────────────────────────────────────────────>          │
│  │                                                   实例 1           │
│  │                                                   (复用连接)       │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 附录

### A. 消息类型参考

| 消息类型 | 方向 | 说明 |
|---------|------|------|
| `chat` | 客户端→服务端 | 聊天消息 |
| `ping` | 客户端→服务端 | 心跳请求 |
| `pong` | 客户端→服务端 | 心跳响应 |
| `close` | 客户端→服务端 | 关闭连接请求 |
| `read_receipt` | 客户端→服务端 | 已读回执 |
| `connected` | 服务端→客户端 | 连接成功 |
| `message` | 服务端→客户端 | 消息内容 |
| `read_receipt` | 服务端→客户端 | 已读通知 |
| `kicked` | 服务端→客户端 | 被踢出 |
| `error` | 服务端→客户端 | 错误消息 |

### B. 关闭码参考

| 关闭码 | 名称 | 说明 | 客户端行为 |
|--------|------|------|-----------|
| 1000 | NORMAL | 正常关闭 | - |
| 1001 | GOING_AWAY | 端点离开 | - |
| 4001 | AUTH_REQUIRED | 需要认证 | 重新登录 |
| 4002 | INVALID_TOKEN | Token无效 | 重新登录 |
| 4004 | USER_NOT_FOUND | 用户不存在 | - |
| 4005 | USER_INACTIVE | 用户被禁用 | - |
| 4100 | KICKED_BY_NEW_LOGIN | 被新登录踢掉 | 不自动重连 |
| 4101 | HEARTBEAT_TIMEOUT | 心跳超时 | 自动重连 |
| 4102 | KICKED_BY_ADMIN | 被管理员踢掉 | 不自动重连 |
| 6001 | UNKNOWN_MESSAGE | 未知消息类型 | - |
| 6002 | INVALID_MESSAGE | 消息格式错误 | - |

### C. 配置参数

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
| v1.0 | 2026-03-26 | 初始版本，包含聊天系统与已读回执功能设计 |

---

**文档结束**
