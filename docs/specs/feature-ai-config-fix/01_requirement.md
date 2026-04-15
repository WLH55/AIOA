# AI 配置修复 Spec

## Meta

- Phase: Execute
- Approval Status: Plan Approved
- Spec Path: `docs/specs/feature-ai-config-fix/01_requirement.md`
- Date: 2026-04-14

## Goal

修复 AI 助手返回“AI 服务暂时不可用，请稍后重试”的问题，使开发环境后端能够正确加载 `DEEPSEEK_API_KEY` 并正常初始化 LLM。

## In Scope

- 修复开发环境 `.env.development` 缺失 AI 配置的问题
- 可选：补充 AI 输出 token 配置项，避免 `app/ai/llm.py` 中硬编码
- 可选：增强启动日志，帮助后续排查 AI 配置是否加载成功

## Out of Scope

- 切换模型供应商
- 修改业务工具权限设计
- 重构 AI Agent 主流程
- 提交代码或部署服务

## Context Sources

- 用户提供的 `.env` 片段（包含 `DEEPSEEK_API_KEY`）
- `storage/logs/app.log`
- `app/config/settings.py`
- `app/ai/llm.py`
- `app/main.py`

## Research Findings

1. 当前运行时错误已由日志确认：`DEEPSEEK_API_KEY 未配置，AI Agent 功能不可用`
2. `Settings` 根据 `ENVIRONMENT` 加载根目录 `.env.development`
3. 当前根目录 `.env.development` 仅包含基础配置，到 JWT 结束，缺少 AI 配置段
4. `app/ai/llm.py` 会在 `get_chat_llm()` 中强校验 `settings.DEEPSEEK_API_KEY`
5. 当前 `AI_MODEL_CONTEXT_WINDOW=128000` 已在 `app/config/settings.py` 中配置，问题不是上下文窗口缺失
6. 当前 `ChatOpenAI` 的 `max_tokens` 仍为硬编码：聊天 4096、摘要 1024

## Plan

### File Changes

1. `.env.development`
   - 追加 AI 配置段：`DEEPSEEK_API_KEY`、`DEEPSEEK_BASE_URL`、`DEEPSEEK_MODEL`、内存与超时配置

2. `app/config/settings.py`
   - 新增可配置项：`AI_CHAT_MAX_TOKENS`、`AI_SUMMARY_MAX_TOKENS`

3. `app/ai/llm.py`
   - 将 `max_tokens=4096/1024` 改为读取 settings

4. `app/main.py`
   - 启动日志增加 AI 配置加载状态与关键参数摘要（不打印密钥明文）

## Checklist

- [ ] 更新 `.env.development` 中 AI 配置
- [ ] 新增输出 token 配置项
- [ ] 替换 LLM 硬编码输出上限
- [ ] 增强启动日志可观测性

## Risks

- `.env.development` 包含真实密钥，修改时不能泄露到日志或响应文本
- 仅修改文件不会让已运行进程自动生效，仍需重启后端
- 如果实际启动时 `ENVIRONMENT` 不是 `development`，则仍可能读取其他 env 文件

## Validation

- 启动日志不再出现 `DEEPSEEK_API_KEY 未配置`
- 启动日志出现 `AI Agent 配置完成`
- AI 对话接口不再直接返回通用不可用错误

## Open Questions

- 是否只修复 `.env.development`，还是顺手把 `max_tokens` 配置化一起做

## Next Action

按计划执行 `.env.development`、`app/config/settings.py`、`app/ai/llm.py`、`app/main.py` 的最小修改。
