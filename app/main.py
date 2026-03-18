"""
FastAPI 应用入口
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings, setup_logging
from app.config.exceptions import register_exception_handlers

# 导入路由
from app.routers import example

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

    yield

    # 关闭时执行
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
    @app.middleware("http")
    async def cache_request_body(request: Request, call_next):
        if request.method in ("POST", "PUT", "PATCH"):
            try:
                body = await request.body()
                if body:
                    request.state.body = body.decode("utf-8")
            except Exception:
                pass
        return await call_next(request)

    # ========== 注册全局异常处理器 ==========
    register_exception_handlers(app)

    # ========== 注册路由 ==========
    app.include_router(example.router, prefix=settings.API_PREFIX)

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
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
