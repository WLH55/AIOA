# 实施计划 - 未读消息红点功能

## 实施步骤

### 阶段 1：数据模型层

#### 1.1 创建 UnreadMessage 模型

**文件**：`app/models/unread_message.py`

```python
from typing import Optional
from pydantic import BaseModel, Field
from app.models.base import BaseDocument

class UnreadMessage(BaseDocument):
    """
    未读消息计数模型
    """
    userId: str = Field(..., description="用户ID")
    conversationId: str = Field(..., description="会话ID")
    conversationType: int = Field(..., description="会话类型：1=群组，2=私聊")
    unreadCount: int = Field(default=0, description="未读消息数量")
    lastReadTime: Optional[int] = Field(None, description="最后阅读时间")
```

**验收**：
- [ ] 模型定义完成
- [ ] 字段类型正确
- [ ] 通过类型检查

#### 1.2 创建 UnreadMessage Repository

**文件**：`app/repository/unread_message_repository.py`

**方法**：
- `find_by_user_id(userId)` - 获取用户所有未读计数
- `find_by_conversation(userId, conversationId)` - 获取指定会话未读计数
- `increment(userId, conversationId, delta)` - 增加未读计数
- `clear(userId, conversationId)` - 清除未读计数
- `create_or_update(...)` - 创建或更新未读记录

**验收**：
- [ ] 所有方法实现完成
- [ ] 索引配置正确
- [ ] 通过单元测试

---

### 阶段 2：服务层

#### 2.1 创建 UnreadService

**文件**：`app/services/unread_service.py`

**方法**：
- `get_list(userId, conversationType)` - 获取未读列表
- `clear(userId, conversationId)` - 清除未读
- `increment(userId, conversationId, delta)` - 增加未读
- `increment_for_conversation(conversationId, sendId, chatType)` - 为会话中的所有接收者增加未读

**核心逻辑**：
```python
@staticmethod
async def increment_for_conversation(
    conversationId: str,
    sendId: str,
    chatType: int
) -> List[dict]:
    """
    为会话中的所有接收者增加未读计数

    Args:
        conversationId: 会话ID
        sendId: 发送者ID（不增加未读）
        chatType: 聊天类型（1=群组，2=私聊）
    """
    if chatType == CHAT_TYPE_PRIVATE:
        # 私聊：找到接收者
        # 解析私聊会话ID获取接收者ID
        recvId = extract_recv_id_from_private_conversation(conversationId, sendId)
        await UnreadService.increment(recvId, conversationId, 1)
    elif chatType == CHAT_TYPE_GROUP:
        # 群聊：获取所有成员，排除发送者
        group = await GroupRepository.find_by_id(conversationId)
        for memberId in group.memberIds:
            if memberId != sendId:
                await UnreadService.increment(memberId, conversationId, 1)
```

**验收**：
- [ ] 所有方法实现完成
- [ ] 私聊逻辑正确
- [ ] 群聊逻辑正确
- [ ] 发送者不增加未读

---

### 阶段 3：路由层

#### 3.1 创建未读消息路由

**文件**：`app/routers/unread.py`

**端点**：
- `POST /v1/chat/unread/list` - 获取未读列表
- `POST /v1/chat/unread/clear` - 清除未读

**注册路由**：
```python
# app/main.py
from app.routers import unread as unread_router

app.include_router(unread_router.router, prefix=settings.API_PREFIX)
```

**验收**：
- [ ] 路由注册成功
- [ ] 认证中间件生效
- [ ] 接口可访问

---

### 阶段 4：消息处理集成

#### 4.1 修改 ChatService

**文件**：`app/services/chat_service.py`

**修改点**：
- `_handle_private_message()` 发送消息后，调用 `UnreadService.increment()`
- `_handle_group_message()` 发送消息后，调用 `UnreadService.increment_for_conversation()`

```python
# 私聊消息处理中
await ChatLogRepository.create(chat_log)
# 增加接收者未读计数
await UnreadService.increment(recvId, conversationId, 1)

# 群聊消息处理中
await ChatLogRepository.create(chat_log)
# 增加所有成员（除发送者）未读计数
await UnreadService.increment_for_conversation(conversationId, sendId, CHAT_TYPE_GROUP)
```

**验收**：
- [ ] 私聊消息未读计数正确
- [ ] 群聊消息未读计数正确
- [ ] 发送者不增加未读

---

### 阶段 5：前端实现

#### 5.1 添加 API 函数

**文件**：`src/api/chat.ts`

```typescript
// 获取未读消息列表
export function getUnreadList(params?: {
  conversationType?: 1 | 2
}): Promise<ApiResponse<UnreadListResponse>> {
  return request({
    url: '/v1/chat/unread/list',
    method: 'post',
    data: params || {}
  })
}

// 清除会话未读
export function clearUnread(data: { conversationId: string }): Promise<ApiResponse<void>> {
  return request({
    url: '/v1/chat/unread/clear',
    method: 'post',
    data
  })
}
```

**验收**：
- [ ] API 函数实现完成
- [ ] 类型定义正确

#### 5.2 添加状态管理

**文件**：`src/views/chat/Index.vue`

```typescript
// 未读计数状态
const unreadCounts = reactive<Record<string, number>>({})

// 获取未读数量
const getUnreadCount = (conversationId: string): number => {
  return unreadCounts[conversationId] || 0
}

// 加载未读列表
const loadUnreadList = async () => {
  const res = await getUnreadList()
  if (res.code === 200 && res.data) {
    res.data.list.forEach(item => {
      unreadCounts[item.conversationId] = item.unreadCount
    })
  }
}

// 清除未读
const clearConversationUnread = async (conversationId: string) => {
  if (unreadCounts[conversationId] > 0) {
    await clearUnread({ conversationId })
    unreadCounts[conversationId] = 0
  }
}

// WebSocket 消息处理 - 未读更新
const handleUnreadUpdate = (data: any) => {
  if (data.type === 'unread_update') {
    unreadCounts[data.conversationId] = data.unreadCount
  }
}
```

**验收**：
- [ ] 状态管理正确
- [ ] 未读计数实时更新

#### 5.3 修改聊天页面 UI

**文件**：`src/views/chat/Index.vue`

**修改点**：
1. 在 `conversation-item` 中添加徽章
2. 切换会话时清除未读
3. 页面加载时获取未读列表

```vue
<div class="conversation-item">
  <el-avatar :size="40">{{ conv.name[0] }}</el-avatar>
  <div class="conversation-info">
    <div class="conversation-name">{{ conv.name }}</div>
    <div class="conversation-last">{{ conv.lastMessage }}</div>
  </div>
  <!-- 未读徽章 -->
  <el-badge
    v-if="getUnreadCount(conv.id) > 0"
    :value="getUnreadCount(conv.id)"
    :max="99"
    class="unread-badge"
  />
</div>
```

**样式**：
```css
.unread-badge {
  margin-left: auto;
}

.unread-badge :deep(.el-badge__content) {
  background-color: #F56C6C;
  border: 2px solid white;
  min-width: 16px;
  height: 16px;
  line-height: 12px;
  font-size: 12px;
  font-weight: bold;
}
```

**验收**：
- [ ] 徽章显示正确
- [ ] 切换会话后徽章消失
- [ ] 收到消息后徽章更新

#### 5.4 WebSocket 集成

**修改**：`src/utils/websocket.ts` 或 `src/views/chat/Index.vue`

```typescript
// 消息处理器增加未读更新类型
const handleUnreadMessage = (data: any) => {
  if (data.type === 'unread_update') {
    unreadCounts[data.conversationId] = data.unreadCount
  }
}
```

**验收**：
- [ ] 实时更新生效
- [ ] 无需刷新页面

---

### 阶段 6：样式调整

#### 6.1 徽章样式

**文件**：`src/views/chat/Index.vue` style 部分

**调整点**：
- 徽章位置
- 徽章颜色
- 徽章大小
- 圆角

**验收**：
- [ ] 样式符合设计稿
- [ ] 响应式适配

---

## 任务依赖关系

```
阶段 1 (数据模型)
    ↓
阶段 2 (服务层)
    ↓
阶段 3 (路由层)
    ↓
阶段 4 (消息集成)
    ↓
阶段 5 (前端实现)
    ↓
阶段 6 (样式调整)
```

---

## 交付物检查清单

- [ ] 数据模型代码
- [ ] Repository 代码
- [ ] Service 代码
- [ ] Router 代码
- [ ] 前端 API 代码
- [ ] 前端组件代码
- [ ] 样式代码
- [ ] 单元测试
- [ ] 接口文档
- [ ] 部署说明