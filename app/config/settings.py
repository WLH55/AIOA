"""
配置管理模块（Pydantic V2）
"""
import os
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


# 提取基础路径（常量）
_BASE_PATH = Path(__file__).resolve().parent.parent.parent


def get_env_file() -> str:
    """根据环境变量 ENVIRONMENT 获取 .env 文件路径"""
    env = os.getenv("ENVIRONMENT", "development")
    env_files = {
        "development": ".env.development",
        "production": ".env.production",
        "test": ".env.test",
    }
    target_file = env_files.get(env, ".env.development")
    return str(_BASE_PATH / target_file)


class Settings(BaseSettings):
    """应用配置类（使用 Pydantic V2 model_config）"""

    model_config = SettingsConfigDict(
        env_file=get_env_file(),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    # ========== 环境配置 ==========
    ENVIRONMENT: str = "development"

    # ========== 应用基础配置 ==========
    APP_NAME: str = "FastAPI Application"
    APP_VERSION: str = "1.0.0"
    API_PREFIX: str = "/v1"
    DEBUG: bool = False

    # ========== 服务器与 HTTP 配置 ==========
    HOST: str = "0.0.0.0"
    PORT: int = 8888
    HTTP_TIMEOUT: int = 30

    # ========== CORS 配置 ==========
    ALLOW_ORIGINS: List[str] = ["*"]
    ALLOW_CREDENTIALS: bool = True
    ALLOW_METHODS: List[str] = ["*"]
    ALLOW_HEADERS: List[str] = ["*"]

    # ========== 日志配置 ==========
    LOG_LEVEL: str = "INFO"
    STORAGE_DIR: Path = _BASE_PATH / "storage"
    LOGS_DIR: Path = _BASE_PATH / "storage" / "logs"
    LOG_RETENTION_DAYS: int = 30

    # ========== 数据库配置 ==========
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DATABASE: str = "aiworkhelper"
    REDIS_URI: str = "redis://localhost:6379/0"

    # ========== JWT 配置 ==========
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    ACCESS_TOKEN_EXPIRE_DAYS: int = 7
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # ========== AI Agent 配置 ==========
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    DEEPSEEK_MODEL: str = "deepseek-chat"
    # 上下文管理配置（基于模型窗口动态计算阈值）
    AI_MODEL_CONTEXT_WINDOW: int = 128000  # 模型上下文窗口（tokens），DeepSeek 128K
    AI_MEMORY_RESERVED_TOKENS: int = 20000  # 摘要预留空间（tokens）
    AI_MEMORY_BUFFER_TOKENS: int = 13000   # 压缩缓冲区（tokens）
    AI_MEMORY_MAX_FAILURES: int = 3         # 熔断器阈值：连续失败次数
    AI_MEMORY_KEEP_RECENT_COUNT: int = 10   # 降级策略：保留最近消息数
    # 旧配置项保留（兼容），将被动态计算替代
    AI_MEMORY_MAX_TOKEN_LIMIT: int = 2000   # 已弃用，由动态阈值替代
    AI_MEMORY_REDIS_TTL: int = 86400
    AI_CONVERSATION_MAX_COUNT: int = 50
    AI_TIMEOUT: int = 120
    AI_SUMMARY_MODEL: str = "deepseek-chat"
    AI_MAX_TOOL_ROUNDS: int = 10
    AI_MAX_MESSAGE_LENGTH: int = 4000

    # ========== 其他配置 ==========


# 全局配置实例
settings = Settings()
