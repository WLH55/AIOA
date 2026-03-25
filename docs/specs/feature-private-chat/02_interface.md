# 私聊消息转发功能 - 接口文档

## 1. WebSocket 消息接口

### 1.1 客户端发送消息

**请求格式：**
```json
{
  "type": "chat",
  "conversationId": "private_user1_user2",  // 私聊时可为空，后端生成
  "recvId": "user2",                        // 接收者ID（私聊必填）
  "sendId": "user1",                        // 发送者ID
  "chatType": 2,                            // 1=群聊, 2=私聊
  "content": "你好",                         // 消息内容
  "contentType": 1                          // 1=文字, 2=图片
}
```

**字段说明：**
| 字段 | 类型 | 必填 | 说明 |
|-----|------|------|------|
| type | string | 是 | 固定值 "chat" |
| conversationId | string | 否 | 私聊可为空，后端自动生成 |
| recvId | string | 条件 | 私聊时必填 |
| sendId | string | 是 | 发送者用户ID |
| chatType | int | 是 | 1=群聊, 2=私聊 |
| content | string | 是 | 消息内容 |
| contentType | int | 是 | 1=文字, 2=图片 |

### 1.2 服务端响应（发送者收到）

**成功响应：**
```json
{
  "type": "message",
  "conversationId": "private_user1_user2",
  "sendId": "user1",
  "recvId": "user2",
  "chatType": 2,
  "content": "你好",
  "contentType": 1,
  "sendTime": 1704067200000,
  "status": "sent"  // sent=已发送, offline=对方不在线
}
```

**错误响应：**
```json
{
  "type": "error",
  "code": 4001,
  "message": "消息内容不能为空"
}
```

### 1.3 接收者收到的消息

```json
{
  "type": "message",
  "conversationId": "private_user1_user2",
  "sendId": "user1",
  "recvId": "user2",
  "chatType": 2,
  "content": "你好",
  "contentType": 1,
  "sendTime": 1704067200000
}
```

## 2. 群聊消息广播

### 2.1 客户端发送群聊消息

```json
{
  "type": "chat",
  "conversationId": "group_abc123",
  "recvId": "",                              // 群聊为空
  "sendId": "user1",
  "chatType": 1,                             // 群聊
  "content": "@所有人 大家好",
  "contentType": 1
}
```

### 2.2 群成员收到的消息

```json
{
  "type": "message",
  "conversationId": "group_abc123",
  "sendId": "user1",
  "recvId": "",
  "chatType": 1,
  "content": "@所有人 大家好",
  "contentType": 1,
  "sendTime": 1704067200000
}
```

## 3. 错误码定义

| 错误码 | 说明 |
|-------|------|
| 4001 | 消息内容不能为空 |
| 4002 | 不能给自己发消息 |
| 4003 | 接收者不存在 |
| 4004 | 群聊不存在 |
| 4005 | 无效的消息类型 |

## 4. 会话ID生成规则

### 4.1 私聊会话ID

**规则：** `private_{min(userId1, userId2)}_{max(userId1, userId2)}`

**示例：**
- user1 和 user2 聊天 → `private_user1_user2`
- user2 和 user1 聊天 → `private_user1_user2`（相同）

### 4.2 群聊会话ID

**规则：** 直接使用 groupId

**示例：**
- `group_abc123`
- `group_xyz789`
