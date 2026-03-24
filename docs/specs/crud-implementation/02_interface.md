# 接口契约文档 - CRUD 业务接口实现

## 1. 概述

本文档定义所有 CRUD 业务接口的 Request/Response 格式、错误码、示例。

---

## 2. 通用定义

### 2.1 统一响应格式

```json
{
  "code": 200,
  "message": "success",
  "data": { ... }
}
```

### 2.2 通用错误码

| 错误码 | 说明 |
|-------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 401 | 未认证 |
| 403 | 无权限 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

---

## 3. User 模块接口

### 3.1 POST /api/v1/user/login

**请求**：
```json
{
  "name": "admin",
  "password": "123456"
}
```

**响应**：
```json
{
  "code": 200,
  "message": "登录成功",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer",
    "expires_in": 864000,
    "user": {
      "user_id": "507f1f77bcf86cd799439011",
      "name": "admin",
      "status": 0,
      "is_admin": true
    }
  }
}
```

### 3.2 GET /api/v1/user/{user_id}

**响应**：
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "user_id": "507f1f77bcf86cd799439011",
    "name": "admin",
    "status": 0,
    "is_admin": true,
    "create_at": 1704067200000,
    "update_at": 1704067200000
  }
}
```

### 3.3 POST /api/v1/user

**请求**：
```json
{
  "name": "zhangsan",
  "password": "123456",
  "status": 1
}
```

**响应**：
```json
{
  "code": 200,
  "message": "创建用户成功",
  "data": null
}
```

### 3.4 GET /api/v1/user/list

**请求参数**：
| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| page | int | 否 | 页码，默认 1 |
| count | int | 否 | 每页数量，默认 10 |
| name | string | 否 | 用户名筛选 |
| ids | array | 否 | 用户ID列表筛选 |

**响应**：
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "count": 100,
    "data": [
      {
        "user_id": "507f1f77bcf86cd799439011",
        "name": "admin",
        "status": 0,
        "is_admin": true,
        "create_at": 1704067200000,
        "update_at": 1704067200000
      }
    ]
  }
}
```

---

## 4. Todo 模块接口

### 4.1 POST /api/v1/todo

**请求**：
```json
{
  "title": "完成项目报告",
  "deadline_at": 1704153600000,
  "desc": "需要在周五前完成Q4项目报告",
  "execute_ids": ["507f1f77bcf86cd799439012"]
}
```

**响应**：
```json
{
  "code": 200,
  "message": "创建待办成功",
  "data": "507f1f77bcf86cd799439013"
}
```

### 4.2 GET /api/v1/todo/{todo_id}

**响应**：
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": "507f1f77bcf86cd799439013",
    "creator_id": "507f1f77bcf86cd799439011",
    "creator_name": "admin",
    "title": "完成项目报告",
    "deadline_at": 1704153600000,
    "desc": "需要在周五前完成Q4项目报告",
    "status": 1,
    "todo_status": 1,
    "execute_ids": [
      {
        "id": "uuid-xxx",
        "user_id": "507f1f77bcf86cd799439012",
        "user_name": "zhangsan",
        "todo_id": "507f1f77bcf86cd799439013",
        "todo_status": 1
      }
    ],
    "records": []
  }
}
```

### 4.3 POST /api/v1/todo/finish

**请求**：
```json
{
  "todo_id": "507f1f77bcf86cd799439013",
  "user_id": "507f1f77bcf86cd799439012"
}
```

**响应**：
```json
{
  "code": 200,
  "message": "完成待办成功",
  "data": null
}
```

### 4.4 GET /api/v1/todo/list

**请求参数**：
| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| page | int | 否 | 页码，默认 1 |
| count | int | 否 | 每页数量，默认 10 |
| start_time | int | 否 | 开始时间戳（毫秒） |
| end_time | int | 否 | 结束时间戳（毫秒） |

**响应**：
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "count": 10,
    "data": [
      {
        "id": "507f1f77bcf86cd799439013",
        "creator_id": "507f1f77bcf86cd799439011",
        "creator_name": "admin",
        "title": "完成项目报告",
        "deadline_at": 1704153600000,
        "desc": "需要在周五前完成Q4项目报告",
        "status": 1,
        "todo_status": 1,
        "execute_ids": ["zhangsan"],
        "create_at": 1704067200000,
        "update_at": 1704067200000
      }
    ]
  }
}
```

---

## 5. Approval 模块接口

### 5.1 POST /api/v1/approval

**请求（请假）**：
```json
{
  "type": 2,
  "leave": {
    "type": 3,
    "start_time": 1704067200,
    "end_time": 1704153600,
    "reason": "身体不适",
    "time_type": 2
  }
}
```

**响应**：
```json
{
  "code": 200,
  "message": "创建审批成功",
  "data": "507f1f77bcf86cd799439014"
}
```

### 5.2 GET /api/v1/approval/{approval_id}

**响应**：
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": "507f1f77bcf86cd799439014",
    "user": {
      "user_id": "507f1f77bcf86cd799439011",
      "user_name": "admin",
      "status": 0
    },
    "no": "12345678901",
    "type": 2,
    "status": 1,
    "title": "admin 提交的 请假审批",
    "abstract": "【病假】: 【2024-01-01 00:00】-【2024-01-02 00:00】",
    "reason": "身体不适",
    "approvers": [
      {
        "user_id": "507f1f77bcf86cd799439015",
        "user_name": "leader",
        "status": 0
      }
    ],
    "leave": {
      "type": 3,
      "start_time": 1704067200,
      "end_time": 1704153600,
      "reason": "身体不适",
      "time_type": 2,
      "duration": 1.0
    }
  }
}
```

### 5.3 PUT /api/v1/approval/dispose

**请求**：
```json
{
  "approval_id": "507f1f77bcf86cd799439014",
  "status": 2,
  "reason": "同意"
}
```

**响应**：
```json
{
  "code": 200,
  "message": "处理审批成功",
  "data": null
}
```

### 5.4 GET /api/v1/approval/list

**请求参数**：
| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| page | int | 否 | 页码，默认 1 |
| count | int | 否 | 每页数量，默认 10 |
| type | int | 否 | 1-我提交的，2-待我审批的 |

**响应**：
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "count": 5,
    "data": [
      {
        "id": "507f1f77bcf86cd799439014",
        "no": "12345678901",
        "type": 2,
        "status": 1,
        "title": "admin 提交的 请假审批",
        "abstract": "【病假】: 【2024-01-01 00:00】-【2024-01-02 00:00】",
        "create_id": "507f1f77bcf86cd799439011",
        "create_at": 1704067200000
      }
    ]
  }
}
```

---

## 6. Department 模块接口

### 6.1 GET /api/v1/dep/soa

**响应**：
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "child": [
      {
        "id": "507f1f77bcf86cd799439016",
        "name": "总公司",
        "parent_id": null,
        "parent_path": null,
        "level": 1,
        "leader_id": "507f1f77bcf86cd799439011",
        "leader": "admin",
        "count": 100,
        "users": [],
        "child": [
          {
            "id": "507f1f77bcf86cd799439017",
            "name": "技术部",
            "parent_id": "507f1f77bcf86cd799439016",
            "parent_path": ":507f1f77bcf86cd799439016",
            "level": 2,
            "leader_id": "507f1f77bcf86cd799439015",
            "leader": "leader",
            "count": 20,
            "users": [],
            "child": null
          }
        ]
      }
    ]
  }
}
```

### 6.2 POST /api/v1/dep

**请求**：
```json
{
  "name": "技术部",
  "parent_id": "507f1f77bcf86cd799439016",
  "level": 2,
  "leader_id": "507f1f77bcf86cd799439015"
}
```

**响应**：
```json
{
  "code": 200,
  "message": "创建部门成功",
  "data": null
}
```

### 6.3 POST /api/v1/dep/user/add

**请求**：
```json
{
  "dep_id": "507f1f77bcf86cd799439017",
  "user_id": "507f1f77bcf86cd799439012"
}
```

**响应**：
```json
{
  "code": 200,
  "message": "添加部门员工成功",
  "data": null
}
```

---

## 7. ChatLog 模块接口

### 7.1 POST /api/v1/chat

**请求**：
```json
{
  "conversation_id": "conv-123",
  "send_id": "507f1f77bcf86cd799439011",
  "recv_id": "507f1f77bcf86cd799439012",
  "chat_type": 2,
  "msg_content": "你好，请问有什么可以帮助你的？"
}
```

**响应**：
```json
{
  "code": 200,
  "message": "创建聊天记录成功",
  "data": "507f1f77bcf86cd799439018"
}
```

### 7.2 GET /api/v1/chat/list

**请求参数**：
| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| page | int | 否 | 页码，默认 1 |
| count | int | 否 | 每页数量，默认 20 |
| conversation_id | string | 否 | 会话ID筛选 |
| send_id | string | 否 | 发送者ID筛选 |
| chat_type | int | 否 | 聊天类型筛选 |

**响应**：
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "count": 50,
    "data": [
      {
        "id": "507f1f77bcf86cd799439018",
        "conversation_id": "conv-123",
        "send_id": "507f1f77bcf86cd799439011",
        "send_name": "admin",
        "recv_id": "507f1f77bcf86cd799439012",
        "recv_name": "zhangsan",
        "chat_type": 2,
        "msg_content": "你好，请问有什么可以帮助你的？",
        "send_time": 1704067200000,
        "create_at": 1704067200000
      }
    ]
  }
}
```

---

## 8. 业务错误码

| 错误消息 | HTTP 状态码 | 说明 |
|---------|------------|------|
| 用户不存在 | 404 | 用户ID无效 |
| 已存在该用户 | 400 | 用户名重复 |
| 原密码错误 | 400 | 修改密码时原密码不正确 |
| 待办事项不存在 | 404 | 待办ID无效 |
| 您不能删除该待办事项 | 403 | 非创建人尝试删除 |
| 用户不在待办执行人列表中 | 400 | 完成待办时用户不是执行人 |
| 审批记录不存在 | 404 | 审批ID无效 |
| 您不是当前审批人 | 403 | 无权处理审批 |
| 该审批已撤销/通过/拒绝 | 400 | 审批状态不允许操作 |
| 部门不存在 | 404 | 部门ID无效 |
| 该部门下还存在用户，不能删除该部门 | 400 | 部门有成员时不允许删除 |
| 不能删除部门负责人 | 403 | 尝试删除部门负责人 |
| 该用户已在此部门中 | 400 | 重复添加部门成员 |