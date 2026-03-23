# Test Spec: AIWorkHelper 数据模型

## Test Scope (测试范围)

- 单元测试：枚举类型转换、内嵌文档验证
- 集成测试：Beanie 模型初始化、MongoDB 连接

## Test Strategy (测试策略)

- 枚举测试：验证 from_value 方法正确转换
- 模型测试：验证字段类型、必填校验、默认值
- 索引测试：验证唯一索引约束

## Test Cases (用例列表)

| 编号 | 场景 | 期望结果 |
|------|------|----------|
| TC1 | TodoStatus.from_value(1) | 返回 PENDING |
| TC2 | TodoStatus.from_value(99) | 返回 PENDING (默认值) |
| TC3 | User 创建时无 name | 抛出 ValidationError |
| TC4 | User name 重复插入 | 抛出 DuplicateKeyError |
| TC5 | Todo 嵌入 executes 列表 | 正确序列化/反序列化 |
| TC6 | Approval 可选详情字段 | makeCard/leave/goOut 可为 None |

## Data Preparation (数据准备)

- 前置数据：无（模型定义测试）
- Mock 依赖：MongoDB 测试实例

## Regression Impact (回归影响)

- 现有 User 模型字段变更，需更新 auth_service.py 相关逻辑
- 现有测试 test_jwt.py、test_auth.py 可能需要调整