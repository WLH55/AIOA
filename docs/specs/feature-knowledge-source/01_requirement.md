# Feature: 知识库来源标注 + 文档预览

## 1. Background (背景)

RAG 知识库系统已实现基础功能（文档上传、解析、分块、向量化、KNN 检索、Agent 工具集成），但存在两个不足：

1. **来源标注不精确**：AI 回答仅标注文件名 `[参考1 - 来源: 员工手册.pdf]`，没有行号或页码，用户无法定位到原文档的具体位置
2. **无法查看原文**：没有文件下载/预览接口，用户无法将 AI 回答与原文档内容对比验证

现有基础：
- `DocumentParser` 支持 PDF/Word/TXT/Markdown 解析，但返回纯文本（`str`），无位置信息
- `TextChunker` 的 metadata 仅有 `filename` 和 `chunk_index`
- Redis Hash 的 `metadata` 字段存储 JSON，可扩展
- `queryKnowledge` 工具拼接结果时仅使用 `filename`
- 前端知识库页面已实现 SSE 流式对话

## 2. Goals (目标)

- parser 输出带位置信息的结构化数据（PDF→页码，TXT/MD→行号，Word→段落标题）
- chunk metadata 携带精确位置范围
- AI 回答标注格式变为 `[参考1 - 来源: 员工手册.pdf 第3页 第45-52行]`
- 后端新增解析文本查询接口 `GET /v1/knowledge/file/{doc_id}/content`
- 前端 AI 回复中的来源标注可点击，弹窗显示原文（带行号），自动定位到来源位置

## 3. In Scope / Out of Scope

### In Scope

1. parser 返回值重构：`str` → `List[TextBlock]`（含位置信息）
2. chunker 位置追踪：分块时计算位置范围，写入 metadata
3. queryKnowledge 输出增强：带页码/行号的来源标注
4. 后端新增文档内容查询接口
5. 前端来源标注可点击 + 弹窗预览

### Out of Scope

- 原始文件下载（后续迭代）
- PDF/Word 原格式预览（后续迭代）
- 来源文本高亮标注（后续迭代）

## 4. Acceptance Criteria (验收标准)

### AC1: PDF 文档标注页码
- Given: 上传一份 PDF 文件并更新知识库
- When: 用户提问并命中第 3 页的内容
- Then: AI 回答包含 `[参考1 - 来源: xxx.pdf 第3页]`

### AC2: TXT/MD 文档标注行号
- Given: 上传一份 TXT 文件并更新知识库
- When: 用户提问并命中第 15-22 行的内容
- Then: AI 回答包含 `[参考1 - 来源: xxx.txt 第15-22行]`

### AC3: Word 文档标注段落标题
- Given: 上传一份 Word 文件并更新知识库
- When: 用户提问并命中"第三章 假期规定"下的内容
- Then: AI 回答包含 `[参考1 - 来源: xxx.docx 第三章 假期规定]`

### AC4: 点击来源弹窗预览
- Given: AI 回答中包含来源标注
- When: 用户点击 `[参考1 - 来源: xxx]`
- Then: 弹出对话框显示原文档解析文本（带行号），自动滚动到引用位置

### AC5: 文档内容接口
- Given: 文档已上传并处理完成
- When: 调用 `GET /v1/knowledge/file/{doc_id}/content`
- Then: 返回解析后的文本内容，TXT/MD 带行号，PDF 带页码标记

## 5. Impact Analysis (影响分析)

| 文件 | 变更类型 | 说明 |
|------|---------|------|
| `app/ai/document/parser.py` | 重构 | 返回值从 `str` 改为 `ParseResult` |
| `app/ai/document/chunker.py` | 修改 | 接收 `ParseResult`，追踪位置范围 |
| `app/ai/tools/knowledge_tool.py` | 修改 | updateKnowledge 适配新 parser 返回值；queryKnowledge 增强输出格式 |
| `app/routers/knowledge.py` | 新增端点 | `GET /file/{doc_id}/content` |
| 前端 `Index.vue` | 修改 | 来源标注可点击 + 弹窗组件 |
| `app/ai/vectorstore/redis_store.py` | 无变更 | metadata 字段已支持扩展 |
