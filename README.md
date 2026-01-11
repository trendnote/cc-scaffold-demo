# RAG 기반 사내 정보 검색 플랫폼

AI 기반 자연어 검색으로 사내 문서를 빠르게 찾고 정확한 답변을 제공하는 플랫폼입니다.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Next.js 16](https://img.shields.io/badge/Next.js-16-black.svg)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)

## 🎯 주요 기능

- ✅ **자연어 검색** - 한국어 질의응답 지원
- ✅ **RAG 기반 답변 생성** - LLM을 활용한 정확한 답변 제공
- ✅ **출처 문서 추적** - 답변 근거 문서 링크 제공
- ✅ **권한 기반 필터링** - 사용자 권한에 따른 문서 접근 제어 (L1, L2, L3)
- ✅ **검색 히스토리** - 사용자별 검색 기록 관리
- ✅ **사용자 피드백** - 답변 품질 개선을 위한 피드백 수집
- ✅ **구조화된 로깅** - 개인정보 마스킹 및 JSON 형식 로그

## 🚀 빠른 시작 (30분 이내 실행)

### 사전 요구사항

- **Docker** 및 **Docker Compose** (필수)
- **Git** (필수)
- **Node.js 20+** (프론트엔드 개발 시)
- **Python 3.11+** (백엔드 개발 시)

### 1. 저장소 클론

```bash
git clone https://github.com/trendnote/cc-scaffold-demo.git
cd cc-scaffold-demo
```

### 2. 환경 변수 설정

```bash
# .env 파일 생성
cp .env.example .env

# 필수 환경 변수 설정
vi .env
```

**필수 환경 변수 설정**:
```env
# PostgreSQL 비밀번호 설정
POSTGRES_PASSWORD=your-secure-password

# JWT 비밀 키 생성 및 설정 (필수!)
JWT_SECRET=your-secret-key-change-this-in-production

# 랜덤 키 생성 (권장)
# openssl rand -hex 32
```

### 3. 인프라 서비스 시작

```bash
# Docker Compose로 전체 서비스 시작
docker-compose up -d

# 서비스 상태 확인
docker-compose ps
```

**실행되는 서비스**:
| 서비스 | 포트 | 용도 | 접속 URL |
|--------|------|------|----------|
| PostgreSQL | 5432 | 메타데이터 저장 | `localhost:5432` |
| Milvus | 19530, 9091 | 벡터 DB | `localhost:19530` |
| etcd | 2379 | Milvus 메타데이터 | - |
| MinIO | 9000, 9001 | Milvus 스토리지 | - |
| Attu | 8080 | Milvus Web UI | http://localhost:8080 |
| Ollama | 11434 | LLM API | http://localhost:11434 |
| Open WebUI | 3001 | Ollama UI | http://localhost:3001 |

### 4. Ollama 모델 다운로드

```bash
# Ollama 컨테이너에 접속
docker exec -it rag-ollama bash

# LLM 모델 다운로드 (약 1.3GB - llama3.2:1b 사용)
ollama pull llama3.2:1b

# 임베딩 모델 다운로드 (약 274MB)
ollama pull nomic-embed-text

# 모델 확인
ollama list

# 컨테이너 종료
exit
```

### 5. 백엔드 실행

```bash
cd backend

# 가상 환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 데이터베이스 마이그레이션
alembic upgrade head

# 개발 서버 실행
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**백엔드 접속**:
- API: http://localhost:8000
- API 문서 (Swagger): http://localhost:8000/docs
- Health Check: http://localhost:8000/health

### 6. 프론트엔드 실행

새 터미널에서:

```bash
cd frontend

# 의존성 설치
npm install

# 개발 서버 실행
npm run dev
```

**프론트엔드 접속**:
- 웹 애플리케이션: http://localhost:3000

### 7. 접속 및 테스트

**테스트 계정**:
| 계정 | 이메일 | 비밀번호 | 권한 | 부서 |
|------|--------|----------|------|------|
| 일반 사용자 | user@example.com | password123 | L1 | Engineering |
| 팀장 | teamlead@example.com | password123 | L2 | Engineering |
| 관리자 | admin@example.com | password123 | L3 | Management |

1. http://localhost:3000 접속
2. 로그인 (위 테스트 계정 사용)
3. 검색창에 질문 입력 (예: "연차 사용 방법")
4. 답변 및 출처 문서 확인

## 🛠️ 인프라 관리

### 서비스 시작/종료

```bash
# 모든 서비스 시작
docker-compose up -d

# 모든 서비스 종료
docker-compose down

# 특정 서비스만 재시작
docker-compose restart postgres
docker-compose restart milvus-standalone
docker-compose restart ollama

# 로그 확인
docker-compose logs -f backend
docker-compose logs -f milvus-standalone
```

### Docker 컨테이너 관리

```bash
# 실행 중인 컨테이너 확인
docker-compose ps

# 컨테이너 상태 및 리소스 사용량
docker stats

# 특정 컨테이너 로그
docker logs rag-postgres
docker logs rag-milvus
docker logs rag-ollama

# 컨테이너 내부 접속
docker exec -it rag-postgres bash
docker exec -it rag-milvus bash
docker exec -it rag-ollama bash
```

### PostgreSQL 관리

```bash
# PostgreSQL 컨테이너 접속
docker exec -it rag-postgres psql -U raguser -d rag_platform

# 데이터베이스 확인
\l

# 테이블 확인
\dt

# 연결 테스트
docker exec -it rag-postgres psql -U raguser -d rag_platform -c "SELECT 1"

# 백업
docker exec rag-postgres pg_dump -U raguser rag_platform > backup.sql

# 복원
cat backup.sql | docker exec -i rag-postgres psql -U raguser -d rag_platform
```

### Milvus 관리

```bash
# Milvus 상태 확인
curl http://localhost:9091/healthz

# Attu UI로 관리 (추천)
# http://localhost:8080 접속

# Collection 리스트 확인 (Python)
cd backend
source venv/bin/activate
python -c "from app.db.milvus_client import get_milvus_client; print(get_milvus_client().list_collections())"

# Collection 삭제
python -c "from app.db.milvus_client import get_milvus_client; get_milvus_client().drop_collection('rag_document_chunks')"
```

### Ollama 관리

```bash
# 모델 리스트 확인
docker exec -it rag-ollama ollama list

# 모델 다운로드
docker exec -it rag-ollama ollama pull llama3.2:1b
docker exec -it rag-ollama ollama pull nomic-embed-text

# 모델 삭제
docker exec -it rag-ollama ollama rm llama3.2:1b

# 모델 테스트
docker exec -it rag-ollama ollama run llama3.2:1b "안녕하세요"

# Ollama API 테스트
curl http://localhost:11434/api/tags
```

### 볼륨 관리

```bash
# 볼륨 리스트 확인
docker volume ls | grep rag

# 볼륨 상세 정보
docker volume inspect rag-platform_postgres-data
docker volume inspect rag-platform_milvus-data
docker volume inspect rag-platform_ollama-data

# 볼륨 삭제 (주의! 데이터 손실)
docker-compose down -v

# 특정 볼륨만 삭제
docker volume rm rag-platform_postgres-data
```

### 네트워크 관리

```bash
# 네트워크 확인
docker network ls | grep rag

# 네트워크 상세 정보
docker network inspect rag-platform_rag-network

# 컨테이너의 IP 확인
docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' rag-postgres
```

## 📖 상세 사용 방법

### 검색하기

1. **로그인**: http://localhost:3000/login
2. **검색**: 검색창에 자연어 질문 입력
   - 예: "연차 사용 방법을 알려주세요"
   - 예: "급여 지급일은 언제인가요?"
   - 예: "회의실 예약은 어떻게 하나요?"
3. **결과 확인**:
   - AI 생성 답변 확인
   - 출처 문서 및 신뢰도 점수 확인
   - 마크다운 형식 답변 렌더링
4. **피드백**: 답변에 대한 별점 및 코멘트 제공

### 검색 히스토리 확인

1. 상단 메뉴에서 "히스토리" 클릭
2. 과거 검색 기록 확인
3. 특정 검색 클릭하여 결과 재확인
4. 검색 날짜 및 시간 확인

### API 직접 호출

```bash
# 로그인
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password123"}'

# 응답에서 access_token 복사

# 검색 요청
curl -X POST http://localhost:8000/api/v1/search/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your-token>" \
  -d '{"query":"연차 사용 방법","limit":5}'

# 히스토리 조회
curl -X GET "http://localhost:8000/api/v1/users/me/history?page=1&page_size=10" \
  -H "Authorization: Bearer <your-token>"
```

## 🧪 테스트 실행

### 백엔드 테스트

```bash
cd backend

# 단위 테스트
pytest tests/ -v

# 커버리지 포함
pytest tests/ -v --cov=app --cov-report=html

# 특정 테스트만 실행
pytest tests/integration/test_access_control.py -v
pytest tests/security/test_sql_injection.py -v
pytest tests/security/test_xss.py -v

# 로깅 테스트
pytest tests/test_logging_integration.py -v
```

### 프론트엔드 E2E 테스트

```bash
cd frontend

# Playwright 브라우저 설치 (최초 1회)
npx playwright install

# E2E 테스트 실행
npm run test:e2e

# UI 모드로 실행 (디버깅)
npm run test:e2e:ui

# 특정 브라우저로 실행
npx playwright test --project=chromium
npx playwright test --project=firefox
npx playwright test --project=webkit

# 헤드리스 모드 해제 (브라우저 보기)
npm run test:e2e:headed

# 테스트 리포트 확인
npm run test:e2e:report
```

### 성능 테스트

```bash
cd backend

# 응답 시간 테스트 (100 requests)
python tests/performance/test_response_time.py

# 부하 테스트 (100 concurrent users, 5 minutes)
bash scripts/run_load_test.sh

# Locust UI 모드
locust -f tests/performance/locustfile.py
# 브라우저에서 http://localhost:8089 접속
# Users: 100, Spawn rate: 10, Host: http://localhost:8000 입력
```

### 보안 테스트

```bash
cd backend

# 정적 보안 분석 (Bandit)
bandit -c .bandit -r app/

# 의존성 취약점 검사 (Safety)
bash scripts/check_dependencies.sh

# 하드코드 시크릿 검사
bash scripts/scan_secrets.sh app/

# 모든 보안 테스트 실행
pytest tests/security/ -v
```

## 📊 모니터링

### 로그 확인

```bash
# 백엔드 로그 (실시간)
docker-compose logs -f backend

# 프론트엔드 로그
cd frontend
npm run dev  # 콘솔에서 로그 확인

# Docker 로그
docker-compose logs -f postgres
docker-compose logs -f milvus-standalone
docker-compose logs -f ollama

# 최근 100줄
docker-compose logs --tail=100 backend

# 에러만 필터링
docker-compose logs backend | grep ERROR

# 특정 시간대 로그
docker-compose logs --since 2026-01-11T10:00:00 backend
docker-compose logs --until 2026-01-11T12:00:00 backend
```

**로그 파일 위치** (로컬 개발):
```bash
# 백엔드 로그
backend/logs/app.log        # 일반 로그
backend/logs/error.log      # 에러 로그

# 로그 확인
tail -f backend/logs/app.log
tail -f backend/logs/error.log

# 로그 검색
grep "ERROR" backend/logs/error.log
grep "user@example.com" backend/logs/app.log | grep "search"
```

### 서비스 상태 확인

```bash
# 모든 컨테이너 상태
docker-compose ps

# Health Check
curl http://localhost:8000/health
curl http://localhost:9091/healthz  # Milvus
curl http://localhost:11434/api/tags  # Ollama

# 리소스 사용량 모니터링
docker stats

# PostgreSQL 연결 확인
docker exec -i rag-postgres psql -U raguser -d rag_platform -c "SELECT version();"

# Milvus 상태 (Attu UI)
# http://localhost:8080
```

### 성능 메트릭

```bash
# API 응답 시간 측정
time curl -X POST http://localhost:8000/api/v1/search/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"query":"연차 사용 방법","limit":5}'

# 로그에서 성능 데이터 확인
grep "response_time" backend/logs/app.log | tail -20

# 데이터베이스 성능
docker exec -i rag-postgres psql -U raguser -d rag_platform -c "
SELECT
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
"
```

## 🐛 트러블슈팅

자세한 내용은 [트러블슈팅 가이드](docs/operations/troubleshooting.md)를 참고하세요.

### 자주 발생하는 문제

#### 1. Milvus 연결 실패

**증상**:
```
pymilvus.exceptions.MilvusException: <MilvusClient: timeout>
```

**해결 방법**:
```bash
# Milvus 및 의존 서비스 재시작
docker-compose restart milvus-standalone etcd minio

# 로그 확인
docker-compose logs milvus-standalone
docker-compose logs etcd
docker-compose logs minio

# Health check
curl http://localhost:9091/healthz

# Attu UI로 상태 확인
# http://localhost:8080
```

#### 2. PostgreSQL 연결 실패

**증상**:
```
sqlalchemy.exc.OperationalError: could not connect to server
```

**해결 방법**:
```bash
# PostgreSQL 상태 확인
docker-compose ps postgres

# PostgreSQL 재시작
docker-compose restart postgres

# 연결 테스트
docker exec -it rag-postgres psql -U raguser -d rag_platform -c "SELECT 1"

# 로그 확인
docker-compose logs postgres
```

#### 3. LLM 응답 느림 (> 30초)

Ollama (llama3.2:1b)는 로컬 실행으로 느릴 수 있습니다.

**해결 방법**:

**옵션 1: GPU 사용 (권장)**
```bash
# docker-compose.yml에서 GPU 설정 주석 해제
# services:
#   ollama:
#     deploy:
#       resources:
#         reservations:
#           devices:
#             - driver: nvidia
#               count: 1
#               capabilities: [gpu]

docker-compose up -d ollama
```

**옵션 2: OpenAI로 전환 (빠름, 유료)**
```bash
# .env 파일 수정
vi .env
# LLM_PROVIDER=openai
# OPENAI_API_KEY=sk-your-key-here

# 백엔드 재시작
cd backend
uvicorn app.main:app --reload
```

**옵션 3: 더 작은 모델 사용**
```bash
# llama3.2:1b 사용 (기본값, 가장 빠름)
docker exec -it rag-ollama ollama pull llama3.2:1b

# .env 파일 수정
OLLAMA_MODEL_LLM=llama3.2:1b
```

#### 4. 프론트엔드 빌드 에러

```bash
cd frontend

# 캐시 및 의존성 재설치
rm -rf node_modules package-lock.json .next
npm install

# TypeScript 에러 확인
npm run type-check

# 빌드 재시도
npm run build

# 개발 서버 재시작
npm run dev
```

#### 5. 포트 충돌

```bash
# 사용 중인 포트 확인
lsof -i :5432   # PostgreSQL
lsof -i :19530  # Milvus
lsof -i :8000   # Backend
lsof -i :3000   # Frontend
lsof -i :11434  # Ollama

# 프로세스 종료
kill -9 <PID>

# Docker Compose에서 포트 변경
# docker-compose.yml 편집
# ports:
#   - "15432:5432"  # 5432 대신 15432 사용
```

#### 6. Docker 볼륨 문제

```bash
# 볼륨 리스트
docker volume ls | grep rag

# 특정 볼륨 상세 정보
docker volume inspect rag-platform_postgres-data

# 볼륨 정리 (주의! 데이터 손실)
docker-compose down
docker volume prune

# 볼륨 재생성
docker-compose up -d
```

#### 7. Ollama 모델 다운로드 실패

```bash
# Ollama 컨테이너 재시작
docker-compose restart ollama

# 수동 다운로드 재시도
docker exec -it rag-ollama ollama pull llama3.2:1b

# 네트워크 확인
docker exec -it rag-ollama ping -c 3 ollama.ai

# 디스크 공간 확인
docker exec -it rag-ollama df -h
```

## 📚 문서

- **Operations**
  - [배포 가이드](docs/operations/deployment-guide.md)
  - [트러블슈팅](docs/operations/troubleshooting.md)
  - [모니터링](docs/operations/monitoring.md)
  - [백업 및 복구](docs/operations/backup-restore.md)

- **Development**
  - [개발 환경 설정](docs/development/setup.md)
  - [테스트 가이드](docs/development/testing-guide.md)
  - [코딩 표준](docs/development/coding-standards.md)

- **API**
  - [API 레퍼런스](docs/api/api-reference.md)
  - [Swagger UI](http://localhost:8000/docs)

- **Project**
  - [PRD](docs/prd/rag-platform-prd.md)
  - [Architecture](docs/architecture/architecture.md)
  - [Tech Stack](docs/tech-stack/tech-stack.md)
  - [Task Breakdown](docs/tasks/task-breakdown.md)

## 🏗️ 아키텍처

```
┌─────────────────────────────────────────────┐
│         Frontend (Next.js 16)               │
│  - React 19 + TypeScript                   │
│  - TanStack Query (데이터 fetching)        │
│  - Tailwind CSS (스타일링)                 │
│  - React Markdown (마크다운 렌더링)        │
└──────────────────┬──────────────────────────┘
                   │ REST API (JWT Auth)
┌──────────────────▼──────────────────────────┐
│        Backend (FastAPI 0.115+)             │
│  - RAG Pipeline (검색 + 생성)               │
│  - JWT Authentication                       │
│  - Permission-based Access Control          │
│  - Structured Logging (structlog)           │
└──────────────────┬──────────────────────────┘
                   │
        ┌──────────┼──────────┬──────────┐
        ▼          ▼          ▼          ▼
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│PostgreSQL│ │  Milvus  │ │  Ollama  │ │   etcd   │
│   15     │ │  2.3.3   │ │  Latest  │ │  3.5.5   │
│(메타데이터)│ │  (벡터)  │ │  (LLM)   │ │(Milvus)  │
└──────────┘ └──────────┘ └──────────┘ └──────────┘
                   │
        ┌──────────┴──────────┐
        ▼                     ▼
┌──────────┐          ┌──────────┐
│  MinIO   │          │   Attu   │
│(Storage) │          │  (UI)    │
└──────────┘          └──────────┘
```

### 기술 스택

**Frontend**:
- Next.js 16 (React 19)
- TypeScript 5
- TanStack Query 5 (데이터 fetching)
- Tailwind CSS 4
- React Markdown + rehype-sanitize
- Lucide React (아이콘)

**Backend**:
- FastAPI 0.115+
- Python 3.11+
- SQLAlchemy 2.0 (ORM)
- Alembic (마이그레이션)
- python-jose (JWT)
- bcrypt (비밀번호 해싱)
- structlog (구조화된 로깅)
- httpx (async HTTP 클라이언트)

**Infrastructure**:
- Docker & Docker Compose
- PostgreSQL 15 (메타데이터)
- Milvus 2.3.3 (벡터 DB)
- Ollama (LLM - llama3.2:1b, nomic-embed-text)
- etcd 3.5.5 (Milvus 메타데이터)
- MinIO (Milvus 스토리지)
- Attu 2.3.10 (Milvus Web UI)

**Testing**:
- pytest (백엔드 단위/통합 테스트)
- pytest-asyncio (비동기 테스트)
- Playwright (E2E 테스트)
- Locust (성능 테스트)
- Bandit (보안 정적 분석)
- Safety (의존성 취약점 검사)

## 🔐 보안 고려사항

### 인증 & 인가
- **JWT 토큰 기반 인증** (Bearer Token)
- **Access Level 제어** (L1, L2, L3)
- **부서별 문서 필터링** (Engineering, HR, Management)
- **토큰 만료 시간**: 1시간

### 데이터 보호
- **비밀번호 해싱** (bcrypt, salt rounds: 12)
- **개인정보 로그 마스킹** (이메일, IP, 민감한 쿼리)
- **환경 변수 분리** (.env 파일, .gitignore에 포함)
- **SQL Injection 방어** (SQLAlchemy ORM 파라미터화)

### API 보안
- **XSS 방어** (JSON 응답, rehype-sanitize)
- **CSRF 방어** (JWT 헤더 인증, 쿠키 미사용)
- **CORS 설정** (허용된 Origin만 접근)
- **Rate Limiting** (향후 구현 예정)

### 로깅 보안
- **개인정보 자동 마스킹** (이메일, IP, 주민등록번호, 카드번호)
- **로그 파일 권한 제어** (0600)
- **로그 로테이션** (90일 보관)
- **에러 로그 장기 보관** (365일)

## 🚧 현재 제한사항

### 인증
- **Mock 인증 사용 중** (실제 사용자 DB 미구현)
- 사용자 등록 기능 없음
- 비밀번호 재설정 기능 없음
- 소셜 로그인 미지원

### 문서 관리
- 문서 업로드 UI 없음
- 자동 인덱싱 미구현
- 문서 삭제 기능 없음
- PDF/DOCX 등 파일 파싱 미구현

### 성능
- **Ollama 로컬 실행 시 응답 시간 느림** (15-30초)
  - llama3.2:1b 모델 사용 (경량)
  - GPU 사용 시 개선
- 대량 문서 처리 최적화 필요
- **캐싱 미구현** (Redis 계획)

### 기타
- 다국어 미지원 (한국어만)
- 음성 검색 미지원
- 검색 필터 기능 제한적
- 대시보드 및 통계 미구현

## 🔄 향후 개발 계획

### Phase 5: 프로덕션 준비
- [ ] 실제 사용자 인증 (DB 기반)
- [ ] 사용자 등록 및 관리
- [ ] 문서 업로드 API 및 UI
- [ ] 자동 인덱싱 스케줄러
- [ ] Redis 캐싱
- [ ] Rate Limiting
- [ ] SSL/TLS 설정
- [ ] 프로덕션 환경 설정

### Phase 6: 고급 기능
- [ ] 다중 파일 포맷 지원 (PDF, DOCX, PPTX, HWP)
- [ ] 문서 OCR 처리
- [ ] 고급 검색 필터 (날짜, 카테고리, 태그)
- [ ] 대시보드 및 통계
- [ ] 관리자 페이지
- [ ] 사용자 알림 시스템

### Phase 7: 최적화
- [ ] 검색 결과 캐싱 (Redis)
- [ ] 벡터 인덱스 최적화
- [ ] LLM 응답 스트리밍
- [ ] CDN 적용
- [ ] 데이터베이스 샤딩
- [ ] 로드 밸런싱

### Phase 8: 확장 기능
- [ ] 다국어 지원 (영어, 중국어, 일본어)
- [ ] 음성 검색 (STT)
- [ ] 검색 추천 시스템
- [ ] 협업 기능 (공유, 코멘트)
- [ ] 모바일 앱

## 🤝 기여하기

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m '✨ feat: Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Commit Convention

```
✨ feat: 새로운 기능
🐛 fix: 버그 수정
📝 docs: 문서 수정
🎨 style: 코드 포맷팅
♻️  refactor: 리팩토링
✅ test: 테스트 추가/수정
🚀 perf: 성능 개선
🔧 chore: 빌드/설정 변경
🔒 security: 보안 수정
```

## 📄 라이선스

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 팀

- **Backend Team** - FastAPI, RAG Pipeline, Database
- **Frontend Team** - Next.js, UI/UX
- **Infrastructure Team** - Docker, Milvus, PostgreSQL
- **QA Team** - Testing, Security, Performance

## 📧 문의

- **GitHub Issues**: https://github.com/trendnote/cc-scaffold-demo/issues
- **Email**: support@kakaopay.com
- **Documentation**: [docs/](docs/)

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/)
- [Next.js](https://nextjs.org/)
- [Milvus](https://milvus.io/)
- [Ollama](https://ollama.ai/)
- [LangChain](https://python.langchain.com/)

---

**Made with ❤️ by KakaoPay Team**
