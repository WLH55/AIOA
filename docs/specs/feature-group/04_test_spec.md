# 群组功能测试规范

## 1. 单元测试

### 1.1 GroupRepository 测试

| 测试用例 | 描述 | 预期结果 |
|----------|------|----------|
| test_create_group | 创建群组 | 成功创建，返回 Group 对象 |
| test_find_by_id | 根据ID查询 | 返回正确的群组 |
| test_find_by_id_not_found | 查询不存在的群组 | 返回 None |
| test_find_by_member_id | 根据成员ID查询 | 返回该成员参与的所有群组 |
| test_update_group | 更新群组信息 | 成功更新 |
| test_delete_group | 删除群组 | 成功删除 |

### 1.2 GroupService 测试

| 测试用例 | 描述 | 预期结果 |
|----------|------|----------|
| test_create_group_success | 创建群组成功 | 返回群组ID |
| test_create_group_empty_members | 成员列表为空 | 抛出异常 |
| test_create_group_exceed_limit | 成员超过100人 | 抛出异常 |
| test_invite_member_success | 邀请成员成功 | 成员数量增加 |
| test_invite_member_not_owner | 非群主邀请 | 抛出无权限异常 |
| test_invite_member_already_exists | 邀请已存在成员 | 抛出异常 |
| test_remove_member_success | 移除成员成功 | 成员从列表中移除 |
| test_remove_member_not_owner | 非群主移除 | 抛出无权限异常 |
| test_remove_self | 移除自己 | 抛出异常 |
| test_exit_group_success | 退出群组成功 | 成员从列表中移除 |
| test_exit_group_owner | 群主退出 | 抛出异常 |
| test_dismiss_group_success | 解散群组成功 | 状态更新为已解散 |
| test_dismiss_group_not_owner | 非群主解散 | 抛出无权限异常 |

---

## 2. 集成测试

### 2.1 API 测试

#### 创建群组

```python
async def test_create_group_api(client, auth_token):
    response = await client.post(
        "/v1/group/create",
        json={
            "name": "测试群组",
            "memberIds": ["user1", "user2"]
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 201
    assert "data" in response.json()
```

#### 获取群组列表

```python
async def test_get_group_list_api(client, auth_token):
    response = await client.get(
        "/v1/group/list?page=1&count=20",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "count" in data["data"]
    assert "data" in data["data"]
```

#### 邀请成员

```python
async def test_invite_member_api(client, auth_token, group_id):
    response = await client.post(
        f"/v1/group/{group_id}/invite",
        json={"memberIds": ["user3"]},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
```

---

## 3. 边界条件测试

| 场景 | 测试数据 | 预期结果 |
|------|----------|----------|
| 群名称为空 | name="" | 400 错误 |
| 群名称超长 | name="a"*51 | 400 错误 |
| 群名称最大长度 | name="a"*50 | 成功 |
| 成员数量为0 | memberIds=[] | 400 错误 |
| 成员数量101 | memberIds=[...] (101个) | 400 错误 |
| 成员数量100 | memberIds=[...] (100个) | 成功 |
| page=0 | page=0 | 400 错误 |
| count=101 | count=101 | 400 错误 |

---

## 4. 并发测试

| 场景 | 描述 |
|------|------|
| 同时邀请成员 | 多个请求同时邀请不同成员 |
| 同时移除成员 | 多个请求同时移除成员 |

---

## 5. 性能测试

| 指标 | 目标 |
|------|------|
| 创建群组响应时间 | < 300ms |
| 获取群组列表响应时间 | < 500ms |
| 获取群组详情响应时间 | < 300ms |
| 邀请成员响应时间 | < 300ms |

---

## 6. 回归测试清单

完成开发后，验证以下功能未受影响：

- [ ] 用户注册/登录功能正常
- [ ] WebSocket 连接正常
- [ ] 私聊消息功能正常
- [ ] 其他 CRUD 接口正常
