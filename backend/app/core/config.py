from pydantic_settings import BaseSettings
from typing import List, Optional


class Settings(BaseSettings):
    """환경 변수 기반 설정"""

    # 앱 설정
    APP_NAME: str = "RAG Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # API 설정
    API_V1_PREFIX: str = "/api/v1"

    # CORS 설정
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",  # Next.js 개발 서버
        "http://localhost:8000",  # FastAPI 자체
    ]

    # 데이터베이스 설정
    DATABASE_URL: str
    POSTGRES_USER: Optional[str] = None
    POSTGRES_PASSWORD: Optional[str] = None
    POSTGRES_DB: Optional[str] = None

    # Milvus 설정
    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: str = "19530"
    MILVUS_COLLECTION_NAME: str = "rag_document_chunks"

    # Ollama 설정
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2:1b"

    # 보안 설정 [HARD RULE]
    SECRET_KEY: str  # 필수! .env에서 로드
    JWT_SECRET: str  # JWT 토큰 서명 키 (필수!)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # 타임아웃 설정
    REQUEST_TIMEOUT_SECONDS: int = 30

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
