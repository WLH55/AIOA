# 群组功能接口文档

## 1. 创建群组

### 1.1 请求

```
POST /v1/group/create
Authorization: Bearer {token}
Content-Type: application/json
```

**请求体**:
```json
{
  "name": "产品研发讨论组",
  "avatar": "https://example.com/avatar.png",
  "memberIds": ["user123", "user456", "user789"]
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | 是 | 群组名称，1-50字符 |
| avatar | string | 否 | 群头像URL |
| memberIds | string[] | 是 | 初始成员ID列表（必须包含创建者） |

### 1.2 响应

**成功** (201):
```json
{
  "code": 200,
  "message": "创建群组成功",
  "data": "group123456"
}
```

**失败** (400):
```json
{
  "code": 400,
  "message": "成员数量不能超过100人",
  "data": null
}
```

---

## 2. 获取群组列表

### 2.1 请求

```
GET /v1/group/list?page=1&count=20
Authorization: Bearer {token}
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | int | 否 | 页码，默认1 |
| count | int | 否 | 每页数量，默认20 |

### 2.2 响应

**成功** (200):
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "count": 5,
    "data": [
      {
        "id": "group123",
        "name": "产品研发讨论组",
        "avatar": "https://example.com/avatar.png",
        "ownerId": "user123",
        "ownerName": "张三",
        "memberCount": 15,
        "status": 1,
        "createAt": 1704067200000
      }
    ]
  }
}
```

---

## 3. 获取群组详情

### 3.1 请求

```
GET /v1/group/{id}
Authorization: Bearer {token}
```

| 参数 | 类型 | 说明 |
|------|------|------|
| id | string | 群组ID |

### 3.2 响应

**成功** (200):
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": "group123",
    "name": "产品研发讨论组",
    "avatar": "https://example.com/avatar.png",
    "ownerId": "user123",
    "ownerName": "张三",
    "memberIds": ["user123", "user456", "user789"],
    "members": [
      {
        "userId": "user123",
        "userName": "张三",
        "isOwner": true
      },
      {
        "userId": "user456",
        "userName": "李四",
        "isOwner": false
      }
    ],
    "memberCount": 3,
    "status": 1,
    "createAt": 1704067200000,
    "updateAt": 1704067200000
  }
}
```

---

## 4. 邀请成员

### 4.1 请求

```
POST /v1/group/{id}/invite
Authorization: Bearer {token}
Content-Type: application/json
```

**请求体**:
```json
{
  "memberIds": ["user456", "user789"]
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| memberIds | string[] | 是 | 要邀请的成员ID列表 |

### 4.2 响应

**成功** (200):
```json
{
  "code": 200,
  "message": "邀请成员成功",
  "data": null
}
```

**失败** (403):
```json
{
  "code": 403,
  "message": "只有群主可以邀请成员",
  "data": null
}
```

---

## 5. 移除成员

### 5.1 请求

```
POST /v1/group/{id}/remove
Authorization: Bearer {token}
Content-Type: application/json
```

**请求体**:
```json
{
  "memberId": "user456"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| memberId | string | 是 | 要移除的成员ID |

### 5.2 响应

**成功** (200):
```json
{
  "code": 200,
  "message": "移除成员成功",
  "data": null
}
```

---

## 6. 退出群组

### 6.1 请求

```
POST /v1/group/{id}/exit
Authorization: Bearer {token}
```

### 6.2 响应

**成功** (200):
```json
{
  "code": 200,
  "message": "退出群组成功",
  "data": null
}
```

**失败** (400):
```json
{
  "code": 400,
  "message": "群主不能退出群组",
  "data": null
}
```

---

## 7. 修改群组信息

### 7.1 请求

```
PUT /v1/group/{id}
Authorization: Bearer {token}
Content-Type: application/json
```

**请求体**:
```json
{
  "name": "新的群名称",
  "avatar": "https://example.com/new-avatar.png"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | 否 | 新的群组名称 |
| avatar | string | 否 | 新的群头像URL |

### 7.2 响应

**成功** (200):
```json
{
  "code": 200,
  "message": "修改群组信息成功",
  "data": null
}
```

---

## 8. 解散群组

### 8.1 请求

```
DELETE /v1/group/{id}
Authorization: Bearer {token}
```

### 8.2 响应

**成功** (200):
```json
{
  "code": 200,
  "message": "解散群组成功",
  "data": null
}
```

---

## 9. WebSocket 系统消息

### 9.1 群组创建通知

```json
{
  "type": "message",
  "systemType": "group_create",
  "conversationId": "group123",
  "chatType": 1,
  "content": "张三 创建了群组",
  "groupInfo": {
    "groupId": "group123",
    "groupName": "产品研发讨论组",
    "memberIds": ["user123", "user456"],
    "creatorId": "user123"
  }
}
```

### 9.2 群组解散通知

```json
{
  "type": "message",
  "systemType": "group_dismiss",
  "conversationId": "group123",
  "chatType": 1,
  "content": "群组已解散"
}
```

### 9.3 成员邀请通知

```json
{
  "type": "message",
  "systemType": "group_invite",
  "conversationId": "group123",
  "chatType": 1,
  "content": "张三 邀请了 李四 加入群组"
}
```

### 9.4 成员移除通知

```json
{
  "type": "message",
  "systemType": "group_remove",
  "conversationId": "group123",
  "chatType": 1,
  "content": "李四 被移出群组"
}
```

### 9.5 成员退出通知

```json
{
  "type": "message",
  "systemType": "group_exit",
  "conversationId": "group123",
  "chatType": 1,
  "content": "李四 退出了群组"
}
```

---

## 10. 错误码

| 错误码 | 说明 |
|--------|------|
| 400 | 请求参数错误 |
| 403 | 无权限操作 |
| 404 | 群组不存在 |
| 409 | 成员已存在 |
| 410 | 群组已解散 |
