# 需求规格文档 - CRUD 业务接口实现

## 1. 需求概述

### 1.1 背景

参考 `.claude/main` 目录下的 Java 代码结构，为 Python/FastAPI 项目实现完整的 CRUD 业务接口代码。

### 1.2 目标

为 6 个业务实体实现完整的 CRUD 业务接口：
- User（用户）
- Todo（待办事项）
- Approval（审批）
- Department（部门）
- DepartmentUser（部门用户关联）
- ChatLog（聊天记录）

---

## 2. 功能范围

### 2.1 In Scope（范围内）

| 模块 | 功能 | 说明 |
|------|------|------|
| User | 登录、CRUD、修改密码、列表 | 扩展现有实现 |
| Todo | CRUD、完成待办、创建操作记录、列表 | 全新实现 |
| Approval | 详情、创建、处理审批、列表 | 全新实现 |
| Department | 树结构、CRUD、用户关联管理 | 全新实现 |
| ChatLog | 详情、创建、列表、按会话查询 | 全新实现 |

### 2.2 Out of Scope（范围外）

- 前端界面开发
- 数据库迁移脚本
- 性能优化（缓存、索引优化）
- WebSocket 实时推送
- AI 聊天功能

---

## 3. 验收标准（Acceptance Criteria）

### AC-001: User 模块
- [ ] 用户可通过用户名密码登录，返回 JWT Token
- [ ] 可创建、编辑、删除、查询用户
- [ ] 可分页查询用户列表
- [ ] 可修改密码（需验证原密码）

### AC-002: Todo 模块
- [ ] 可创建待办事项，支持指定执行人
- [ ] 可编辑、删除待办（仅创建人可删除）
- [ ] 可标记待办完成
- [ ] 可创建操作记录
- [ ] 可分页查询待办列表（按执行人筛选）
- [ ] 超时待办自动标记超时状态

### AC-003: Approval 模块
- [ ] 可创建审批申请（支持请假、外出、补卡类型）
- [ ] 审批流程根据部门层级自动确定审批人
- [ ] 审批人可通过/拒绝审批
- [ ] 申请人可撤销审批
- [ ] 可分页查询审批列表（我提交的/待我审批的）

### AC-004: Department 模块
- [ ] 可创建、编辑、删除部门
- [ ] 可获取部门树结构
- [ ] 可添加/删除部门员工（级联到上下级部门）
- [ ] 可获取用户所属部门层级信息

### AC-005: ChatLog 模块
- [ ] 可创建聊天记录
- [ ] 可分页查询聊天记录
- [ ] 可按会话ID查询聊天记录

---

## 4. 约束条件

### 4.1 技术约束
- 后端框架：FastAPI
- 数据库：MongoDB + Beanie ODM
- 认证：JWT Bearer Token
- 数据校验：Pydantic V2

### 4.2 架构约束
- 三层架构：Router → Service → Repository
- DTO 分离：Request DTO 和 Response DTO
- 统一响应格式：ApiResponse[T]
- 统一异常处理：BusinessValidationException, ResourceNotFoundException

### 4.3 代码规范
- 所有公开方法必须有文档注释
- 时间戳使用毫秒级 Unix 时间戳
- ID 使用 MongoDB ObjectId 字符串形式

---

## 5. 依赖关系

### 5.1 现有依赖
- `app/config/` - 配置模块
- `app/security/` - 安全模块（JWT、密码加密）
- `app/models/` - 数据模型（已定义）

### 5.2 新增依赖
- 无额外第三方库依赖

---

## 6. 风险评估

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| 审批流程复杂度高 | 中 | 参考 Java 实现逻辑，保持一致性 |
| 部门树操作级联复杂 | 中 | 充分测试边界条件 |
| 时间戳单位不一致 | 低 | 统一使用毫秒级时间戳 |

---

## 7. 参考

- Java 参考实现：`.claude/main/java/com/aiwork/helper/`
- 现有 Python 实现：`app/routers/auth.py`, `app/services/auth_service.py`