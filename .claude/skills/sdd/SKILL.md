---
name: sdd
description: Spec-Driven Development (SDD) 规范驱动开发范式。当用户要求开发新功能、修复 Bug、重构代码时，遵循 RIPER 工作流（Research → Innovate → Plan → Execute → Review）和 LAFR 故障排查协议，以 Spec 文档作为唯一事实来源驱动 AI 编码。触发场景：开发新功能、修复复杂 Bug、重构模块、用户提到 SDD/RIPER/Spec 驱动/规范驱动等。不适用于简单 Bug 修复、单文件修改、快速原型。
---

# 执行 SDD 工作流

## 核心原则

**文档是上下文锚点**：防止上下文腐烂、审查瘫痪、维护断层。

三大价值：
1. **上下文锚定** - Spec 文档锁定任务意图，可随时恢复
2. **验收标准** - 代码必须兑现文档承诺，而非逐行 Review
3. **知识资产** - 代码可抛弃，文档才是长期资产

## 准备目录结构

确保项目有以下结构：

```
docs/
├── specs/feature-xxx/
│   ├── 01_requirement.md
│   ├── 02_interface.md
│   ├── 03_implementation.md
│   └── 04_test_spec.md
├── decisions/
│   └── AI_CHANGELOG.md
└── skills/
    └── SKILL.md
```

---

## 执行 RIPER 工作流

### R - Research (调研)

**目标**：把模糊需求变成清晰的需求规格

**步骤**：

1. **复述需求** - 用自己的话复述，指出不清晰的地方，列出需要参考的现有代码/模块
2. **澄清边界** - 功能范围（In Scope / Out of Scope）、边界条件、异常处理、性能要求
3. **生成需求文档** - 创建 `docs/specs/feature-xxx/01_requirement.md`

**验收门禁**：
- [ ] 所有"模糊点"都已解答
- [ ] 完全理解需求意图和项目结构
- [ ] 需求文档包含可验证的 AC

**模板**：见 [references/templates.md](references/templates.md)

---

### I - Innovate (设计)

**目标**：找到最优技术方案，而非第一个想到的方案

**步骤**：

1. **生成技术方案草案** - 技术选型、核心流程设计、数据结构设计、Pros/Cons 分析
2. **强制互问互答** - 问："除了这个方案，还有没有更好的？这样做的坏处是什么？"
3. **引入专家视角** - 问："顶尖架构师会如何设计这个功能？" 从性能、可维护性、扩展性分析
4. **生成设计文档** - 如果涉及接口，生成 `docs/specs/feature-xxx/02_interface.md`

**验收门禁**：
- [ ] 用户对设计方案进行了 Review 和 Sign-off
- [ ] 方案包含 Pros/Cons 分析
- [ ] 关键技术决策有明确理由

---

### P - Plan (规划)

**目标**：把设计变成可执行的实施计划

**步骤**：

1. **生成实施计划** - 创建 `docs/specs/feature-xxx/03_implementation.md`
2. **Mock 数据定义** - 在写代码前，先定义好接口的 Request/Response 示例
3. **认知对齐** - 问："为什么要在 Service 层做这个校验？"
4. **生成测试策略** - 创建 `docs/specs/feature-xxx/04_test_spec.md`

**验收门禁**：
- [ ] 实施计划拆解到"原子级"任务
- [ ] 文件路径、方法签名明确
- [ ] 如果换一个 AI 能否 100% 按计划实施

**模板**：见 [references/templates.md](references/templates.md)

---

### E - Execute (执行)

**目标**：结对编程，分步实施

**步骤**：

1. **分步指令** - 按照 Plan 的步骤，一步一步来
2. **实时自检** - 每完成一步，总结：完成了什么？是否符合 Spec？
3. **人工干预** - 如果发现跑偏，立刻暂停，回滚这一步
4. **硬性门禁检查** - Lint Check、Compile Check、类型检查

**验收门禁**：
- [ ] 代码通过 Lint Check
- [ ] 代码通过 Compile Check
- [ ] 每一步都有自检确认

---

### R - Review (审查)

**目标**：让另一个 AI 检查第一个 AI 的作业

**步骤**：

1. **法医式审查** - 阅读 Spec 文档和代码变更，寻找潜在 Bug、逻辑漏洞、性能问题、安全隐患
2. **旁观者视角** - 问："Google 的 Principal Engineer 会指出哪些隐患？"
3. **生成测试** - 基于 Spec 生成单元测试，覆盖主流程、边界条件、异常情况
4. **更新决策日志** - 更新 `docs/decisions/AI_CHANGELOG.md`

**验收门禁**：
- [ ] 自动化测试全绿
- [ ] 接口响应与 `02_interface.md` 完全一致
- [ ] Review 报告无重大问题

---

## 执行 LAFR 故障排查

**触发时机**：遇到 Bug、测试失败、生产问题

### 1. Locate (定位)

构建"案发现场"：
- Spec 文档：`docs/specs/feature-xxx/`
- 相关代码：[文件路径]
- 错误日志：[日志内容]

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

- 不要问："你觉得这个方案怎么样？"
- 要问："顶尖架构师会如何评价这个方案？"

### 旁观者视角

- 不要问："你的代码对吗？"
- 要问："Google 的 Principal Engineer 会指出哪些问题？"

### 强制批判性思维

从以下角度审查设计：
1. 性能瓶颈在哪里？
2. 安全隐患在哪里？
3. 可维护性如何？
4. 有没有更简单的方案？

---

## 参考资源

- **文档模板**：见 [references/templates.md](references/templates.md)
- **工作流示例**：见 [references/examples.md](references/examples.md)