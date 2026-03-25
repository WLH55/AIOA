# 接口文档 - 未读消息红点功能

## 接口概览

| 接口 | 方法 | 说明 |
|------|------|------|
| `/v1/chat/unread/list` | POST | 获取当前用户的未读消息计数列表 |
| `/v1/chat/unread/clear` | POST | 清除指定会话的未读计数 |
| `/v1/chat/unread/increment` | POST | 增加指定会话的未读计数（内部） |

---

## 1. 获取未读消息计数列表

### 接口信息

- **路径**：`/v1/chat/unread/list`
- **方法**：POST
- **认证**：需要 Bearer Token

### 请求参数

```typescript
{
  // 可选：过滤会话类型
  conversationType?: 1 | 2,  // 1=群组，2=私聊
}
```

### 响应数据

```typescript
{
  "code": 200,
  "msg": "success",
  "data": {
    "total": 5,              // 总未读数
    "list": [
      {
        "conversationId": "private_abc123",
        "conversationType": 2,
        "unreadCount": 3,
        "updateAt": 1712345678000
      },
      {
        "conversationId": "group_xyz789",
        "conversationType": 1,
        "unreadCount": 2,
        "updateAt": 1712345679000
      }
    ]
  }
}
```

### 错误响应

| 错误码 | 说明 |
|--------|------|
| 401 | 未认证 |
| 500 | 服务器错误 |

---

## 2. 清除会话未读计数

### 接口信息

- **路径**：`/v1/chat/unread/clear`
- **方法**：POST
- **认证**：需要 Bearer Token

### 请求参数

```typescript
{
  "conversationId": "private_abc123"  // 会话ID
}
```

### 响应数据

```typescript
{
  "code": 200,
  "msg": "清除成功",
  "data": null
}
```

### 错误响应

| 错误码 | 说明 |
|--------|------|
| 400 | 参数错误 |
| 401 | 未认证 |
| 404 | 会话不存在 |
| 500 | 服务器错误 |

---

## 3. 增加会话未读计数（内部）

### 接口信息

- **路径**：`/v1/chat/unread/increment`
- **方法**：POST
- **认证**：不需要（内部服务调用）

### 请求参数

```typescript
{
  "userId": "abc123",           // 用户ID
  "conversationId": "group_xyz", // 会话ID
  "conversationType": 1,        // 会话类型
  "increment": 1                // 增加数量
}
```

### 响应数据

```typescript
{
  "code": 200,
  "msg": "success",
  "data": {
    "userId": "abc123",
    "conversationId": "group_xyz",
    "unreadCount": 5            // 更新后的未读数
  }
}
```

---

## WebSocket 消息格式

### 未读计数更新通知

当未读计数发生变化时，服务器通过 WebSocket 推送更新通知：

```typescript
{
  "type": "unread_update",
  "conversationId": "group_xyz",
  "unreadCount": 3
}
```

### 批量未读计数更新

登录或重连后，服务器推送初始未读计数：

```typescript
{
  "type": "unread_sync",
  "data": [
    {
      "conversationId": "private_abc123",
      "unreadCount": 3
    },
    {
      "conversationId": "group_xyz",
      "unreadCount": 2
    }
  ]
}
```

---

## 数据模型

### UnreadMessage 模型

```typescript
{
  "_id": ObjectId,
  "userId": ObjectId,           // 用户ID
  "conversationId": String,     // 会话ID
  "conversationType": Integer,  // 会话类型：1=群组，2=私聊
  "unreadCount": Integer,       // 未读消息数量
  "lastReadTime": Integer,      // 最后阅读时间（可选）
  "createAt": Integer,          // 创建时间戳
  "updateAt": Integer           // 更新时间戳
}
```

### 索引设计

```javascript
// 复合唯一索引
db.unread_message.createIndex({ userId: 1, conversationId: 1 }, { unique: true })

// 用户查询索引
db.unread_message.createIndex({ userId: 1, unreadCount: 1 })
```

---

## 前端类型定义

```typescript
// src/types/index.ts

export interface UnreadCountItem {
  conversationId: string
  conversationType: number
  unreadCount: number
  updateAt: number
}

export interface UnreadListResponse {
  total: number
  list: UnreadCountItem[]
}

export interface ClearUnreadRequest {
  conversationId: string
}
```