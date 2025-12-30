# System Architecture: RAG 기반 사내 정보 검색 플랫폼

---

## Meta
- PRD Reference: [docs/prd/rag-platform-prd.md](../prd/rag-platform-prd.md)
- Tech Stack Reference: [docs/tech-stack/tech-stack.md](../tech-stack/tech-stack.md)
- Architecture Owner: Architecture Designer
- Status: Draft
- Last Updated: 2025-12-30
- Version: 1.0.0

---

## 1. Executive Summary

본 문서는 RAG 기반 사내 정보 검색 플랫폼의 시스템 아키텍처를 정의합니다. Python/FastAPI 기반의 백엔드, Next.js 14 프론트엔드, PostgreSQL 주 데이터베이스, Milvus 벡터 데이터베이스, Ollama 로컬 LLM을 활용하여 30초 이내 자연어 검색 응답을 제공하는 시스템을 설계했습니다.

**핵심 설계 원칙:**
- **안전 우선:** CLAUDE.md 보안 규칙 준수, 문서 권한 철저히 검증
- **성능 목표:** 응답 시간 P95 < 30초, 동시 사용자 100명 지원
- **확장 가능:** Phase별 단계적 확장 (Standalone → Cluster)
- **운영 가능:** 로컬 개발 환경과 프로덕션 환경 일관성

---

## 2. System Context

### 2.1 System Context Diagram

```mermaid
graph TB
    User[사용자<br/>전사 구성원] -->|검색 요청| WebUI[Web UI<br/>Next.js 14]
    WebUI -->|API 호출| API[API Gateway<br/>FastAPI]

    API -->|인증 확인| SSO[사내 SSO<br/>인증 시스템]
    API -->|검색 실행| RAG[RAG Service<br/>검색/답변 생성]
    API -->|문서 처리| DocProc[Document Processor<br/>문서 파싱/벡터화]

    RAG -->|벡터 검색| Milvus[(Milvus<br/>Vector DB)]
    RAG -->|메타데이터 조회| PG[(PostgreSQL<br/>Primary DB)]
    RAG -->|답변 생성| LLM[LLM API<br/>Ollama/OpenAI]

    DocProc -->|문서 가져오기| DocStore[문서 저장소<br/>SharePoint/Confluence]
    DocProc -->|벡터 저장| Milvus
    DocProc -->|메타데이터 저장| PG

    Admin[관리자] -->|문서 관리| DocProc

    style User fill:#e1f5ff
    style Admin fill:#ffe1e1
    style WebUI fill:#d4edda
    style API fill:#d4edda
    style RAG fill:#fff3cd
    style DocProc fill:#fff3cd
    style Milvus fill:#f8d7da
    style PG fill:#f8d7da
    style LLM fill:#d1ecf1
    style SSO fill:#e2e3e5
    style DocStore fill:#e2e3e5
```

### 2.2 External Dependencies

| 외부 시스템 | 역할 | 인터페이스 | 의존성 수준 |
|------------|------|-----------|------------|
| **사내 SSO** | 사용자 인증 | OAuth 2.0 / SAML | 높음 (필수) |
| **문서 저장소** | 원본 문서 제공 | REST API | 높음 (필수) |
| **Ollama** | LLM 답변 생성 | HTTP API | 높음 (대체 가능) |
| **OpenAI** | LLM 답변 생성 (선택) | REST API | 낮음 (선택적) |

---

## 3. High-Level Architecture

### 3.1 Layered Architecture

```mermaid
graph TB
    subgraph "Presentation Layer"
        UI[Next.js 14 Web UI<br/>TypeScript + Tailwind CSS]
    end

    subgraph "API Layer"
        Gateway[API Gateway<br/>FastAPI]
        Auth[Authentication Middleware<br/>JWT/SSO]
    end

    subgraph "Application Layer"
        SearchSvc[Search Service<br/>검색 쿼리 처리]
        RAGSvc[RAG Service<br/>답변 생성]
        DocSvc[Document Service<br/>문서 관리]
        UserSvc[User Service<br/>사용자/권한 관리]
    end

    subgraph "Domain Layer"
        SearchDomain[Search Domain<br/>검색 비즈니스 로직]
        DocDomain[Document Domain<br/>문서 처리 로직]
        RAGDomain[RAG Domain<br/>RAG 파이프라인]
    end

    subgraph "Infrastructure Layer"
        PGRepo[PostgreSQL Repository<br/>메타데이터 저장]
        MilvusRepo[Milvus Repository<br/>벡터 저장/검색]
        LLMClient[LLM Client<br/>Ollama/OpenAI]
        DocParser[Document Parser<br/>파싱 라이브러리]
    end

    subgraph "Data Layer"
        PG[(PostgreSQL 15<br/>Primary DB)]
        Milvus[(Milvus Standalone<br/>Vector DB)]
    end

    UI --> Gateway
    Gateway --> Auth
    Auth --> SearchSvc
    Auth --> DocSvc
    Auth --> UserSvc

    SearchSvc --> SearchDomain
    DocSvc --> DocDomain
    SearchDomain --> RAGDomain

    RAGDomain --> RAGSvc
    RAGSvc --> MilvusRepo
    RAGSvc --> PGRepo
    RAGSvc --> LLMClient

    DocDomain --> DocParser
    DocDomain --> MilvusRepo
    DocDomain --> PGRepo

    MilvusRepo --> Milvus
    PGRepo --> PG

    style UI fill:#d4edda
    style Gateway fill:#d4edda
    style SearchSvc fill:#fff3cd
    style RAGSvc fill:#fff3cd
    style DocSvc fill:#fff3cd
    style PG fill:#f8d7da
    style Milvus fill:#f8d7da
```

### 3.2 Technology Stack Mapping

| Layer | Component | Technology | Rationale |
|-------|-----------|------------|-----------|
| **Presentation** | Web UI | Next.js 14, TypeScript, Tailwind CSS | SSR/SSG, React 생태계, 빠른 개발 |
| **API** | API Gateway | FastAPI | 비동기 지원, 자동 문서화, 고성능 |
| **Application** | Services | Python 3.11 | RAG 생태계 최강, LangChain 지원 |
| **Domain** | Business Logic | Python + LangChain | RAG 파이프라인 구축 최적 |
| **Infrastructure** | Vector DB | Milvus Standalone | 고성능 벡터 검색, 오픈소스 |
| **Infrastructure** | Primary DB | PostgreSQL 15 | ACID 보장, JSON 지원, 성숙한 생태계 |
| **Infrastructure** | LLM | Ollama (llama3) | 무료, 로컬 실행, 데이터 프라이버시 |
| **Infrastructure** | Document Parser | pypdf, python-docx, pdfplumber | Python 문서 파싱 표준 |

---

## 4. Component Architecture

### 4.1 Frontend (Next.js 14)

```mermaid
graph TB
    subgraph "Next.js 14 App Router"
        Pages[Pages<br/>app/]
        Components[Components<br/>components/]
        Layouts[Layouts<br/>app/layout.tsx]

        subgraph "State Management"
            ReactQuery[React Query<br/>서버 상태]
            Zustand[Zustand<br/>클라이언트 상태]
        end

        subgraph "API Integration"
            ApiClient[API Client<br/>axios]
            AuthProvider[Auth Provider<br/>SSO 연동]
        end

        subgraph "UI Components"
            SearchBar[SearchBar<br/>검색 입력]
            SearchResults[SearchResults<br/>결과 표시]
            DocumentViewer[DocumentViewer<br/>문서 뷰어]
            FeedbackForm[FeedbackForm<br/>만족도 평가]
        end
    end

    Pages --> Components
    Pages --> Layouts
    Components --> ReactQuery
    Components --> Zustand
    ApiClient --> ReactQuery
    AuthProvider --> ApiClient

    SearchBar -.-> Components
    SearchResults -.-> Components
    DocumentViewer -.-> Components
    FeedbackForm -.-> Components

    style ReactQuery fill:#d1ecf1
    style Zustand fill:#d1ecf1
```

**주요 책임:**
- 사용자 검색 인터페이스 제공
- 검색 결과 및 출처 표시
- 검색 히스토리 관리
- 사용자 피드백 수집
- SSO 인증 처리

**주요 페이지:**
- `/` - 홈/검색 페이지
- `/search` - 검색 결과 페이지
- `/history` - 검색 히스토리
- `/document/[id]` - 문서 상세 보기

**State Management:**
- **React Query**: 검색 결과, 문서 데이터 (서버 상태, 캐싱)
- **Zustand**: UI 상태 (검색어, 필터, 모달 등)

---

### 4.2 Backend API (FastAPI)

```mermaid
graph TB
    subgraph "FastAPI Application"
        Router[API Router<br/>routers/]
        Middleware[Middleware<br/>auth, logging, CORS]

        subgraph "API Endpoints"
            SearchAPI[Search API<br/>/api/v1/search]
            DocAPI[Document API<br/>/api/v1/documents]
            UserAPI[User API<br/>/api/v1/users]
            FeedbackAPI[Feedback API<br/>/api/v1/feedback]
        end

        subgraph "Services"
            SearchSvc[Search Service]
            RAGSvc[RAG Service]
            DocSvc[Document Service]
            AuthSvc[Auth Service]
        end

        subgraph "Dependencies"
            DBSession[DB Session<br/>SQLAlchemy]
            MilvusClient[Milvus Client]
            LLMClient[LLM Client]
        end
    end

    Router --> Middleware
    Middleware --> SearchAPI
    Middleware --> DocAPI
    Middleware --> UserAPI
    Middleware --> FeedbackAPI

    SearchAPI --> SearchSvc
    SearchAPI --> RAGSvc
    DocAPI --> DocSvc
    UserAPI --> AuthSvc
    FeedbackAPI --> SearchSvc

    SearchSvc --> DBSession
    SearchSvc --> MilvusClient
    RAGSvc --> MilvusClient
    RAGSvc --> LLMClient
    DocSvc --> DBSession

    style SearchAPI fill:#d4edda
    style DocAPI fill:#d4edda
    style SearchSvc fill:#fff3cd
    style RAGSvc fill:#fff3cd
```

**주요 책임:**
- RESTful API 제공
- 요청 검증 (Pydantic)
- 인증/권한 확인
- 비즈니스 로직 조율
- 에러 핸들링

**코드 구조:**
```
backend/
├── app/
│   ├── main.py              # FastAPI 앱 진입점
│   ├── config.py            # 설정 (LLM Provider 전환)
│   ├── routers/             # API 라우터
│   │   ├── search.py        # 검색 API
│   │   ├── documents.py     # 문서 API
│   │   ├── users.py         # 사용자 API
│   │   └── feedback.py      # 피드백 API
│   ├── services/            # 비즈니스 로직
│   │   ├── search_service.py
│   │   ├── rag_service.py
│   │   ├── document_service.py
│   │   └── auth_service.py
│   ├── models/              # SQLAlchemy 모델
│   ├── schemas/             # Pydantic 스키마
│   ├── repositories/        # DB 접근 계층
│   └── utils/               # 유틸리티
└── tests/
```

---

### 4.3 RAG Service

```mermaid
graph TB
    subgraph "RAG Service"
        QueryProcessor[Query Processor<br/>전처리]
        VectorSearch[Vector Search<br/>유사도 검색]
        ContextBuilder[Context Builder<br/>컨텍스트 구성]
        AnswerGenerator[Answer Generator<br/>답변 생성]
        SourceTracker[Source Tracker<br/>출처 추적]
    end

    Query[사용자 질문] --> QueryProcessor
    QueryProcessor -->|임베딩| VectorSearch
    VectorSearch -->|상위 N개 청크| ContextBuilder
    ContextBuilder -->|프롬프트 구성| AnswerGenerator
    AnswerGenerator -->|답변 + 출처| SourceTracker
    SourceTracker -->|최종 응답| Response[검색 응답]

    VectorSearch -.->|벡터 검색| Milvus[(Milvus)]
    VectorSearch -.->|메타데이터| PG[(PostgreSQL)]
    AnswerGenerator -.->|LLM 호출| LLM[Ollama/OpenAI]

    style QueryProcessor fill:#fff3cd
    style VectorSearch fill:#fff3cd
    style AnswerGenerator fill:#d1ecf1
```

**RAG 파이프라인 (LangChain):**

```python
# 의사 코드
def search_and_generate_answer(query: str, user_id: str) -> SearchResponse:
    # 1. 쿼리 전처리
    processed_query = preprocess_query(query)  # 검증, 정규화

    # 2. 쿼리 임베딩
    query_embedding = embeddings.embed_query(processed_query)

    # 3. 벡터 검색 (Milvus)
    search_results = milvus.search(
        collection_name="documents",
        data=[query_embedding],
        limit=5,  # 상위 5개
        filter=f"access_level <= {user.access_level}"  # 권한 필터
    )

    # 4. 컨텍스트 구성
    context = build_context(search_results)  # 청크 텍스트 조합

    # 5. 프롬프트 생성
    prompt = f"""
    다음 문서를 참고하여 질문에 답변하세요.

    문서:
    {context}

    질문: {query}

    답변 시 반드시 출처를 명시하세요.
    """

    # 6. LLM 답변 생성
    answer = llm.invoke(prompt)

    # 7. 출처 추적
    sources = extract_sources(search_results)

    # 8. 응답 반환
    return SearchResponse(
        answer=answer,
        sources=sources,
        relevance_scores=[hit.score for hit in search_results]
    )
```

**Hallucination 방지:**
- 반드시 검색된 문서만 사용
- 출처 없는 답변 금지
- Confidence score < 0.5 시 "답변을 찾을 수 없습니다" 반환
- 프롬프트에 "문서에 없는 내용은 답하지 마세요" 명시

---

### 4.4 Document Processor

```mermaid
graph TB
    subgraph "Document Processor"
        Collector[Document Collector<br/>문서 수집]
        Parser[Document Parser<br/>파싱]
        Chunker[Text Chunker<br/>청크 분할]
        Embedder[Embedder<br/>벡터화]
        Indexer[Indexer<br/>인덱싱]
    end

    DocStore[문서 저장소] -->|문서 가져오기| Collector
    Collector -->|원본 파일| Parser
    Parser -->|텍스트 추출| Chunker
    Chunker -->|청크 리스트| Embedder
    Embedder -->|임베딩| Indexer

    Indexer -->|벡터 저장| Milvus[(Milvus)]
    Indexer -->|메타데이터 저장| PG[(PostgreSQL)]

    style Parser fill:#fff3cd
    style Chunker fill:#fff3cd
    style Embedder fill:#d1ecf1
```

**문서 처리 파이프라인:**

```python
# 의사 코드
def process_document(file_path: str, metadata: dict):
    # 1. 문서 파싱
    if file_path.endswith('.pdf'):
        text = parse_pdf(file_path)
    elif file_path.endswith('.docx'):
        text = parse_docx(file_path)
    elif file_path.endswith('.txt'):
        text = read_text(file_path)
    elif file_path.endswith('.md'):
        text = parse_markdown(file_path)

    # 2. 청크 분할 (RecursiveCharacterTextSplitter)
    chunks = text_splitter.split_text(
        text,
        chunk_size=500,      # 토큰 제한 고려
        chunk_overlap=50     # 컨텍스트 유지
    )

    # 3. 임베딩 생성
    embeddings = embedder.embed_documents(chunks)

    # 4. Milvus에 저장
    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        milvus.insert({
            "id": f"{document_id}_{i}",
            "document_id": document_id,
            "content": chunk,
            "embedding": embedding,
            "chunk_index": i,
            "metadata": {
                "document_title": metadata['title'],
                "document_source": metadata['source'],
                "department": metadata['department'],
                "access_level": metadata['access_level']
            }
        })

    # 5. PostgreSQL에 메타데이터 저장
    db.insert(Document(
        id=document_id,
        title=metadata['title'],
        source=file_path,
        document_type=get_file_type(file_path),
        department=metadata['department'],
        access_level=metadata['access_level']
    ))
```

**지원 문서 형식:**
- PDF: `pypdf` 또는 `pdfplumber`
- DOCX: `python-docx`
- TXT: 기본 파일 읽기
- Markdown: 기본 파일 읽기 (향후 구조화 파싱)

**청크 분할 전략:**
- 기본 크기: 500자 (토큰 약 125개)
- Overlap: 50자 (문맥 유지)
- 분할 기준: 문장 경계 우선 (RecursiveCharacterTextSplitter)

---

### 4.5 Database Architecture

#### 4.5.1 PostgreSQL (Primary DB)

**역할:**
- 문서 메타데이터 저장
- 사용자 정보 및 인증
- 검색 히스토리
- 사용자 피드백
- 문서 접근 권한

**장점:**
- ACID 트랜잭션 보장
- JSON/JSONB로 유연한 메타데이터 저장
- 성숙한 생태계 (SQLAlchemy, Alembic)
- pgvector 확장으로 하이브리드 검색 가능 (향후)

#### 4.5.2 Milvus (Vector DB)

**역할:**
- 문서 청크 임베딩 저장
- 벡터 유사도 검색 (ANN Search)
- 메타데이터 필터링

**장점:**
- 고성능 벡터 검색 (HNSW, IVF 인덱스)
- 메타데이터 필터링 지원
- LangChain 완벽 통합
- Standalone → Cluster 확장 경로

**Collection Schema:**
```python
{
    "collection_name": "documents",
    "fields": [
        {"name": "id", "type": "VARCHAR", "max_length": 255, "is_primary": True},
        {"name": "document_id", "type": "VARCHAR", "max_length": 255},
        {"name": "content", "type": "VARCHAR", "max_length": 5000},
        {"name": "embedding", "type": "FLOAT_VECTOR", "dim": 768},  # nomic-embed-text
        {"name": "chunk_index", "type": "INT64"},
        {"name": "document_title", "type": "VARCHAR", "max_length": 500},
        {"name": "document_source", "type": "VARCHAR", "max_length": 1000},
        {"name": "department", "type": "VARCHAR", "max_length": 100},
        {"name": "access_level", "type": "INT64"}
    ],
    "index_params": {
        "metric_type": "COSINE",
        "index_type": "HNSW",
        "params": {"M": 16, "efConstruction": 256}
    }
}
```

---

## 5. Data Flow

### 5.1 Search Flow (검색 흐름)

```mermaid
sequenceDiagram
    participant User as 사용자
    participant UI as Next.js UI
    participant API as FastAPI
    participant Auth as Auth Service
    participant Search as Search Service
    participant RAG as RAG Service
    participant Milvus as Milvus
    participant PG as PostgreSQL
    participant LLM as Ollama/OpenAI

    User->>UI: 검색 질문 입력
    UI->>API: POST /api/v1/search
    API->>Auth: 토큰 검증
    Auth-->>API: 사용자 정보

    API->>Search: search(query, user_id)
    Search->>RAG: generate_answer(query, user)

    RAG->>RAG: 쿼리 전처리
    RAG->>RAG: 쿼리 임베딩

    RAG->>Milvus: vector_search(embedding, filter)
    Milvus-->>RAG: 상위 5개 청크

    RAG->>PG: get_documents_metadata(doc_ids)
    PG-->>RAG: 메타데이터 (제목, 출처 등)

    RAG->>RAG: 컨텍스트 구성
    RAG->>LLM: generate(prompt + context)
    LLM-->>RAG: 답변 텍스트

    RAG->>RAG: 출처 추적
    RAG-->>Search: SearchResponse

    Search->>PG: save_search_history()
    Search-->>API: 검색 결과

    API-->>UI: JSON Response
    UI-->>User: 답변 + 출처 표시
```

**Performance SLA:**
- 전체 응답 시간: P95 < 30초
- 벡터 검색: < 1초
- LLM 응답: < 25초 (타임아웃 30초)
- 메타데이터 조회: < 0.5초

**Error Handling:**
- LLM 타임아웃 → Fallback: 검색 결과만 반환
- 벡터 검색 실패 → 에러 메시지 + 재시도
- 권한 없는 문서 → 결과에서 제외

---

### 5.2 Document Indexing Flow (문서 인덱싱 흐름)

```mermaid
sequenceDiagram
    participant Admin as 관리자
    participant Scheduler as Batch Scheduler
    participant DocProc as Document Processor
    participant DocStore as 문서 저장소
    participant Parser as Document Parser
    participant Milvus as Milvus
    participant PG as PostgreSQL

    Admin->>Scheduler: 수동 트리거 또는 스케줄
    Scheduler->>DocProc: start_indexing()

    DocProc->>DocStore: fetch_new_documents()
    DocStore-->>DocProc: 문서 리스트

    loop 각 문서
        DocProc->>Parser: parse(file_path, file_type)
        Parser-->>DocProc: 텍스트 추출

        DocProc->>DocProc: text_chunking(text)
        DocProc->>DocProc: embed_chunks(chunks)

        DocProc->>Milvus: insert_vectors(chunks + embeddings)
        Milvus-->>DocProc: 저장 완료

        DocProc->>PG: insert_document_metadata()
        PG-->>DocProc: 저장 완료
    end

    DocProc-->>Scheduler: 인덱싱 완료 (성공/실패)
    Scheduler-->>Admin: 결과 리포트
```

**Batch Schedule:**
- 기본: 일 1회 (새벽 2시)
- 우선순위 문서: 4시간마다
- 수동 트리거 지원 (관리자)

**Indexing Performance:**
- 처리 속도: 100 페이지/분 (PDF 기준)
- 병렬 처리: 5개 문서 동시 처리
- 실패 시 재시도: 3회 (exponential backoff)

---

## 6. API Design

### 6.1 API Endpoints

#### 6.1.1 Search API

**POST /api/v1/search**

자연어 검색 요청

**Request:**
```json
{
  "query": "연차 사용 방법",
  "user_id": "user-uuid",
  "limit": 5,
  "session_id": "session-uuid"
}
```

**Response:**
```json
{
  "query_id": "query-uuid",
  "query": "연차 사용 방법",
  "answer": "연차는 다음과 같이 사용합니다...",
  "sources": [
    {
      "document_id": "doc-uuid-1",
      "document_title": "인사 규정",
      "document_source": "https://internal/docs/hr-policy.pdf",
      "chunk_content": "연차 사용 시에는...",
      "page_number": 5,
      "relevance_score": 0.92
    }
  ],
  "response_time_ms": 2500,
  "timestamp": "2025-12-30T10:00:00Z"
}
```

**Validation:**
- `query`: 5-200자
- `user_id`: 필수, UUID 형식
- `limit`: 1-10 (기본 5)

**Error Codes:**
- 400: 잘못된 요청 (쿼리 길이 초과 등)
- 401: 인증 실패
- 404: 답변을 찾을 수 없음
- 500: 서버 오류 (LLM 장애 등)
- 504: 타임아웃 (30초 초과)

---

#### 6.1.2 Document API

**GET /api/v1/documents/{document_id}**

문서 메타데이터 조회

**Response:**
```json
{
  "id": "doc-uuid",
  "title": "인사 규정",
  "source": "https://internal/docs/hr-policy.pdf",
  "document_type": "pdf",
  "metadata": {
    "department": "HR",
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-12-01T00:00:00Z",
    "access_level": "L2",
    "tags": ["HR", "Policy"]
  }
}
```

**POST /api/v1/documents**

문서 업로드 (관리자용)

**Request (multipart/form-data):**
```
file: [binary]
metadata: {
  "title": "신규 정책",
  "department": "HR",
  "access_level": "L2"
}
```

**Response:**
```json
{
  "document_id": "doc-uuid",
  "status": "processing",
  "message": "문서 인덱싱이 시작되었습니다."
}
```

---

#### 6.1.3 Feedback API

**POST /api/v1/feedback**

검색 결과 만족도 평가

**Request:**
```json
{
  "query_id": "query-uuid",
  "user_id": "user-uuid",
  "rating": 4,
  "comment": "정확한 답변이었습니다."
}
```

**Response:**
```json
{
  "feedback_id": "feedback-uuid",
  "message": "피드백이 저장되었습니다."
}
```

---

#### 6.1.4 User API

**GET /api/v1/users/me**

현재 사용자 정보 조회

**Response:**
```json
{
  "user_id": "user-uuid",
  "email": "user@company.com",
  "department": "Engineering",
  "access_level": "L2",
  "created_at": "2025-01-01T00:00:00Z"
}
```

**GET /api/v1/users/me/history**

검색 히스토리 조회

**Response:**
```json
{
  "history": [
    {
      "query_id": "query-uuid",
      "query": "연차 사용 방법",
      "timestamp": "2025-12-30T10:00:00Z",
      "rating": 4
    }
  ],
  "total": 50,
  "page": 1,
  "page_size": 20
}
```

---

### 6.2 API Versioning

- **Current Version:** v1
- **Base URL:** `/api/v1`
- **Future Versions:** v2 (하위 호환성 유지)

---

## 7. Database Schema

### 7.1 PostgreSQL Schema

```sql
-- Users Table (사용자)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    department VARCHAR(100),
    access_level VARCHAR(10) NOT NULL DEFAULT 'L1',  -- L1, L2, L3
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);

-- Documents Table (문서 메타데이터)
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    source VARCHAR(1000) NOT NULL,  -- 원본 경로/URL
    document_type VARCHAR(50) NOT NULL,  -- pdf, docx, txt, markdown
    metadata JSONB,  -- 유연한 메타데이터 저장
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    indexed_at TIMESTAMP,  -- 마지막 인덱싱 시간

    -- 메타데이터 예시:
    -- {
    --   "department": "HR",
    --   "access_level": "L2",
    --   "tags": ["policy", "hr"],
    --   "page_count": 10,
    --   "file_size_bytes": 1024000
    -- }
);

CREATE INDEX idx_documents_type ON documents(document_type);
CREATE INDEX idx_documents_metadata ON documents USING GIN(metadata);

-- Search Queries Table (검색 히스토리)
CREATE TABLE search_queries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    query TEXT NOT NULL,
    session_id UUID,
    timestamp TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_search_queries_user_id ON search_queries(user_id);
CREATE INDEX idx_search_queries_timestamp ON search_queries(timestamp);

-- Search Responses Table (검색 응답)
CREATE TABLE search_responses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query_id UUID REFERENCES search_queries(id) ON DELETE CASCADE,
    answer TEXT NOT NULL,
    sources JSONB NOT NULL,  -- 출처 문서 리스트
    relevance_scores JSONB,  -- 관련도 점수
    response_time_ms INTEGER,
    timestamp TIMESTAMP DEFAULT NOW(),

    -- sources 예시:
    -- [
    --   {
    --     "document_id": "doc-uuid",
    --     "document_title": "인사 규정",
    --     "chunk_content": "...",
    --     "relevance_score": 0.92
    --   }
    -- ]
);

CREATE INDEX idx_search_responses_query_id ON search_responses(query_id);

-- User Feedback Table (사용자 피드백)
CREATE TABLE user_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query_id UUID REFERENCES search_queries(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    comment TEXT,
    timestamp TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_user_feedback_query_id ON user_feedback(query_id);
CREATE INDEX idx_user_feedback_user_id ON user_feedback(user_id);
CREATE INDEX idx_user_feedback_rating ON user_feedback(rating);
```

**데이터 보관 정책:**
- `search_queries`, `search_responses`: 90일 (감사 목적)
- `user_feedback`: 1년
- `documents`: 영구 보관 (삭제 시 soft delete)

---

### 7.2 Milvus Collection Schema

```python
from pymilvus import CollectionSchema, FieldSchema, DataType

# Collection: documents
fields = [
    FieldSchema(name="id", dtype=DataType.VARCHAR, max_length=255, is_primary=True),
    FieldSchema(name="document_id", dtype=DataType.VARCHAR, max_length=255),
    FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=5000),
    FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=768),  # nomic-embed-text
    FieldSchema(name="chunk_index", dtype=DataType.INT64),
    FieldSchema(name="document_title", dtype=DataType.VARCHAR, max_length=500),
    FieldSchema(name="document_source", dtype=DataType.VARCHAR, max_length=1000),
    FieldSchema(name="department", dtype=DataType.VARCHAR, max_length=100),
    FieldSchema(name="access_level", dtype=DataType.INT64),  # 1, 2, 3
]

schema = CollectionSchema(
    fields=fields,
    description="Document chunks with embeddings"
)

# Index: HNSW (Hierarchical Navigable Small World)
index_params = {
    "metric_type": "COSINE",      # 코사인 유사도
    "index_type": "HNSW",         # 고성능 ANN 알고리즘
    "params": {
        "M": 16,                  # 연결 수 (높을수록 정확, 느림)
        "efConstruction": 256     # 구축 시 탐색 범위
    }
}

# Search params
search_params = {
    "metric_type": "COSINE",
    "params": {
        "ef": 64                  # 검색 시 탐색 범위
    }
}
```

**임베딩 차원:**
- Ollama `nomic-embed-text`: 768차원
- OpenAI `text-embedding-3-small`: 1536차원 (전환 시 재인덱싱 필요)

**메타데이터 필터링 예시:**
```python
# 특정 부서 + 접근 권한 레벨 이하만 검색
filter_expr = f"department == 'HR' and access_level <= 2"
results = collection.search(
    data=[query_embedding],
    anns_field="embedding",
    param=search_params,
    limit=5,
    expr=filter_expr
)
```

---

## 8. Deployment Architecture

### 8.1 Development Environment (Docker Compose)

```mermaid
graph TB
    subgraph "Docker Compose (로컬 개발)"
        Frontend[Next.js Container<br/>Port: 3000]
        Backend[FastAPI Container<br/>Port: 8000]

        PG[PostgreSQL Container<br/>Port: 5432]
        MilvusStandalone[Milvus Standalone<br/>Port: 19530]
        Etcd[Etcd<br/>Milvus 메타데이터]
        MinIO[MinIO<br/>Milvus 스토리지]

        Ollama[Ollama Container<br/>Port: 11434]

        Attu[Attu Web UI<br/>Port: 8080<br/>Milvus 관리]
    end

    Frontend --> Backend
    Backend --> PG
    Backend --> MilvusStandalone
    Backend --> Ollama

    MilvusStandalone --> Etcd
    MilvusStandalone --> MinIO

    Attu --> MilvusStandalone

    style Frontend fill:#d4edda
    style Backend fill:#d4edda
    style PG fill:#f8d7da
    style MilvusStandalone fill:#f8d7da
    style Ollama fill:#d1ecf1
```

**docker-compose.yml 구성:**

```yaml
version: '3.8'

services:
  # PostgreSQL
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: rag_platform
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  # Milvus (Standalone)
  etcd:
    image: quay.io/coreos/etcd:v3.5.5
    environment:
      - ETCD_AUTO_COMPACTION_MODE=revision
      - ETCD_AUTO_COMPACTION_RETENTION=1000
    volumes:
      - etcd_data:/etcd

  minio:
    image: minio/minio:RELEASE.2023-03-20T20-16-18Z
    environment:
      MINIO_ACCESS_KEY: minioadmin
      MINIO_SECRET_KEY: minioadmin
    volumes:
      - minio_data:/minio_data
    command: minio server /minio_data

  milvus:
    image: milvusdb/milvus:v2.3.3
    environment:
      ETCD_ENDPOINTS: etcd:2379
      MINIO_ADDRESS: minio:9000
    ports:
      - "19530:19530"
      - "9091:9091"
    depends_on:
      - etcd
      - minio

  # Attu (Milvus Web UI)
  attu:
    image: zilliz/attu:v2.3
    environment:
      MILVUS_URL: milvus:19530
    ports:
      - "8080:3000"
    depends_on:
      - milvus

  # Ollama
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama

  # Backend (FastAPI)
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://postgres:postgres@postgres:5432/rag_platform
      MILVUS_HOST: milvus
      MILVUS_PORT: 19530
      LLM_PROVIDER: ollama
      OLLAMA_BASE_URL: http://ollama:11434
    depends_on:
      - postgres
      - milvus
      - ollama

  # Frontend (Next.js)
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:8000
    depends_on:
      - backend

volumes:
  postgres_data:
  etcd_data:
  minio_data:
  ollama_data:
```

**개발 환경 시작:**
```bash
# 모든 서비스 시작
docker-compose up -d

# Ollama 모델 다운로드
docker exec -it ollama ollama pull llama3
docker exec -it ollama ollama pull nomic-embed-text

# 서비스 확인
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/docs
- Attu (Milvus UI): http://localhost:8080
- PostgreSQL: localhost:5432
```

---

### 8.2 Production Environment (Future)

```mermaid
graph TB
    subgraph "Load Balancer"
        LB[Nginx/ALB]
    end

    subgraph "Application Tier"
        App1[FastAPI App 1]
        App2[FastAPI App 2]
        App3[FastAPI App 3]
    end

    subgraph "Frontend Tier"
        Next1[Next.js 1]
        Next2[Next.js 2]
    end

    subgraph "Database Tier"
        PGPrimary[(PostgreSQL Primary)]
        PGReplica1[(PostgreSQL Replica 1)]
        PGReplica2[(PostgreSQL Replica 2)]
    end

    subgraph "Vector DB Tier"
        MilvusCluster[Milvus Cluster<br/>Query Nodes]
        MilvusData[(Milvus Data Nodes)]
    end

    subgraph "LLM Tier"
        OllamaCluster[Ollama Cluster<br/>또는 OpenAI API]
    end

    LB --> Next1
    LB --> Next2
    Next1 --> App1
    Next1 --> App2
    Next2 --> App2
    Next2 --> App3

    App1 --> PGPrimary
    App2 --> PGReplica1
    App3 --> PGReplica2

    App1 --> MilvusCluster
    App2 --> MilvusCluster
    App3 --> MilvusCluster

    App1 --> OllamaCluster
    App2 --> OllamaCluster

    MilvusCluster --> MilvusData

    style LB fill:#e2e3e5
    style App1 fill:#d4edda
    style PGPrimary fill:#f8d7da
    style MilvusCluster fill:#f8d7da
```

**확장 계획:**
- **Phase 1 (현재):** Docker Compose Standalone
- **Phase 2:** Kubernetes 배포 (Frontend, Backend만)
- **Phase 3:** Milvus Cluster, PostgreSQL Replication
- **Phase 4:** Auto-scaling, CDN, Redis Cache

---

## 9. Security Architecture

### 9.1 Authentication Flow

```mermaid
sequenceDiagram
    participant User as 사용자
    participant UI as Next.js
    participant API as FastAPI
    participant SSO as 사내 SSO
    participant DB as PostgreSQL

    User->>UI: 로그인 버튼 클릭
    UI->>SSO: OAuth 2.0 인증 요청
    SSO-->>UI: 인증 코드
    UI->>API: POST /auth/callback (code)
    API->>SSO: 토큰 교환
    SSO-->>API: Access Token + User Info
    API->>DB: 사용자 정보 저장/업데이트
    API-->>UI: JWT Token
    UI->>UI: 토큰 저장 (httpOnly Cookie)
    UI-->>User: 로그인 완료
```

**JWT Payload:**
```json
{
  "sub": "user-uuid",
  "email": "user@company.com",
  "department": "Engineering",
  "access_level": "L2",
  "exp": 1735574400,
  "iat": 1735488000
}
```

**Token 관리:**
- Access Token: 1시간 유효
- Refresh Token: 7일 유효 (httpOnly Cookie)
- Rotation: Access Token 만료 시 자동 갱신

---

### 9.2 Authorization (접근 권한)

**접근 레벨:**
- **L1 (Public):** 전사 공개 문서 (모든 직원)
- **L2 (Internal):** 부서 내부 문서 (부서원만)
- **L3 (Confidential):** 기밀 문서 (임원진, 담당자만)

**권한 확인 로직:**
```python
def check_document_access(user: User, document: Document) -> bool:
    # 1. 접근 레벨 확인
    if user.access_level < document.access_level:
        return False

    # 2. 부서 확인 (L2 이상)
    if document.access_level >= 2:
        if document.department != user.department:
            # 예외: 경영지원팀은 모든 부서 접근 가능
            if user.department != "Management":
                return False

    return True
```

**벡터 검색 시 필터링:**
```python
# Milvus 검색 시 권한 필터 자동 적용
filter_expr = f"access_level <= {user.access_level}"

if user.department != "Management":
    filter_expr += f" and (department == '{user.department}' or access_level == 1)"

results = collection.search(
    data=[query_embedding],
    expr=filter_expr,
    limit=5
)
```

---

### 9.3 Security Measures

| 위협 | 대응 방안 | 구현 위치 |
|------|----------|----------|
| **SQL Injection** | SQLAlchemy ORM 사용, 파라미터화 쿼리 | Backend |
| **XSS** | React 자동 이스케이핑, CSP 헤더 | Frontend |
| **CSRF** | SameSite Cookie, CSRF 토큰 | Frontend + Backend |
| **민감 정보 노출** | 문서 접근 권한 검증, TLS 암호화 | Backend + Network |
| **API 남용** | Rate Limiting (100 req/min/user) | API Gateway |
| **LLM Prompt Injection** | 입력 검증, 프롬프트 샌드박싱 | RAG Service |
| **데이터 유출** | 접근 로그 기록, 감사 추적 | Backend + DB |

**CLAUDE.md 보안 규칙 준수:**
- ✅ No hardcoded secrets (환경 변수 사용)
- ✅ No real customer data in logs
- ✅ Access control for all documents
- ✅ TLS encryption in transit
- ✅ Audit logging (90일 보관)

---

## 10. Performance Considerations

### 10.1 Performance Targets

| Metric | Target | Strategy |
|--------|--------|----------|
| **검색 응답 시간 (P95)** | < 30초 | LLM 타임아웃, 비동기 처리, 캐싱 |
| **벡터 검색 시간** | < 1초 | HNSW 인덱스, Milvus 최적화 |
| **문서 인덱싱** | 100 페이지/분 | 병렬 처리 (5개 문서 동시) |
| **동시 사용자** | 100명 | Auto-scaling (Phase 3) |
| **가용성** | 99% | Health check, 자동 재시작 |

---

### 10.2 Performance Optimization

#### 10.2.1 LLM 최적화

```python
# 타임아웃 설정
llm = Ollama(
    model="llama3",
    timeout=30  # 30초 타임아웃
)

# Streaming 응답 (UX 개선)
for chunk in llm.stream(prompt):
    yield chunk  # 실시간 스트리밍

# Fallback 전략
try:
    answer = llm.invoke(prompt)
except TimeoutError:
    # Fallback: 검색 결과만 반환
    answer = "답변 생성에 실패했습니다. 아래 검색 결과를 참고하세요."
```

#### 10.2.2 벡터 검색 최적화

```python
# HNSW 인덱스 파라미터 튜닝
index_params = {
    "metric_type": "COSINE",
    "index_type": "HNSW",
    "params": {
        "M": 16,              # 연결 수 (정확도 ↑, 속도 ↓)
        "efConstruction": 256 # 구축 품질 (정확도 ↑, 구축 시간 ↑)
    }
}

search_params = {
    "metric_type": "COSINE",
    "params": {
        "ef": 64  # 검색 범위 (정확도 ↑, 속도 ↓)
    }
}

# 권장 설정 (P95 < 1초):
# - M: 8-16
# - efConstruction: 128-256
# - ef: 32-64
```

#### 10.2.3 Database 최적화

```sql
-- 자주 사용하는 쿼리 인덱스
CREATE INDEX idx_documents_metadata_department
ON documents ((metadata->>'department'));

CREATE INDEX idx_search_queries_user_timestamp
ON search_queries(user_id, timestamp DESC);

-- 쿼리 예시 (인덱스 활용)
SELECT * FROM documents
WHERE metadata->>'department' = 'HR'
AND metadata->>'access_level' <= '2';
```

#### 10.2.4 Caching Strategy (Phase 2)

```python
# Redis 캐싱 (향후 추가)
# - 자주 검색되는 쿼리 캐싱 (TTL: 1시간)
# - LLM 답변 캐싱 (동일 질문)
# - 문서 메타데이터 캐싱 (TTL: 10분)

cache_key = f"search:{hash(query)}"
cached = redis.get(cache_key)
if cached:
    return json.loads(cached)

result = search_and_generate_answer(query)
redis.setex(cache_key, 3600, json.dumps(result))
return result
```

---

## 11. Scalability & Future Extensions

### 11.1 Scalability Roadmap

#### Phase 1: Standalone (현재)
- Docker Compose
- Milvus Standalone
- PostgreSQL Single Instance
- Ollama Single Container
- 동시 사용자: ~100명

#### Phase 2: Horizontal Scaling (6개월 후)
- Kubernetes 배포
- FastAPI 앱 3개 인스턴스
- PostgreSQL Primary + 2 Replicas (Read 분산)
- Milvus Standalone → Cluster 전환
- 동시 사용자: ~500명

#### Phase 3: Full Cluster (1년 후)
- Milvus Cluster (Query Nodes 3개, Data Nodes 2개)
- PostgreSQL HA (Patroni + etcd)
- Redis Cache Layer
- Auto-scaling (CPU > 70% 시)
- 동시 사용자: ~2000명

#### Phase 4: Advanced Features (2년 후)
- 멀티모달 지원 (이미지, 표 검색)
- 다국어 지원 (영어, 중국어)
- 음성 입력 (STT)
- 하이브리드 검색 (키워드 + 벡터)
- Fine-tuned LLM (사내 데이터)

---

### 11.2 Milvus Standalone → Cluster Migration

```mermaid
graph LR
    subgraph "Standalone (Phase 1)"
        MS[Milvus Standalone]
        Etcd1[Etcd]
        MinIO1[MinIO]
    end

    subgraph "Cluster (Phase 2)"
        Root[Root Coordinator]
        Query1[Query Node 1]
        Query2[Query Node 2]
        Data1[Data Node 1]
        Data2[Data Node 2]
        Index[Index Node]
        Proxy[Proxy]

        Etcd2[Etcd Cluster]
        S3[S3 / MinIO]
    end

    MS -->|Migration| Root
    Etcd1 -->|Migration| Etcd2
    MinIO1 -->|Migration| S3

    Root --> Query1
    Root --> Query2
    Root --> Data1
    Root --> Data2
    Root --> Index
    Proxy --> Query1
    Proxy --> Query2

    style MS fill:#f8d7da
    style Root fill:#d4edda
```

**마이그레이션 계획:**
1. 데이터 백업 (MinIO → S3)
2. Milvus Cluster 배포 (Kubernetes)
3. 데이터 복원 및 재인덱싱
4. DNS 전환 (Standalone → Cluster)
5. 성능 검증 (벡터 검색 < 1초 유지)

---

### 11.3 Future Architecture (Phase 4)

```mermaid
graph TB
    subgraph "Multi-Region"
        LB[Global Load Balancer]
        CDN[CDN<br/>Static Assets]

        subgraph "Region A"
            AppA[App Cluster A]
            DBA[(DB Primary)]
            MilvusA[(Milvus Cluster A)]
        end

        subgraph "Region B"
            AppB[App Cluster B]
            DBB[(DB Replica)]
            MilvusB[(Milvus Cluster B)]
        end
    end

    LB --> CDN
    LB --> AppA
    LB --> AppB

    AppA --> DBA
    AppA --> MilvusA
    AppB --> DBB
    AppB --> MilvusB

    DBA -.->|Replication| DBB
    MilvusA -.->|Sync| MilvusB

    style LB fill:#e2e3e5
    style CDN fill:#d1ecf1
```

---

## 12. Technology Mapping (PRD → Architecture)

### 12.1 Functional Requirements Mapping

| PRD Requirement | Component | Technology | Implementation |
|-----------------|-----------|------------|----------------|
| **FR-1: 자연어 검색** | Search Service | FastAPI + LangChain | POST /api/v1/search |
| **FR-2: RAG 답변 생성** | RAG Service | Ollama + Milvus | LangChain RAG 파이프라인 |
| **FR-3: 문서 인덱싱** | Document Processor | pypdf + python-docx | Batch 스케줄러 (일 1회) |
| **FR-4: 인증/권한** | Auth Service | FastAPI Middleware | SSO 연동 + JWT |

### 12.2 Non-Functional Requirements Mapping

| NFR | Target | Component | Strategy |
|-----|--------|-----------|----------|
| **응답 시간 P95 < 30초** | RAG Service | LLM 타임아웃 30초, HNSW 인덱스 |
| **동시 사용자 100명** | FastAPI | 비동기 처리, Connection Pool |
| **가용성 99%** | All | Health check, Auto-restart |
| **보안 (SSO)** | Auth Service | OAuth 2.0 + JWT |
| **보안 (권한)** | RAG Service | 문서 레벨 접근 제어 |

---

## 13. Development Guidelines

### 13.1 Code Structure

```
rag-platform/
├── frontend/               # Next.js 14
│   ├── app/               # App Router
│   │   ├── layout.tsx
│   │   ├── page.tsx       # 홈/검색
│   │   ├── search/
│   │   ├── history/
│   │   └── document/
│   ├── components/
│   │   ├── SearchBar.tsx
│   │   ├── SearchResults.tsx
│   │   └── DocumentViewer.tsx
│   ├── lib/
│   │   ├── api-client.ts  # axios
│   │   └── auth.ts
│   └── store/             # Zustand
│
├── backend/               # FastAPI
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── routers/
│   │   │   ├── search.py
│   │   │   ├── documents.py
│   │   │   └── users.py
│   │   ├── services/
│   │   │   ├── search_service.py
│   │   │   ├── rag_service.py
│   │   │   └── document_service.py
│   │   ├── models/        # SQLAlchemy
│   │   ├── schemas/       # Pydantic
│   │   ├── repositories/
│   │   └── utils/
│   └── tests/
│
├── docs/
│   ├── prd/
│   ├── tech-stack/
│   └── architecture/      # 본 문서
│
├── docker-compose.yml
└── README.md
```

---

### 13.2 Coding Standards

**Backend (Python):**
- PEP 8 스타일 가이드
- Type hints 필수 (`def search(query: str) -> SearchResponse:`)
- Docstrings (Google Style)
- FastAPI Dependency Injection 활용
- Pydantic으로 검증

**Frontend (TypeScript):**
- ESLint + Prettier
- React Functional Components (Hooks)
- TypeScript strict mode
- Tailwind CSS 유틸리티 클래스
- 컴포넌트별 파일 분리

**Testing:**
- Unit Tests: pytest (Backend), Jest (Frontend)
- Integration Tests: pytest + TestClient
- E2E Tests: Playwright (추후)
- Coverage: 80% 이상 목표

---

## 14. Monitoring & Observability (Phase 2)

### 14.1 Metrics

**Application Metrics (Prometheus):**
- `search_request_duration_seconds` (P50, P95, P99)
- `search_request_total` (총 검색 수)
- `llm_api_call_duration_seconds`
- `vector_search_duration_seconds`
- `document_indexing_total`

**System Metrics:**
- CPU, Memory, Disk Usage
- Database Connection Pool
- Milvus Query Latency

**Business Metrics:**
- DAU (Daily Active Users)
- 평균 만족도 (1-5점)
- 재검색률

---

### 14.2 Logging

**Structured Logging (JSON):**
```python
import structlog

logger = structlog.get_logger()

logger.info(
    "search_request",
    user_id=user.id,
    query=query,
    response_time_ms=response_time,
    sources_count=len(sources)
)
```

**Log Levels:**
- ERROR: LLM 호출 실패, DB 연결 오류
- WARNING: 응답 시간 > 25초, confidence < 0.5
- INFO: 모든 검색 요청, 문서 인덱싱
- DEBUG: 상세 디버깅 (개발 환경만)

**로그 보관:**
- 검색 로그: 90일 (감사 목적)
- 에러 로그: 1년
- 개인정보 최소화 (이메일 마스킹)

---

### 14.3 Alerting

**Critical Alerts (즉시 알림):**
- 시스템 다운 (Health check 실패)
- 에러율 > 10%
- DB 연결 실패

**Warning Alerts:**
- 응답 시간 P95 > 35초
- 에러율 > 5%
- Disk 사용량 > 80%

---

## 15. Disaster Recovery

### 15.1 Backup Strategy

**PostgreSQL:**
- Full Backup: 일 1회 (새벽 3시)
- WAL Archiving: 실시간 (PITR 지원)
- 보관 기간: 30일

**Milvus:**
- Collection Snapshot: 주 1회
- MinIO 데이터 백업: 일 1회
- 보관 기간: 30일

**Recovery Time Objective (RTO):** 4시간
**Recovery Point Objective (RPO):** 24시간

---

### 15.2 Failure Scenarios

| Scenario | Impact | Recovery Strategy |
|----------|--------|-------------------|
| **PostgreSQL 장애** | 검색 불가 | Replica 승격 (30분) |
| **Milvus 장애** | 검색 불가 | 재시작, 백업 복원 (2시간) |
| **LLM API 장애** | 답변 생성 불가 | Fallback: 검색 결과만 표시 |
| **Frontend 장애** | UI 접근 불가 | 재배포 (10분) |
| **Network 장애** | 전체 서비스 중단 | ISP 복구 대기 |

---

## 16. Change Log

| Date | Version | Author | Changes |
|------|---------|--------|---------|
| 2025-12-30 | 1.0.0 | Architecture Designer | Initial architecture design |

---

## 17. Approval

- [ ] Technical Lead
- [ ] Backend Team
- [ ] Frontend Team
- [ ] Infrastructure Team
- [ ] Security Team

**Review Deadline:** 2026-01-15
**Implementation Start:** After approval

---

## 18. References

- **PRD**: [docs/prd/rag-platform-prd.md](../prd/rag-platform-prd.md)
- **Tech Stack**: [docs/tech-stack/tech-stack.md](../tech-stack/tech-stack.md)
- **LangChain Docs**: https://python.langchain.com/docs/get_started/introduction
- **Milvus Docs**: https://milvus.io/docs
- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **Next.js Docs**: https://nextjs.org/docs

---

**END OF ARCHITECTURE DOCUMENT**
