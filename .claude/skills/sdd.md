---
name: sdd
description: Spec-Driven Development (SDD) workflow for complex feature development. Use when: (1) Building new features requiring multiple files, (2) Complex refactoring with architectural changes, (3) API/interface design requiring frontend-backend collaboration, (4) Long-term maintainable modules. Do NOT use for: simple bug fixes, single-file changes, quick prototypes, or trivial modifications.
---

# SDD (Spec-Driven Development) 工作流

## 核心原则

**文档是上下文锚点**：防止上下文腐烂、审查瘫痪、维护断层。

三大价值：
1. **上下文锚定** - Spec 文档锁定任务意图，可随时恢复
2. **验收标准** - 代码必须兑现文档承诺，而非逐行 Review
3. **知识资产** - 代码可抛弃，文档才是长期资产

---

## 目录结构

确保项目有以下结构：

```
docs/
├── specs/feature-xxx/
│   ├── 01_requirement.md      # 需求规格
│   ├── 02_interface.md        # 接口契约
│   ├── 03_implementation.md   # 实施细节
│   └── 04_test_spec.md        # 测试策略
├── decisions/
│   └── AI_CHANGELOG.md        # AI 决策日志
└── skills/
    └── SKILL.md               # 团队规则库
```

---

## RIPER 工作流

### R - Research (调研)

**目标**：把模糊需求变成清晰的需求规格

**步骤**：

1. **复述需求**
   - 用自己的话复述需求
   - 指出不清晰的地方
   - 列出需要参考的现有代码/模块

2. **澄清边界**
   - 功能范围（In Scope / Out of Scope）
   - 边界条件、异常处理、性能要求

3. **生成需求文档**
   - 创建 `docs/specs/feature-xxx/01_requirement.md`
   - 包含：Background、Goals、In/Out Scope、Acceptance Criteria、Constraints、Risks

**验收门禁**：
- [ ] 所有"模糊点"都已解答
- [ ] 完全理解需求意图和项目结构
- [ ] 需求文档包含可验证的 AC

**模板**：见文档末尾

---

### I - Innovate (设计)

**目标**：找到最优技术方案，而非第一个想到的方案

**步骤**：

1. **生成技术方案草案**
   - 技术选型
   - 核心流程设计
   - 数据结构设计
   - Pros/Cons 分析

2. **强制互问互答**
   - 问："除了这个方案，还有没有更好的？这样做的坏处是什么？"
   - 对业务逻辑有不确定时，立刻提问，不要猜测

3. **引入专家视角**（去拟人化）
   - 问："顶尖架构师和技术专家会如何设计这个功能？"
   - 从性能、可维护性、扩展性三个维度分析

4. **生成设计文档**
   - 如果涉及接口，生成 `docs/specs/feature-xxx/02_interface.md`

**验收门禁**：
- [ ] 用户对设计方案进行了 Review 和 Sign-off
- [ ] 方案包含 Pros/Cons 分析
- [ ] 关键技术决策有明确理由

---

### P - Plan (规划)

**目标**：把设计变成可执行的实施计划

**步骤**：

1. **生成实施计划**
   - 创建 `docs/specs/feature-xxx/03_implementation.md`
   - 包含：
     - 要修改的文件列表（带完整路径）
     - 要新增的类/方法（带签名）
     - 核心流程伪代码
     - 数据库变更（如适用）
     - 分步执行计划（Step 1/2/3...）
     - 关键校验与异常处理
     - 回滚与兼容性方案

2. **Mock 数据定义**
   - 在写代码前，先定义好接口的 Request/Response 示例
   - 写入 `02_interface.md`

3. **认知对齐**
   - 问："为什么要在 Service 层做这个校验，而不是 Controller 层？"
   - 确保理解了逻辑，而不是在套模板

4. **生成测试策略**
   - 创建 `docs/specs/feature-xxx/04_test_spec.md`

**验收门禁**：
- [ ] 实施计划拆解到"原子级"任务
- [ ] 文件路径、方法签名明确
- [ ] 如果换一个 AI 能否 100% 按计划实施

**模板**：见文档末尾

---

### E - Execute (执行)

**目标**：结对编程，分步实施

**步骤**：

1. **分步指令**
   - 按照 Plan 的步骤，一步一步来
   - 每完成一步，自检：是否符合 Spec 要求？

2. **实时自检**
   - 每完成一步，总结：完成了什么？是否符合 Spec？

3. **人工干预**
   - 如果发现跑偏，立刻暂停
   - 回滚这一步，修正后重试

4. **硬性门禁检查**
   - Lint Check（语法检查）
   - Compile Check（编译检查）
   - 类型检查（如适用）

**验收门禁**：
- [ ] 代码通过 Lint Check
- [ ] 代码通过 Compile Check
- [ ] 每一步都有自检确认

---

### R - Review (审查)

**目标**：让另一个 AI 检查第一个 AI 的作业

**步骤**：

1. **法医式审查**
   - 阅读 Spec 文档和代码变更
   - 基于 Spec 审查代码，寻找：
     - 潜在 Bug
     - 逻辑漏洞
     - 不符合规范的地方
     - 性能问题
     - 安全隐患

2. **旁观者视角**
   - 问："如果请 Google 的 Principal Engineer 来做 Code Review，他会指出这段代码的哪些隐患？"

3. **生成测试**
   - 基于 Spec 生成单元测试
   - 覆盖：主流程、边界条件、异常情况

4. **更新决策日志**
   - 更新 `docs/decisions/AI_CHANGELOG.md`
   - 记录：Decision、Reason、Risk、Files

**验收门禁**：
- [ ] 自动化测试全绿
- [ ] 接口响应与 `02_interface.md` 完全一致
- [ ] Review 报告无重大问题

---

## L.A.F.R. 故障排查

**触发时机**：遇到 Bug、测试失败、生产问题

### 1. Locate (定位)

构建"案发现场"：
- Spec 文档：`docs/specs/feature-xxx/`
- 相关代码：[文件路径]
- 错误日志：[日志内容]

定位问题根因。

### 2. Analyze (分析)

判断是：
- **执行层错误**（代码写错了）
- **设计层错误**（文档没写对）

### 3. Fix (修复)

- 如果是代码错 → 生成补丁
- 如果是文档错 → **必须先改文档，再重新生成代码**

### 4. Record (留痕)

更新以下文档：
- `docs/skills/SKILL.md` - 添加防复发规则
- `docs/decisions/AI_CHANGELOG.md` - 记录此次修复
- `docs/specs/feature-xxx/04_test_spec.md` - 补充回归用例

---

## 关键技巧

### 去拟人化交互

❌ 不要问："你觉得这个方案怎么样？"
✅ 要问："顶尖架构师会如何评价这个方案？"

### 旁观者视角

❌ 不要问："你的代码对吗？"
✅ 要问："Google 的 Principal Engineer 会指出哪些问题？"

### 强制批判性思维

从以下角度审查设计：
1. 性能瓶颈在哪里？
2. 安全隐患在哪里？
3. 可维护性如何？
4. 有没有更简单的方案？

---

## 文档模板

### 01_requirement.md

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

### 02_interface.md

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

### 03_implementation.md

```markdown
# Implementation: [功能名称]

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
- Step 1: [任务描述]
- Step 2: [任务描述]

## Rollback & Compatibility (回滚与兼容)
- 如何关闭：
- 如何回退：
- 影响面：
```

### 04_test_spec.md

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

---

## 工作流程示例

**用户**：使用 SDD 开发用户签到功能

**AI**：

【阶段 1: Research】

让我先理解需求：

1. 用户签到功能需要包含哪些功能？
   - 每日签到
   - 查询签到状态
   - 签到奖励

2. 幂等性要求？
   - 同一天只能签到一次

3. 性能要求？
   - 接口响应时间 < 200ms

请回答以上问题，我会生成需求文档。

**用户**：[回答问题]

**AI**：

【阶段 2: Innovate】

基于你的回答，我提出以下方案：

**方案 A**：使用 Redis 计数
- Pros: 性能好
- Cons: 一致性风险

**方案 B**：使用数据库唯一约束
- Pros: 一致性强
- Cons: 并发性能稍差

推荐方案 B，理由是...

你同意吗？

**用户**：同意

**AI**：

【阶段 3: Plan】

正在生成文档：
- ✅ `docs/specs/feature-001-checkin/01_requirement.md`
- ✅ `docs/specs/feature-001-checkin/02_interface.md`
- ✅ `docs/specs/feature-001-checkin/03_implementation.md`
- ✅ `docs/specs/feature-001-checkin/04_test_spec.md`

实施计划：
- Step 1: 创建 checkin_record 表
- Step 2: 实现 CheckInService.checkIn()
- Step 3: 实现 CheckInController
- Step 4: 编写单元测试

准备好开始执行了吗？

**用户**：开始

**AI**：

【阶段 4: Execute】

Step 1: 创建 checkin_record 表...
[生成代码]

自检：✅ 符合 Spec 要求

继续 Step 2？

[... 继续执行 ...]

**AI**：

【阶段 5: Review】

所有步骤已完成，现在进行审查：

✅ 代码通过 Lint Check
✅ 代码通过类型检查
✅ 单元测试全绿
✅ 接口响应与文档一致

已更新：
- `docs/decisions/AI_CHANGELOG.md`
- `docs/skills/SKILL.md`（添加幂等性规则）

功能开发完成！
