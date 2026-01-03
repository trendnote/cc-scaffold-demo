import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """요청/응답 로깅 미들웨어"""

    async def dispatch(self, request: Request, call_next):
        """
        요청 시작/종료 로깅 및 응답 시간 측정
        """
        start_time = time.time()

        # 요청 정보 로깅
        logger.info(
            f"Request: {request.method} {request.url.path}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "client": request.client.host if request.client else None
            }
        )

        # 요청 처리
        response = await call_next(request)

        # 응답 시간 계산
        process_time = (time.time() - start_time) * 1000  # ms

        # 응답 정보 로깅
        logger.info(
            f"Response: {response.status_code} - {process_time:.2f}ms",
            extra={
                "status_code": response.status_code,
                "process_time_ms": round(process_time, 2)
            }
        )

        # 응답 헤더에 처리 시간 추가
        response.headers["X-Process-Time"] = f"{process_time:.2f}ms"

        return response
