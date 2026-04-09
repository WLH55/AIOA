# Implementation: 知识库来源标注 + 文档预览

## 1. 数据结构设计

### 1.1 ParseResult / TextBlock (parser.py 新增)

```python
class TextBlock:
    """解析后的文本块（含位置信息）"""
    content: str                    # 文本内容
    locationType: str               # "page" | "line" | "section"
    locationValue: str              # "3" / "15" / "第三章 假期规定"

class ParseResult:
    """文档解析结果"""
    blocks: List[TextBlock]         # 文本块列表
    fullText: str                   # 完整纯文本（向后兼容）
```

### 1.2 Chunk Metadata 扩展

```python
# 当前 metadata
{ "filename": "员工手册.pdf", "doc_id": "xxx", "chunk_index": 0 }

# 新增字段
{ "locationLabel": "第3页" }                      # PDF
{ "locationLabel": "第15-22行" }                   # TXT/MD
{ "locationLabel": "第三章 假期规定" }              # Word
```

### 1.3 queryKnowledge 输出格式

```
旧: [参考1 - 来源: 员工手册.pdf]\n内容...
新: [参考1 - 来源: 员工手册.pdf 第3页]\n内容...
新: [参考1 - 来源: 规章制度.txt 第15-22行]\n内容...
```

### 1.4 文档内容接口 Response

```
GET /v1/knowledge/file/{doc_id}/content

Response: {
  "code": 200,
  "data": {
    "filename": "员工手册.pdf",
    "fileType": "pdf",
    "content": "行号\t内容\n1\t第一章 总则\n2\t第一条...\n..."  // TXT/MD带行号
  }
}
```

PDF 的 content 格式: `[第1页]\n原始文本\n[第2页]\n原始文本`

## 2. 实施步骤

### Step 1: 重构 parser.py

**文件**: `app/ai/document/parser.py`

- 新增 `TextBlock` 和 `ParseResult` 数据类
- 新增 `parse_structured(file_path) -> ParseResult` 方法
- 保留原 `parse(file_path) -> str` 方法向后兼容（内部调用 parse_structured）
- 各格式解析器返回 `List[TextBlock]`：
  - `_parse_pdf`: 每个 TextBlock = 一页，locationType="page"
  - `_parse_text`: 每 N 行一个 TextBlock，locationType="line"，locationValue="起始行号"
  - `_parse_markdown`: 同 _parse_text
  - `_parse_docx`: 每个段落一个 TextBlock，标题段落 locationType="section"，正文段落 locationType="paragraph"

### Step 2: 修改 chunker.py

**文件**: `app/ai/document/chunker.py`

- 新增 `chunk_structured(parse_result, metadata) -> List[Dict]` 方法
- 接收 `ParseResult`，合并 TextBlock 时计算位置范围
- 生成 `locationLabel` 写入每个 chunk 的 metadata
- 保留原 `chunk(text, metadata) -> List[Dict]` 向后兼容

位置范围计算逻辑：
- 连续多个 page 类型 TextBlock 合并 → "第3-5页"
- 单个 page → "第3页"
- 连续 line 类型 → "第15-22行"
- section 类型 → "第三章 假期规定"

### Step 3: 修改 knowledge_tool.py

**文件**: `app/ai/tools/knowledge_tool.py`

**updateKnowledge**:
- 调用 `DocumentParser.parse_structured()` 替代 `parse()`
- 调用 `TextChunker.chunk_structured()` 替代 `chunk()`

**queryKnowledge**:
- 从 `result.metadata` 读取 `locationLabel`
- 输出格式: `[参考{i} - 来源: {filename} {locationLabel}]`

### Step 4: 新增文档内容接口

**文件**: `app/routers/knowledge.py`

新增端点:
```
GET /v1/knowledge/file/{doc_id}/content
```

实现:
- 根据 doc_id 查询 KnowledgeDocument
- 验证用户权限（userId 匹配）
- 调用 `DocumentParser.parse_structured()` 重新解析
- TXT/MD: 读取文件内容，每行添加行号前缀
- PDF: 返回带页码标记的文本
- Word: 返回带段落/标题标记的文本

### Step 5: 前端来源标注可点击 + 弹窗

**文件**: `.claude/aiworkhelper-web/src/views/knowledge/Index.vue`

- 修改 `renderMessage()` 方法，正则匹配 `[参考X - 来源: xxx]` 模式
- 渲染为可点击的链接元素，绑定 doc_id
- 新增 `DocumentPreviewDialog` 组件:
  - 调用 `GET /v1/knowledge/file/{doc_id}/content` 获取文本
  - 等宽字体显示，行号高亮
  - 自动滚动到引用位置（根据 locationLabel）

**文件**: `.claude/aiworkhelper-web/src/api/knowledge.ts`

- 新增 `getKnowledgeFileContent(docId: string)` API 方法

## 3. 变更文件清单

| 文件 | 变更类型 | 关键改动 |
|------|---------|---------|
| `app/ai/document/parser.py` | 重构 | +TextBlock, +ParseResult, +parse_structured() |
| `app/ai/document/chunker.py` | 修改 | +chunk_structured(), 位置范围计算 |
| `app/ai/tools/knowledge_tool.py` | 修改 | 适配新 API, 增强输出格式 |
| `app/routers/knowledge.py` | 新增端点 | GET /file/{doc_id}/content |
| `.claude/aiworkhelper-web/src/api/knowledge.ts` | 新增方法 | getKnowledgeFileContent() |
| `.claude/aiworkhelper-web/src/views/knowledge/Index.vue` | 修改 | 来源可点击 + 弹窗预览 |
