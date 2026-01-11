# 배포 가이드 (Deployment Guide)

## 목차

1. [환경 준비](#환경-준비)
2. [인프라 배포](#인프라-배포)
3. [백엔드 배포](#백엔드-배포)
4. [프론트엔드 배포](#프론트엔드-배포)
5. [배포 검증](#배포-검증)
6. [롤백 절차](#롤백-절차)

---

## 환경 준비

### 필수 요구사항

**시스템 요구사항**:
- OS: Linux/macOS/Windows (WSL2)
- RAM: 최소 8GB (권장 16GB)
- Disk: 최소 20GB 여유 공간
- Network: 인터넷 연결 (모델 다운로드용)

**설치 필요 소프트웨어**:
```bash
# Docker & Docker Compose 확인
docker --version         # Docker 20.10+
docker-compose --version # Docker Compose 2.0+

# Git 확인
git --version           # Git 2.30+

# Node.js 확인 (프론트엔드)
node --version          # Node.js 20+
npm --version           # npm 10+

# Python 확인 (백엔드)
python3 --version       # Python 3.11+
```

### 환경별 설정

#### Development (개발 환경)

```bash
# 1. 저장소 클론
git clone https://github.com/your-org/cc-scaffold-demo.git
cd cc-scaffold-demo

# 2. 환경 변수 설정
cp .env.example .env

# .env 파일 수정 (개발 환경용)
vi .env
```

**.env 개발 환경 설정**:
```env
# PostgreSQL
POSTGRES_USER=raguser
POSTGRES_PASSWORD=dev_password_123
POSTGRES_DB=rag_platform

# Database URL
DATABASE_URL=postgresql+asyncpg://raguser:dev_password_123@localhost:5432/rag_platform

# Milvus
MILVUS_HOST=localhost
MILVUS_PORT=19530

# LLM Provider
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL_LLM=llama3.2:1b
OLLAMA_MODEL_EMBED=nomic-embed-text

# JWT Secret (개발용)
JWT_SECRET=dev_secret_key_change_in_production_123456789
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30

# CORS
BACKEND_CORS_ORIGINS=["http://localhost:3000","http://localhost:8000"]

# Logging
LOG_LEVEL=DEBUG
```

#### Staging (스테이징 환경)

```bash
# 1. 환경 변수 설정
cp .env.example .env.staging

# .env.staging 파일 수정
vi .env.staging
```

**.env 스테이징 설정**:
```env
# PostgreSQL
POSTGRES_PASSWORD=staging_secure_password_CHANGE_ME

# Database URL
DATABASE_URL=postgresql+asyncpg://raguser:staging_secure_password_CHANGE_ME@postgres:5432/rag_platform

# LLM Provider (OpenAI 사용 권장)
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-staging-key-CHANGE_ME
OPENAI_MODEL_LLM=gpt-4o-mini
OPENAI_MODEL_EMBED=text-embedding-3-small

# JWT Secret (강력한 랜덤 키)
JWT_SECRET=staging_random_secret_GENERATE_RANDOM_STRING_HERE
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60

# CORS (스테이징 도메인)
BACKEND_CORS_ORIGINS=["https://staging-fe.example.com"]

# Logging
LOG_LEVEL=INFO
```

**강력한 JWT Secret 생성**:
```bash
# 방법 1: OpenSSL
openssl rand -hex 32

# 방법 2: Python
python3 -c "import secrets; print(secrets.token_hex(32))"

# 방법 3: Node.js
node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"
```

#### Production (프로덕션 환경)

```bash
# 1. 환경 변수 설정 (절대 .env 파일을 커밋하지 마세요!)
cp .env.example .env.production

# .env.production 파일 수정
vi .env.production
```

**.env 프로덕션 설정**:
```env
# PostgreSQL
POSTGRES_PASSWORD=PRODUCTION_SECURE_PASSWORD_CHANGE_ME

# Database URL
DATABASE_URL=postgresql+asyncpg://raguser:PRODUCTION_SECURE_PASSWORD_CHANGE_ME@postgres:5432/rag_platform

# LLM Provider (OpenAI 사용 권장)
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-prod-key-CHANGE_ME
OPENAI_MODEL_LLM=gpt-4o
OPENAI_MODEL_EMBED=text-embedding-3-large

# JWT Secret (최소 64자 이상 랜덤)
JWT_SECRET=PRODUCTION_RANDOM_SECRET_MINIMUM_64_CHARS_CHANGE_ME
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=120

# CORS (프로덕션 도메인만)
BACKEND_CORS_ORIGINS=["https://app.example.com"]

# Logging
LOG_LEVEL=WARNING
```

**프로덕션 보안 체크리스트**:
- [ ] JWT_SECRET이 최소 64자 이상의 랜덤 문자열인지 확인
- [ ] POSTGRES_PASSWORD가 강력한 비밀번호인지 확인
- [ ] OPENAI_API_KEY가 프로덕션용 키인지 확인
- [ ] CORS_ORIGINS에 프로덕션 도메인만 설정되어 있는지 확인
- [ ] LOG_LEVEL이 WARNING 또는 ERROR로 설정되어 있는지 확인
- [ ] .env 파일이 .gitignore에 포함되어 있는지 확인

---

## 인프라 배포

### 1. Docker Compose로 인프라 시작

```bash
# 1. 인프라 서비스 시작
docker-compose up -d

# 2. 서비스 상태 확인
docker-compose ps

# 3. 로그 확인 (모든 서비스 정상 시작 확인)
docker-compose logs

# 4. 개별 서비스 상태 확인
docker-compose logs postgres
docker-compose logs milvus-standalone
docker-compose logs etcd
docker-compose logs minio
docker-compose logs ollama
docker-compose logs attu
```

**예상 출력**:
```
NAME                    STATUS      PORTS
rag-postgres            running     0.0.0.0:5432->5432/tcp
rag-milvus              running     0.0.0.0:19530->19530/tcp, 0.0.0.0:9091->9091/tcp
rag-etcd                running     2379/tcp, 2380/tcp
rag-minio               running     9000/tcp, 9001/tcp
rag-ollama              running     0.0.0.0:11434->11434/tcp
rag-attu                running     0.0.0.0:8080->3000/tcp
```

### 2. PostgreSQL 초기화 확인

```bash
# PostgreSQL 접속
docker exec -it rag-postgres psql -U raguser -d rag_platform

# 데이터베이스 확인
\l

# 접속 종료
\q
```

### 3. Milvus 연결 확인

```bash
# Milvus Health Check
curl http://localhost:9091/healthz

# Attu UI 접속 (브라우저)
# http://localhost:8080
```

**Attu 초기 연결 정보**:
- Milvus Address: `milvus-standalone:19530`
- Connection Name: `RAG Platform`

### 4. Ollama 모델 다운로드

```bash
# 1. Ollama 컨테이너 상태 확인
docker exec -it rag-ollama ollama --version

# 2. LLM 모델 다운로드 (llama3.2:1b - 1.3GB)
docker exec -it rag-ollama ollama pull llama3.2:1b

# 3. Embedding 모델 다운로드 (nomic-embed-text - 274MB)
docker exec -it rag-ollama ollama pull nomic-embed-text

# 4. 다운로드 확인
docker exec -it rag-ollama ollama list

# 5. 모델 테스트
docker exec -it rag-ollama ollama run llama3.2:1b "안녕하세요"
```

**예상 출력**:
```
NAME                    ID              SIZE    MODIFIED
llama3.2:1b             baf6a787fdff    1.3 GB  2 minutes ago
nomic-embed-text:latest 0a109f422b47    274 MB  1 minute ago
```

### 5. 인프라 상태 검증

```bash
# 모든 서비스 Health Check
./scripts/health_check.sh
```

**또는 수동 확인**:
```bash
# PostgreSQL
docker exec rag-postgres pg_isready -U raguser

# Milvus
curl -f http://localhost:9091/healthz

# Ollama
curl -f http://localhost:11434/api/tags

# etcd
docker exec rag-etcd etcdctl endpoint health

# MinIO
curl -f http://localhost:9000/minio/health/live
```

---

## 백엔드 배포

### 1. Python 가상환경 설정

```bash
cd backend

# Python 버전 확인
python3 --version  # 3.11 이상 필요

# 가상환경 생성
python3 -m venv venv

# 가상환경 활성화
# macOS/Linux:
source venv/bin/activate

# Windows (PowerShell):
# .\venv\Scripts\Activate.ps1

# pip 업그레이드
pip install --upgrade pip
```

### 2. 의존성 설치

```bash
# 의존성 설치
pip install -r requirements.txt

# 설치 확인
pip list | grep -E "(fastapi|sqlalchemy|milvus)"
```

**예상 출력**:
```
fastapi                0.115.6
milvus                 2.4.11
sqlalchemy             2.0.36
```

### 3. 데이터베이스 마이그레이션

```bash
# Alembic 초기화 확인
alembic current

# 마이그레이션 실행
alembic upgrade head

# 마이그레이션 버전 확인
alembic current
```

**예상 출력**:
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade -> 001_initial_schema
INFO  [alembic.runtime.migration] Running upgrade 001_initial_schema -> head
```

### 4. Milvus Collection 생성

```bash
# Milvus Collection 초기화 스크립트 실행
python -m app.db.init_milvus
```

**또는 Python에서 직접**:
```python
from app.db.milvus_client import get_milvus_client

client = get_milvus_client()

# Collection 확인
collections = client.list_collections()
print(f"Collections: {collections}")

# 예상: ["rag_documents"] 또는 프로젝트 설정에 따라
```

### 5. 백엔드 서버 시작

#### Development 모드

```bash
# 개발 서버 시작 (hot-reload)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 로그 레벨 설정
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --log-level debug
```

#### Production 모드

```bash
# 프로덕션 서버 시작 (멀티 워커)
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120 \
  --access-logfile - \
  --error-logfile -
```

**또는 Docker로 실행**:
```bash
# Docker 이미지 빌드
docker build -t rag-backend:latest -f backend/Dockerfile .

# Docker 컨테이너 실행
docker run -d \
  --name rag-backend \
  --network rag-platform_rag-network \
  -p 8000:8000 \
  --env-file .env \
  rag-backend:latest
```

### 6. 백엔드 상태 검증

```bash
# Health Check
curl http://localhost:8000/health

# API Docs 확인
curl http://localhost:8000/docs

# 브라우저에서 확인
# http://localhost:8000/docs (Swagger UI)
# http://localhost:8000/redoc (ReDoc)
```

**예상 Health Check 응답**:
```json
{
  "status": "healthy",
  "database": "connected",
  "milvus": "connected",
  "llm": "available"
}
```

---

## 프론트엔드 배포

### 1. Node.js 의존성 설치

```bash
cd frontend

# Node.js 버전 확인
node --version  # 20 이상 필요
npm --version   # 10 이상 필요

# 의존성 설치
npm install

# 또는 (더 빠름)
npm ci
```

### 2. 환경 변수 설정

```bash
# 프론트엔드 환경 변수
cp .env.example .env.local

# .env.local 수정
vi .env.local
```

**.env.local 설정**:
```env
# API URL
NEXT_PUBLIC_API_URL=http://localhost:8000

# Environment
NEXT_PUBLIC_ENV=development
```

**Staging/Production 설정**:
```env
# Staging
NEXT_PUBLIC_API_URL=https://api-staging.example.com
NEXT_PUBLIC_ENV=staging

# Production
NEXT_PUBLIC_API_URL=https://api.example.com
NEXT_PUBLIC_ENV=production
```

### 3. 프론트엔드 빌드

#### Development 모드

```bash
# 개발 서버 시작 (hot-reload)
npm run dev

# 포트 변경
npm run dev -- -p 3001
```

**브라우저 접속**:
```
http://localhost:3000
```

#### Production 빌드

```bash
# 1. 프로덕션 빌드
npm run build

# 2. 빌드 결과 확인
ls -lh .next/

# 3. 프로덕션 서버 시작
npm run start

# 4. 포트 변경
npm run start -- -p 3000
```

**예상 빌드 출력**:
```
Route (app)                              Size     First Load JS
┌ ○ /                                    5.2 kB         95.3 kB
├ ○ /login                               3.8 kB         93.9 kB
├ ○ /search                              8.4 kB         98.5 kB
└ ○ /history                             6.1 kB         96.2 kB

○  (Static)  prerendered as static content
```

### 4. Docker로 프론트엔드 배포 (선택)

```bash
# 1. Docker 이미지 빌드
docker build -t rag-frontend:latest -f frontend/Dockerfile .

# 2. Docker 컨테이너 실행
docker run -d \
  --name rag-frontend \
  -p 3000:3000 \
  --env-file frontend/.env.local \
  rag-frontend:latest

# 3. 상태 확인
docker logs rag-frontend
```

---

## 배포 검증

### 1. 인프라 검증

```bash
# Docker 서비스 확인
docker-compose ps

# 모든 서비스가 "running" 상태여야 함
```

### 2. 백엔드 검증

```bash
# Health Check
curl http://localhost:8000/health

# API 응답 확인
curl http://localhost:8000/docs

# 로그인 테스트 (예시)
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "test@example.com", "password": "test123"}'
```

### 3. 프론트엔드 검증

```bash
# 브라우저에서 확인
# http://localhost:3000

# 페이지 로드 테스트
curl -I http://localhost:3000

# 예상: HTTP/1.1 200 OK
```

### 4. 통합 테스트

```bash
# E2E 테스트 실행
cd frontend
npm run test:e2e

# 또는 특정 테스트만
npx playwright test tests/e2e/search.spec.ts
```

### 5. 성능 테스트 (선택)

```bash
cd backend

# Locust 부하 테스트
./scripts/run_load_test.sh

# 리포트 확인
open load-test-report.html
```

---

## 롤백 절차

### 1. 백엔드 롤백

#### 코드 롤백

```bash
cd backend

# 1. 이전 버전 확인
git log --oneline -10

# 2. 특정 커밋으로 롤백
git checkout <commit-hash>

# 3. 서버 재시작
# PID 확인
ps aux | grep uvicorn

# 종료
kill <pid>

# 재시작
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

#### 데이터베이스 롤백

```bash
# 1. 현재 마이그레이션 확인
alembic current

# 2. 이전 버전으로 다운그레이드
alembic downgrade -1

# 또는 특정 버전으로
alembic downgrade <revision>

# 3. 롤백 확인
alembic current
```

#### Docker 이미지 롤백

```bash
# 1. 이전 이미지 확인
docker images rag-backend

# 2. 이전 버전으로 교체
docker stop rag-backend
docker rm rag-backend

docker run -d \
  --name rag-backend \
  --network rag-platform_rag-network \
  -p 8000:8000 \
  --env-file .env \
  rag-backend:<previous-tag>

# 3. 상태 확인
docker logs -f rag-backend
```

### 2. 프론트엔드 롤백

```bash
cd frontend

# 1. 이전 버전으로 체크아웃
git checkout <previous-commit>

# 2. 의존성 재설치
npm ci

# 3. 빌드
npm run build

# 4. 재시작
pm2 restart rag-frontend

# 또는
npm run start
```

### 3. 인프라 롤백

```bash
# 1. 서비스 중지
docker-compose down

# 2. 이전 docker-compose.yml 복원
git checkout HEAD~1 docker-compose.yml

# 3. 재시작
docker-compose up -d

# 4. 상태 확인
docker-compose ps
docker-compose logs
```

### 4. 데이터 복원 (긴급)

```bash
# PostgreSQL 복원
cat backup-YYYYMMDD.sql | \
  docker exec -i rag-postgres psql -U raguser -d rag_platform

# Milvus 복원 (백업이 있는 경우)
# Milvus는 MinIO에 데이터를 저장하므로 MinIO 백업 복원
docker-compose stop milvus-standalone
docker volume rm rag-platform_milvus-data
docker volume create rag-platform_milvus-data

# 백업에서 복원
docker run --rm -v rag-platform_milvus-data:/data \
  -v $(pwd)/backups:/backup \
  alpine sh -c "cd /data && tar xzf /backup/milvus-backup-YYYYMMDD.tar.gz"

docker-compose start milvus-standalone
```

---

## 배포 체크리스트

### Pre-Deployment (배포 전)

- [ ] 환경 변수 파일(.env) 확인
- [ ] JWT_SECRET, POSTGRES_PASSWORD 등 시크릿 변경 확인
- [ ] CORS 설정 확인 (프로덕션 도메인만 허용)
- [ ] 로그 레벨 확인 (프로덕션: WARNING 이상)
- [ ] 데이터베이스 백업 완료
- [ ] Git 브랜치 확인 (main/master)
- [ ] 모든 테스트 통과 확인

### Deployment (배포 중)

- [ ] 인프라 서비스 시작 확인
- [ ] PostgreSQL 연결 확인
- [ ] Milvus 연결 확인
- [ ] Ollama 모델 다운로드 완료
- [ ] 데이터베이스 마이그레이션 완료
- [ ] 백엔드 서버 시작 확인
- [ ] 프론트엔드 빌드 & 시작 확인
- [ ] Health Check API 응답 확인

### Post-Deployment (배포 후)

- [ ] 로그 모니터링 (최소 10분)
- [ ] 에러 발생 여부 확인
- [ ] 성능 지표 확인 (응답 시간, CPU, 메모리)
- [ ] 사용자 테스트 시나리오 실행
- [ ] 알림 설정 확인
- [ ] 배포 완료 문서화

---

## 트러블슈팅

배포 중 문제 발생 시 [troubleshooting.md](./troubleshooting.md)를 참고하세요.

### 빠른 문제 해결

**인프라 시작 실패**:
```bash
# 로그 확인
docker-compose logs

# 개별 서비스 재시작
docker-compose restart postgres
docker-compose restart milvus-standalone
```

**백엔드 시작 실패**:
```bash
# 의존성 재설치
pip install --force-reinstall -r requirements.txt

# 데이터베이스 연결 확인
alembic current
```

**프론트엔드 빌드 실패**:
```bash
# node_modules 재설치
rm -rf node_modules package-lock.json
npm install

# 캐시 삭제
rm -rf .next
npm run build
```

---

## 관련 문서

- [Monitoring Guide](./monitoring.md) - 모니터링 및 로그 확인
- [Troubleshooting Guide](./troubleshooting.md) - 문제 해결 가이드
- [Backup & Restore](./backup-restore.md) - 백업 및 복원 절차
- [README.md](../../README.md) - 프로젝트 개요 및 빠른 시작

---

**배포 완료 후 반드시 모니터링하세요!** 📊
