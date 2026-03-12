# AIOA 项目

## 项目简介

[项目描述待补充]

## 技术栈

- Python
- [其他技术栈待补充]

## 项目结构

```
AIOA/
├── .claude/
│   └── skills/
│       └── sdd.md                  # SDD 工作流技能（按需加载）
├── docs/
│   ├── specs/                      # 功能规格文档
│   ├── decisions/
│   │   └── AI_CHANGELOG.md         # AI 决策日志
│   └── skills/
│       └── SKILL.md                # 团队规则库
├── CLAUDE.md                       # 项目配置（精简版）
├── SDD使用指南.md                   # 使用说明
└── test.py
```

## 开发工作流

本项目采用 **按需加载的 SDD 工作流**：

### 简单任务（默认）
直接提问，快速响应，不生成文档。

### 复杂任务（SDD 模式）
使用 `/sdd` 命令启动完整工作流：
1. **Research** - 分析问题，生成需求文档
2. **Innovate** - 设计方案，评估 Pros/Cons
3. **Plan** - 制定实施计划，生成文档
4. **Execute** - 分步执行，实时检查
5. **Review** - 审查验收，生成测试

**详细说明**：`SDD使用指南.md`

## 快速开始

### 1. 初始化项目上下文

```bash
/init
```

### 2. 简单开发

```bash
# 直接提问，无需特殊命令
你：帮我写一个读取 JSON 的函数
AI：[快速生成代码]
```

### 3. 复杂功能开发

```bash
# 使用 SDD 模式
你：/sdd 实现用户认证系统
AI：【阶段 1: Research】开始分析需求...
```

## 核心优势

- ✅ **节省上下文**：简单对话不加载 SDD（节省 85% 上下文）
- ✅ **按需加载**：复杂任务时才加载完整工作流
- ✅ **灵活切换**：可以随时在两种模式间切换
- ✅ **文档驱动**：防止上下文腐烂、审查瘫痪、维护断层

## 文档规范

### 何时生成文档

- ✅ 新功能开发（多文件协作）
- ✅ 复杂重构（架构调整）
- ✅ 接口设计（前后端协作）
- ❌ 简单 Bug 修复
- ❌ 单文件小改动

### 文档位置

```
docs/specs/feature-xxx/
├── 01_requirement.md      # 需求规格
├── 02_interface.md        # 接口契约
├── 03_implementation.md   # 实施细节
└── 04_test_spec.md        # 测试策略
```

## 贡献指南

1. 复杂功能开发前，使用 `/sdd` 生成 Spec 文档
2. 代码变更时，同步更新对应文档
3. 重要决策记录到 `docs/decisions/AI_CHANGELOG.md`
4. 团队规则记录到 `docs/skills/SKILL.md`

## 参考文档

- `CLAUDE.md` - 项目配置
- `SDD使用指南.md` - 详细使用说明
- `Claude_Code_AI编程工作流.md` - 完整工作流文档
- `.claude/skills/sdd.md` - SDD 技能定义
