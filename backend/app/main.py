from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import logging

from app.routers import health, search, documents, users
from app.middleware.logging import LoggingMiddleware
from app.middleware.error_handler import (
    global_exception_handler,
    validation_exception_handler
)
from app.core.config import settings
from app.utils.logger import configure_logging, get_logger

logger = logging.getLogger(__name__)
struct_logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 시작/종료 시 실행"""
    # Startup
    # Task 2.9: 구조화된 로깅 초기화
    configure_logging(log_level=settings.LOG_LEVEL if hasattr(settings, 'LOG_LEVEL') else "INFO")
    logger.info("FastAPI 서버 시작")
    struct_logger.info("server_startup", version="1.0.0", environment=settings.ENVIRONMENT if hasattr(settings, 'ENVIRONMENT') else "development")
    yield
    # Shutdown
    logger.info("FastAPI 서버 종료")
    struct_logger.info("server_shutdown")


app = FastAPI(
    title="RAG Platform API",
    description="사내 정보 검색 플랫폼 REST API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,  # 환경 변수에서 로드
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 미들웨어 추가
app.add_middleware(LoggingMiddleware)

# 에러 핸들러 등록 (Task 2.8)
app.add_exception_handler(Exception, global_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

# 라우터 등록
app.include_router(health.router, tags=["Health"])
app.include_router(search.router, prefix="/api/v1/search", tags=["Search"])
app.include_router(documents.router, prefix="/api/v1/documents", tags=["Documents"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "RAG Platform API",
        "version": "1.0.0",
        "docs": "/docs"
    }
