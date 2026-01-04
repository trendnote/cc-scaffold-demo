"""
DB 세션 관리 및 Connection Pool 설정

Task 2.9: 성능 최적화 및 로깅

[HARD RULE] 성능 목표:
- DB 저장: P95 < 500ms
- Connection Pool: pool_size=20
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings


# DB Connection Pool 설정
# [성능 최적화] pool_size=20, max_overflow=10
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=20,             # 최대 20개 연결 유지
    max_overflow=10,          # 추가 10개 overflow 허용 (총 30개)
    pool_recycle=3600,        # 1시간(3600초)마다 연결 재생성 (stale connection 방지)
    pool_pre_ping=True,       # 연결 유효성 사전 확인 (자동 재연결)
    echo=False,               # SQL 로그 비활성화 (성능 향상)
    pool_timeout=30,          # Connection 획득 타임아웃 30초
    connect_args={
        "connect_timeout": 10  # PostgreSQL 연결 타임아웃 10초
    }
)

# Session Factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """
    DB 세션 의존성

    FastAPI Depends에서 사용됩니다.
    자동으로 세션을 생성하고 요청 완료 후 닫습니다.

    Usage:
        @app.get("/")
        def read_root(db: Session = Depends(get_db)):
            return db.query(User).all()

    Yields:
        Session: DB 세션
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
