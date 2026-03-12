# Claude Code AI 编程工作流 - SDD 实践指南

基于 SDD (Spec-Driven Development) 方法论，整理出配合 Claude Code 使用的完整 AI 编程工作流。

## 核心理念

**文档驱动开发 (SDD)**: 让文档成为人与 AI 之间的"通信协议"，代码变成可抛弃的消耗品。

### 三大痛点与解决方案

1. **上下文腐烂** → 用 Spec 文档锚定任务
2. **审查瘫痪** → 用文档验证代码，而非逐行 Review
3. **维护断层** → 文档即知识库，随时可恢复上下文

---

## 一、目录结构规范

```
项目根目录/
├── docs/
│   ├── specs/                      # 功能规格文档
│   │   ├── feature-001-xxx/
│   │   │   ├── 00_context.md      # 可选：业务背景
│   │   │   ├── 01_requirement.md  # 需求规格
│   │   │   ├── 02_interface.md    # 接口契约
│   │   │   ├── 03_implementation.md # 实施细节
│   │   │   └── 04_test_spec.md    # 测试策略
│   ├── decisions/
│   │   ├── AI_CHANGELOG.md        # AI 决策日志
│   │   └── ADR-xxxx.md            # 架构决策记录
│   ├── skills/
│   │   └── SKILL.md               # 团队规则库/"家规"
│   └── logs/
│       └── ai-review-reports/     # Review 报告归档
└── .cursorrules                   # Claude Code 项目规则
```

---

## 二、完整工作流：Initialization + RIPER

### 阶段 0：初始化 (Initialization) - 装载大脑

**目标**: 让 Claude Code 理解项目上下文和约束

#### 操作步骤

1. **装载 SDD 协议**

发送给 Claude Code：

```markdown
# Role
你是一位遵循 "Spec-Driven Development" 协议的高级工程师。

# Workflow Rules
1. **Context First**: 编码前，始终检查 `docs/` 中是否存在相关 Spec 文件
2. **No Hallucinations**: 如果用户需求与 Spec 矛盾，停止并要求澄清
3. **Update Loop**: 如果改变代码逻辑，立即建议更新对应的 Spec 文件

# File Structure Strategy
- 使用 `01_requirement.md` 记录用户故事
- 使用 `02_interface.md` 记录技术栈和数据结构
- 使用 `03_implementation.md` 记录详细逻辑
- 使用 `04_test_spec.md` 记录测试策略
```

2. **加载项目规则** (如果有 `.cursorrules` 或 `SKILL.md`)

```markdown
请阅读项目的 .cursorrules 文件和 docs/skills/SKILL.md，
理解项目的技术偏好和业务铁律。
```

3. **注入项目记忆**

```markdown
请阅读 README.md 和相关功能的历史文档，
简要总结项目的核心架构和主要约束。
```

#### 验收门禁

- [ ] Claude Code 确认收到上下文（让它复述主要约束）
- [ ] Claude Code 理解项目结构和技术栈

---

### 阶段 1：Research (调研与意图锁定)

**目标**: 把模糊需求变成清晰的需求规格

#### 操作步骤

1. **提供需求描述**

```markdown
我需要实现一个功能：[描述你的需求]

请先不要写代码，帮我：
1. 用你自己的话复述这个需求
2. 指出其中不清晰的地方
3. 列出需要参考的现有代码/模块
```

2. **澄清边界**

回答 Claude Code 提出的问题，明确：
- 功能范围（In Scope / Out of Scope）
- 边界条件
- 异常处理
- 性能要求

3. **生成需求文档**

```markdown
基于我们的讨论，请生成 `docs/specs/feature-xxx/01_requirement.md`，
包含：背景、目标、范围、验收标准、约束、风险。
```

#### 验收门禁

- [ ] AI 指出的"模糊点"都已解答
- [ ] AI 完全理解需求意图和项目结构
- [ ] 需求文档包含可验证的验收标准（AC）

---

### 阶段 2：Innovate (设计与推演)

**目标**: 找到最优技术方案，而非第一个想到的方案

#### 操作步骤

1. **生成技术方案草案**

```markdown
请基于需求文档，生成技术实施草案（HLD），包括：
- 技术选型
- 核心流程设计
- 数据结构设计
- Pros/Cons 分析
```

2. **强制互问互答**

```markdown
除了这个方案，还有没有更好的？这样做的坏处是什么？

如果你对现有业务逻辑或代码细节有任何不确定的地方，
请立刻向我提问，不要自己猜测。
```

3. **引入专家视角**（去拟人化）

```markdown
顶尖架构师和技术专家会如何设计这个功能？
请从性能、可维护性、扩展性三个维度分析。
```

4. **生成设计文档**

```markdown
请将最终方案整理成 `docs/specs/feature-xxx/02_interface.md`
（如果涉及接口）和设计说明。
```

#### 验收门禁

- [ ] 你对设计方案进行了 Review 和 Sign-off
- [ ] 方案包含 Pros/Cons 分析
- [ ] 关键技术决策有明确理由

---

### 阶段 3：Plan (规划与契约)

**目标**: 把设计变成可执行的实施计划

#### 操作步骤

1. **生成实施计划**

```markdown
请基于设计方案，生成详细的实施计划
`docs/specs/feature-xxx/03_implementation.md`，包括：

1. 要修改的文件列表（带完整路径）
2. 要新增的类/方法（带签名）
3. 核心流程伪代码
4. 数据库变更（如适用）
5. 分步执行计划（Step 1/2/3...）
6. 关键校验与异常处理
7. 回滚与兼容性方案
```

2. **Mock 数据定义**

```markdown
在写代码前，请先定义好接口的 Request/Response 示例
（写入 02_interface.md）。
```

3. **认知对齐**

```markdown
为什么要在 Service 层做这个校验，而不是 Controller 层？
请确保你理解了逻辑，而不是在套模板。
```

#### 验收门禁

- [ ] 实施计划拆解到"原子级"任务
- [ ] 文件路径、方法签名明确
- [ ] 如果换一个 AI 能否 100% 按计划实施

---

### 阶段 4：Execute (执行与编码)

**目标**: 结对编程，分步实施

#### 操作步骤

1. **分步指令**

```markdown
好的，先完成 Step 1：[具体任务]
完成后请自检：是否符合 Spec 要求？
```

2. **实时自检**

每完成一步：
```markdown
请总结：你完成了什么？这是否符合 Spec 的要求？
```

3. **人工干预**

如果发现跑偏：
```markdown
暂停！这里的实现与 Spec 不符，请回滚这一步，
我们重新明确需求后再试。
```

4. **硬性门禁检查**

```markdown
请运行以下检查：
1. Lint Check（语法检查）
2. Compile Check（编译检查）
3. 类型检查（如适用）

如果有错误，必须先修复再继续。
```

#### 验收门禁

- [ ] 代码通过 Lint Check
- [ ] 代码通过 Compile Check
- [ ] 每一步都有自检确认

---

### 阶段 5：Review (验收与对齐)

**目标**: 让另一个 AI 检查第一个 AI 的作业

#### 操作步骤

1. **开启新对话**

在 Claude Code 中开启新对话（或使用 `/clear`），或者换一个模型。

2. **法医式审查**

```markdown
我刚完成了一个功能实现，请帮我审查。

请阅读：
1. Spec 文档：docs/specs/feature-xxx/
2. 代码变更：[提供 git diff 或文件路径]

请基于 Spec 审查代码，寻找：
- 潜在 Bug
- 逻辑漏洞
- 不符合规范的地方
- 性能问题
- 安全隐患
```

3. **旁观者视角**

```markdown
如果请 Google 的 Principal Engineer 来做 Code Review，
他会指出这段代码的哪些隐患？
```

4. **迭代修正**

把审查报告交给原来的 AI（或自己修改），循环直到"评审官"满意。

5. **生成测试**

```markdown
请基于 Spec 生成单元测试，覆盖：
- 主流程
- 边界条件
- 异常情况
```

#### 验收门禁

- [ ] 自动化测试全绿
- [ ] 接口响应与 `02_interface.md` 完全一致
- [ ] Review 报告无重大问题

---

## 三、旁路流程：L.A.F.R. 故障排查

当遇到 Bug 时，不要直接改代码，执行以下流程：

### 1. Locate (定位)

```markdown
出现了一个问题：[描述错误]

请阅读：
1. Spec 文档：docs/specs/feature-xxx/
2. 相关代码：[文件路径]
3. 错误日志：[日志内容]

请帮我定位问题根因。
```

### 2. Analyze (分析)

```markdown
请判断这是：
- 执行层错误（代码写错了）
- 设计层错误（文档没写对）
```

### 3. Fix (修复)

- **如果是代码错** → 生成补丁
- **如果是文档错** → 必须先改文档，再重新生成代码

```markdown
请先更新 Spec 文档，然后基于新文档重新生成代码。
```

### 4. Record (留痕)

```markdown
请更新以下文档：
1. docs/skills/SKILL.md - 添加防复发规则
2. docs/decisions/AI_CHANGELOG.md - 记录此次修复
3. docs/specs/feature-xxx/04_test_spec.md - 补充回归用例
```

---

## 四、文档模板

### 模板 1: 需求规格 (01_requirement.md)

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

### 模板 2: 接口契约 (02_interface.md)

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




### 模板 3: 实施细节 (03_implementation.md)

```markdown
# Implementation: [功能名称]

## Objective (目标复述)
用 3-5 行复述本次要实现什么。

## File Changes (变更范围)
- `src/xxx/Controller.java` - 新增接口
- `src/xxx/Service.java` - 实现业务逻辑
- `src/xxx/Repository.java` - 数据访问

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
- Step 3: [任务描述]

## Rollback & Compatibility (回滚与兼容)
- 如何关闭：
- 如何回退：
- 影响面：
```

### 模板 4: 测试策略 (04_test_spec.md)

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

## 五、团队协作 SOP

### 角色分工

| 文档 | Owner | Sign-off |
|------|-------|----------|
| 01_requirement.md | PM/需求提出人 | 业务 Owner + TL |
| 02_interface.md | 后端 | 前端/客户端 + QA |
| 03_implementation.md | 实现负责人 | TL/核心评审人 |
| 04_test_spec.md | QA | 实现负责人 + QA |

### 并行开发流程

1. **后端先行**：生成 `02_interface.md`
2. **前端并行**：基于接口文档生成 Mock 和类型定义
3. **测试并行**：基于需求和接口文档生成测试用例
4. **联调验收**：后端实现完成后，前端切换真实接口

---

## 六、基础设施

### 1. 团队规则库 (SKILL.md)

```markdown
# Team Skills & Rules

## 技术偏好
- 本项目使用 Java 17
- 优先使用 Record 类
- 禁止使用 Lombok

## 业务铁律
- 所有金额字段：数据库用 Decimal(19,4)，Java 用 BigDecimal
- 所有时间字段：使用 UTC 时区存储

## 测试规范
- 单元测试使用 JUnit 5
- 必须覆盖空指针异常

## 错误记录
- [日期] Bug #42: 分页参数遗漏 → 规则：所有列表接口必须包含分页
```

### 2. 决策日志 (AI_CHANGELOG.md)

```markdown
# AI Decision Changelog

## 2026-03-12 feature-001-checkin
- **Decision**: 幂等通过数据库唯一约束实现
- **Reason**: 降低一致性风险，数据库作为最终一致性来源
- **Risk**: 高并发写入压力，需关注索引性能
- **Files**: CheckInService.java, checkin_record 表

## 2026-03-10 bugfix-payment
- **Decision**: 修复支付金额精度问题
- **Root Cause**: 使用了 Double 而非 BigDecimal
- **Fix**: 更新 SKILL.md，强制金额使用 BigDecimal
- **Files**: PaymentService.java
```

---

## 七、快速上手（30 分钟）

### Lite 版工作流

适用于个人开发、快速迭代。

1. **0-3min**: 初始化 - 装载 SDD 协议
2. **3-10min**: Research - 生成需求文档，你 Sign-off
3. **10-15min**: Plan - 生成实施计划
4. **15-25min**: Execute - 分步写代码 + 最小单测
5. **25-30min**: Review - 新对话审查 Spec + Diff

### 第一次实践建议

1. 选择一个小功能（1-2 小时可完成）
2. 严格按照 RIPER 流程走一遍
3. 重点体会"文档锚定上下文"的价值
4. 完成后归档到 `docs/specs/`

---

## 八、常见问题

### Q1: 这会不会增加工作量？

**A**: 短期看多了写文档的时间，长期看：
- 减少了反复沟通的时间
- 减少了 Debug 的时间
- 减少了维护的时间
- 让 AI 起草，你只做 Review

### Q2: 小改动也要写文档吗？

**A**: 灵活处理：
- **小 bugfix**: 可以直接改，但要更新 `AI_CHANGELOG.md`
- **复杂功能**: 强制走完整流程
- **核心模块**: 即使小改动也建议写文档

### Q3: 文档会不会过时？

**A**: 建立触发机制：
- 需求变更 → 先改 `01_requirement.md`
- 代码重构 → 先改 `03_implementation.md`
- 线上 Bug → 回填 `04_test_spec.md` + `SKILL.md`

### Q4: 如何处理遗留项目？

**A**: 增量补充：
- 不要试图一次性补齐全量文档
- 从下一个 feature 开始写文档
- 每次修改时补充相关文档
- 逐步建立知识库

---

## 九、进阶技巧

### 1. 去拟人化交互

❌ 不要问："你觉得这个方案怎么样？"
✅ 要问："顶尖架构师会如何评价这个方案？"

### 2. 旁观者视角

❌ 不要问："你的代码对吗？"
✅ 要问："Google 的 Principal Engineer 会指出哪些问题？"

### 3. 强制批判性思维

```markdown
请从以下角度审查这个设计：
1. 性能瓶颈在哪里？
2. 安全隐患在哪里？
3. 可维护性如何？
4. 有没有更简单的方案？
```

### 4. 文档即代码

- 文档也要版本管理（Git）
- 文档变更也要 PR Review
- 文档也要有 Owner

---

## 十、工具集成

### Claude Code 配置

在项目根目录创建 `.cursorrules`：

```markdown
# SDD Protocol
本项目遵循 Spec-Driven Development 协议。

## 工作流
1. 编码前检查 docs/specs/ 中的相关文档
2. 代码变更必须对应文档更新
3. 新功能必须先有 Spec 文档

## 文档结构
- 01_requirement.md: 需求规格
- 02_interface.md: 接口契约
- 03_implementation.md: 实施细节
- 04_test_spec.md: 测试策略

## 团队规则
[从 docs/skills/SKILL.md 复制]
```

### Git Hooks（可选）

```bash
# .git/hooks/pre-commit
# 检查是否有对应的 Spec 文档更新

#!/bin/bash
changed_files=$(git diff --cached --name-only)

if echo "$changed_files" | grep -q "^src/"; then
    if ! echo "$changed_files" | grep -q "^docs/specs/"; then
        echo "警告：代码变更但未更新 Spec 文档"
        echo "是否继续提交？(y/n)"
        read answer
        if [ "$answer" != "y" ]; then
            exit 1
        fi
    fi
fi
```

---

## 十一、成功指标

### 个人层面

- [ ] 能在 30 分钟内完成一个小功能的完整闭环
- [ ] New Chat 后能快速恢复上下文
- [ ] 代码 Review 时间减少 50%
- [ ] Bug 修复时能快速定位根因

### 团队层面

- [ ] 前后端并行开发效率提升
- [ ] 接口对接时间减少
- [ ] 新人上手时间缩短
- [ ] 知识库持续增长

---

## 总结

SDD 不是让你写更多文档，而是：

1. **把思考前置** - 先想清楚再动手
2. **让 AI 起草** - 你只做 Review 和决策
3. **文档即协议** - 人与 AI 的共同语言
4. **代码可抛弃** - 文档才是资产

**记住**: 代码会过时，工具会迭代，模型会换代。但你对业务的理解、对架构的审美、以及驾驭 AI 的能力，将是你在这个时代最坚固的护城河。

---

**开始你的第一次 SDD 之旅吧！**
