# Task 4.4 실행 계획: README 및 운영 문서 작성

## 📋 작업 정보
- **Task ID**: 4.4
- **Task명**: README 및 운영 문서 작성
- **예상 시간**: 4시간
- **담당**: All (Backend, Frontend, Infrastructure)
- **의존성**: Task 4.3a, 4.3b, 4.3c (모든 테스트 완료)
- **GitHub Issue**: #35

---

## 🎯 작업 목표

새로운 팀원이 README만으로 30분 이내에 시스템을 실행할 수 있도록 명확한 문서 작성

---

## 📝 문서 구조

```
docs/
├── README.md                        # 프로젝트 개요 및 빠른 시작
├── operations/
│   ├── deployment-guide.md          # 배포 가이드
│   ├── troubleshooting.md           # 트러블슈팅
│   ├── monitoring.md                # 모니터링 가이드
│   └── backup-restore.md            # 백업 및 복구
├── development/
│   ├── setup.md                     # 개발 환경 설정
│   ├── coding-standards.md          # 코딩 표준
│   └── testing-guide.md             # 테스트 가이드
└── api/
    └── api-reference.md             # API 레퍼런스
```

---

## 📝 구현 계획

### Phase 1: README.md 작성 (1시간)

**파일**: `README.md`
```markdown
# RAG 기반 사내 정보 검색 플랫폼

AI 기반 자연어 검색으로 사내 문서를 빠르게 찾고 정확한 답변을 제공하는 플랫폼입니다.

## 🎯 주요 기능

- ✅ 자연어 검색 (한국어 지원)
- ✅ RAG 기반 정확한 답변 생성
- ✅ 출처 문서 추적 및 링크 제공
- ✅ 권한 기반 문서 필터링
- ✅ 검색 히스토리 관리
- ✅ 사용자 피드백 수집

## 🚀 빠른 시작

### 사전 요구사항

- Docker 및 Docker Compose
- Git
- Node.js 18+ (프론트엔드 개발 시)
- Python 3.11+ (백엔드 개발 시)

### 1. 저장소 클론

\`\`\`bash
git clone https://github.com/your-org/rag-platform.git
cd rag-platform
\`\`\`

### 2. 환경 변수 설정

\`\`\`bash
# .env 파일 생성
cp .env.example .env

# 필수 환경 변수 설정
vi .env
\`\`\`

**필수 환경 변수**:
```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/rag_db

# JWT
JWT_SECRET=your-secret-key-here  # openssl rand -hex 32

# LLM Provider (ollama 또는 openai)
LLM_PROVIDER=ollama

# OpenAI (선택사항)
# OPENAI_API_KEY=sk-...
```

### 3. 서비스 시작

\`\`\`bash
# Docker Compose로 전체 서비스 시작
docker-compose up -d

# 서비스 확인
docker-compose ps
\`\`\`

**실행되는 서비스**:
- Backend API: http://localhost:8000
- Frontend: http://localhost:3000
- PostgreSQL: localhost:5432
- Milvus: localhost:19530
- Attu (Milvus UI): http://localhost:8080

### 4. 초기 데이터 설정

\`\`\`bash
# DB 마이그레이션
docker-compose exec backend alembic upgrade head

# 테스트 문서 인덱싱 (선택사항)
docker-compose exec backend python scripts/index_sample_docs.py
\`\`\`

### 5. 접속 확인

- **프론트엔드**: http://localhost:3000
- **API 문서**: http://localhost:8000/docs
- **Milvus UI**: http://localhost:8080

**테스트 계정**:
- 일반 사용자: `user@example.com` / `password123`
- 관리자: `admin@example.com` / `password123`

## 📖 사용 방법

### 검색하기

1. http://localhost:3000 접속
2. 로그인 (테스트 계정 사용)
3. 검색창에 질문 입력 (예: "연차 사용 방법")
4. 답변 및 출처 문서 확인

### 문서 인덱싱

\`\`\`bash
# 문서 저장소에 파일 추가
cp your-document.pdf /path/to/document-storage/

# 수동 인덱싱 트리거 (관리자 권한 필요)
curl -X POST http://localhost:8000/api/v1/admin/index \
  -H "Authorization: Bearer <admin-token>"

# 자동 인덱싱 (매일 새벽 2시 자동 실행)
# 별도 설정 불필요
\`\`\`

## 🛠️ 개발 환경 설정

자세한 내용은 [개발 환경 설정 가이드](docs/development/setup.md)를 참고하세요.

### 백엔드 개발

\`\`\`bash
cd backend

# 가상 환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\\Scripts\\activate

# 의존성 설치
pip install -r requirements.txt

# 개발 서버 실행
uvicorn app.main:app --reload
\`\`\`

### 프론트엔드 개발

\`\`\`bash
cd frontend

# 의존성 설치
npm install

# 개발 서버 실행
npm run dev
\`\`\`

## 🧪 테스트 실행

\`\`\`bash
# 백엔드 테스트
cd backend
pytest tests/ -v

# 프론트엔드 테스트
cd frontend
npm run test

# E2E 테스트
cd frontend
npm run test:e2e

# 성능 테스트
cd backend
bash scripts/run_load_test.sh
\`\`\`

## 📊 모니터링

- **로그 위치**: `/var/log/rag-platform/`
- **로그 확인**: `docker-compose logs -f backend`
- **성능 메트릭**: API 응답에 포함 (개발 모드)

자세한 내용은 [모니터링 가이드](docs/operations/monitoring.md)를 참고하세요.

## 🐛 트러블슈팅

일반적인 문제 해결은 [트러블슈팅 가이드](docs/operations/troubleshooting.md)를 참고하세요.

### 자주 발생하는 문제

#### 1. Milvus 연결 실패
\`\`\`bash
# Milvus 재시작
docker-compose restart milvus-standalone

# 로그 확인
docker-compose logs milvus-standalone
\`\`\`

#### 2. LLM 응답 느림
\`\`\`bash
# Ollama → OpenAI 전환
vi .env
# LLM_PROVIDER=openai
# OPENAI_API_KEY=sk-...

docker-compose restart backend
\`\`\`

#### 3. 프론트엔드 빌드 에러
\`\`\`bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run build
\`\`\`

## 📚 문서

- [배포 가이드](docs/operations/deployment-guide.md)
- [API 레퍼런스](docs/api/api-reference.md)
- [코딩 표준](docs/development/coding-standards.md)
- [테스트 가이드](docs/development/testing-guide.md)

## 🏗️ 아키텍처

```
┌─────────────────────────────────────────────┐
│              Frontend (Next.js)             │
│  - 검색 UI                                   │
│  - 히스토리 관리                              │
│  - 피드백 수집                                │
└──────────────────┬──────────────────────────┘
                   │ REST API
┌──────────────────▼──────────────────────────┐
│           Backend (FastAPI)                 │
│  - RAG Pipeline                             │
│  - 권한 제어                                 │
│  - API Gateway                              │
└──────────────────┬──────────────────────────┘
                   │
        ┌──────────┼──────────┐
        ▼          ▼          ▼
┌──────────┐ ┌──────────┐ ┌──────────┐
│PostgreSQL│ │  Milvus  │ │  Ollama  │
│(메타데이터)│ │  (벡터)  │ │  (LLM)   │
└──────────┘ └──────────┘ └──────────┘
```

## 🤝 기여하기

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 라이선스

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 팀

- Backend Team
- Frontend Team
- Infrastructure Team

## 📧 문의

- 이슈 트래커: https://github.com/your-org/rag-platform/issues
- 이메일: support@your-company.com
```

---

### Phase 2: 운영 문서 작성 (2시간)

#### 2.1 배포 가이드
**파일**: `docs/operations/deployment-guide.md`
```markdown
# 배포 가이드

## 목차
1. [환경 준비](#환경-준비)
2. [배포 절차](#배포-절차)
3. [환경별 설정](#환경별-설정)
4. [롤백 절차](#롤백-절차)

## 환경 준비

### 시스템 요구사항

**최소 사양**:
- CPU: 4 cores
- RAM: 8GB
- Disk: 100GB SSD
- OS: Ubuntu 20.04 LTS

**권장 사양**:
- CPU: 8 cores
- RAM: 16GB
- Disk: 500GB SSD
- OS: Ubuntu 22.04 LTS

### 필수 소프트웨어

\`\`\`bash
# Docker 및 Docker Compose 설치
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Docker Compose 설치
sudo apt-get install docker-compose-plugin
\`\`\`

## 배포 절차

### 1. 코드 배포

\`\`\`bash
# 저장소 클론
git clone https://github.com/your-org/rag-platform.git
cd rag-platform

# 특정 버전 체크아웃
git checkout tags/v1.0.0
\`\`\`

### 2. 환경 변수 설정

\`\`\`bash
# 운영 환경 변수 설정
cp .env.production .env
vi .env

# [HARD RULE] 필수 확인 사항:
# - JWT_SECRET: 강력한 랜덤 값 설정
# - DATABASE_URL: 실제 DB 연결 정보
# - ALLOWED_ORIGINS: 실제 프론트엔드 도메인만 허용
\`\`\`

### 3. 서비스 시작

\`\`\`bash
# 운영 환경으로 시작
docker-compose -f docker-compose.prod.yml up -d

# 서비스 상태 확인
docker-compose ps
docker-compose logs -f
\`\`\`

### 4. DB 마이그레이션

\`\`\`bash
# 마이그레이션 실행
docker-compose exec backend alembic upgrade head

# 마이그레이션 확인
docker-compose exec backend alembic current
\`\`\`

### 5. Health Check

\`\`\`bash
# API Health Check
curl http://localhost:8000/health

# 예상 응답:
# {"status":"healthy","timestamp":"...","version":"1.0.0"}
\`\`\`

## 환경별 설정

### Development
\`\`\`env
ENVIRONMENT=development
LOG_LEVEL=DEBUG
\`\`\`

### Staging
\`\`\`env
ENVIRONMENT=staging
LOG_LEVEL=INFO
\`\`\`

### Production
\`\`\`env
ENVIRONMENT=production
LOG_LEVEL=WARNING
\`\`\`

## 롤백 절차

### 1. 이전 버전으로 롤백

\`\`\`bash
# 서비스 중지
docker-compose down

# 이전 버전 체크아웃
git checkout tags/v0.9.0

# 서비스 재시작
docker-compose -f docker-compose.prod.yml up -d
\`\`\`

### 2. DB 롤백

\`\`\`bash
# 마이그레이션 롤백
docker-compose exec backend alembic downgrade -1

# 확인
docker-compose exec backend alembic current
\`\`\`

## 백업 및 복구

자세한 내용은 [백업 및 복구 가이드](backup-restore.md)를 참고하세요.
```

#### 2.2 트러블슈팅 가이드
**파일**: `docs/operations/troubleshooting.md`
```markdown
# 트러블슈팅 가이드

## 목차
1. [서비스 시작 문제](#서비스-시작-문제)
2. [성능 문제](#성능-문제)
3. [연결 문제](#연결-문제)
4. [로그 확인](#로그-확인)

## 서비스 시작 문제

### PostgreSQL 연결 실패

**증상**:
\`\`\`
sqlalchemy.exc.OperationalError: could not connect to server
\`\`\`

**해결 방법**:
\`\`\`bash
# 1. PostgreSQL 상태 확인
docker-compose ps postgres

# 2. PostgreSQL 로그 확인
docker-compose logs postgres

# 3. PostgreSQL 재시작
docker-compose restart postgres

# 4. 연결 테스트
docker-compose exec postgres psql -U postgres -c "SELECT 1"
\`\`\`

### Milvus 연결 실패

**증상**:
\`\`\`
pymilvus.exceptions.MilvusException: <MilvusClient: timeout>
\`\`\`

**해결 방법**:
\`\`\`bash
# 1. Milvus 상태 확인
docker-compose ps milvus-standalone

# 2. Milvus 재시작
docker-compose restart milvus-standalone etcd minio

# 3. Attu UI로 확인
# http://localhost:8080

# 4. Collection 확인
docker-compose exec backend python -c "
from app.db.milvus_client import get_milvus_client
client = get_milvus_client()
print(client.list_collections())
"
\`\`\`

## 성능 문제

### 검색 응답 느림 (> 30초)

**진단**:
\`\`\`bash
# 로그에서 컴포넌트별 시간 확인
docker-compose logs backend | grep "response_time"
\`\`\`

**해결 방법**:

1. **벡터 검색 느림** (> 2초)
   \`\`\`python
   # backend/app/core/config.py
   MILVUS_SEARCH_EF = 32  # 64 → 32로 감소
   \`\`\`

2. **LLM 호출 느림** (> 25초)
   \`\`\`bash
   # Ollama → OpenAI 전환
   vi .env
   # LLM_PROVIDER=openai
   # OPENAI_API_KEY=sk-...

   docker-compose restart backend
   \`\`\`

3. **DB 쿼리 느림** (> 1초)
   \`\`\`bash
   # Connection Pool 증가
   # backend/app/core/config.py
   DB_POOL_SIZE = 20  # 5 → 20
   \`\`\`

### 메모리 부족

**증상**:
\`\`\`
MemoryError: Unable to allocate array
\`\`\`

**해결 방법**:
\`\`\`bash
# Docker 메모리 제한 확인
docker stats

# docker-compose.yml 수정
services:
  backend:
    mem_limit: 4g  # 메모리 제한 증가
\`\`\`

## 연결 문제

### CORS 에러

**증상**:
\`\`\`
Access to XMLHttpRequest has been blocked by CORS policy
\`\`\`

**해결 방법**:
\`\`\`python
# backend/app/core/config.py
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "https://your-domain.com"  # 운영 도메인 추가
]
\`\`\`

## 로그 확인

### 로그 위치

- **백엔드**: `/var/log/rag-platform/app.log`
- **에러 로그**: `/var/log/rag-platform/error.log`

### 로그 확인 명령어

\`\`\`bash
# 실시간 로그 확인
docker-compose logs -f backend

# 최근 100줄
docker-compose logs --tail=100 backend

# 에러만 필터링
docker-compose logs backend | grep ERROR

# 특정 시간대 로그
docker-compose logs --since 2026-01-10T10:00:00 backend
\`\`\`

## 자주 묻는 질문 (FAQ)

### Q1: 서비스 재시작 시 데이터가 사라지나요?
A: 아니요. PostgreSQL과 Milvus 데이터는 Docker 볼륨에 저장되어 영구 보존됩니다.

### Q2: LLM 모델을 변경하려면?
A: `.env` 파일에서 `LLM_PROVIDER`를 변경하고 서비스를 재시작하세요.

### Q3: 관리자 계정을 추가하려면?
A: 현재는 Mock 인증이므로 `backend/app/routers/auth.py`에서 `MOCK_USERS`에 추가하세요.
```

---

### Phase 3: 개발 문서 작성 (0.5시간)

**파일**: `docs/development/setup.md`
```markdown
# 개발 환경 설정

## 백엔드 개발

### 1. 가상 환경 설정
\`\`\`bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt  # 개발 의존성
\`\`\`

### 2. 개발 서버 실행
\`\`\`bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
\`\`\`

### 3. 테스트 실행
\`\`\`bash
pytest tests/ -v --cov=app
\`\`\`

## 프론트엔드 개발

### 1. 의존성 설치
\`\`\`bash
cd frontend
npm install
\`\`\`

### 2. 개발 서버 실행
\`\`\`bash
npm run dev
\`\`\`

### 3. 빌드
\`\`\`bash
npm run build
npm run start
\`\`\`

## 코드 품질 도구

### 백엔드
\`\`\`bash
# Linting
black app/
isort app/
flake8 app/

# 타입 체크
mypy app/
\`\`\`

### 프론트엔드
\`\`\`bash
# Linting
npm run lint
npm run lint:fix

# 타입 체크
npm run type-check
\`\`\`
```

---

### Phase 4: API 문서 작성 (0.5시간)

**파일**: `docs/api/api-reference.md`
```markdown
# API 레퍼런스

## 기본 정보

- **Base URL**: `http://localhost:8000/api/v1`
- **인증**: JWT Bearer Token
- **응답 포맷**: JSON

## 인증 API

### POST /auth/login
사용자 로그인 및 JWT 토큰 발급

**Request**:
\`\`\`json
{
  "email": "user@example.com",
  "password": "password123"
}
\`\`\`

**Response** (200):
\`\`\`json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user": {
    "id": "...",
    "email": "user@example.com",
    "name": "일반 사용자"
  }
}
\`\`\`

## 검색 API

### POST /search/
자연어 검색 및 RAG 답변 생성

**Request**:
\`\`\`json
{
  "query": "연차 사용 방법",
  "limit": 5
}
\`\`\`

**Response** (200):
\`\`\`json
{
  "query_id": "qry_abc123",
  "query": "연차 사용 방법",
  "answer": "연차는 입사일 기준 1년 후부터 사용 가능하며...",
  "sources": [
    {
      "document_id": "doc_001",
      "document_title": "휴가 규정",
      "relevance_score": 0.95
    }
  ],
  "performance": {
    "total_time_ms": 2500
  }
}
\`\`\`

자세한 API 문서는 http://localhost:8000/docs 참고
```

---

## ✅ 검증 기준

### 문서 완성도
- [ ] README.md 완성
- [ ] 배포 가이드 완성
- [ ] 트러블슈팅 가이드 완성
- [ ] API 레퍼런스 완성

### 사용성 테스트
- [ ] **새로운 팀원 테스트**
  - README만으로 30분 이내 실행 성공
  - 2명의 신규 팀원 테스트
  - 피드백 수집 및 반영

---

## 📂 파일 구조

```
docs/
├── README.md
├── operations/
│   ├── deployment-guide.md
│   ├── troubleshooting.md
│   ├── monitoring.md
│   └── backup-restore.md
├── development/
│   ├── setup.md
│   ├── coding-standards.md
│   └── testing-guide.md
└── api/
    └── api-reference.md
```

---

## 🔄 문서 유지보수

### 업데이트 주기
- **README.md**: 메이저 릴리스 시
- **API 문서**: API 변경 시
- **트러블슈팅**: 새로운 이슈 발생 시

### 문서 리뷰
- 분기별 문서 리뷰
- 신규 팀원 피드백 수집

---

**작성자**: Task Planner
**작성일**: 2026-01-10
**버전**: 1.0.0
