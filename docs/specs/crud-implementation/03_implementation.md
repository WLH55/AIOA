# CRUD 业务接口实施计划

## 概述

参考 `.claude/main` 目录下的 Java 代码结构，为 6 个业务实体实现完整的 CRUD 业务接口代码。

## 文件清单

### 1. User 模块 (扩展现有)

**DTO 层**
- `app/dto/user/user_request.py` - 新增

**Repository 层**
- `app/repository/user_repository.py` - 扩展（添加分页查询、批量查询等方法）

**Service 层**
- `app/services/user_service.py` - 新增

**Router 层**
- `app/routers/user.py` - 新增

### 2. Todo 模块

**DTO 层**
- `app/dto/todo/__init__.py` - 新增
- `app/dto/todo/todo_request.py` - 新增
- `app/dto/todo/todo_response.py` - 新增

**Repository 层**
- `app/repository/todo_repository.py` - 新增

**Service 层**
- `app/services/todo_service.py` - 新增

**Router 层**
- `app/routers/todo.py` - 新增

### 3. Approval 模块

**DTO 层**
- `app/dto/approval/__init__.py` - 新增
- `app/dto/approval/approval_request.py` - 新增
- `app/dto/approval/approval_response.py` - 新增

**Repository 层**
- `app/repository/approval_repository.py` - 新增

**Service 层**
- `app/services/approval_service.py` - 新增

**Router 层**
- `app/routers/approval.py` - 新增

### 4. Department 模块

**DTO 层**
- `app/dto/department/__init__.py` - 新增
- `app/dto/department/department_request.py` - 新增
- `app/dto/department/department_response.py` - 新增

**Repository 层**
- `app/repository/department_repository.py` - 新增
- `app/repository/department_user_repository.py` - 新增

**Service 层**
- `app/services/department_service.py` - 新增

**Router 层**
- `app/routers/department.py` - 新增

### 5. ChatLog 模块

**DTO 层**
- `app/dto/chat_log/__init__.py` - 新增
- `app/dto/chat_log/chat_log_request.py` - 新增
- `app/dto/chat_log/chat_log_response.py` - 新增

**Repository 层**
- `app/repository/chat_log_repository.py` - 新增

**Service 层**
- `app/services/chat_log_service.py` - 新增

**Router 层**
- `app/routers/chat_log.py` - 新增

## 执行步骤

### Step 1: User 模块
1.1 创建 `app/dto/user/user_request.py`
1.2 扩展 `app/repository/user_repository.py`
1.3 创建 `app/services/user_service.py`
1.4 创建 `app/routers/user.py`

### Step 2: Todo 模块
2.1 创建 DTO 层 (`__init__.py`, `todo_request.py`, `todo_response.py`)
2.2 创建 `app/repository/todo_repository.py`
2.3 创建 `app/services/todo_service.py`
2.4 创建 `app/routers/todo.py`

### Step 3: Approval 模块
3.1 创建 DTO 层
3.2 创建 `app/repository/approval_repository.py`
3.3 创建 `app/services/approval_service.py`
3.4 创建 `app/routers/approval.py`

### Step 4: Department 模块
4.1 创建 DTO 层
4.2 创建 `app/repository/department_repository.py`
4.3 创建 `app/repository/department_user_repository.py`
4.4 创建 `app/services/department_service.py`
4.5 创建 `app/routers/department.py`

### Step 5: ChatLog 模块
5.1 创建 DTO 层
5.2 创建 `app/repository/chat_log_repository.py`
5.3 创建 `app/services/chat_log_service.py`
5.4 创建 `app/routers/chat_log.py`

### Step 6: 注册路由
6.1 更新 `app/main.py` 注册所有新路由

## 验收标准

- [x] 所有 API 端点可正常访问
- [x] DTO 数据校验正确
- [x] Repository 数据库操作正确
- [x] Service 业务逻辑符合 Java 参考实现
- [x] 权限校验正确

## 代码审查修复记录

### 2026-03-24 代码审查发现及修复

| 问题 | 风险级别 | 修复状态 | 修复说明 |
|------|---------|---------|---------|
| 用户编辑/删除接口无权限验证 | 🔴 严重 | ✅ 已修复 | 添加管理员权限校验，普通用户只能编辑自己 |
| 待办完成接口身份验证漏洞 | 🔴 严重 | ✅ 已修复 | 验证请求 user_id 必须为当前用户 |
| 用户创建默认状态为禁用 | 🔴 严重 | ✅ 已修复 | 默认 status=0（正常状态） |
| 审批通过时未设置完成时间 | 🔴 严重 | ✅ 已修复 | 添加 finishAt/finishDay/finishMonth/finishYeas |
| 审批编号可能重复 | 🟡 中等 | ✅ 已修复 | 使用时间戳+随机数生成唯一编号 |
| 部门用户模型缺少索引 | 🟡 中等 | ✅ 已修复 | 添加 depId/userId 索引 |

### 修改的文件

1. `app/services/user_service.py`
   - 修复用户创建默认状态
   - 添加 edit 方法权限校验
   - 添加 delete 方法权限校验
   - 添加 update_password 方法权限校验

2. `app/routers/user.py`
   - 更新 edit/delete 接口传递 current_user

3. `app/services/todo_service.py`
   - 添加 finish 方法身份验证

4. `app/routers/todo.py`
   - 更新 finish 接口传递 current_user

5. `app/services/approval_service.py`
   - 添加审批完成时间戳
   - 优化审批编号生成算法

6. `app/models/department_user.py`
   - 添加 depId/userId 索引