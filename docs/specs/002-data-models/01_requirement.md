# Feature: AIWorkHelper 数据模型

## Background (背景)

AIWorkHelper 是一个企业办公助手系统，需要建立核心数据模型以支撑用户管理、待办事项、审批流程、聊天记录、部门管理等业务功能。

## Goals (目标)

- 基于 MongoDB + Beanie ODM 创建 6 个核心数据模型
- 实现内嵌文档设计（Todo 的 executes/records，Approval 的详情对象）
- 定义枚举类型保证类型安全
- 确保模型与现有 Java 实体类字段一一对应

## In Scope / Out of Scope (范围)

### In Scope
- 6 个 Document 模型：User、Todo、Approval、ChatLog、Department、DepartmentUser
- 6 个内嵌文档：UserTodo、TodoRecord、Approver、MakeCard、Leave、GoOut
- 5 个枚举类型：TodoStatus、ApprovalStatus、ApprovalType、ChatType、LeaveType
- Beanie 索引配置

### Out of Scope
- Repository 层实现
- Service 层实现
- API 接口开发

## Acceptance Criteria (验收标准)

- AC1: User 模型字段与 Java 实体类完全一致（name/password/status/isAdmin/createAt/updateAt）
- AC2: Todo 模型支持内嵌文档 executes（UserTodo 列表）和 records（TodoRecord 列表）
- AC3: Approval 模型支持多态 Schema（makeCard/leave/goOut 可选对象）
- AC4: 所有时间字段使用 long 类型（Unix 时间戳）
- AC5: 所有状态字段使用 int 类型
- AC6: 枚举类型提供 fromValue() 方法支持值转换
- AC7: 模型在 `app/models/__init__.py` 中正确导出

## Constraints (约束)

- 性能要求：User.name 需要唯一索引
- 兼容性要求：字段命名与 Java 实体类保持一致（MongoDB 字段名）
- 技术约束：使用 Beanie ODM + Pydantic V2

## Data Model Specification

### 1. User (用户集合)

| 字段名 | MongoDB字段 | 类型 | 说明 | 索引 |
|-------|------------|------|------|------|
| id | _id | str | 主键 | PK |
| name | name | str | 用户名 | UK |
| password | Password | str | 密码(BCrypt) | - |
| status | status | int | 状态(0正常,1禁用) | - |
| isAdmin | isAdmin | bool | 是否管理员 | - |
| createAt | createAt | int | 创建时间戳 | - |
| updateAt | updateAt | int | 更新时间戳 | - |

### 2. Todo (待办事项集合)

| 字段名 | MongoDB字段 | 类型 | 说明 |
|-------|------------|------|------|
| id | _id | str | 主键 |
| creatorId | creatorId | str | 创建者ID |
| title | title | str | 标题 |
| deadlineAt | deadlineAt | int | 截止时间戳 |
| desc | desc | str | 描述 |
| executes | executes | List[UserTodo] | 执行人列表(内嵌) |
| records | records | List[TodoRecord] | 操作记录(内嵌) |
| todoStatus | todo_status | int | 状态(1待处理/2进行中/3已完成/4已取消/5已超时) |
| createAt | createAt | int | 创建时间戳 |
| updateAt | updateAt | int | 更新时间戳 |

### 3. Approval (审批集合)

| 字段名 | MongoDB字段 | 类型 | 说明 |
|-------|------------|------|------|
| id | _id | str | 主键 |
| userId | userId | str | 申请人ID |
| no | no | str | 审批编号 |
| type | type | int | 审批类型 |
| status | status | int | 审批状态 |
| title | title | str | 审批标题 |
| abstract | abstract | str | 审批摘要 |
| reason | reason | str | 申请理由 |
| approvalId | approvalId | str | 当前审批人ID |
| approvalIdx | approvalIdx | int | 当前审批人索引 |
| approvers | approvers | List[Approver] | 审批人列表 |
| copyPersons | copyPersons | List[Approver] | 抄送人列表 |
| participation | participation | List[str] | 参与人员ID列表 |
| finishAt | finishAt | int | 完成时间戳 |
| finishDay | finishDay | int | 完成日期 |
| finishMonth | finishMonth | int | 完成月份 |
| finishYeas | finishYeas | int | 完成年份 |
| makeCard | makeCard | MakeCard | 补卡详情(可选) |
| leave | leave | Leave | 请假详情(可选) |
| goOut | goOut | GoOut | 外出详情(可选) |
| createAt | createAt | int | 创建时间戳 |
| updateAt | updateAt | int | 更新时间戳 |

### 4. ChatLog (聊天记录集合)

| 字段名 | MongoDB字段 | 类型 | 说明 | 索引 |
|-------|------------|------|------|------|
| id | _id | str | 主键 | PK |
| conversationId | conversationId | str | 会话ID | IDX |
| sendId | sendId | str | 发送者ID | - |
| recvId | recvId | str | 接收者ID | - |
| chatType | chatType | int | 聊天类型(1群聊/2私聊) | - |
| msgContent | msgContent | str | 消息内容 | - |
| sendTime | sendTime | int | 发送时间戳 | - |
| createAt | createAt | int | 创建时间戳 | - |
| updateAt | updateAt | int | 更新时间戳 | - |

### 5. Department (部门集合)

| 字段名 | MongoDB字段 | 类型 | 说明 |
|-------|------------|------|------|
| id | _id | str | 主键 |
| name | name | str | 部门名称 |
| parentId | parentId | str | 父部门ID |
| parentPath | parentPath | str | 祖先路径 |
| level | level | int | 层级 |
| leaderId | leaderId | str | 负责人ID |
| leader | leader | str | 负责人姓名 |
| count | count | int | 部门人数 |
| createAt | createAt | int | 创建时间戳 |
| updateAt | updateAt | int | 更新时间戳 |

### 6. DepartmentUser (部门用户关联表)

| 字段名 | MongoDB字段 | 类型 | 说明 |
|-------|------------|------|------|
| id | _id | str | 主键 |
| depId | depId | str | 部门ID |
| userId | userId | str | 用户ID |
| createAt | createAt | int | 创建时间戳 |
| updateAt | updateAt | int | 更新时间戳 |

### 内嵌文档定义

#### UserTodo (执行人)

| 字段名 | 类型 | 说明 |
|-------|------|------|
| id | str | 唯一标识 |
| userId | str | 用户ID |
| userName | str | 用户名 |
| todoId | str | 待办ID |
| todoStatus | int | 待办状态 |
| createAt | int | 创建时间戳 |
| updateAt | int | 更新时间戳 |

#### TodoRecord (操作记录)

| 字段名 | 类型 | 说明 |
|-------|------|------|
| userId | str | 操作用户ID |
| userName | str | 操作用户名 |
| content | str | 操作内容 |
| image | str | 操作图片 |
| createAt | int | 操作时间戳 |

#### Approver (审批人)

| 字段名 | 类型 | 说明 |
|-------|------|------|
| userId | str | 用户ID |
| userName | str | 用户姓名 |
| status | int | 审批状态 |
| reason | str | 审批理由 |

#### MakeCard (补卡详情)

| 字段名 | 类型 | 说明 |
|-------|------|------|
| date | int | 补卡时间戳 |
| reason | str | 补卡理由 |
| day | int | 补卡日期(格式20221011) |
| checkType | int | 补卡类型(1上班卡/2下班卡) |

#### Leave (请假详情)

| 字段名 | 类型 | 说明 |
|-------|------|------|
| type | int | 请假类型(1事假/2调休/3病假/4年假/5产假/6陪产假/7婚假/8丧假/9哺乳假) |
| startTime | int | 开始时间戳 |
| endTime | int | 结束时间戳 |
| reason | str | 请假原因 |
| timeType | int | 时长类型(1小时/2天) |
| duration | float | 请假时长 |

#### GoOut (外出详情)

| 字段名 | 类型 | 说明 |
|-------|------|------|
| startTime | int | 开始时间戳 |
| endTime | int | 结束时间戳 |
| duration | float | 时长(小时) |
| reason | str | 外出原因 |

### 枚举定义

#### TodoStatus (待办状态)
- PENDING(1) - 待处理
- IN_PROGRESS(2) - 进行中
- FINISHED(3) - 已完成
- CANCELLED(4) - 已取消
- TIMEOUT(5) - 已超时

#### ApprovalStatus (审批状态)
- NOT_STARTED(0) - 未开始
- PROCESSED(1) - 处理中
- PASS(2) - 通过
- REFUSE(3) - 拒绝
- CANCEL(4) - 撤销
- AUTO_PASS(5) - 自动通过

#### ApprovalType (审批类型)
- UNIVERSAL(1) - 通用审批
- LEAVE(2) - 请假审批
- MAKE_CARD(3) - 补卡审批
- GO_OUT(4) - 外出审批
- REIMBURSE(5) - 报销审批
- PAYMENT(6) - 付款审批
- BUYER(7) - 采购审批
- PROCEEDS(8) - 收款审批
- POSITIVE(9) - 转正审批
- DIMISSION(10) - 离职审批
- OVERTIME(11) - 加班审批
- BUYER_CONTRACT(12) - 采购合同审批

#### ChatType (聊天类型)
- GROUP(1) - 群聊
- SINGLE(2) - 私聊

#### LeaveType (请假类型)
- MATTER(1) - 事假
- REST(2) - 调休
- FALL(3) - 病假
- ANNUAL(4) - 年假
- MATERNITY(5) - 产假
- PATERNITY(6) - 陪产假
- MARRIAGE(7) - 婚假
- FUNERAL(8) - 丧假
- BREASTFEEDING(9) - 哺乳假

## Risks & Rollout (风险与上线)

- 风险点：现有 User 模型字段会被覆盖，需确认是否影响现有认证模块
- 回滚预案：保留原 User 模型备份，可通过 git 回退