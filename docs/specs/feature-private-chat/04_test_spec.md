# 私聊消息转发功能 - 测试规范

## 1. 单元测试

### 1.1 ChatService.generate_conversation_id()

| 测试用例 | 输入 | 预期输出 |
|---------|------|---------|
| 正常情况（id1 < id2） | "user1", "user2" | "private_user1_user2" |
| 正常情况（id1 > id2） | "user2", "user1" | "private_user1_user2" |
| 相同ID | "user1", "user1" | 错误 |

### 1.2 ChatService.handle_message()

| 测试用例 | 输入 | 预期结果 |
|---------|------|---------|
| 私聊-接收者在线 | chatType=2, recv在线 | status="sent", 消息保存 |
| 私聊-接收者离线 | chatType=2, recv离线 | status="offline", 消息保存 |
| 私聊-给自己发消息 | chatType=2, send=recv | 返回错误 |
| 私聊-消息为空 | chatType=2, content="" | 返回错误 |
| 群聊-正常 | chatType=1, group存在 | 广播给成员 |
| 群聊-群不存在 | chatType=1, group不存在 | 返回错误 |

## 2. 集成测试

### 2.1 私聊消息端到端测试

**场景1：双方在线**
```
1. UserA 连接 WebSocket
2. UserB 连接 WebSocket
3. UserA 发送消息 "你好" 给 UserB
4. 验证：UserB 收到消息
5. 验证：UserA 收到确认（status=sent）
6. 验证：数据库中有记录
```

**场景2：接收者离线**
```
1. UserA 连接 WebSocket
2. UserB 未连接
3. UserA 发送消息给 UserB
4. 验证：UserA 收到确认（status=offline）
5. 验证：数据库中有记录
6. UserB 上线后，能查询到历史消息
```

### 2.2 群聊消息端到端测试

**场景：群成员在线**
```
1. UserA, UserB, UserC 连接 WebSocket
2. UserA 发送群聊消息
3. 验证：UserB 和 UserC 都收到消息
4. 验证：UserA 收到确认
5. 验证：数据库中有记录
```

## 3. 边界测试

| 场景 | 预期行为 |
|-----|---------|
| 发送空消息 | 返回错误，不保存 |
| 发送超长消息 | 正常处理 |
| 特殊字符消息 | 正常处理 |
| 不存在的接收者 | 返回错误 |
| 不存在的群聊 | 返回错误 |
| 无效的 chatType | 返回错误 |

## 4. 性能测试

| 指标 | 目标 |
|-----|------|
| 消息转发延迟 | < 100ms |
| 并发消息处理 | 支持 100 msg/s |

## 5. 回归测试清单

- [ ] AI 对话功能不受影响
- [ ] 群聊创建功能不受影响
- [ ] WebSocket 连接/断开不受影响
- [ ] 历史消息查询不受影响
