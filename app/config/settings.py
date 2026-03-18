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
    API_PREFIX: str = "/api/v1"
    DEBUG: bool = False

    # ========== 服务器与 HTTP 配置 ==========
    HOST: str = "0.0.0.0"
    PORT: int = 8000
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

    # ========== 数据库配置（可选） ==========
    DATABASE_URL: str = ""

    # ========== 其他配置 ==========


# 全局配置实例
settings = Settings()
