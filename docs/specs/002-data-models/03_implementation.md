# Implementation: AIWorkHelper 数据模型

## Execution Status (执行状态)

| 字段 | 值 |
|------|-----|
| **Phase** | Complete |
| **Progress** | 12/12 steps (100%) |
| **Current Task** | 完成 |
| **Last Updated** | 2026-03-23 |

---

## Objective (目标复述)

基于 Java 实体类，使用 Beanie ODM 创建 6 个 MongoDB Document 模型、6 个内嵌文档、5 个枚举类型，实现与现有系统的字段对应。同时更新认证模块以适配新的 User 模型。

## File Changes (变更范围)

### 新增文件
- `app/models/enums/__init__.py` - 枚举模块导出
- `app/models/enums/todo_status.py` - 待办状态枚举
- `app/models/enums/approval_status.py` - 审批状态枚举
- `app/models/enums/approval_type.py` - 审批类型枚举
- `app/models/enums/chat_type.py` - 聊天类型枚举
- `app/models/enums/leave_type.py` - 请假类型枚举
- `app/models/todo.py` - Todo 模型 + 内嵌文档
- `app/models/approval.py` - Approval 模型 + 内嵌文档
- `app/models/chat_log.py` - ChatLog 模型
- `app/models/department.py` - Department 模型
- `app/models/department_user.py` - DepartmentUser 模型

### 修改文件
- `app/models/user.py` - 重构为匹配数据字典
- `app/models/__init__.py` - 导出所有模型
- `app/repository/user_repository.py` - 适配新字段
- `app/services/auth_service.py` - 适配新字段
- `app/security/dependencies.py` - 状态检查逻辑
- `app/dto/auth/register.py` - 简化字段
- `app/dto/auth/login.py` - 简化字段
- `app/dto/user/user_response.py` - 简化字段
- `app/routers/auth.py` - 更新文档注释
- `tests/conftest.py` - 更新测试 fixtures
- `tests/api/test_auth.py` - 更新测试用例

## Data Changes (数据变更)

- User 模型字段重构，原有字段将被替换
- 新增 5 个 Collection 的模型定义

## Execution Plan (分步计划)

> **状态图例**：✅ 完成 | 🔄 进行中 | ⏳ 待开始 | ❌ 阻塞

---

### Step 1: 创建枚举类型 ✅

**任务清单**：
- [x] 创建 `app/models/enums/` 目录
- [x] 创建 `todo_status.py` - TodoStatus 枚举
- [x] 创建 `approval_status.py` - ApprovalStatus 枚举
- [x] 创建 `approval_type.py` - ApprovalType 枚举
- [x] 创建 `chat_type.py` - ChatType 枚举
- [x] 创建 `leave_type.py` - LeaveType 枚举
- [x] 创建 `__init__.py` 导出所有枚举

**产出文件**：
- `app/models/enums/__init__.py`
- `app/models/enums/todo_status.py`
- `app/models/enums/approval_status.py`
- `app/models/enums/approval_type.py`
- `app/models/enums/chat_type.py`
- `app/models/enums/leave_type.py`

---

### Step 2: 重构 User 模型 ✅

**任务清单**：
- [x] 修改 `user.py` 匹配数据字典
- [x] 添加 name 唯一索引
- [x] 时间戳改为 int 类型

**产出文件**：
- `app/models/user.py`

---

### Step 3: 创建 Todo 模型 ✅

**任务清单**：
- [x] 创建 UserTodo 内嵌文档
- [x] 创建 TodoRecord 内嵌文档
- [x] 创建 Todo Document 模型

**产出文件**：
- `app/models/todo.py`

---

### Step 4: 创建 Approval 模型 ✅

**任务清单**：
- [x] 创建 Approver 内嵌文档
- [x] 创建 MakeCard 内嵌文档
- [x] 创建 Leave 内嵌文档
- [x] 创建 GoOut 内嵌文档
- [x] 创建 Approval Document 模型

**产出文件**：
- `app/models/approval.py`

---

### Step 5: 创建 ChatLog 模型 ✅

**任务清单**：
- [x] 创建 ChatLog Document 模型
- [x] 添加 conversationId 索引

**产出文件**：
- `app/models/chat_log.py`

---

### Step 6: 创建 Department 和 DepartmentUser 模型 ✅

**任务清单**：
- [x] 创建 Department Document 模型
- [x] 创建 DepartmentUser Document 模型

**产出文件**：
- `app/models/department.py`
- `app/models/department_user.py`

---

### Step 7: 更新模型导出 ✅

**任务清单**：
- [x] 更新 `app/models/__init__.py` 导出所有模型

**产出文件**：
- `app/models/__init__.py`

---

### Step 8: 更新 UserRepository ✅

**任务清单**：
- [x] 更新字段名 `username` → `name`
- [x] 更新字段名 `password_hash` → `password`
- [x] 删除 email/employee_id 相关方法
- [x] 更新 exists_by_name 方法

**产出文件**：
- `app/repository/user_repository.py`

---

### Step 9: 更新 Auth DTOs ✅

**任务清单**：
- [x] 简化 RegisterRequest（去掉 email/full_name 等字段）
- [x] 简化 LoginRequest（去掉邮箱登录）
- [x] 简化 UserInfo 和 UserResponse

**产出文件**：
- `app/dto/auth/register.py`
- `app/dto/auth/login.py`
- `app/dto/user/user_response.py`

---

### Step 10: 更新 AuthService ✅

**任务清单**：
- [x] 更新字段名映射
- [x] 更新状态检查逻辑（int 类型）
- [x] 删除邮箱相关逻辑

**产出文件**：
- `app/services/auth_service.py`

---

### Step 11: 更新 Security Dependencies ✅

**任务清单**：
- [x] 更新状态检查逻辑（status == 0 为正常）

**产出文件**：
- `app/security/dependencies.py`

---

### Step 12: 更新 Auth Router 和测试 ✅

**任务清单**：
- [x] 更新接口文档注释
- [x] 更新测试 fixtures
- [x] 更新测试用例

**产出文件**：
- `app/routers/auth.py`
- `tests/conftest.py`
- `tests/api/test_auth.py`

---

## Rollback & Compatibility (回滚与兼容)

- 如何回退：git checkout 恢复原文件
- 影响面：认证模块已同步更新，测试用例已更新