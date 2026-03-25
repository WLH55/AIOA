# 私聊消息转发功能 - 实施计划

## 1. 文件变更清单

| 文件 | 操作 | 说明 |
|-----|------|------|
| `app/services/chat_service.py` | 新增 | 聊天消息处理服务 |
| `app/routers/ws.py` | 修改 | 修改 `_handle_chat` 调用新服务 |
| `app/dto/ws/response.py` | 新增 | WebSocket 响应 DTO |

## 2. 实施步骤

### 步骤1：创建 `app/services/chat_service.py`

**功能：**
- 处理聊天消息发送逻辑
- 区分私聊和群聊
- 生成会话ID
- 保存消息到数据库

**方法签名：**
```python
class ChatService:
    @staticmethod
    async def handle_message(message: ChatMessage, current_user: User) -> dict:
        """
        处理聊天消息

        Args:
            message: 聊天消息
            current_user: 当前用户

        Returns:
            响应消息字典
        """

    @staticmethod
    def generate_conversation_id(user1_id: str, user2_id: str) -> str:
        """
        生成私聊会话ID

        Args:
            user1_id: 用户1 ID
            user2_id: 用户2 ID

        Returns:
            会话ID，格式：private_{min(id1,id2)}_{max(id1,id2)}
        """

    @staticmethod
    async def send_private_message(
        send_id: str,
        recv_id: str,
        content: str,
        content_type: int,
        conversation_id: str
    ) -> dict:
        """
        发送私聊消息

        Returns:
            包含 status 字段的响应：sent/offline/error
        """

    @staticmethod
    async def send_group_message(
        send_id: str,
        group_id: str,
        content: str,
        content_type: int
    ) -> dict:
        """
        发送群聊消息

        Returns:
            响应消息字典
        """
```

### 步骤2：修改 `app/routers/ws.py`

**修改 `_handle_chat` 函数：**
```python
async def _handle_chat(
    websocket: WebSocket,
    session_id: str,
    user: User,
    data: dict
) -> None:
    """
    处理聊天消息
    """
    try:
        message = ChatMessage(**data)
    except Exception as e:
        await _send_error(websocket, WSErrorCode.INVALID_MESSAGE, f"Invalid chat message: {e}")
        return

    logger.info(
        f"收到聊天消息: user_id={user.id}, "
        f"chatType={message.chatType}, content_length={len(message.content)}"
    )

    # 调用 ChatService 处理消息
    from app.services.chat_service import ChatService

    response = await ChatService.handle_message(message, user)

    # 发送响应给发送者
    await ws_manager.send_to_user(str(user.id), response)
```

### 步骤3：创建 `app/dto/ws/response.py`

**定义响应 DTO：**
```python
class ChatResponse(BaseModel):
    """
    聊天响应 DTO
    """
    type: str = "message"
    conversationId: str
    sendId: str
    recvId: Optional[str] = None
    chatType: int
    content: str
    contentType: int
    sendTime: int
    status: Optional[str] = None  # sent/offline/error
```

### 步骤4：错误处理

**错误类型：**
| 错误 | 处理方式 |
|-----|---------|
| 消息为空 | 返回错误，不保存 |
| 不能给自己发消息 | 返回错误 |
| 接收者不存在 | 返回错误 |
| 群聊不存在 | 返回错误 |

## 3. Mock 数据

### 私聊消息发送请求
```json
{
  "type": "chat",
  "conversationId": "",
  "recvId": "69c39d57a4dd62694c34d9f2",
  "sendId": "69c39d88a4dd62694c34d9f3",
  "chatType": 2,
  "content": "你好",
  "contentType": 1
}
```

### 私聊消息响应（接收者在线）
```json
{
  "type": "message",
  "conversationId": "private_69c39d57a4dd62694c34d9f2_69c39d88a4dd62694c34d9f3",
  "sendId": "69c39d88a4dd62694c34d9f3",
  "recvId": "69c39d57a4dd62694c34d9f2",
  "chatType": 2,
  "content": "你好",
  "contentType": 1,
  "sendTime": 1704067200000,
  "status": "sent"
}
```

### 私聊消息响应（接收者离线）
```json
{
  "type": "message",
  "conversationId": "private_69c39d57a4dd62694c34d9f2_69c39d88a4dd62694c34d9f3",
  "sendId": "69c39d88a4dd62694c34d9f3",
  "recvId": "69c39d57a4dd62694c34d9f2",
  "chatType": 2,
  "content": "你好",
  "contentType": 1,
  "sendTime": 1704067200000,
  "status": "offline"
}
```

## 4. 认知对齐

**Q: 为什么要在 Service 层处理而不是直接在 Router 层？**
A: 职责分离原则。Router 层只负责 WebSocket 协议解析和认证，业务逻辑在 Service 层，便于测试和复用。

**Q: 为什么私聊会话ID需要排序？**
A: 确保同一对用户的会话ID唯一，无论谁先发起聊天。

**Q: 接收者离线时消息是否保存？**
A: 保存。消息先持久化，再检查在线状态，确保历史记录完整。

## 5. 依赖检查

- [ ] `app/repository/user_repository.py` - UserRepository.find_by_id
- [ ] `app/repository/group_repository.py` - GroupRepository.find_by_id
- [ ] `app/repository/chat_log_repository.py` - ChatLogRepository.create
- [ ] `app/services/ws_manager.py` - ws_manager.send_to_user, broadcast
