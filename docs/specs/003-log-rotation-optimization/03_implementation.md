# 实施计划

## 修改文件

- `app/config/logger_config.py`

## 技术方案

自定义 `SizeTimeRotatingFileHandler` 类，继承 `TimedRotatingFileHandler`：

```
SizeTimeRotatingFileHandler
├── __init__(maxBytes=50MB)    # 新增大小限制参数
├── shouldRollover(record)     # 重写：时间 OR 大小触发轮转
├── doRollover()               # 重写：压缩旧日志
└── _cleanup_old_logs()        # 清理过期日志
```

## 核心逻辑

### shouldRollover(record)

```python
def shouldRollover(self, record):
    # 时间轮转 OR 大小轮转
    time_rollover = super().shouldRollover(record)
    size_rollover = os.path.getsize(self.baseFilename) >= self.maxBytes
    return time_rollover or size_rollover
```

### doRollover()

1. 关闭当前文件流
2. 生成带时间戳的 `.gz` 文件名
3. 压缩当前日志文件
4. 删除原文件
5. 创建新日志文件
6. 清理过期日志

## 配置参数

| 参数 | 值 | 说明 |
|-----|-----|------|
| maxBytes | 50MB | 单文件大小上限 |
| when | midnight | 每天午夜轮转 |
| backupCount | LOG_RETENTION_DAYS | 保留天数 |

## 已完成

- [x] 实现 `SizeTimeRotatingFileHandler` 类
- [x] 替换原有 `TimedRotatingFileHandler`
- [x] 语法检查通过