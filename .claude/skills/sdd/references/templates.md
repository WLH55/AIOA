# SDD 文档模板

## 01_requirement.md

```markdown
# Feature: [功能名称]

## Background (背景)
为什么要做这个功能？

## Goals (目标)
- 目标 1
- 目标 2

## In Scope / Out of Scope (范围)
### In Scope
- 包含的功能点

### Out of Scope
- 本期不做的功能点

## Acceptance Criteria (验收标准)
- AC1: [可验证的标准]
- AC2: [可验证的标准]

## Constraints (约束)
- 性能要求：
- 安全要求：
- 兼容性要求：

## Risks & Rollout (风险与上线)
- 风险点：
- 灰度策略：
- 回滚预案：
```

---

## 02_interface.md

```markdown
# API: [接口名称]

## Overview
- Method: POST/GET
- Path: /api/v1/xxx
- Auth: Bearer Token
- Idempotency: [幂等性说明]

## Request
| 字段 | 类型 | 必填 | 说明 | 校验规则 |
|------|------|------|------|----------|
| field1 | string | 是 | 描述 | 规则 |

## Response (Success)
| 字段 | 类型 | 说明 |
|------|------|------|
| field1 | string | 描述 |

## Error Codes
| 错误码 | 含义 | 触发条件 |
|--------|------|----------|
| INVALID_PARAM | 参数非法 | 当 xxx 时 |

## Examples
### Success
```json
{
  "field1": "value1"
}
```

### Error
```json
{
  "error": "INVALID_PARAM",
  "message": "xxx"
}
```
```

---

## 03_implementation.md

```markdown
# Implementation: [功能名称]

## Execution Status (执行状态)

| 字段 | 值 |
|------|-----|
| **Phase** | Execute |
| **Progress** | 0/N steps (0%) |
| **Current Task** | Step 1 - [任务名称] |
| **Last Updated** | YYYY-MM-DD HH:MM |

---

## Objective (目标复述)
用 3-5 行复述本次要实现什么。

## File Changes (变更范围)
- `src/xxx/Controller.java` - 新增接口
- `src/xxx/Service.java` - 实现业务逻辑

## Data Changes (数据变更)
- 表结构变更：
- 索引变更：
- 数据迁移：

## Core Logic (核心流程)
```
1. 解析参数
2. 校验权限
3. 执行业务逻辑
4. 返回结果
```

## Key Validations (关键校验)
- 输入校验：
- 业务校验：
- 异常处理：

## Execution Plan (分步计划)

> **状态图例**：✅ 完成 | 🔄 进行中 | ⏳ 待开始 | ❌ 阻塞

---

### Step 1: [任务名称] ⏳

**任务清单**：
- [ ] 子任务 1
- [ ] 子任务 2
- [ ] 子任务 3

**产出文件**：
- `path/to/file1.py`
- `path/to/file2.py`

---

### Step 2: [任务名称] ⏳

**任务清单**：
- [ ] 子任务 1
- [ ] 子任务 2

**产出文件**：
- `path/to/file.py`

---

### Step 3: [任务名称] ⏳

**任务清单**：
- [ ] 子任务 1
- [ ] 子任务 2

**产出文件**：
- `path/to/file.py`

---

## Rollback & Compatibility (回滚与兼容)
- 如何关闭：
- 如何回退：
- 影响面：
```

> **使用说明**：
> 1. 开始执行时，更新顶部 `Execution Status` 表格
> 2. 每完成一个子任务，将 `[ ]` 改为 `[x]`
> 3. Step 状态随子任务进度更新：⏳ → 🔄 → ✅
> 4. 新 AI 接手时，读取 `Execution Status` 快速定位断点

---

## 04_test_spec.md

```markdown
# Test Spec: [功能名称]

## Test Scope (测试范围)
- 单元测试：Service 层
- 集成测试：API 层
- 契约测试：接口字段

## Test Strategy (测试策略)
- 单测覆盖：核心逻辑、边界条件
- 集成测试：端到端流程
- 性能测试：并发场景

## Test Cases (用例列表)
| 编号 | 场景 | 期望结果 |
|------|------|----------|
| TC1 | 正常流程 | 返回成功 |
| TC2 | 边界条件 | 返回错误码 |
| TC3 | 并发场景 | 幂等性保证 |

## Data Preparation (数据准备)
- 前置数据：
- Mock 依赖：
- 时区假设：

## Regression Impact (回归影响)
可能影响的老功能：
- 功能 A
- 功能 B
```