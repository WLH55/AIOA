# SDD 工作流使用指南

## 📊 优化效果对比

### 之前（全部写在 CLAUDE.md）
- ❌ 每次对话都加载完整 SDD 协议（~400 行）
- ❌ 简单问答也消耗大量上下文
- ❌ 无法灵活选择是否使用 SDD

### 现在（按需加载 Skill）
- ✅ CLAUDE.md 精简到 67 行（减少 85%）
- ✅ 简单对话不加载 SDD，节省上下文
- ✅ 复杂任务时通过 `/sdd` 动态加载
- ✅ 更灵活、更高效

---

## 🚀 使用方式

### 1. 简单任务（默认模式）

直接提问，无需任何命令：

```
你：这段代码有什么问题？
AI：[快速分析回答]

你：帮我写一个排序函数
AI：[直接生成代码]
```

**特点**：
- 快速响应
- 不生成文档
- 适合单文件小改动、快速问答

---

### 2. 复杂任务（SDD 模式）

当需要开发复杂功能时，使用 `/sdd` 命令：

```
你：/sdd 开发用户签到功能
AI：【阶段 1: Research】
    已加载 SDD 工作流。

    让我先理解需求...
    [开始走完整 RIPER 流程]
```

**适用场景**：
- ✅ 新功能开发（多文件协作）
- ✅ 复杂重构（架构调整）
- ✅ 接口设计（前后端协作）
- ✅ 需要长期维护的模块

**不适用场景**：
- ❌ 简单 Bug 修复
- ❌ 单文件小改动
- ❌ 快速原型验证

---

### 3. 项目初始化

每次新会话开始时：

```
你：/init
AI：【初始化】
    正在读取项目文档...
    - README.md
    - docs/skills/SKILL.md
    - 历史 Spec 文档

    项目概况：[总结]
    技术栈：[列出]
    关键约束：[列出]
```

---

## 📁 文件结构说明

```
AIOA/
├── CLAUDE.md                       # 精简配置（67 行）
│                                   # - 基本规则
│                                   # - 项目结构
│                                   # - 工作模式说明
│
├── .claude/
│   └── skills/
│       └── sdd.md                  # SDD 完整工作流（426 行）
│                                   # - RIPER 五阶段详细说明
│                                   # - L.A.F.R. 故障排查
│                                   # - 文档模板
│
├── docs/
│   ├── specs/                      # 功能规格文档
│   │   └── feature-xxx/            # 每个功能一个目录
│   │       ├── 01_requirement.md   # 需求规格
│   │       ├── 02_interface.md     # 接口契约
│   │       ├── 03_implementation.md # 实施细节
│   │       └── 04_test_spec.md     # 测试策略
│   │
│   ├── decisions/
│   │   └── AI_CHANGELOG.md         # AI 决策日志
│   │
│   └── skills/
│       └── SKILL.md                # 团队规则库
│
├── README.md                       # 项目说明
└── Claude_Code_AI编程工作流.md     # 完整工作流文档（参考）
```

---

## 🎯 SDD 工作流程（RIPER）

当你使用 `/sdd` 后，会经历以下五个阶段：

### 1️⃣ Research（调研）
- 复述需求，指出不清晰的地方
- 搜索相关代码
- 生成 `01_requirement.md`

### 2️⃣ Innovate（设计）
- 提出技术方案
- Pros/Cons 分析
- 专家视角评审

### 3️⃣ Plan（规划）
- 生成 `02_interface.md`（接口契约）
- 生成 `03_implementation.md`（实施计划）
- 生成 `04_test_spec.md`（测试策略）

### 4️⃣ Execute（执行）
- 分步实施
- 实时自检
- Lint/Compile 检查

### 5️⃣ Review（审查）
- 基于 Spec 审查代码
- 生成单元测试
- 更新决策日志

---

## 💡 实战示例

### 示例 1：简单问答（不用 SDD）

```
你：Python 如何读取 JSON 文件？
AI：使用 json 模块：
    import json
    with open('file.json', 'r') as f:
        data = json.load(f)
```

### 示例 2：复杂功能（使用 SDD）

```
你：/sdd 实现一个用户认证系统，支持 JWT Token
AI：【阶段 1: Research】

    让我理解需求：
    1. 用户认证系统需要包含哪些功能？
       - 注册
       - 登录
       - Token 刷新
       - 登出

    2. JWT Token 的存储方式？
       - 存储在哪里（Redis/数据库）
       - 过期时间多久

    3. 安全要求？
       - 密码加密方式
       - Token 签名算法

    请回答以上问题，我会生成需求文档。

你：[回答问题]

AI：【阶段 2: Innovate】

    基于你的回答，我提出以下方案：

    方案 A：使用 Flask + PyJWT + Redis
    Pros: 轻量、灵活
    Cons: 需要自己实现很多细节

    方案 B：使用 FastAPI + python-jose + PostgreSQL
    Pros: 类型安全、自动文档
    Cons: 学习曲线稍陡

    推荐方案 B，理由是...

    你同意吗？

你：同意

AI：【阶段 3: Plan】

    正在生成文档：
    ✅ docs/specs/feature-001-auth/01_requirement.md
    ✅ docs/specs/feature-001-auth/02_interface.md
    ✅ docs/specs/feature-001-auth/03_implementation.md
    ✅ docs/specs/feature-001-auth/04_test_spec.md

    实施计划：
    Step 1: 创建用户模型和数据库表
    Step 2: 实现密码加密和验证
    Step 3: 实现 JWT Token 生成和验证
    Step 4: 实现注册/登录/刷新接口
    Step 5: 编写单元测试

    准备好开始执行了吗？

你：开始

AI：【阶段 4: Execute】

    Step 1: 创建用户模型...
    [生成代码]

    自检：✅ 符合 Spec 要求

    继续 Step 2？

[... 继续执行 ...]

AI：【阶段 5: Review】

    所有步骤已完成，现在进行审查：

    ✅ 代码通过 Lint Check
    ✅ 代码通过类型检查
    ✅ 单元测试全绿
    ✅ 接口响应与文档一致

    已更新：
    - docs/decisions/AI_CHANGELOG.md
    - docs/skills/SKILL.md（添加安全规则）

    功能开发完成！
```

---

## 🔧 故障排查（L.A.F.R.）

当遇到 Bug 时，使用 L.A.F.R. 流程：

```
你：登录接口报错 500
AI：让我使用 L.A.F.R. 流程排查：

    【Locate】定位问题
    请提供：
    1. Spec 文档路径
    2. 错误日志
    3. 相关代码

你：[提供信息]

AI：【Analyze】分析根因
    这是执行层错误：Token 验证逻辑有问题

    【Fix】修复
    正在生成补丁...

    【Record】留痕
    已更新：
    - docs/skills/SKILL.md（添加防复发规则）
    - docs/decisions/AI_CHANGELOG.md
    - docs/specs/feature-001-auth/04_test_spec.md（补充回归用例）
```

---

## 📝 最佳实践

### 1. 何时使用 SDD

**使用 SDD**：
- 功能会被长期维护
- 需要多人协作
- 涉及多个文件
- 有复杂的业务逻辑

**不使用 SDD**：
- 一次性脚本
- 快速验证想法
- 简单的工具函数

### 2. 文档维护

- **开发期**：文档是你的草稿本，随改随用
- **归档期**：月度/季度复盘时，精简后上传到知识库

### 3. 团队协作

- `SKILL.md`：记录团队规则，防止重复犯错
- `AI_CHANGELOG.md`：记录重要决策，方便追溯
- Spec 文档：前后端并行开发的契约

---

## ❓ 常见问题

### Q1: 每次都要输入 `/sdd` 吗？

A: 不是。简单任务直接问就行。只有复杂功能开发时才需要 `/sdd`。

### Q2: SDD 会不会很慢？

A: 前期会多花 10-15 分钟写文档，但后期维护、Debug、协作会快很多。

### Q3: 可以中途退出 SDD 吗？

A: 可以。任何时候都可以说"暂停 SDD"，切换回普通模式。

### Q4: 文档会过时吗？

A: 代码变更时，AI 会提醒你同步更新文档。养成习惯后不会过时。

---

## 🎉 总结

**核心优势**：
1. ✅ **节省上下文**：简单对话不加载 SDD（节省 85% 上下文）
2. ✅ **按需加载**：复杂任务时才加载完整工作流
3. ✅ **灵活切换**：可以随时在两种模式间切换
4. ✅ **文档驱动**：防止上下文腐烂、审查瘫痪、维护断层

**使用建议**：
- 日常开发：默认模式（快速高效）
- 重要功能：SDD 模式（稳定可靠）
- 定期归档：沉淀知识资产

现在开始使用吧！🚀
