import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from voice_dialogue.utils.logger import logger


class LoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件"""

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # 记录请求信息
        logger.info(
            f"请求开始: {request.method} {request.url.path} "
            f"客户端: {request.client.host if request.client else 'unknown'}"
        )

        # 处理请求
        response = await call_next(request)

        # 计算处理时间
        process_time = time.time() - start_time

        # 记录响应信息
        logger.info(
            f"请求完成: {request.method} {request.url.path} "
            f"状态码: {response.status_code} "
            f"处理时间: {process_time:.3f}s"
        )

        # 添加处理时间到响应头
        response.headers["X-Process-Time"] = str(process_time)

        return response
