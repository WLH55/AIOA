# SDD 工作流程示例

## 示例：用户签到功能

**用户**：使用 SDD 开发用户签到功能

**AI**：

### 阶段 1: Research

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

---

### 阶段 2: Innovate

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

---

### 阶段 3: Plan

正在生成文档：
- `docs/specs/feature-001-checkin/01_requirement.md`
- `docs/specs/feature-001-checkin/02_interface.md`
- `docs/specs/feature-001-checkin/03_implementation.md`
- `docs/specs/feature-001-checkin/04_test_spec.md`

实施计划：
- Step 1: 创建 checkin_record 表
- Step 2: 实现 CheckInService.checkIn()
- Step 3: 实现 CheckInController
- Step 4: 编写单元测试

准备好开始执行了吗？

**用户**：开始

---

### 阶段 4: Execute

Step 1: 创建 checkin_record 表...
[生成代码]

自检：符合 Spec 要求

继续 Step 2？

[... 继续执行 ...]

---

### 阶段 5: Review

所有步骤已完成，现在进行审查：

- 代码通过 Lint Check
- 代码通过类型检查
- 单元测试全绿
- 接口响应与文档一致

已更新：
- `docs/decisions/AI_CHANGELOG.md`
- `docs/skills/SKILL.md`（添加幂等性规则）

功能开发完成！