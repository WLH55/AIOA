# 测试规格 - 未读消息红点功能

## 测试策略

### 测试范围

| 模块 | 测试类型 |
|------|----------|
| 数据模型 | 单元测试 |
| Repository | 单元测试 |
| Service | 单元测试 + 集成测试 |
| Router | API 集成测试 |
| 前端组件 | 单元测试 + E2E 测试 |

---

## 单元测试

### 1. UnreadMessage 模型测试

**文件**：`tests/test_models/test_unread_message.py`

```python
import pytest
from app.models.unread_message import UnreadMessage

def test_create_unread_message():
    """测试创建未读消息记录"""
    unread = UnreadMessage(
        userId="user123",
        conversationId="conv456",
        conversationType=2,
        unreadCount=3
    )
    assert unread.userId == "user123"
    assert unread.unreadCount == 3
```

**验收**：
- [ ] 模型创建测试通过
- [ ] 字段验证测试通过

---

### 2. UnreadMessageRepository 测试

**文件**：`tests/test_repositories/test_unread_message_repository.py`

```python
import pytest
from app.repository.unread_message_repository import UnreadMessageRepository

@pytest.mark.asyncio
async def test_increment_unread():
    """测试增加未读计数"""
    # 先创建记录
    await UnreadMessageRepository.create_unread("user1", "conv1", 2)
    # 增加
    await UnreadMessageRepository.increment("user1", "conv1", 1)
    # 验证
    result = await UnreadMessageRepository.find_by_conversation("user1", "conv1")
    assert result.unreadCount == 3

@pytest.mark.asyncio
async def test_clear_unread():
    """测试清除未读计数"""
    await UnreadMessageRepository.create_unread("user1", "conv1", 5)
    await UnreadMessageRepository.clear("user1", "conv1")
    result = await UnreadMessageRepository.find_by_conversation("user1", "conv1")
    assert result.unreadCount == 0
```

**验收**：
- [ ] 增加计数测试通过
- [ ] 清除计数测试通过
- [ ] 查询测试通过

---

### 3. UnreadService 测试

**文件**：`tests/test_services/test_unread_service.py`

```python
import pytest
from app.services.unread_service import UnreadService

@pytest.mark.asyncio
async def test_increment_for_private_chat():
    """测试私聊消息增加未读"""
    # 私聊会话ID格式：private_user1_user2
    await UnreadService.increment_for_conversation(
        "private_user1_user2",
        "user1",
        2
    )
    # 验证 user2 的未读计数增加
    user2_unread = await UnreadService.get_list("user2")
    assert len([u for u in user2_unread if u.conversationId == "private_user1_user2"]) > 0

@pytest.mark.asyncio
async def test_sender_not_incremented():
    """测试发送者不增加未读"""
    # 发送前查询
    before = await UnreadService.find_by_conversation("user1", "conv1")
    before_count = before.unreadCount if before else 0

    # 发送消息
    await UnreadService.increment_for_conversation("conv1", "user1", 2)

    # 验证发送者未读计数不变
    after = await UnreadService.find_by_conversation("user1", "conv1")
    after_count = after.unreadCount if after else 0
    assert after_count == before_count
```

**验收**：
- [ ] 私聊未读测试通过
- [ ] 群聊未读测试通过
- [ ] 发送者不计数测试通过

---

## 集成测试

### 1. API 集成测试

**文件**：`tests/test_api/test_unread_api.py`

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_get_unread_list(client: AsyncClient, auth_headers):
    """测试获取未读列表"""
    response = await client.post(
        "/v1/chat/unread/list",
        headers=auth_headers,
        json={}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert "list" in data["data"]

@pytest.mark.asyncio
async def test_clear_unread(client: AsyncClient, auth_headers):
    """测试清除未读"""
    # 先增加未读
    await client.post(
        "/v1/chat/unread/clear",  # 实际应该是增加接口
        headers=auth_headers,
        json={}
    )

    # 清除
    response = await client.post(
        "/v1/chat/unread/clear",
        headers=auth_headers,
        json={"conversationId": "conv1"}
    )
    assert response.status_code == 200
```

**验收**：
- [ ] 获取列表测试通过
- [ ] 清除未读测试通过
- [ ] 认证测试通过

### 2. 消息处理集成测试

**文件**：`tests/test_integration/test_chat_message_flow.py`

```python
import pytest
from app.services.chat_service import ChatService

@pytest.mark.asyncio
async def test_private_message_increments_unread():
    """测试私聊消息增加接收者未读"""
    from app.models.user import User
    from app.dto.ws.message import ChatMessage

    sender = await User.find_one(User.name == "user1")
    message = ChatMessage(
        type="chat",
        conversationId="private_user1_user2",
        recvId="user2",
        sendId="user1",
        chatType=2,
        content="test",
        contentType=1
    )

    await ChatService.handle_message(message, sender)

    # 验证 user2 未读计数
    from app.services.unread_service import UnreadService
    user2_unread = await UnreadService.find_by_conversation("user2", "private_user1_user2")
    assert user2_unread.unreadCount > 0
```

**验收**：
- [ ] 私聊消息流程测试通过
- [ ] 群聊消息流程测试通过

---

## E2E 测试

### 1. 前端 E2E 测试

**文件**：`tests/e2e/test_unread_badge.spec.ts`

```typescript
import { test, expect } from '@playwright/test'

test('显示未读消息红点', async ({ page }) => {
  // 登录
  await page.goto('/login')
  await page.fill('input[name="name"]', 'testuser')
  await page.fill('input[name="password"]', 'password')
  await page.click('button[type="submit"]')

  // 进入聊天页面
  await page.goto('/chat')

  // 模拟收到消息（通过 WebSocket）
  await page.evaluate(() => {
    window.simulateMessage({
      type: 'unread_update',
      conversationId: 'private_abc123',
      unreadCount: 3
    })
  })

  // 验证徽章显示
  const badge = page.locator('.unread-badge').first()
  await expect(badge).toBeVisible()
  await expect(badge).toContainText('3')
})

test('切换会话清除未读', async ({ page }) => {
  // 登录并进入聊天
  await page.goto('/chat')

  // 点击有未读消息的会话
  await page.click('.conversation-item[data-id="private_abc123"]')

  // 验证徽章消失
  const badge = page.locator('.unread-badge[data-id="private_abc123"]')
  await expect(badge).not.toBeVisible()
})

test('99+ 显示', async ({ page }) => {
  // 模拟 100 条未读消息
  await page.evaluate(() => {
    window.simulateMessage({
      type: 'unread_update',
      conversationId: 'private_abc123',
      unreadCount: 100
    })
  })

  // 验证显示 99+
  const badge = page.locator('.unread-badge').first()
  await expect(badge).toContainText('99+')
})
```

**验收**：
- [ ] 显示红点测试通过
- [ ] 清除未读测试通过
- [ ] 99+ 显示测试通过

---

## 性能测试

### 1. 未读计数查询性能

**测试目标**：查询 100 个会话的未读计数 < 50ms

```python
import time
import pytest
from app.services.unread_service import UnreadService

@pytest.mark.asyncio
async def test_query_performance():
    """测试未读计数查询性能"""
    # 准备 100 条未读记录
    for i in range(100):
        await UnreadService.increment(f"user{i}", f"conv{i}", i)

    # 测试查询
    start = time.time()
    result = await UnreadService.get_list("user1")
    elapsed = time.time() - start

    assert elapsed < 0.05  # 50ms
```

### 2. 并发写入性能

**测试目标**：100 个并发写入操作，无死锁，无数据错误

```python
import asyncio
import pytest

@pytest.mark.asyncio
async def test_concurrent_writes():
    """测试并发写入"""
    tasks = []
    for i in range(100):
        task = UnreadService.increment("user1", "conv1", 1)
        tasks.append(task)

    await asyncio.gather(*tasks)

    # 验证最终数量
    result = await UnreadService.find_by_conversation("user1", "conv1")
    assert result.unreadCount == 100
```

---

## 边界条件测试

| 测试场景 | 预期结果 |
|----------|----------|
| 未读数量为 0 | 不显示徽章 |
| 未读数量为负数 | 强制设为 0 |
| 未读数量超过 99 | 显示 "99+" |
| 会话不存在 | 清除操作返回 404 |
| 用户不存在 | 返回 401 |
| 重复清除 | 后续清除操作无效果 |
| 同时收到多条消息 | 未读数量正确累加 |

---

## 回归测试

每次部署前必须执行：

- [ ] 单元测试全绿
- [ ] 集成测试全绿
- [ ] E2E 测试全绿
- [ ] 性能测试通过
- [ ] 手动测试验证

---

## 测试数据准备

**测试用户**：
- user1, user2, user3

**测试会话**：
- private_user1_user2
- group_test (members: user1, user2, user3)

**测试消息**：
- 私聊消息 10 条
- 群聊消息 10 条