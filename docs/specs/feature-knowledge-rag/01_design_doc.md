# Feature: RAG 知识库系统

## 1. Background (背景)

AIWorkHelper 已实现 AI Agent 对话系统（ReAct 循环 + Function Calling + SSE 流式推送），具备待办、审批、用户、部门等 7 个 ToolProvider 共 12 个工具。但企业内部文档（规章制度、操作手册等）检索效率低、信息分散，用户无法通过 AI 直接查询文档内容。

现有基础：
- AI Agent ReAct 循环已完备，支持插件化工具注册（ToolProvider + TOOL_REGISTRY）
- SSE 流式对话已实现（独立对话页面 + 群聊 @AI 桥接）
- 记忆管理（摘要缓冲 + 熔断降级）已完备
- Redis 已接入（会话缓存），但未启用向量检索
- Decision #005 已决策使用 Redis + RediSearch 作为向量存储
- 前端知识库页面已有占位 UI（左上传 + 右对话布局）

## 2. Goals (目标)

- 实现 RAG (Retrieval-Augmented Generation) 架构，知识库作为 Agent 的原子工具，而非独立系统
- 支持企业文档上传（PDF/Word/TXT/Markdown）、解析、分块、向量化、存储
- 基于 Redis RediSearch 实现语义检索（KNN 向量搜索）
- 使用 SiliconFlow BAAI/bge-m3 模型生成文本嵌入向量
- 复用现有 AI 对话 SSE 端点，知识库工具自动注入到所有 AI 会话
- 前端知识库页面复用已有 UI，对话区改为 SSE 流式

## 3. Architecture (整体架构)

```
用户问题
  ↓
现有 AI Chat SSE 端点 (/v1/ai/chat/stream)
  ↓
Agent ReAct 循环（已有）
  ↓
┌─────────────────────────────────────┐
│ queryKnowledge 工具                  │
│  1. SiliconFlow Embedding → 问题向量  │
│  2. Redis FT.SEARCH → KNN 检索      │
│  3. 返回 Top-K 相关文档片段          │
│  4. Agent 基于上下文生成回答          │
└─────────────────────────────────────┘
  ↓
SSE 流式推送回答（已有机制）
```

### 查询流程

```
用户问题 → 加载记忆摘要 → Agent → queryKnowledge → 生成问题向量
→ KNN 检索 → 拼装上下文 → LLM 生成回答 → 存入记忆
```

### 更新流程

```
用户指令 → Agent → updateKnowledge → 查询待处理文档
→ 解析文档 → 文本分块 → 批量 Embedding → 存入 Redis → 返回成功
```

## 4. Key Concepts (核心概念)

### 4.1 向量索引 (Vector Index)

文本经过 Embedding 模型处理后，会变成一个固定长度的浮点数数组（向量）。

```
"请假流程是什么" → [0.023, -0.145, 0.678, ..., 0.034]  (1024个float)
"年假怎么申请"     → [0.021, -0.139, 0.671, ..., 0.031]  (语义接近)
"今天中午吃什么"   → [0.812, 0.334, -0.221, ..., 0.778]  (语义远离)
```

向量索引是专门存储和检索这些高维数组的索引结构。普通数据库索引（B-Tree）无法做"相似度"搜索，向量索引解决的就是这个问题。

### 4.2 KNN (K-Nearest Neighbors)

KNN = K 个最近邻居，即"找最相似的 K 个结果"。

```
用户问: "婚假有几天?"
        ↓ embedding → 查询向量
        ↓ KNN 搜索 (K=5)，计算余弦距离

结果排序:
  1. [距离 0.05] "第三章 假期规定：婚假为3天..."     ← 最相关
  2. [距离 0.08] "第四章 婚假需提前一周申请..."
  3. [距离 0.12] "第五条 丧假为1-3天..."
  4. [距离 0.31] "第六条 年假按工龄计算..."           ← 超过阈值，丢弃
  5. [距离 0.42] "第七条 事假扣除当天工资..."          ← 超过阈值，丢弃
```

超过阈值（配置值 0.3）的结果会被过滤，只返回真正相关的内容给 LLM 生成回答。

### 4.3 向量在 Redis 中的存储

Redis 使用 Hash 结构存储每个文档块，向量以 FLOAT32 字节流存储：

```
Key: knowledge:chunk:a1b2c3d4-xxxx-xxxx-xxxx-xxxxxxxxxxxx
Hash Fields:
  doc_id    = "671abc..."          ← 所属文档 ID
  content   = "第三章 假期规定..."   ← 原始文本
  embedding = \x00\x00\xb8?\x00... ← 1024个float32的二进制（4096字节）
  metadata  = {"filename":"员工手册.pdf","chunk_index":5}
```

每个 float32 占 4 字节，1024 维 = 4096 字节/块。100 页文档约切 200 个块，占 Redis 约 800KB。

### 4.4 RediSearch 模块

Redis 原生只支持 String/Hash/List/Set/Sorted Set，不支持向量检索。RediSearch 是 Redis 的扩展模块，为其增加全文搜索和向量检索能力。

安装方式：
- **Redis Stack**（推荐）：开箱即用，`docker run -d -p 6379:6379 redis/redis-stack-server:latest`
- **手动加载**：在 redis.conf 中添加 `loadmodule /path/to/redisearch.so`

### 4.5 索引算法

FT.CREATE 建索引时需要选择两项：

**索引算法（怎么找）：**

| 算法 | 原理 | 适用场景 |
|------|------|---------|
| FLAT（暴力搜索） | 与所有向量逐一计算距离 | 数据量 < 10万，精确结果 |
| HNSW（层次导航小世界图） | 预建图结构，查询沿图跳转 | 数据量 > 10万，近似但极快 |

**距离度量（怎么算相似）：**

| 度量 | 含义 | 适用场景 |
|------|------|---------|
| COSINE（余弦距离） | 比较向量方向，不看大小 | 文本语义相似度（最常用） |
| L2（欧氏距离） | 两点直线距离 | 数值型特征 |
| IP（内积） | 向量点乘 | 已归一化的向量 |

本项目选择 **FLAT + COSINE**，适合企业内部文档规模。

## 5. Technology Stack (技术选型)

| 组件 | 选型 | 理由 |
|------|------|------|
| 向量数据库 | Redis + RediSearch | 复用现有 Redis 基础设施 |
| Embedding 模型 | SiliconFlow BAAI/bge-m3 | 中文效果好，OpenAI 兼容接口，有免费额度 |
| 向量维度 | 1024 | bge-m3 模型输出维度 |
| 文档解析 | pdfplumber + python-docx | 轻量、无外部依赖 |
| 文本分块 | 段落+长度切分，overlap 策略 | 保留语义完整性 |
| 文档格式 | PDF / Word / TXT / Markdown | 覆盖主流办公文档 |

## 6. Data Model (数据模型)

### 6.1 MongoDB: KnowledgeDocument

文档元数据存储在 MongoDB，向量数据存储在 Redis。

```python
class KnowledgeDocument(Document):
    filename: str           # 原始文件名
    filepath: str           # 服务器存储路径
    fileSize: int           # 文件大小（字节）
    fileType: str           # 文件类型（pdf/docx/txt/md）
    chunkCount: int         # 分块数量
    status: int             # 0=处理中, 1=已完成, 2=失败
    userId: str             # 上传者 ID
    uploadTime: int         # 上传时间（毫秒时间戳）
    updateTime: int         # 更新时间（毫秒时间戳）
```

### 6.2 Redis: 向量索引

```
索引名: idx:knowledge_chunks
Key 前缀: knowledge:chunk:

FT.CREATE idx:knowledge_chunks ON HASH PREFIX 1 knowledge:chunk:
  SCHEMA
    doc_id    TAG
    content   TEXT
    embedding VECTOR FLAT 6 TYPE FLOAT32 DIM 1024 DISTANCE_METRIC COSINE
    metadata  TEXT
```

## 7. Implementation (实现清单)

### 7.1 新增文件

| 文件 | 说明 |
|------|------|
| `app/ai/embedding.py` | SiliconFlow Embedding 客户端，支持单条和批量向量化 |
| `app/ai/vectorstore/__init__.py` | 向量存储模块初始化 |
| `app/ai/vectorstore/redis_store.py` | Redis RediSearch 封装：索引创建、KNN 检索、CRUD |
| `app/ai/document/__init__.py` | 文档处理模块初始化 |
| `app/ai/document/parser.py` | 文档解析器（PDF/Word/TXT/Markdown） |
| `app/ai/document/chunker.py` | 文本分块器（段落+长度切分，overlap 策略） |
| `app/ai/tools/knowledge_tool.py` | Agent 工具：queryKnowledge + updateKnowledge |
| `app/models/knowledge.py` | KnowledgeDocument MongoDB 模型 |
| `app/repository/knowledge_repository.py` | 知识库数据访问层 |
| `app/config/redis.py` | 全局 Redis 客户端引用（供工具层访问） |
| `app/routers/knowledge.py` | 知识库 API：文件上传、文档列表、文档删除 |

### 7.2 修改文件

| 文件 | 变更 |
|------|------|
| `app/config/settings.py` | +SiliconFlow API 配置、向量索引配置、文档处理配置 |
| `.env.development` | +SILICONFLOW_API_KEY / BASE_URL / MODEL / DIMENSIONS |
| `app/ai/tools/__init__.py` | 注册 KnowledgeToolProvider |
| `app/ai/prompts/system_prompt.py` | 系统提示词新增知识库查询/更新能力描述 |
| `app/main.py` | +KnowledgeDocument 模型注册、knowledge 路由注册、全局 Redis 引用设置 |
| `.claude/aiworkhelper-web/src/views/knowledge/Index.vue` | 对话区改为 SSE 流式，复用 AI 对话端点 |
| `.claude/aiworkhelper-web/src/api/knowledge.ts` | API 改为文档管理接口（上传/列表/删除） |
| `requirements.txt` | +pdfplumber、python-docx、python-multipart |

### 7.3 Agent 工具注册

实现后 TOOL_REGISTRY 共 5 个 Provider、14 个工具：

| Provider | 工具 | 类别 |
|----------|------|------|
| TimeToolProvider | parseTime, getCurrentTime | utility |
| UserToolProvider | getUserByName | query |
| TodoToolProvider | createTodo, findTodos | business |
| ApprovalToolProvider | createLeaveApproval, createPunchApproval, createGoOutApproval, findApprovals | business |
| DepartmentToolProvider | getDepartmentTree, getDepartmentInfo | query |
| **KnowledgeToolProvider** | **queryKnowledge, updateKnowledge** | **knowledge** |

## 8. API Endpoints (接口)

### 8.1 文件上传

```
POST /v1/knowledge/upload
Content-Type: multipart/form-data

Request: file (PDF/Word/TXT/Markdown)
Response: { id, filename, fileSize, fileType, status, uploadTime }
```

### 8.2 文档列表

```
GET /v1/knowledge/list?page=1&pageSize=20

Response: { list: [{id, filename, fileSize, fileType, chunkCount, status, uploadTime}], total }
```

### 8.3 文档删除

```
POST /v1/knowledge/delete

Request: { id: "文档ID" }
Response: 删除文件 + MongoDB 记录 + Redis 向量数据
```

### 8.4 知识库对话

复用现有 SSE 端点：

```
POST /v1/ai/chat/stream

Request: { conversationId, content }
Response: SSE 事件流（ai_chunk / ai_tool_call / ai_tool_result / ai_complete / ai_error）
```

Agent 自动判断是否需要调用 queryKnowledge 或 updateKnowledge。

## 9. Configuration (配置项)

| 配置 | 默认值 | 说明 |
|------|--------|------|
| SILICONFLOW_API_KEY | (必填) | SiliconFlow API Key |
| SILICONFLOW_BASE_URL | https://api.siliconflow.cn/v1 | API 地址 |
| SILICONFLOW_EMBEDDING_MODEL | BAAI/bge-m3 | Embedding 模型 |
| SILICONFLOW_EMBEDDING_DIMENSIONS | 1024 | 向量维度 |
| KNOWLEDGE_INDEX_NAME | idx:knowledge_chunks | Redis 向量索引名 |
| KNOWLEDGE_KEY_PREFIX | knowledge:chunk: | Redis Key 前缀 |
| KNOWLEDGE_CHUNK_SIZE | 500 | 分块最大字符数 |
| KNOWLEDGE_CHUNK_OVERLAP | 100 | 分块重叠字符数 |
| KNOWLEDGE_TOP_K | 5 | KNN 检索返回数量 |
| KNOWLEDGE_SCORE_THRESHOLD | 0.3 | 余弦距离阈值 |
| KNOWLEDGE_UPLOAD_DIR | storage/knowledge | 文件上传目录 |

## 10. Prerequisites (前置条件)

1. Redis 需加载 RediSearch 模块（当前远程 Redis 未加载，需安装）
2. SiliconFlow API Key 已配置
3. 文件上传目录 `storage/knowledge` 自动创建
