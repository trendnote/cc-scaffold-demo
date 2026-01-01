# Task Execution Plan: 1.2 - PostgreSQL 스키마 및 마이그레이션 설정

---

## Meta
- **Task ID**: 1.2
- **Task Name**: PostgreSQL 스키마 및 마이그레이션 설정
- **Original Estimate**: 4시간
- **Revised Estimate**: 4.5시간
- **Variance**: +0.5시간 (SQLAlchemy 2.0 async 설정 추가)
- **담당**: Backend
- **Dependencies**: Task 1.1 (Docker Compose 환경 구축)
- **Created**: 2025-12-31
- **Status**: Ready for Implementation

---

## 1. Task Overview

### 1.1 목표
PostgreSQL 데이터베이스 스키마를 정의하고 Alembic을 통한 마이그레이션 시스템을 구축합니다. 사용자, 문서, 검색 쿼리, 피드백 테이블을 포함한 전체 데이터 모델을 SQLAlchemy ORM으로 구현하고, 프로덕션 환경에서 안전하게 스키마를 관리할 수 있는 기반을 마련합니다.

### 1.2 Task Breakdown 정보
- **작업 내용**:
  - SQLAlchemy 모델 정의 (Users, Documents, SearchQueries, SearchResponses, UserFeedback)
  - Alembic 마이그레이션 설정
  - 초기 스키마 생성 스크립트
  - 인덱스 생성 (idx_users_email, idx_documents_metadata, idx_search_queries_user_id)

- **검증 기준**:
  - [ ] `alembic upgrade head` 성공
  - [ ] 모든 테이블 생성 확인 (psql)
  - [ ] 제약 조건 검증 (FK, INDEX)
  - [ ] 샘플 데이터 삽입 성공

- **출력물**:
  - `backend/app/models/` (모든 모델 파일)
  - `alembic/versions/` (마이그레이션 파일)
  - `backend/tests/test_models.py` (단위 테스트)

### 1.3 주요 기술 스택
- **ORM**: SQLAlchemy 2.0 (async 지원)
- **Migration Tool**: Alembic 1.13+
- **Database**: PostgreSQL 15
- **Testing**: pytest, pytest-asyncio
- **Type Checking**: Pydantic v2

---

## 2. Research & Design

### 2.1 기술 조사 결과

#### SQLAlchemy 2.0 Best Practices
최신 연구(2024-2025)에 따른 권장사항:

1. **Naming Conventions**: 자동 네이밍 규칙 설정으로 인덱스/제약조건 일관성 확보
2. **Autogenerate with Caution**: `--autogenerate` 사용 후 반드시 수동 검토
3. **Static Table Definitions**: 데이터 마이그레이션 시 정적 테이블 정의 사용
4. **PostgreSQL-Specific**: JSONB, GIN 인덱스, ENUM 타입 처리 주의
5. **Async Support**: SQLAlchemy 2.0의 async engine 사용 (FastAPI와 호환)
6. **Mixins for Reusability**: 공통 필드(created_at, updated_at) mixin으로 관리

출처:
- [Best Practices for Alembic and SQLAlchemy - DEV Community](https://dev.to/welel/best-practices-for-alembic-and-sqlalchemy-3b34)
- [Best Practices for Alembic Schema Migration - PingCAP](https://www.pingcap.com/article/best-practices-alembic-schema-migration/)
- [Using Alembic With FastAPI and PostgreSQL - Medium](https://medium.com/@rajeshpachaikani/using-alembic-with-fastapi-and-postgresql-no-bullshit-guide-b564ae89f4be)

### 2.2 데이터베이스 스키마 설계

#### ER Diagram
```
┌─────────────┐         ┌──────────────┐
│   Users     │         │  Documents   │
├─────────────┤         ├──────────────┤
│ id (PK)     │         │ id (PK)      │
│ email       │         │ title        │
│ name        │         │ content      │
│ department  │         │ document_type│
│ access_level│         │ source       │
│ created_at  │         │ access_level │
│ updated_at  │         │ department   │
└──────┬──────┘         │ metadata     │
       │                │ created_at   │
       │                │ updated_at   │
       │                └──────┬───────┘
       │                       │
       │      ┌────────────────┘
       │      │
       ▼      ▼
┌─────────────────┐
│ SearchQueries   │
├─────────────────┤
│ id (PK)         │
│ user_id (FK)    │◄──────┐
│ query           │       │
│ session_id      │       │
│ timestamp       │       │
└────────┬────────┘       │
         │                │
         ▼                │
┌─────────────────┐       │
│SearchResponses  │       │
├─────────────────┤       │
│ id (PK)         │       │
│ query_id (FK)   │       │
│ answer          │       │
│ sources (JSONB) │       │
│ response_time_ms│       │
│ timestamp       │       │
└─────────────────┘       │
                          │
┌─────────────────┐       │
│  UserFeedback   │       │
├─────────────────┤       │
│ id (PK)         │       │
│ query_id (FK)   │───────┘
│ user_id (FK)    │
│ rating          │
│ comment         │
│ timestamp       │
└─────────────────┘
```

#### 테이블 상세 명세

**1. Users (사용자 관리)**
```python
- id: UUID (PK)
- email: String(255), unique, not null, indexed
- name: String(100), not null
- department: String(50), not null
- access_level: Integer (1=L1, 2=L2, 3=L3), not null, default=1
- is_active: Boolean, default=True
- created_at: DateTime(timezone=True), server_default=now()
- updated_at: DateTime(timezone=True), onupdate=now()

Indexes:
- idx_users_email (email)
- idx_users_department (department)
```

**2. Documents (문서 메타데이터)**
```python
- id: UUID (PK)
- title: String(500), not null
- content: Text, not null
- document_type: String(50), not null (PDF, DOCX, TXT, MARKDOWN)
- source: String(500), not null (원본 파일 경로)
- access_level: Integer (1-3), not null, default=1
- department: String(50), nullable (부서 제한 문서)
- metadata: JSONB, nullable (페이지 수, 크기, 작성자 등)
- created_at: DateTime(timezone=True), server_default=now()
- updated_at: DateTime(timezone=True), onupdate=now()

Indexes:
- idx_documents_metadata (metadata) GIN index
- idx_documents_access_level (access_level)
- idx_documents_department (department)
```

**3. SearchQueries (검색 쿼리 기록)**
```python
- id: UUID (PK)
- user_id: UUID (FK -> Users.id), not null
- query: Text, not null
- session_id: String(100), nullable
- timestamp: DateTime(timezone=True), server_default=now()

Indexes:
- idx_search_queries_user_id (user_id)
- idx_search_queries_timestamp (timestamp)
```

**4. SearchResponses (검색 응답 기록)**
```python
- id: UUID (PK)
- query_id: UUID (FK -> SearchQueries.id), not null, unique
- answer: Text, not null
- sources: JSONB, not null (검색된 문서 정보 배열)
- response_time_ms: Integer, not null
- timestamp: DateTime(timezone=True), server_default=now()

Indexes:
- idx_search_responses_query_id (query_id)
```

**5. UserFeedback (사용자 피드백)**
```python
- id: UUID (PK)
- query_id: UUID (FK -> SearchQueries.id), not null
- user_id: UUID (FK -> Users.id), not null
- rating: Integer (1-5), not null
- comment: Text, nullable
- timestamp: DateTime(timezone=True), server_default=now()

Indexes:
- idx_user_feedback_query_id (query_id)
- idx_user_feedback_user_id (user_id)
```

### 2.3 설계 결정 사항

#### Decision 1: UUID vs Auto-Increment ID
**선택**: UUID (uuid4)
**이유**:
- 분산 시스템 확장성 (향후 멀티 데이터센터 대비)
- 외부 노출 시 예측 불가능성 (보안)
- 병합/마이그레이션 시 충돌 없음
**Trade-off**: 저장 공간 증가 (16 bytes vs 8 bytes), 인덱스 성능 약간 저하 (허용 범위)

#### Decision 2: JSONB for metadata and sources
**선택**: PostgreSQL JSONB 타입 사용
**이유**:
- 스키마 유연성 (문서 타입별 메타데이터 다름)
- GIN 인덱스로 JSON 필드 검색 가능
- 정규화 비용 대비 유연성 우수
**Trade-off**: 쿼리 복잡도 증가, 타입 안정성 감소 (Pydantic으로 보완)

#### Decision 3: Soft Delete vs Hard Delete
**선택**: Hard Delete (is_active flag는 Users만)
**이유**:
- 검색 기록은 90일 보관 정책 (배치 삭제)
- 감사 로그는 별도 시스템 (향후 Phase 추가)
- 단순성 우선 (MVP)
**향후 고려**: Phase 2에서 감사 로그 테이블 추가

#### Decision 4: Async SQLAlchemy Engine
**선택**: SQLAlchemy 2.0 async engine (asyncpg)
**이유**:
- FastAPI의 async/await 패턴과 일관성
- 성능 향상 (I/O bound 작업 최적화)
- 현대적 Python 비동기 표준 준수
**주의사항**: Alembic은 동기 컨텍스트 (sync_engine 사용)

---

## 3. Implementation Steps

### Step 1: 프로젝트 구조 및 의존성 설정 (30분)

**작업 내용**:
1. 디렉토리 구조 생성
   ```bash
   mkdir -p backend/app/models
   mkdir -p backend/app/db
   mkdir -p backend/tests
   mkdir -p backend/alembic/versions
   ```

2. 의존성 추가 (`backend/requirements.txt`)
   ```
   sqlalchemy[asyncio]==2.0.25
   alembic==1.13.1
   asyncpg==0.29.0
   psycopg2-binary==2.9.9  # Alembic 동기 연결용
   pydantic==2.5.3
   python-dotenv==1.0.0
   ```

3. 환경 변수 설정 (`.env`)
   ```
   DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/rag_platform
   DATABASE_SYNC_URL=postgresql://user:password@localhost:5432/rag_platform
   ```
   **[HARD RULE]** 실제 비밀번호는 환경 변수로만 관리, 하드코딩 금지

**검증**:
- [ ] 디렉토리 구조 확인
- [ ] `pip install -r requirements.txt` 성공
- [ ] `.env` 파일 생성 확인

**출력물**:
- `backend/requirements.txt`
- `backend/.env.example`
- 디렉토리 구조

---

### Step 2: Base Model 및 Database Connection 설정 (45분)

**작업 내용**:
1. `backend/app/db/base.py` 생성
   ```python
   from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
   from sqlalchemy.orm import declarative_base
   from sqlalchemy import MetaData
   import os
   from dotenv import load_dotenv

   load_dotenv()

   # Naming convention for automatic constraint naming
   NAMING_CONVENTION = {
       "ix": "ix_%(column_0_label)s",
       "uq": "uq_%(table_name)s_%(column_0_name)s",
       "ck": "ck_%(table_name)s_%(constraint_name)s",
       "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
       "pk": "pk_%(table_name)s"
   }

   metadata = MetaData(naming_convention=NAMING_CONVENTION)
   Base = declarative_base(metadata=metadata)

   DATABASE_URL = os.getenv("DATABASE_URL")

   engine = create_async_engine(
       DATABASE_URL,
       echo=True,  # Development only
       pool_size=5,
       max_overflow=10,
       pool_pre_ping=True,  # 연결 검증
   )

   async_session_maker = async_sessionmaker(
       engine,
       class_=AsyncSession,
       expire_on_commit=False
   )

   async def get_db():
       async with async_session_maker() as session:
           yield session
   ```

2. `backend/app/db/__init__.py` 생성
   ```python
   from .base import Base, engine, get_db

   __all__ = ["Base", "engine", "get_db"]
   ```

3. `backend/app/models/base_model.py` (공통 Mixin)
   ```python
   from sqlalchemy import Column, DateTime
   from sqlalchemy.sql import func

   class TimestampMixin:
       created_at = Column(
           DateTime(timezone=True),
           server_default=func.now(),
           nullable=False
       )
       updated_at = Column(
           DateTime(timezone=True),
           server_default=func.now(),
           onupdate=func.now(),
           nullable=False
       )
   ```

**검증**:
- [ ] `base.py` 임포트 에러 없음
- [ ] 환경 변수 로딩 확인
- [ ] Naming convention 설정 확인

**출력물**:
- `backend/app/db/base.py`
- `backend/app/db/__init__.py`
- `backend/app/models/base_model.py`

---

### Step 3: SQLAlchemy 모델 정의 - Users, Documents (1시간)

**작업 내용**:
1. `backend/app/models/user.py`
   ```python
   from sqlalchemy import Column, String, Integer, Boolean
   from sqlalchemy.dialects.postgresql import UUID
   from sqlalchemy.orm import relationship
   import uuid

   from ..db.base import Base
   from .base_model import TimestampMixin

   class User(Base, TimestampMixin):
       __tablename__ = "users"

       id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
       email = Column(String(255), unique=True, nullable=False, index=True)
       name = Column(String(100), nullable=False)
       department = Column(String(50), nullable=False, index=True)
       access_level = Column(Integer, nullable=False, default=1)
       is_active = Column(Boolean, default=True, nullable=False)

       # Relationships
       search_queries = relationship("SearchQuery", back_populates="user", cascade="all, delete-orphan")
       feedbacks = relationship("UserFeedback", back_populates="user", cascade="all, delete-orphan")

       def __repr__(self):
           return f"<User(email='{self.email}', department='{self.department}')>"
   ```

2. `backend/app/models/document.py`
   ```python
   from sqlalchemy import Column, String, Text, Integer
   from sqlalchemy.dialects.postgresql import UUID, JSONB
   import uuid

   from ..db.base import Base
   from .base_model import TimestampMixin

   class Document(Base, TimestampMixin):
       __tablename__ = "documents"

       id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
       title = Column(String(500), nullable=False)
       content = Column(Text, nullable=False)
       document_type = Column(String(50), nullable=False)
       source = Column(String(500), nullable=False)
       access_level = Column(Integer, nullable=False, default=1, index=True)
       department = Column(String(50), nullable=True, index=True)
       metadata = Column(JSONB, nullable=True)

       def __repr__(self):
           return f"<Document(title='{self.title[:30]}...', type='{self.document_type}')>"
   ```

**검증**:
- [ ] 모델 임포트 에러 없음
- [ ] Relationship 정의 확인
- [ ] `__repr__` 메서드 정의 확인

**출력물**:
- `backend/app/models/user.py`
- `backend/app/models/document.py`

---

### Step 4: SQLAlchemy 모델 정의 - Search, Feedback (45분)

**작업 내용**:
1. `backend/app/models/search.py`
   ```python
   from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey
   from sqlalchemy.dialects.postgresql import UUID, JSONB
   from sqlalchemy.orm import relationship
   from sqlalchemy.sql import func
   import uuid

   from ..db.base import Base

   class SearchQuery(Base):
       __tablename__ = "search_queries"

       id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
       user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
       query = Column(Text, nullable=False)
       session_id = Column(String(100), nullable=True)
       timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

       # Relationships
       user = relationship("User", back_populates="search_queries")
       response = relationship("SearchResponse", back_populates="query", uselist=False, cascade="all, delete-orphan")
       feedbacks = relationship("UserFeedback", back_populates="query", cascade="all, delete-orphan")

       def __repr__(self):
           return f"<SearchQuery(query='{self.query[:50]}...', user_id='{self.user_id}')>"

   class SearchResponse(Base):
       __tablename__ = "search_responses"

       id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
       query_id = Column(UUID(as_uuid=True), ForeignKey("search_queries.id"), nullable=False, unique=True, index=True)
       answer = Column(Text, nullable=False)
       sources = Column(JSONB, nullable=False)
       response_time_ms = Column(Integer, nullable=False)
       timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

       # Relationships
       query = relationship("SearchQuery", back_populates="response")

       def __repr__(self):
           return f"<SearchResponse(query_id='{self.query_id}', response_time={self.response_time_ms}ms)>"
   ```

2. `backend/app/models/feedback.py`
   ```python
   from sqlalchemy import Column, Text, Integer, DateTime, ForeignKey
   from sqlalchemy.dialects.postgresql import UUID
   from sqlalchemy.orm import relationship
   from sqlalchemy.sql import func
   import uuid

   from ..db.base import Base

   class UserFeedback(Base):
       __tablename__ = "user_feedback"

       id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
       query_id = Column(UUID(as_uuid=True), ForeignKey("search_queries.id"), nullable=False, index=True)
       user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
       rating = Column(Integer, nullable=False)
       comment = Column(Text, nullable=True)
       timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

       # Relationships
       query = relationship("SearchQuery", back_populates="feedbacks")
       user = relationship("User", back_populates="feedbacks")

       def __repr__(self):
           return f"<UserFeedback(query_id='{self.query_id}', rating={self.rating})>"
   ```

3. `backend/app/models/__init__.py`
   ```python
   from .user import User
   from .document import Document
   from .search import SearchQuery, SearchResponse
   from .feedback import UserFeedback

   __all__ = [
       "User",
       "Document",
       "SearchQuery",
       "SearchResponse",
       "UserFeedback",
   ]
   ```

**검증**:
- [ ] 모든 모델 임포트 에러 없음
- [ ] Foreign Key 관계 정의 확인
- [ ] Relationship bidirectional 확인

**출력물**:
- `backend/app/models/search.py`
- `backend/app/models/feedback.py`
- `backend/app/models/__init__.py`

---

### Step 5: Alembic 초기 설정 및 마이그레이션 생성 (45분)

**작업 내용**:
1. Alembic 초기화
   ```bash
   cd backend
   alembic init alembic
   ```

2. `backend/alembic.ini` 수정
   ```ini
   # Remove this line:
   # sqlalchemy.url = driver://user:pass@localhost/dbname

   # Add at the end:
   # sqlalchemy.url is set in env.py from environment variables
   ```

3. `backend/alembic/env.py` 수정
   ```python
   from logging.config import fileConfig
   from sqlalchemy import engine_from_config, pool
   from alembic import context
   import os
   import sys
   from dotenv import load_dotenv

   # Add parent directory to path
   sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

   load_dotenv()

   # Import models
   from app.db.base import Base
   from app.models import User, Document, SearchQuery, SearchResponse, UserFeedback

   config = context.config

   # Override sqlalchemy.url with environment variable
   config.set_main_option("sqlalchemy.url", os.getenv("DATABASE_SYNC_URL"))

   if config.config_file_name is not None:
       fileConfig(config.config_file_name)

   target_metadata = Base.metadata

   # ... (keep existing run_migrations_offline and run_migrations_online)
   ```

4. 초기 마이그레이션 생성
   ```bash
   alembic revision --autogenerate -m "Initial schema with users, documents, search, feedback tables"
   ```

5. 생성된 마이그레이션 파일 검토 및 수정
   - GIN 인덱스 수동 추가
   ```python
   def upgrade():
       # ... (autogenerated code)

       # Add GIN index for JSONB metadata
       op.create_index(
           'idx_documents_metadata',
           'documents',
           ['metadata'],
           postgresql_using='gin'
       )

   def downgrade():
       op.drop_index('idx_documents_metadata', table_name='documents')
       # ... (autogenerated code)
   ```

**검증**:
- [ ] Alembic 초기화 성공
- [ ] `env.py`에서 모든 모델 임포트 확인
- [ ] 마이그레이션 파일 생성 확인
- [ ] GIN 인덱스 정의 확인

**출력물**:
- `backend/alembic.ini`
- `backend/alembic/env.py`
- `backend/alembic/versions/xxxx_initial_schema.py`

---

### Step 6: 마이그레이션 실행 및 DB 검증 (30분)

**작업 내용**:
1. PostgreSQL 연결 확인
   ```bash
   psql $DATABASE_SYNC_URL -c "SELECT version();"
   ```

2. 마이그레이션 실행
   ```bash
   alembic upgrade head
   ```

3. 테이블 생성 확인
   ```bash
   psql $DATABASE_SYNC_URL -c "\dt"
   psql $DATABASE_SYNC_URL -c "\d users"
   psql $DATABASE_SYNC_URL -c "\d documents"
   ```

4. 인덱스 확인
   ```sql
   SELECT
       tablename,
       indexname,
       indexdef
   FROM
       pg_indexes
   WHERE
       schemaname = 'public'
   ORDER BY
       tablename,
       indexname;
   ```

5. Foreign Key 제약조건 확인
   ```sql
   SELECT
       tc.table_name,
       kcu.column_name,
       ccu.table_name AS foreign_table_name,
       ccu.column_name AS foreign_column_name
   FROM
       information_schema.table_constraints AS tc
       JOIN information_schema.key_column_usage AS kcu
         ON tc.constraint_name = kcu.constraint_name
       JOIN information_schema.constraint_column_usage AS ccu
         ON ccu.constraint_name = tc.constraint_name
   WHERE tc.constraint_type = 'FOREIGN KEY';
   ```

**검증**:
- [ ] 5개 테이블 생성 확인 (users, documents, search_queries, search_responses, user_feedback)
- [ ] 모든 인덱스 생성 확인 (7개 이상)
- [ ] Foreign Key 제약조건 확인 (4개)
- [ ] `alembic_version` 테이블 확인

**출력물**:
- DB 검증 결과 로그
- 스키마 검증 스크립트

---

### Step 7: 단위 테스트 작성 (45분)

**작업 내용**:
1. `backend/tests/conftest.py` (테스트 설정)
   ```python
   import pytest
   import asyncio
   from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
   from sqlalchemy.pool import NullPool
   from app.db.base import Base
   import os

   TEST_DATABASE_URL = os.getenv(
       "TEST_DATABASE_URL",
       "postgresql+asyncpg://user:password@localhost:5432/rag_platform_test"
   )

   @pytest.fixture(scope="session")
   def event_loop():
       loop = asyncio.get_event_loop_policy().new_event_loop()
       yield loop
       loop.close()

   @pytest.fixture(scope="function")
   async def db_engine():
       engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
       async with engine.begin() as conn:
           await conn.run_sync(Base.metadata.create_all)
       yield engine
       async with engine.begin() as conn:
           await conn.run_sync(Base.metadata.drop_all)
       await engine.dispose()

   @pytest.fixture(scope="function")
   async def db_session(db_engine):
       async_session = async_sessionmaker(
           db_engine, class_=AsyncSession, expire_on_commit=False
       )
       async with async_session() as session:
           yield session
   ```

2. `backend/tests/test_models.py`
   ```python
   import pytest
   from app.models import User, Document, SearchQuery, SearchResponse, UserFeedback
   from sqlalchemy import select
   import uuid

   @pytest.mark.asyncio
   async def test_create_user(db_session):
       """사용자 생성 테스트"""
       user = User(
           email="test@example.com",
           name="Test User",
           department="Engineering",
           access_level=2
       )
       db_session.add(user)
       await db_session.commit()
       await db_session.refresh(user)

       assert user.id is not None
       assert user.email == "test@example.com"
       assert user.access_level == 2
       assert user.created_at is not None

   @pytest.mark.asyncio
   async def test_create_document(db_session):
       """문서 생성 테스트"""
       document = Document(
           title="Test Document",
           content="This is test content",
           document_type="PDF",
           source="/path/to/test.pdf",
           access_level=1,
           metadata={"page_count": 10, "author": "Test Author"}
       )
       db_session.add(document)
       await db_session.commit()
       await db_session.refresh(document)

       assert document.id is not None
       assert document.metadata["page_count"] == 10

   @pytest.mark.asyncio
   async def test_search_query_relationship(db_session):
       """검색 쿼리와 사용자 관계 테스트"""
       user = User(
           email="search@example.com",
           name="Search User",
           department="Engineering"
       )
       db_session.add(user)
       await db_session.commit()
       await db_session.refresh(user)

       query = SearchQuery(
           user_id=user.id,
           query="How to use RAG?",
           session_id="test-session-123"
       )
       db_session.add(query)
       await db_session.commit()
       await db_session.refresh(query)

       # Test relationship
       result = await db_session.execute(
           select(SearchQuery).where(SearchQuery.user_id == user.id)
       )
       queries = result.scalars().all()
       assert len(queries) == 1
       assert queries[0].query == "How to use RAG?"

   @pytest.mark.asyncio
   async def test_search_response_relationship(db_session):
       """검색 응답과 쿼리 관계 테스트"""
       user = User(email="resp@example.com", name="Resp User", department="Eng")
       db_session.add(user)
       await db_session.commit()
       await db_session.refresh(user)

       query = SearchQuery(user_id=user.id, query="Test query")
       db_session.add(query)
       await db_session.commit()
       await db_session.refresh(query)

       response = SearchResponse(
           query_id=query.id,
           answer="Test answer",
           sources=[{"document_id": str(uuid.uuid4()), "title": "Test Doc"}],
           response_time_ms=1500
       )
       db_session.add(response)
       await db_session.commit()

       # Test unique constraint
       result = await db_session.execute(
           select(SearchResponse).where(SearchResponse.query_id == query.id)
       )
       responses = result.scalars().all()
       assert len(responses) == 1
       assert responses[0].response_time_ms == 1500

   @pytest.mark.asyncio
   async def test_user_feedback_relationship(db_session):
       """사용자 피드백 관계 테스트"""
       user = User(email="fb@example.com", name="FB User", department="Eng")
       db_session.add(user)
       await db_session.commit()
       await db_session.refresh(user)

       query = SearchQuery(user_id=user.id, query="Feedback test")
       db_session.add(query)
       await db_session.commit()
       await db_session.refresh(query)

       feedback = UserFeedback(
           query_id=query.id,
           user_id=user.id,
           rating=5,
           comment="Great answer!"
       )
       db_session.add(feedback)
       await db_session.commit()

       result = await db_session.execute(
           select(UserFeedback).where(UserFeedback.user_id == user.id)
       )
       feedbacks = result.scalars().all()
       assert len(feedbacks) == 1
       assert feedbacks[0].rating == 5

   @pytest.mark.asyncio
   async def test_cascade_delete(db_session):
       """Cascade delete 테스트"""
       user = User(email="cascade@example.com", name="Cascade User", department="Eng")
       db_session.add(user)
       await db_session.commit()
       await db_session.refresh(user)

       query = SearchQuery(user_id=user.id, query="Cascade test")
       db_session.add(query)
       await db_session.commit()

       # Delete user
       await db_session.delete(user)
       await db_session.commit()

       # Verify cascade delete
       result = await db_session.execute(select(SearchQuery))
       queries = result.scalars().all()
       assert len(queries) == 0

   @pytest.mark.asyncio
   async def test_gin_index_jsonb(db_session):
       """JSONB GIN 인덱스 테스트 (간접 검증)"""
       # Create documents with different metadata
       docs = [
           Document(
               title=f"Doc {i}",
               content="Test",
               document_type="PDF",
               source=f"/test/{i}.pdf",
               metadata={"tags": ["python", "rag"], "priority": i}
           )
           for i in range(5)
       ]
       db_session.add_all(docs)
       await db_session.commit()

       # This query will use GIN index if available
       result = await db_session.execute(
           select(Document).where(Document.metadata.op('@>')({"tags": ["python"]}))
       )
       found_docs = result.scalars().all()
       assert len(found_docs) == 5
   ```

3. 테스트 실행
   ```bash
   pytest backend/tests/test_models.py -v
   ```

**검증**:
- [ ] 7개 테스트 모두 통과
- [ ] Relationship 테스트 성공
- [ ] Cascade delete 테스트 성공
- [ ] JSONB 쿼리 테스트 성공

**출력물**:
- `backend/tests/conftest.py`
- `backend/tests/test_models.py`
- 테스트 실행 결과

---

### Step 8: 샘플 데이터 삽입 및 최종 검증 (30분)

**작업 내용**:
1. `backend/scripts/seed_data.py` 생성
   ```python
   import asyncio
   from app.db.base import async_session_maker
   from app.models import User, Document

   async def seed_sample_data():
       async with async_session_maker() as session:
           # Sample users
           users = [
               User(
                   email="admin@company.com",
                   name="Admin User",
                   department="Management",
                   access_level=3
               ),
               User(
                   email="engineer@company.com",
                   name="Engineer User",
                   department="Engineering",
                   access_level=2
               ),
               User(
                   email="intern@company.com",
                   name="Intern User",
                   department="Engineering",
                   access_level=1
               ),
           ]
           session.add_all(users)

           # Sample documents
           documents = [
               Document(
                   title="Company Handbook",
                   content="This is the company handbook...",
                   document_type="PDF",
                   source="/docs/handbook.pdf",
                   access_level=1,
                   metadata={"page_count": 50, "version": "2024.1"}
               ),
               Document(
                   title="Engineering Best Practices",
                   content="Best practices for engineering...",
                   document_type="MARKDOWN",
                   source="/docs/engineering-bp.md",
                   access_level=2,
                   department="Engineering",
                   metadata={"tags": ["engineering", "best-practices"]}
               ),
               Document(
                   title="Confidential Strategy",
                   content="Company strategy for 2025...",
                   document_type="DOCX",
                   source="/docs/strategy-2025.docx",
                   access_level=3,
                   department="Management",
                   metadata={"confidential": True}
               ),
           ]
           session.add_all(documents)

           await session.commit()
           print("✅ Sample data inserted successfully!")

   if __name__ == "__main__":
       asyncio.run(seed_sample_data())
   ```

2. 샘플 데이터 삽입
   ```bash
   python backend/scripts/seed_data.py
   ```

3. 데이터 확인
   ```sql
   SELECT email, name, department, access_level FROM users;
   SELECT title, document_type, access_level, department FROM documents;
   ```

4. 최종 검증 체크리스트
   ```bash
   # 1. 테이블 확인
   psql $DATABASE_SYNC_URL -c "\dt"

   # 2. 인덱스 확인
   psql $DATABASE_SYNC_URL -c "\di"

   # 3. 제약조건 확인
   psql $DATABASE_SYNC_URL -c "SELECT conname, contype FROM pg_constraint WHERE connamespace = 'public'::regnamespace;"

   # 4. 샘플 데이터 개수 확인
   psql $DATABASE_SYNC_URL -c "SELECT 'users' AS table_name, COUNT(*) FROM users UNION ALL SELECT 'documents', COUNT(*) FROM documents;"
   ```

**검증**:
- [ ] 3명의 사용자 삽입 확인
- [ ] 3개의 문서 삽입 확인
- [ ] 모든 테이블에 데이터 존재
- [ ] JSONB 필드 정상 저장 확인

**출력물**:
- `backend/scripts/seed_data.py`
- 샘플 데이터 삽입 결과
- 최종 검증 리포트

---

## 4. Testing Plan

### 4.1 단위 테스트 (pytest)

**Test Case 1: User 모델 생성 및 제약조건**
```python
def test_user_creation():
    """사용자 생성 및 기본값 확인"""
def test_user_email_unique():
    """이메일 unique 제약조건 확인"""
def test_user_access_level_default():
    """access_level 기본값 1 확인"""
```

**Test Case 2: Document 모델 및 JSONB**
```python
def test_document_creation():
    """문서 생성 및 JSONB 메타데이터 저장"""
def test_document_metadata_query():
    """JSONB 필드 쿼리 확인 (GIN 인덱스 활용)"""
def test_document_access_level_filtering():
    """access_level 필터링 쿼리 테스트"""
```

**Test Case 3: SearchQuery & SearchResponse 관계**
```python
def test_search_query_user_relationship():
    """SearchQuery - User 관계 확인"""
def test_search_response_unique_constraint():
    """query_id unique 제약조건 확인"""
def test_search_response_sources_jsonb():
    """sources JSONB 필드 저장 및 조회"""
```

**Test Case 4: UserFeedback 관계**
```python
def test_user_feedback_creation():
    """피드백 생성 및 관계 확인"""
def test_user_feedback_rating_range():
    """rating 1-5 범위 확인 (애플리케이션 레벨)"""
```

**Test Case 5: Cascade Delete**
```python
def test_user_delete_cascades_queries():
    """User 삭제 시 SearchQuery cascade 확인"""
def test_query_delete_cascades_response():
    """SearchQuery 삭제 시 SearchResponse cascade 확인"""
```

**Test Case 6: 타임스탬프 자동 생성**
```python
def test_created_at_auto_generated():
    """created_at 자동 생성 확인"""
def test_updated_at_on_update():
    """updated_at 수정 시 갱신 확인"""
```

**Test Case 7: 인덱스 성능 (간접 검증)**
```python
def test_email_index_performance():
    """email 인덱스 활용 쿼리 (EXPLAIN ANALYZE)"""
def test_metadata_gin_index():
    """JSONB GIN 인덱스 활용 쿼리"""
```

### 4.2 통합 테스트

**Integration Test 1: Full Workflow**
```python
async def test_full_search_workflow():
    """사용자 생성 → 검색 → 응답 저장 → 피드백 전체 플로우"""
```

**Integration Test 2: Access Control Scenario**
```python
async def test_access_control_scenario():
    """L1 사용자가 L2 문서 필터링 시나리오"""
```

### 4.3 마이그레이션 테스트

**Migration Test 1: Upgrade**
```bash
alembic upgrade head
# Verify all tables created
```

**Migration Test 2: Downgrade**
```bash
alembic downgrade -1
# Verify tables dropped
alembic upgrade head
# Verify re-creation
```

**Migration Test 3: Rollback Safety**
```python
def test_migration_rollback():
    """마이그레이션 롤백 후 데이터 무결성 확인"""
```

### 4.4 데이터 무결성 테스트

**Integrity Test 1: Foreign Key 제약**
```sql
-- Insert SearchQuery with non-existent user_id (should fail)
INSERT INTO search_queries (user_id, query) VALUES ('invalid-uuid', 'test');
```

**Integrity Test 2: Unique 제약**
```sql
-- Insert duplicate email (should fail)
INSERT INTO users (email, name, department) VALUES ('test@example.com', 'User1', 'Eng');
INSERT INTO users (email, name, department) VALUES ('test@example.com', 'User2', 'Eng');
```

### 4.5 성능 테스트

**Performance Test 1: JSONB 쿼리 성능**
```python
async def test_jsonb_query_performance():
    """1000개 문서 삽입 후 JSONB 쿼리 성능 측정 (< 100ms 목표)"""
```

**Performance Test 2: Index 활용도**
```sql
EXPLAIN ANALYZE SELECT * FROM users WHERE email = 'test@example.com';
-- Verify "Index Scan using idx_users_email"
```

---

## 5. Risks & Mitigation

### Risk 1: Alembic Autogenerate 오류 (Medium Probability)

**Impact**: Medium
- 잘못된 마이그레이션 스크립트 생성 → 프로덕션 스키마 손상

**Probability**: Medium (30%)
- Alembic의 autogenerate는 모든 변경사항을 완벽하게 감지하지 못함
- 특히 인덱스, 제약조건, ENUM 타입 변경 누락 가능

**Mitigation**:
1. **자동 생성 후 필수 수동 검토**
   - 모든 autogenerate 마이그레이션은 diff 확인
   - 특히 GIN 인덱스, JSONB 타입 변경 주의 깊게 검토
2. **마이그레이션 테스트 환경 구축**
   - 테스트 DB에서 먼저 upgrade/downgrade 실행
   - 롤백 테스트 (downgrade → upgrade)
3. **Static Table Definitions 사용**
   - 데이터 마이그레이션 시 현재 모델 참조 금지
   - 마이그레이션 파일 내 정적 테이블 정의
4. **Peer Review**
   - 모든 마이그레이션 파일은 팀 리뷰 필수

**Owner**: Backend Lead
**Review**: Step 5 완료 시

---

### Risk 2: PostgreSQL JSONB 성능 저하 (Low Probability)

**Impact**: Medium
- 문서 메타데이터 쿼리 느려짐 → 검색 성능 저하

**Probability**: Low (15%)
- 문서 수 < 10,000개 시 GIN 인덱스로 충분
- 하지만 문서 증가 시 성능 저하 가능

**Mitigation**:
1. **GIN 인덱스 적용**
   - metadata 컬럼에 GIN 인덱스 생성 (Step 5)
   - `@>`, `?` 연산자 활용
2. **성능 모니터링**
   - EXPLAIN ANALYZE로 쿼리 플랜 확인
   - P95 < 100ms 목표 설정
3. **필요 시 정규화**
   - 자주 쿼리하는 메타데이터는 별도 컬럼으로 이동
   - 예: `page_count`, `author` 컬럼 추가
4. **파티셔닝 고려**
   - 문서 수 > 100,000개 시 파티셔닝 검토

**Owner**: Backend Engineer
**Review**: Phase 2 성능 테스트 시 (Task 2.9)

---

### Risk 3: Async SQLAlchemy 호환성 이슈 (Low Probability)

**Impact**: High
- FastAPI와 SQLAlchemy 비동기 연동 실패 → 개발 블로킹

**Probability**: Low (10%)
- SQLAlchemy 2.0의 async 지원 성숙
- 하지만 일부 서드파티 라이브러리 비호환 가능

**Mitigation**:
1. **Alembic 동기 엔진 사용**
   - `DATABASE_SYNC_URL` 환경 변수 별도 관리
   - `engine.sync_engine` 활용
2. **FastAPI 의존성 주입 패턴**
   - `get_db()` 의존성으로 세션 관리
   - `async with` 컨텍스트 매니저 사용
3. **Connection Pool 설정**
   - `pool_pre_ping=True` (연결 검증)
   - `pool_size=5`, `max_overflow=10`
4. **Fallback Plan**
   - 비동기 이슈 지속 시 동기 SQLAlchemy 사용
   - 성능 영향 최소 (I/O bound 작업)

**Owner**: Backend Lead
**Review**: Step 2 완료 시

---

### Risk 4: 마이그레이션 충돌 (Low Probability)

**Impact**: Medium
- 여러 개발자가 동시 마이그레이션 생성 → 브랜치 충돌

**Probability**: Low (20%)
- Phase 1에서는 단일 개발자 작업 예상
- 하지만 Phase 2 이후 팀 확장 시 발생 가능

**Mitigation**:
1. **마이그레이션 순서 관리**
   - Alembic revision ID 사용
   - `down_revision` 명확히 설정
2. **Merge 전 마이그레이션 재생성**
   - main 브랜치와 충돌 시 마이그레이션 재생성
   - `alembic merge heads` 명령어 활용
3. **마이그레이션 파일 네이밍 규칙**
   - `YYYYMMDD_HHMM_description.py` 형식
   - 타임스탬프로 순서 명확화
4. **주간 마이그레이션 리뷰**
   - 금요일 오후 마이그레이션 상태 점검

**Owner**: Backend Team
**Review**: Phase 2 시작 전

---

## 6. Definition of Done

### 6.1 기능 완료 기준
- [ ] **모든 SQLAlchemy 모델 정의 완료**
  - User, Document, SearchQuery, SearchResponse, UserFeedback
  - Relationship bidirectional 설정
  - TimestampMixin 적용
  - `__repr__` 메서드 정의

- [ ] **Alembic 마이그레이션 시스템 구축**
  - `alembic init` 완료
  - `env.py` 환경 변수 설정
  - 초기 마이그레이션 생성 및 검토
  - GIN 인덱스 수동 추가

- [ ] **데이터베이스 스키마 생성 성공**
  - `alembic upgrade head` 성공
  - 5개 테이블 생성 확인
  - 7개 이상 인덱스 생성 확인
  - Foreign Key 제약조건 확인

- [ ] **샘플 데이터 삽입 성공**
  - 3명 사용자 삽입
  - 3개 문서 삽입
  - JSONB 필드 정상 저장 확인

### 6.2 테스트 완료 기준
- [ ] **단위 테스트 7개 이상 작성 및 통과**
  - 모델 생성 테스트
  - Relationship 테스트
  - Cascade delete 테스트
  - JSONB 쿼리 테스트
  - Coverage > 80%

- [ ] **통합 테스트 2개 작성 및 통과**
  - Full search workflow 테스트
  - Access control 시나리오 테스트

- [ ] **마이그레이션 테스트**
  - Upgrade 테스트
  - Downgrade 테스트
  - Rollback 안정성 확인

### 6.3 코드 품질 기준
- [ ] **CLAUDE.md HARD RULE 준수**
  - 비밀번호 하드코딩 없음 (환경 변수 사용)
  - SQL Injection 방어 (ORM 사용)
  - 입력 검증 (Pydantic 모델)

- [ ] **타입 힌트 적용**
  - 모든 함수/메서드 타입 힌트
  - mypy strict mode 통과

- [ ] **문서화**
  - 모든 모델 클래스 docstring
  - 마이그레이션 파일 설명 주석
  - README에 스키마 다이어그램 추가

### 6.4 운영 준비 기준
- [ ] **환경 변수 관리**
  - `.env.example` 파일 생성
  - DATABASE_URL, DATABASE_SYNC_URL 설정
  - 비밀번호 환경 변수화

- [ ] **로깅 설정**
  - SQLAlchemy echo 개발 환경만
  - 프로덕션: echo=False 설정

- [ ] **마이그레이션 문서화**
  - `docs/migrations/README.md` 생성
  - 롤백 절차 문서화
  - 트러블슈팅 가이드

### 6.5 리뷰 및 승인
- [ ] **Peer Review 완료**
  - 모델 설계 리뷰
  - 마이그레이션 파일 리뷰
  - 테스트 코드 리뷰

- [ ] **Tech Lead 승인**
  - 스키마 설계 승인
  - 인덱스 전략 승인

---

## 7. Time Breakdown

| Step | 작업 내용 | 예상 시간 | 누적 시간 |
|------|----------|----------|----------|
| 1 | 프로젝트 구조 및 의존성 설정 | 0.5h | 0.5h |
| 2 | Base Model 및 Database Connection | 0.75h | 1.25h |
| 3 | SQLAlchemy 모델 (User, Document) | 1.0h | 2.25h |
| 4 | SQLAlchemy 모델 (Search, Feedback) | 0.75h | 3.0h |
| 5 | Alembic 설정 및 마이그레이션 생성 | 0.75h | 3.75h |
| 6 | 마이그레이션 실행 및 DB 검증 | 0.5h | 4.25h |
| 7 | 단위 테스트 작성 | 0.75h | 5.0h |
| 8 | 샘플 데이터 삽입 및 최종 검증 | 0.5h | 5.5h |

**Total**: 5.5시간 (예상 4.5시간 + 버퍼 1시간)

**시간 배분**:
- Research/Design: 0% (사전 완료)
- Implementation: 73% (4.0h)
- Testing: 16% (0.9h)
- Verification: 11% (0.6h)

---

## 8. Next Steps

### 8.1 Immediate Next Steps (Task 1.2 완료 후)
1. **Task 1.3 준비**: Milvus Collection 생성
   - Milvus Python SDK 설치
   - Collection 스키마 설계 시작

2. **Documentation Update**
   - README에 데이터베이스 스키마 섹션 추가
   - ER 다이어그램 이미지 생성 및 포함

### 8.2 Follow-up Tasks
- **Task 2.1**: FastAPI 라우터 설정 시 모델 임포트
- **Task 2.7**: 검색 히스토리 조회 시 모델 활용
- **Phase 4**: 90일 보관 정책 배치 작업 (SearchQueries 삭제)

### 8.3 Monitoring & Maintenance
- **주간 점검**: 마이그레이션 이력 확인
- **월간 점검**: 인덱스 성능 분석 (EXPLAIN ANALYZE)
- **분기 점검**: 데이터베이스 스키마 리팩토링 필요 여부

---

## 9. References

### 9.1 Documentation
- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/)
- [Alembic Tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html)
- [PostgreSQL JSONB Documentation](https://www.postgresql.org/docs/current/datatype-json.html)
- [FastAPI with SQLAlchemy](https://fastapi.tiangolo.com/tutorial/sql-databases/)

### 9.2 Best Practices (Web Research)
- [Best Practices for Alembic and SQLAlchemy - DEV Community](https://dev.to/welel/best-practices-for-alembic-and-sqlalchemy-3b34)
- [Best Practices for Alembic Schema Migration - PingCAP](https://www.pingcap.com/article/best-practices-alembic-schema-migration/)
- [Using Alembic With FastAPI and PostgreSQL - Medium](https://medium.com/@rajeshpachaikani/using-alembic-with-fastapi-and-postgresql-no-bullshit-guide-b564ae89f4be)
- [Database Migrations with Alembic and FastAPI - Adex](https://adex.ltd/database-migrations-with-alembic-and-fastapi-a-comprehensive-guide-using-poetry)

### 9.3 Internal References
- Task Breakdown: `docs/tasks/task-breakdown.md`
- PRD: `docs/prd/rag-platform-prd.md`
- Architecture: `docs/architecture/architecture.md`
- Tech Stack: `docs/tech-stack/tech-stack.md`

---

## 10. Approval

**Prepared By**: Claude (Task Planner)
**Date**: 2025-12-31

**Review Status**:
- [ ] Peer Review (Backend Team)
- [ ] Tech Lead Approval
- [ ] Ready for Implementation

**Notes**:
이 계획서는 Task 1.2의 상세 실행 가이드입니다. 각 Step은 30분-1시간 단위로 설계되었으며, 모든 검증 기준과 테스트 케이스를 포함합니다. CLAUDE.md의 HARD RULE을 준수하며 안전한 데이터베이스 마이그레이션을 목표로 합니다.

---

**END OF TASK EXECUTION PLAN**
