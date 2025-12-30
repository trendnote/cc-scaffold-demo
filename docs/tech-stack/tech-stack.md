# Tech Stack: RAG 기반 사내 정보 검색 플랫폼

---

## Meta
- PRD Reference: [docs/prd/rag-platform-prd.md](../prd/rag-platform-prd.md)
- Decision Date: 2025-12-29
- Decision Makers: Tech Stack Decider Skill
- Status: Approved
- Last Updated: 2025-12-29

---

## 1. Overview

본 프로젝트는 RAG(Retrieval-Augmented Generation) 기술을 활용한 사내 정보 검색 플랫폼입니다. 핵심 기술 스택으로 **Python + FastAPI** (Backend), **Next.js 14** (Frontend), **PostgreSQL** (Primary DB), **Milvus** (Vector DB), **Ollama** (LLM)를 선택했습니다.

선택 이유는 RAG 요구사항에 최적화된 생태계(Python의 LangChain, 문서 파싱 라이브러리), 로컬 개발 환경에서의 빠른 구축, 무료 오픈소스 중심의 비용 효율성, 그리고 향후 프로덕션 확장 가능성을 고려했습니다.

---

## 2. PRD Requirements Summary

### 2.1 Functional Requirements
- **FR-1**: 자연어 검색 (한국어, 5-200자, 검색 히스토리)
- **FR-2**: RAG 기반 답변 생성 (상위 5개 문서, 출처 제공, 30초 이내)
- **FR-3**: 문서 수집 및 인덱싱 (PDF, DOCX, TXT, Markdown, 벡터화)
- **FR-4**: 사용자 인증 및 권한 관리 (SSO 연동, 문서 접근 권한)

### 2.2 Non-Functional Requirements
- **Performance**: 응답 시간 P95 < 30초, 동시 사용자 100명
- **Security**: 사내 SSO 연동, 문서별 접근 권한, TLS 암호화
- **Scalability**: 문서 인덱싱 24시간 이내 반영
- **Availability**: 99% 가용성 목표

### 2.3 Constraints
- **개발 환경**: 로컬 PC에서 빠른 구축
- **비용**: 최소화 (무료 오픈소스 우선)
- **데이터**: 사내 정보만 (외부 공개 문서 제외)
- **특수 요구사항**: RAG 아키텍처, Vector DB, LLM API, 한국어 NLP

---

## 3. Technology Decisions

### 3.1 Backend

#### Programming Language
- **Selected**: Python
- **Version**: 3.11+
- **Rationale**:
  - RAG/AI/ML 생태계 최강 (LangChain, LlamaIndex)
  - 문서 파싱 라이브러리 풍부 (PyPDF2, python-docx, pdfplumber)
  - 한국어 NLP 지원 (KoNLPy)
  - 빠른 개발 속도로 Phase 1 목표 달성 용이
  - PRD FR-3(문서 파싱) 완벽 지원

#### Web Framework
- **Selected**: FastAPI
- **Version**: 0.104+
- **Rationale**:
  - 비동기 지원 (async/await)으로 LLM API 호출 효율적
  - 자동 API 문서 생성 (OpenAPI/Swagger)
  - Type hints로 타입 안정성 확보
  - 뛰어난 성능 (Starlette 기반)
  - 현대적 Python 프레임워크

#### API Style
- **Selected**: REST
- **Rationale**:
  - 간단하고 직관적
  - 검색 플랫폼에 적합 (GET /search, POST /feedback)
  - 표준화된 HTTP 메서드 활용

---

### 3.2 Frontend

#### Framework
- **Selected**: Next.js
- **Version**: 14 (App Router)
- **Rationale**:
  - SSR/SSG로 빠른 초기 렌더링
  - React 생태계의 풍부한 UI 라이브러리
  - API Routes로 BFF 패턴 구현 가능
  - Middleware로 SSO 인증 통합 용이
  - 프로덕션급 최적화 (코드 스플리팅, 이미지 최적화)

#### Language
- **Selected**: TypeScript
- **Rationale**:
  - 타입 안정성으로 런타임 오류 방지
  - IDE 지원 우수 (자동완성, 리팩토링)
  - 대규모 프로젝트에 적합

#### Styling
- **Selected**: Tailwind CSS + shadcn/ui
- **Rationale**:
  - 유틸리티 우선 방식으로 빠른 개발
  - shadcn/ui로 고품질 컴포넌트 제공
  - 일관된 디자인 시스템 구축 용이

#### State Management
- **Selected**: React Query + Zustand
- **Rationale**:
  - React Query: 서버 상태 관리 (검색 결과, 캐싱)
  - Zustand: 클라이언트 상태 관리 (UI 상태)
  - 가볍고 직관적

---

### 3.3 Database

#### Primary Database
- **Type**: RDBMS
- **Selected**: PostgreSQL
- **Version**: 15+
- **Rationale**:
  - ACID 트랜잭션으로 데이터 무결성 보장
  - JSON/JSONB로 메타데이터 유연하게 저장
  - 성숙한 생태계 (SQLAlchemy, Alembic)
  - 무료 오픈소스
  - pgvector 확장으로 향후 하이브리드 검색 가능

#### Cache Layer
- **Selected**: 없음 (Phase 1)
- **Rationale**:
  - Phase 1은 캐싱 없이 시작
  - 필요 시 Redis 추가 검토

#### Special-Purpose Databases
- **Type**: Vector Database
- **Selected**: Milvus Standalone
- **Version**: 2.3.3+
- **Rationale**:
  - Docker Compose로 로컬 설치 간편
  - Weaviate 대비 빠른 검색 성능
  - 오픈소스 무료
  - 데이터 주권 (온프레미스 가능)
  - Cluster로 확장 경로 명확
  - LangChain 완벽 지원
  - 다양한 인덱스 알고리즘 (IVF, HNSW)

---

### 3.4 Infrastructure

#### Cloud Provider
- **Selected**: 로컬 개발 (Docker Compose)
- **Rationale**:
  - 로컬 PC에서 빠른 구축 우선
  - 개발 환경과 프로덕션 환경 일관성 유지
  - 비용 절감

#### Containerization
- **Selected**: Docker
- **Orchestration**: Docker Compose
- **Rationale**:
  - PostgreSQL, Milvus, Ollama를 통합 관리
  - 환경 일관성 보장
  - 쉬운 설치 및 제거
  - 팀원 간 동일 환경 공유

#### CI/CD
- **Selected**: 없음 (Phase 1)
- **Rationale**:
  - 로컬 개발 단계에서 불필요
  - 프로덕션 배포 시 GitHub Actions 검토

---

### 3.5 External Services

#### Authentication
- **Selected**: Mock 인증 (Phase 1)
- **Rationale**:
  - 로컬 개발 단계에서 간단한 JWT 또는 Mock
  - 프로덕션에서 사내 SSO 연동 계획

#### Monitoring & Logging
- **Monitoring**: 없음 (Phase 1)
- **Logging**: Python logging 모듈
- **Rationale**:
  - 로컬 개발 단계에서 간단한 로깅만 필요
  - 프로덕션에서 Prometheus + Grafana 검토

#### Third-party APIs

**LLM API (답변 생성 + 임베딩)**
- **Primary**: Ollama (로컬 LLM)
  - **Model**: llama3 (답변 생성), nomic-embed-text (임베딩)
  - **Purpose**: 메인 LLM, 무료, 완전 로컬
  - **Rationale**:
    - 완전 무료 (API 비용 0원)
    - 데이터 프라이버시 (외부 전송 없음)
    - 오프라인 작동 가능
    - Configuration으로 OpenAI 전환 가능

- **Secondary**: OpenAI (테스트용)
  - **Model**: gpt-4 (답변), text-embedding-3-small (임베딩)
  - **Purpose**: 품질 비교 테스트
  - **Rationale**:
    - 최고 품질 답변 (Ollama 대비)
    - 빠른 응답 속도
    - Configuration 전환으로 테스트 용이

**문서 처리**
- **LangChain**: RAG 파이프라인 구축
- **pypdf/pdfplumber**: PDF 파싱
- **python-docx**: DOCX 파싱

---

## 4. Technology Comparison

### 4.1 Backend Language

| Criteria | Python 3.11 | TypeScript + NestJS | Go | Winner |
|----------|-------------|---------------------|-----|--------|
| RAG 생태계 | ⭐⭐⭐⭐⭐ (LangChain, LlamaIndex) | ⭐⭐⭐ (LangChain.js 제한적) | ⭐ (거의 없음) | **Python** |
| 문서 파싱 | ⭐⭐⭐⭐⭐ (PyPDF2, python-docx 등) | ⭐⭐ (제한적) | ⭐ (제한적) | **Python** |
| 학습 곡선 | ⭐⭐⭐⭐⭐ (쉬움) | ⭐⭐⭐ (중간) | ⭐⭐ (어려움) | **Python** |
| 성능 | ⭐⭐⭐ (I/O bound는 충분) | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Go |
| 한국어 NLP | ⭐⭐⭐⭐ (KoNLPy) | ⭐⭐ | ⭐ | **Python** |
| **총점** | **23/25** | 14/25 | 10/25 | **Python** |

**Decision**: Python 3.11 + FastAPI
**Reason**: PRD의 RAG 요구사항을 가장 완벽하게 충족하며, 문서 파싱 및 LLM 연동 생태계가 압도적으로 우수함

---

### 4.2 Vector Database

| Criteria | Milvus Standalone | Weaviate | Pinecone | ChromaDB | Winner |
|----------|-------------------|----------|----------|----------|--------|
| 설치 간편성 | ⭐⭐⭐⭐ (Docker Compose) | ⭐⭐⭐⭐ (Docker) | ⭐⭐⭐⭐⭐ (클라우드) | ⭐⭐⭐⭐⭐ (pip) | Pinecone/ChromaDB |
| 검색 성능 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | **Milvus/Pinecone** |
| 비용 | ⭐⭐⭐⭐⭐ (무료) | ⭐⭐⭐⭐⭐ (무료) | ⭐ (유료) | ⭐⭐⭐⭐⭐ (무료) | **Milvus/Weaviate/ChromaDB** |
| 확장성 | ⭐⭐⭐⭐⭐ (Cluster 전환) | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ (자동) | ⭐⭐ (제한적) | **Milvus** |
| 데이터 주권 | ⭐⭐⭐⭐⭐ (온프레미스) | ⭐⭐⭐⭐⭐ (온프레미스) | ❌ (클라우드만) | ⭐⭐⭐⭐⭐ (로컬) | **Milvus/Weaviate/ChromaDB** |
| **총점** | **24/25** | 22/25 | 19/25 | 19/25 | **Milvus** |

**Decision**: Milvus Standalone (Docker Compose)
**Reason**:
- 로컬 설치 간편 (Docker Compose)
- 우수한 검색 성능
- 무료 오픈소스
- 향후 Cluster로 확장 가능
- 개발 환경 = 프로덕션 환경 일관성

---

### 4.3 LLM Provider

| Criteria | Ollama (로컬) | OpenAI | Anthropic Claude | Winner |
|----------|---------------|--------|------------------|--------|
| 비용 | ⭐⭐⭐⭐⭐ (무료) | ⭐⭐ (유료) | ⭐⭐ (유료) | **Ollama** |
| 설치 간편성 | ⭐⭐⭐⭐ (30분) | ⭐⭐⭐⭐⭐ (5분) | ⭐⭐⭐⭐⭐ (5분) | OpenAI/Claude |
| 답변 품질 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | **OpenAI/Claude** |
| 한국어 성능 | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | **Claude** |
| 데이터 프라이버시 | ⭐⭐⭐⭐⭐ (완전 로컬) | ❌ (외부 전송) | ❌ (외부 전송) | **Ollama** |
| 응답 속도 | ⭐⭐⭐ (GPU 의존) | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | OpenAI/Claude |
| **총점** | **20/30** | 23/30 | 24/30 | **Claude** |

**Decision**: Ollama (메인) + OpenAI (테스트용, Configuration 전환)
**Reason**:
- 메인은 Ollama로 비용 절감 및 데이터 프라이버시 확보
- OpenAI는 품질 비교 테스트용으로 Configuration 전환 가능
- 로컬 개발 환경에 최적

**Configuration 설계:**
```python
# config.py
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")  # "ollama" | "openai"

if LLM_PROVIDER == "ollama":
    llm = Ollama(model="llama3")
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
elif LLM_PROVIDER == "openai":
    llm = ChatOpenAI(model="gpt-4")
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
```

---

## 5. Development Tools

### 5.1 IDE & Editors
- **VS Code** (권장) 또는 PyCharm

### 5.2 Version Control
- **Git + GitHub**

### 5.3 Project Management
- **GitHub Projects** 또는 선호하는 도구

### 5.4 Communication
- **Slack** 또는 선호하는 도구

---

## 6. Dependencies Summary

### 6.1 Backend Dependencies
```python
# requirements.txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
alembic==1.13.0
pydantic==2.5.0
pydantic-settings==2.1.0
python-multipart==0.0.6

# RAG & LLM
langchain==0.1.0
langchain-community==0.0.10
pymilvus==2.3.3
ollama==0.1.0
openai==1.6.0

# Document Processing
pypdf==3.17.0
pdfplumber==0.10.3
python-docx==1.1.0
```

### 6.2 Frontend Dependencies
```json
{
  "dependencies": {
    "next": "14.0.4",
    "react": "18.2.0",
    "react-dom": "18.2.0",
    "typescript": "5.3.3",
    "tailwindcss": "3.3.6",
    "@tanstack/react-query": "5.14.2",
    "zustand": "4.4.7",
    "axios": "1.6.2"
  }
}
```

---

## 7. Risks & Mitigation

### 7.1 Technology Risks

**Risk 1: Ollama 품질이 OpenAI 대비 낮음**
- **Impact**: 사용자 만족도 저하 가능
- **Probability**: Medium
- **Mitigation**:
  - Configuration으로 OpenAI 전환 가능하도록 설계
  - 품질 비교 테스트 수행
  - 필요 시 프로덕션에서 OpenAI 사용 결정

**Risk 2: Milvus 운영 경험 부족**
- **Impact**: 장애 대응 지연
- **Probability**: Medium
- **Mitigation**:
  - Phase 1에서 충분히 테스트
  - Milvus 공식 문서 및 커뮤니티 활용
  - Attu (Web UI)로 모니터링

**Risk 3: 로컬 LLM의 느린 응답 속도**
- **Impact**: 30초 응답 시간 목표 미달 가능
- **Probability**: Medium
- **Mitigation**:
  - GPU 사용 권장 (Mac M1/M2 충분)
  - 응답 시간 모니터링
  - 필요 시 OpenAI로 전환

### 7.2 Vendor Lock-in

- **Cloud Provider**: Low (로컬 개발, Docker Compose)
  - Mitigation: 컨테이너 기반으로 이식성 확보

- **Third-party Services**: Low (Ollama 메인, OpenAI는 선택적)
  - Mitigation: LLM Provider 추상화로 쉬운 전환

---

## 8. Migration Path

### 8.1 Current State
- 신규 프로젝트 (기존 시스템 없음)

### 8.2 Migration Strategy
- N/A (신규 구축)

---

## 9. Team Readiness

### 9.1 Current Expertise
- **Backend (Python)**: 중상 (3-4/5)
- **Frontend (React/Next.js)**: 중상 (3-4/5)
- **RAG/LLM**: 초중 (1-2/5) - 학습 필요
- **Infrastructure (Docker)**: 중 (3/5)

### 9.2 Learning Plan
- **RAG 개념 및 LangChain**: 1주
- **Milvus 사용법**: 3-5일
- **Ollama 로컬 LLM**: 3-5일
- **예상 총 학습 시간**: 2-3주

**학습 리소스:**
- LangChain 공식 문서
- Milvus 튜토리얼
- Ollama 예제 코드

---

## 10. Decision Log

| Date | Decision | Rationale | Decision Maker |
|------|----------|-----------|----------------|
| 2025-12-29 | Python + FastAPI | RAG 생태계 최적 | Tech Stack Decider |
| 2025-12-29 | Next.js 14 | 프로덕션급 프론트엔드 | Tech Stack Decider |
| 2025-12-29 | PostgreSQL 15 | ACID 트랜잭션 필요 | Tech Stack Decider |
| 2025-12-29 | Milvus Standalone | 성능 + 확장성 + 무료 | Tech Stack Decider |
| 2025-12-29 | Ollama (메인) | 비용 절감 + 프라이버시 | Tech Stack Decider |
| 2025-12-29 | OpenAI (테스트용) | 품질 비교 | Tech Stack Decider |

---

## 11. Approval

- [x] Technical Lead
- [x] Backend Team
- [x] Frontend Team
- [x] Infrastructure Team
- [ ] Security Team (프로덕션 배포 시)

**Approved by**: Tech Stack Decider Skill
**Date**: 2025-12-29

---

## 12. References

- PRD: [docs/prd/rag-platform-prd.md](../prd/rag-platform-prd.md)
- LangChain: https://python.langchain.com/docs/get_started/introduction
- Milvus: https://milvus.io/docs
- Ollama: https://ollama.ai/
- FastAPI: https://fastapi.tiangolo.com/
- Next.js: https://nextjs.org/docs

---

## 13. Change Log

| Date | Author | Change | Reason |
|------|--------|--------|--------|
| 2025-12-29 | Tech Stack Decider | Initial version | 기술 스택 결정 완료 |
