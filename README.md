# RAG 기반 사내 정보 검색 플랫폼

## 개요
RAG(Retrieval-Augmented Generation) 기술을 활용한 사내 문서 검색 및 질의응답 플랫폼입니다.

## 기술 스택
- **Backend**: FastAPI (Python 3.11+)
- **Frontend**: Next.js 14 (TypeScript)
- **Database**: PostgreSQL 15
- **Vector DB**: Milvus 2.3.3
- **LLM**: Ollama (llama3, nomic-embed-text)
- **Infrastructure**: Docker Compose

## 사전 요구사항
- Docker 24.0.0+
- Docker Compose 2.0.0+
- 최소 8GB RAM (권장 16GB)
- 최소 20GB 여유 디스크 공간

## 설치 및 실행

### 1. 환경 변수 설정
```bash
# .env.example을 복사하여 .env 생성
cp .env.example .env

# .env 파일을 편집하여 비밀번호 변경
# POSTGRES_PASSWORD, MILVUS_PASSWORD, JWT_SECRET 변경 필수
vi .env
```

### 2. Docker Compose 실행
```bash
# 모든 서비스 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f
```

### 3. 서비스 확인
- **PostgreSQL**: localhost:5432
- **Milvus**: localhost:19530 (gRPC), localhost:9091 (HTTP)
- **Attu (Milvus UI)**: http://localhost:8080
- **Ollama**: localhost:11434

### 4. Health Check
```bash
./scripts/health-check.sh
```

## 서비스 관리

### 컨테이너 중지
```bash
docker-compose down
```

### 컨테이너 재시작
```bash
docker-compose restart
```

### 특정 서비스만 재시작
```bash
docker-compose restart postgres
```

### 볼륨 포함 완전 삭제 (주의!)
```bash
docker-compose down -v
```

## 트러블슈팅

### 포트 충돌 시
1. 사용 중인 포트 확인:
   ```bash
   lsof -i :5432
   lsof -i :19530
   ```
2. `docker-compose.yml`에서 포트 변경

### 컨테이너 시작 실패 시
1. 로그 확인:
   ```bash
   docker-compose logs <service-name>
   ```
2. 컨테이너 재시작:
   ```bash
   docker-compose restart <service-name>
   ```

### 메모리 부족 시
1. Docker Desktop 메모리 설정 증가 (최소 8GB)
2. 불필요한 컨테이너 중지

## Milvus Vector Database

### Collection 생성

Task 1.3에서 구현한 Milvus Collection을 생성합니다:

```bash
cd backend
source venv/bin/activate
python scripts/create_milvus_collection.py
```

### Collection 스키마

- **id** (INT64): Auto-generated primary key
- **document_id** (VARCHAR): Reference to PostgreSQL documents table (UUID)
- **content** (VARCHAR): Text content of chunk (max 2000 chars)
- **embedding** (FLOAT_VECTOR): 768-dimensional embedding vector
- **chunk_index** (INT32): Index within document
- **metadata** (JSON): Additional metadata (page_number, section, etc.)

### Index Configuration

- **Type**: HNSW (Hierarchical Navigable Small World)
- **Metric**: COSINE similarity
- **Parameters**: M=16, efConstruction=256

### 더미 데이터 테스트

```bash
cd backend
source venv/bin/activate
python scripts/test_milvus_operations.py
```

### Attu UI 확인

브라우저에서 http://localhost:8080 접속하여 Collection 확인

### 단위 테스트

```bash
cd backend
source venv/bin/activate
pytest tests/test_milvus.py -v
```

## LLM Provider Configuration

### Ollama (Local)

Task 1.4에서 구현한 Ollama 기반 LLM/Embedding provider를 사용합니다.

1. Start Ollama container:
   ```bash
   docker-compose up -d ollama
   ```

2. Download models:
   ```bash
   docker exec -it ollama ollama pull llama3
   docker exec -it ollama ollama pull nomic-embed-text
   ```

3. Verify models:
   ```bash
   docker exec -it ollama ollama list
   ```

4. Test integration:
   ```bash
   cd backend
   source venv/bin/activate
   python scripts/test_ollama_integration.py
   ```

### OpenAI (Cloud) - Phase 2

1. Set environment variables in `.env`:
   ```bash
   LLM_PROVIDER=openai
   OPENAI_API_KEY=your-api-key
   ```

2. Restart application

### Configuration

Environment variables (`.env`):
```
LLM_PROVIDER=ollama  # or "openai"

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_LLM_MODEL=llama3
OLLAMA_EMBED_MODEL=nomic-embed-text

# OpenAI (optional)
OPENAI_API_KEY=
OPENAI_LLM_MODEL=gpt-4
OPENAI_EMBED_MODEL=text-embedding-3-small
```

### Switching Providers

No code changes required:
1. Change `LLM_PROVIDER` in `.env`
2. Set provider-specific variables
3. Restart application

### Unit Tests

```bash
cd backend
source venv/bin/activate
pytest tests/test_ollama.py -v
```

## 다음 단계
- Task 1.5: LangChain RAG Chain 구성

## 참고 문서
- [PRD](docs/prd/rag-platform-prd.md)
- [Architecture](docs/architecture/architecture.md)
- [Tech Stack](docs/tech-stack/tech-stack.md)
- [Task Breakdown](docs/tasks/task-breakdown.md)

## 라이선스
Internal Use Only - KakaoPay
