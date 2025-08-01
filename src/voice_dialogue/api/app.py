from typing import Dict, Any

from fastapi import FastAPI, HTTPException, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from voice_dialogue.config.paths import FRONTEND_ASSETS_PATH
from voice_dialogue.utils.logger import logger
from .core.config import AppConfig
from .core.lifespan import lifespan
from .middleware.logging import LoggingMiddleware
from .middleware.rate_limit import RateLimitMiddleware
from .routes import tts_routes, asr_routes, system_routes, websocket_routes, settings_routes


def create_app() -> FastAPI:
    """创建并配置FastAPI应用"""

    # 应用配置
    config = AppConfig()

    # 创建FastAPI应用
    app = FastAPI(
        title=config.title,
        description=config.description,
        version=config.version,
        docs_url=config.docs_url,
        redoc_url=config.redoc_url,
        lifespan=lifespan,
    )

    # 添加CORS中间件
    app.add_middleware(CORSMiddleware, **config.get_cors_config())

    # 添加自定义中间件
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(RateLimitMiddleware)

    # 注册路由
    _register_routes(app)

    # 注册异常处理器
    _register_exception_handlers(app)

    # 添加静态文件路由
    app.mount("/app", StaticFiles(directory=FRONTEND_ASSETS_PATH.as_posix(), html=True), name="static")

    return app


def _register_routes(app: FastAPI):
    """注册所有路由"""
    # API路由
    v1_router = APIRouter(prefix="/api/v1")
    v1_router.include_router(tts_routes.router, prefix="/tts", tags=["TTS模型管理"])
    v1_router.include_router(asr_routes.router, prefix="/asr", tags=["ASR模型管理"])
    v1_router.include_router(system_routes.router, prefix="/system", tags=["系统管理"])
    v1_router.include_router(settings_routes.router, prefix="/settings", tags=["设置管理"])
    app.include_router(v1_router)

    app.add_websocket_route("/api/v1/ws", websocket_routes.ws)

    # 根路径和健康检查
    _register_health_routes(app)


def _register_health_routes(app: FastAPI):
    """注册健康检查路由"""

    @app.get("/")
    async def root():
        return RedirectResponse(url='/app/')


def _get_service_status(app_state: Dict[str, Any]) -> dict:
    """获取服务状态信息"""
    service_manager = app_state.get("service_manager")
    if service_manager:
        return service_manager.get_service_status()
    return {"total_services": 0, "services": {}}


def _register_exception_handlers(app: FastAPI):
    """注册全局异常处理器"""

    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        logger.error(f"未处理的异常: {exc}", exc_info=True)
        return HTTPException(
            status_code=500,
            detail="内部服务器错误"
        )


# 创建应用实例
app = create_app()
