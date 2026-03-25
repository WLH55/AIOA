"""
FastAPI 应用入口

单端口架构：HTTP 和 WebSocket 共享同一个端口（8888）
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
import redis.asyncio as redis

from app.config import settings, setup_logging
from app.config.exceptions import register_exception_handlers
from app.models.user import User
from app.models.todo import Todo
from app.models.approval import Approval
from app.models.department import Department
from app.models.department_user import DepartmentUser
from app.models.chat_log import ChatLog
from app.models.group import Group

# 导入路由
from app.routers import auth_router, ws_router
from app.routers import user as user_router
from app.routers import todo as todo_router
from app.routers import approval as approval_router
from app.routers import department as department_router
from app.routers import chat_log as chat_log_router
from app.routers import group as group_router
from app.services.ws_manager import ws_manager

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 配置日志
    setup_logging()

    # 启动时执行
    logger.info(f"应用启动: {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"运行环境: {settings.ENVIRONMENT}")
    logger.info(f"调试模式: {settings.DEBUG}")

    # 初始化 MongoDB
    try:
        motor_client = AsyncIOMotorClient(settings.MONGODB_URI)
        await init_beanie(
            database=motor_client[settings.MONGODB_DATABASE],
            document_models=[
                User,
                Todo,
                Approval,
                Department,
                DepartmentUser,
                ChatLog,
                Group,
            ],
        )
        logger.info(f"MongoDB 连接成功: {settings.MONGODB_DATABASE}")
    except Exception as e:
        logger.error(f"MongoDB 连接失败: {e}")
        raise

    # 初始化 Redis
    try:
        redis_client = redis.from_url(settings.REDIS_URI)
        await redis_client.ping()
        logger.info("Redis 连接成功")
        # 存储 redis 客户端到 app state
        app.state.redis = redis_client
    except Exception as e:
        logger.warning(f"Redis 连接失败: {e}，部分功能可能不可用")
        app.state.redis = None

    # 启动 WebSocket 心跳检测
    await ws_manager.start_heartbeat()
    logger.info("WebSocket 心跳检测已启动")

    yield

    # 关闭时执行
    # 停止心跳检测
    await ws_manager.stop_heartbeat()
    logger.info("WebSocket 心跳检测已停止")

    if app.state.redis:
        await app.state.redis.close()
    logger.info("应用关闭")


def create_app() -> FastAPI:
    """创建 FastAPI 应用"""

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        debug=settings.DEBUG,
        lifespan=lifespan,
    )

    # ========== 配置中间件 ==========

    # 配置 CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOW_ORIGINS,
        allow_credentials=settings.ALLOW_CREDENTIALS,
        allow_methods=settings.ALLOW_METHODS,
        allow_headers=settings.ALLOW_HEADERS,
    )

    # 缓存请求体中间件（用于异常日志记录）
    # @app.middleware("http")
    # async def cache_request_body(request: Request, call_next):
    #     if request.method in ("POST", "PUT", "PATCH"):
    #         try:
    #             body = await request.body()
    #             if body:
    #                 request.state.body = body.decode("utf-8")
    #         except Exception:
    #             pass
    #     return await call_next(request)

    # ========== 注册全局异常处理器 ==========
    register_exception_handlers(app)

    # ========== 注册路由 ==========
    app.include_router(auth_router, prefix=settings.API_PREFIX)
    app.include_router(ws_router, prefix=settings.API_PREFIX)
    # CRUD 业务路由
    app.include_router(user_router.router, prefix=settings.API_PREFIX)
    app.include_router(todo_router.router, prefix=settings.API_PREFIX)
    app.include_router(approval_router.router, prefix=settings.API_PREFIX)
    app.include_router(department_router.router, prefix=settings.API_PREFIX)
    app.include_router(chat_log_router.router, prefix=settings.API_PREFIX)
    app.include_router(group_router.router, prefix=settings.API_PREFIX)

    # ========== 健康检查 ==========
    @app.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
        }

    return app


# 创建应用实例
app = create_app()


if __name__ == "__main__":
    import uvicorn

    logger.info("==============================================")
    logger.info(f"正在启动服务...")
    logger.info(f"HTTP API: http://{settings.HOST}:{settings.PORT}")
    logger.info(f"WebSocket: ws://{settings.HOST}:{settings.PORT}{settings.API_PREFIX}/ws/chat")
    logger.info("==============================================")

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        log_level="info" if settings.DEBUG else "warning",
    )