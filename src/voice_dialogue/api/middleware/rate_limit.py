import time
from collections import defaultdict

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimitMiddleware(BaseHTTPMiddleware):
    """API限流中间件"""

    def __init__(self, app, calls_per_minute: int = 60):
        super().__init__(app)
        self.calls_per_minute = calls_per_minute
        self.calls = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()

        # 清理过期的调用记录
        minute_ago = current_time - 60
        self.calls[client_ip] = [
            call_time for call_time in self.calls[client_ip]
            if call_time > minute_ago
        ]

        # 检查是否超过限制
        if len(self.calls[client_ip]) >= self.calls_per_minute:
            raise HTTPException(
                status_code=429,
                detail=f"请求频率过高，每分钟最多允许 {self.calls_per_minute} 次请求"
            )

        # 记录本次调用
        self.calls[client_ip].append(current_time)

        # 处理请求
        response = await call_next(request)
        return response
