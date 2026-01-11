# 트러블슈팅 가이드 (Troubleshooting Guide)

## 목차

1. [인프라 문제](#인프라-문제)
2. [백엔드 문제](#백엔드-문제)
3. [프론트엔드 문제](#프론트엔드-문제)
4. [성능 문제](#성능-문제)
5. [보안 문제](#보안-문제)
6. [디버깅 도구](#디버깅-도구)

---

## 인프라 문제

### 1. Docker 서비스 시작 실패

**증상**:
```bash
docker-compose up -d
# Error: some services failed to start
```

**원인 및 해결**:

#### 1.1 포트 충돌

```bash
# 증상 확인
docker-compose logs | grep "port is already allocated"

# 해결: 사용 중인 포트 확인
lsof -i :5432   # PostgreSQL
lsof -i :19530  # Milvus
lsof -i :11434  # Ollama
lsof -i :8080   # Attu

# 프로세스 종료
kill -9 <PID>

# 또는 docker-compose.yml에서 포트 변경
# ports:
#   - "5433:5432"  # 호스트 포트 변경
```

#### 1.2 디스크 공간 부족

```bash
# 디스크 사용량 확인
df -h

# Docker 디스크 사용량 확인
docker system df

# 불필요한 이미지/컨테이너/볼륨 정리
docker system prune -a --volumes

# 주의! 이 명령은 모든 미사용 리소스를 삭제합니다
# 백업 후 실행하세요
```

#### 1.3 메모리 부족

```bash
# 메모리 확인
free -h

# Docker 메모리 제한 확인
docker stats

# docker-compose.yml에서 메모리 제한 추가
services:
  milvus-standalone:
    deploy:
      resources:
        limits:
          memory: 2G
```

### 2. PostgreSQL 연결 실패

**증상**:
```python
sqlalchemy.exc.OperationalError: could not connect to server
```

**해결**:

#### 2.1 서비스 상태 확인

```bash
# PostgreSQL 컨테이너 상태
docker-compose ps postgres

# 로그 확인
docker-compose logs postgres

# 재시작
docker-compose restart postgres

# 연결 테스트
docker exec -it rag-postgres pg_isready -U raguser
```

#### 2.2 환경 변수 확인

```bash
# .env 파일 확인
cat .env | grep POSTGRES

# DATABASE_URL 형식 확인
# postgresql+asyncpg://user:password@host:port/database

# 비밀번호에 특수문자가 있으면 URL 인코딩 필요
# @ → %40
# : → %3A
# / → %2F
```

#### 2.3 네트워크 확인

```bash
# Docker 네트워크 확인
docker network ls | grep rag

# 컨테이너가 같은 네트워크에 있는지 확인
docker network inspect rag-platform_rag-network

# 백엔드 컨테이너에서 PostgreSQL 접속 테스트
docker exec -it rag-backend ping postgres
```

### 3. Milvus 연결 실패

**증상**:
```python
MilvusException: <MilvusException: (code=1, message=Fail connecting to server)>
```

**해결**:

#### 3.1 서비스 의존성 확인

```bash
# Milvus는 etcd, MinIO에 의존
docker-compose ps etcd minio milvus-standalone

# 의존 서비스 재시작
docker-compose restart etcd
docker-compose restart minio
docker-compose restart milvus-standalone

# 로그 확인
docker-compose logs etcd
docker-compose logs minio
docker-compose logs milvus-standalone
```

#### 3.2 Health Check

```bash
# Milvus Health Check
curl http://localhost:9091/healthz

# 예상: {"status":"ok"}

# Attu UI 확인
# http://localhost:8080

# Connection 정보:
# Host: milvus-standalone
# Port: 19530
```

#### 3.3 Collection 초기화 문제

```bash
# Python에서 Collection 확인
cd backend
source venv/bin/activate

python3 << EOF
from app.db.milvus_client import get_milvus_client

client = get_milvus_client()
print("Collections:", client.list_collections())

# Collection 재생성이 필요한 경우
# client.drop_collection("rag_documents")
# 그 후 초기화 스크립트 재실행
EOF

# Collection 초기화
python -m app.db.init_milvus
```

### 4. Ollama 모델 문제

**증상**:
```
Error: model not found
```

**해결**:

#### 4.1 모델 다운로드 확인

```bash
# 다운로드된 모델 확인
docker exec -it rag-ollama ollama list

# 모델이 없으면 다운로드
docker exec -it rag-ollama ollama pull llama3.2:1b
docker exec -it rag-ollama ollama pull nomic-embed-text

# 다운로드 진행 상황 확인
docker exec -it rag-ollama ollama list
```

#### 4.2 모델 경로 확인

```bash
# Ollama 데이터 볼륨 확인
docker volume inspect rag-platform_ollama-data

# 볼륨 마운트 확인
docker inspect rag-ollama | grep -A 10 Mounts
```

#### 4.3 Ollama API 테스트

```bash
# API 확인
curl http://localhost:11434/api/tags

# 모델 테스트
curl http://localhost:11434/api/generate -d '{
  "model": "llama3.2:1b",
  "prompt": "Hello",
  "stream": false
}'
```

### 5. 네트워크 연결 문제

**증상**:
```
Error: Network rag-platform_rag-network not found
```

**해결**:

```bash
# 1. 네트워크 재생성
docker network create rag-platform_rag-network

# 2. 또는 docker-compose로 재생성
docker-compose down
docker-compose up -d

# 3. 네트워크 확인
docker network ls | grep rag

# 4. 네트워크 상세 정보
docker network inspect rag-platform_rag-network
```

---

## 백엔드 문제

### 1. 서버 시작 실패

**증상**:
```bash
uvicorn app.main:app --reload
# ImportError, ModuleNotFoundError 등
```

**해결**:

#### 1.1 Python 버전 확인

```bash
# Python 버전
python3 --version

# 3.11 이상 필요
# 낮은 버전이면 Python 업그레이드
brew install python@3.11  # macOS
sudo apt install python3.11  # Ubuntu
```

#### 1.2 가상환경 재생성

```bash
cd backend

# 기존 가상환경 삭제
rm -rf venv

# 새로 생성
python3 -m venv venv
source venv/bin/activate

# 의존성 재설치
pip install --upgrade pip
pip install -r requirements.txt
```

#### 1.3 환경 변수 확인

```bash
# .env 파일 존재 확인
ls -la .env

# .env 내용 확인 (시크릿 제외)
cat .env | grep -v PASSWORD | grep -v SECRET

# 필수 변수 확인
cat .env | grep -E "(DATABASE_URL|MILVUS_HOST|LLM_PROVIDER)"
```

### 2. 데이터베이스 마이그레이션 실패

**증상**:
```bash
alembic upgrade head
# ERROR: relation "users" already exists
```

**해결**:

#### 2.1 마이그레이션 상태 확인

```bash
# 현재 버전 확인
alembic current

# 마이그레이션 히스토리
alembic history

# 마이그레이션 파일 확인
ls -la alembic/versions/
```

#### 2.2 스탬프 수정

```bash
# 현재 데이터베이스 상태를 최신으로 표시
alembic stamp head

# 재시도
alembic upgrade head
```

#### 2.3 마이그레이션 재생성 (개발 환경)

```bash
# ⚠️ 주의: 개발 환경에서만 사용!
# 프로덕션에서는 절대 사용 금지!

# 1. 데이터베이스 삭제 (Docker)
docker-compose down -v postgres
docker-compose up -d postgres

# 2. 마이그레이션 재실행
alembic upgrade head
```

### 3. API 응답 느림

**증상**:
```bash
curl http://localhost:8000/api/v1/search/query
# 30초+ 소요
```

**해결**:

#### 3.1 LLM Provider 확인

```bash
# Ollama 사용 시 - GPU 확인
nvidia-smi  # NVIDIA GPU

# GPU 없으면 작은 모델 사용
docker exec -it rag-ollama ollama pull llama3.2:1b

# 또는 OpenAI로 전환
vi .env
# LLM_PROVIDER=openai
# OPENAI_API_KEY=sk-your-key

# 서버 재시작
pkill -f uvicorn
uvicorn app.main:app --reload
```

#### 3.2 로그 확인

```bash
# 백엔드 로그
tail -f backend/logs/app.log

# LLM 호출 시간 확인
grep "llm_generate" backend/logs/app.log | tail -20

# 데이터베이스 쿼리 시간 확인
grep "query" backend/logs/app.log | tail -20
```

#### 3.3 타임아웃 설정

```python
# app/core/config.py

class Settings(BaseSettings):
    # LLM 타임아웃 증가
    LLM_TIMEOUT: int = 120  # 기본 60 → 120초

    # Milvus 타임아웃 증가
    MILVUS_TIMEOUT: int = 60
```

### 4. 401 Unauthorized 에러

**증상**:
```bash
curl http://localhost:8000/api/v1/search/query
# {"detail":"Not authenticated"}
```

**해결**:

#### 4.1 JWT 토큰 확인

```bash
# 로그인하여 토큰 받기
TOKEN=$(curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test@example.com","password":"test123"}' \
  | jq -r '.access_token')

# 토큰으로 API 호출
curl http://localhost:8000/api/v1/search/query \
  -H "Authorization: Bearer $TOKEN"
```

#### 4.2 JWT Secret 확인

```bash
# .env 파일 확인
cat .env | grep JWT_SECRET

# JWT Secret이 비어있으면 설정
openssl rand -hex 32

# .env에 추가
echo "JWT_SECRET=<generated-secret>" >> .env
```

#### 4.3 토큰 만료 시간 확인

```python
# app/core/config.py

class Settings(BaseSettings):
    JWT_EXPIRE_MINUTES: int = 30  # 토큰 유효 시간

    # 만료 시간 증가 가능 (개발 환경)
    # JWT_EXPIRE_MINUTES: int = 480  # 8시간
```

### 5. CORS 에러

**증상**:
```
Access to fetch at 'http://localhost:8000' from origin 'http://localhost:3000'
has been blocked by CORS policy
```

**해결**:

```bash
# .env 파일 확인
cat .env | grep CORS

# CORS Origins 추가
vi .env

# BACKEND_CORS_ORIGINS를 JSON 배열로 설정
BACKEND_CORS_ORIGINS=["http://localhost:3000","http://localhost:8000"]

# 서버 재시작
pkill -f uvicorn
uvicorn app.main:app --reload
```

**또는 코드 수정**:
```python
# app/main.py

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8000",
        "https://your-domain.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 프론트엔드 문제

### 1. npm install 실패

**증상**:
```bash
npm install
# ERR! code ERESOLVE
```

**해결**:

#### 1.1 npm 캐시 클리어

```bash
# 캐시 삭제
npm cache clean --force

# node_modules 삭제
rm -rf node_modules package-lock.json

# 재설치
npm install
```

#### 1.2 Node.js 버전 확인

```bash
# Node.js 버전
node --version

# 20 이상 필요
# nvm 사용
nvm install 20
nvm use 20

# npm 업그레이드
npm install -g npm@latest
```

#### 1.3 의존성 충돌 해결

```bash
# 레거시 피어 의존성 허용
npm install --legacy-peer-deps

# 또는 강제 설치
npm install --force
```

### 2. 빌드 실패

**증상**:
```bash
npm run build
# Type error: ...
```

**해결**:

#### 2.1 TypeScript 에러

```bash
# TypeScript 컴파일러 확인
npx tsc --version

# tsconfig.json 확인
cat tsconfig.json

# 타입 에러 무시 (임시)
# tsconfig.json에서:
# "strict": false,
# "skipLibCheck": true,
```

#### 2.2 환경 변수 확인

```bash
# .env.local 확인
cat .env.local

# NEXT_PUBLIC_API_URL 필수
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
```

#### 2.3 캐시 삭제

```bash
# .next 캐시 삭제
rm -rf .next

# 재빌드
npm run build
```

### 3. API 호출 실패

**증상**:
```
Network Error: Failed to fetch
```

**해결**:

#### 3.1 백엔드 확인

```bash
# 백엔드 실행 중인지 확인
curl http://localhost:8000/health

# 실행 중이 아니면
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

#### 3.2 API URL 확인

```bash
# .env.local 확인
cat frontend/.env.local

# NEXT_PUBLIC_API_URL 확인
# http://localhost:8000 (개발)
# https://api.example.com (프로덕션)
```

#### 3.3 CORS 확인

백엔드 CORS 설정 확인 (위의 [백엔드 문제 > CORS 에러](#5-cors-에러) 참고)

### 4. 페이지 로딩 느림

**증상**:
- 페이지 전환 시 3초+ 소요
- Hydration mismatch 에러

**해결**:

#### 4.1 개발 모드 확인

```bash
# 개발 모드는 느릴 수 있음
npm run dev

# 프로덕션 빌드 테스트
npm run build
npm run start
```

#### 4.2 이미지 최적화

```typescript
// next.config.ts

const config: NextConfig = {
  images: {
    formats: ['image/avif', 'image/webp'],
    deviceSizes: [640, 750, 828, 1080, 1200],
  },
};
```

#### 4.3 번들 크기 분석

```bash
# 번들 분석 도구 설치
npm install --save-dev @next/bundle-analyzer

# 빌드 & 분석
ANALYZE=true npm run build
```

---

## 성능 문제

### 1. 검색 응답 느림 (30초+)

**원인 분석**:

```bash
# 1. LLM Provider 확인
cat .env | grep LLM_PROVIDER

# 2. 로그 확인 (시간 측정)
tail -f backend/logs/app.log | grep -E "(llm_generate|milvus_search|database_query)"
```

**해결**:

#### 1.1 Ollama → OpenAI 전환

```bash
vi .env

# 변경:
# LLM_PROVIDER=ollama
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL_LLM=gpt-4o-mini
OPENAI_MODEL_EMBED=text-embedding-3-small

# 서버 재시작
```

#### 1.2 Ollama GPU 활성화

```yaml
# docker-compose.yml

services:
  ollama:
    image: ollama/ollama:latest
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

#### 1.3 더 작은 모델 사용

```bash
# 1B 파라미터 모델 (빠름)
docker exec -it rag-ollama ollama pull llama3.2:1b

# .env 수정
vi .env
# OLLAMA_MODEL_LLM=llama3.2:1b
```

### 2. 메모리 부족 (OOM)

**증상**:
```
docker-compose logs | grep "out of memory"
```

**해결**:

#### 2.1 Docker 메모리 제한 증가

```yaml
# docker-compose.yml

services:
  milvus-standalone:
    deploy:
      resources:
        limits:
          memory: 4G  # 2G → 4G
        reservations:
          memory: 2G
```

#### 2.2 Ollama 모델 메모리 확인

```bash
# 모델별 메모리 사용량
# llama3.2:1b - ~1.5GB RAM
# llama3.2:3b - ~3GB RAM
# llama3:8b - ~8GB RAM

# 작은 모델 사용
docker exec -it rag-ollama ollama pull llama3.2:1b
```

#### 2.3 시스템 메모리 확인

```bash
# 메모리 사용량
free -h

# Docker 메모리 사용량
docker stats
```

### 3. 디스크 I/O 느림

**해결**:

#### 3.1 볼륨 타입 확인

```bash
# 볼륨 정보
docker volume inspect rag-platform_postgres-data

# SSD 사용 권장
# HDD 사용 시 성능 저하
```

#### 3.2 로그 로테이션 설정

```bash
# 로그 파일 크기 확인
du -sh backend/logs/*

# 로그 로테이션 설정
# backend/app/core/logging.py
```

```python
# structlog 설정에 로테이션 추가
import logging.handlers

handler = logging.handlers.RotatingFileHandler(
    "logs/app.log",
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5,
)
```

---

## 보안 문제

### 1. JWT Secret 노출

**증상**:
- .env 파일이 Git에 커밋됨
- JWT_SECRET이 약한 문자열

**해결**:

```bash
# 1. .env 파일 Git에서 제거
git rm --cached .env
git commit -m "Remove .env from git"

# 2. .gitignore 확인
cat .gitignore | grep .env

# 3. 강력한 JWT Secret 생성
openssl rand -hex 32

# 4. .env 파일 업데이트
vi .env
# JWT_SECRET=<new-secure-random-string>

# 5. 모든 토큰 무효화 (사용자 재로그인 필요)
# 서버 재시작
```

### 2. SQL Injection 위험

**확인**:

```python
# ❌ 안전하지 않음
query = f"SELECT * FROM users WHERE email = '{email}'"

# ✅ 안전함 (SQLAlchemy 파라미터화)
from sqlalchemy import select

stmt = select(User).where(User.email == email)
```

**해결**:

- SQLAlchemy ORM 사용
- 절대 문자열 결합으로 쿼리 작성 금지

### 3. XSS (Cross-Site Scripting)

**프론트엔드 확인**:

```typescript
// ❌ 안전하지 않음
<div dangerouslySetInnerHTML={{__html: userInput}} />

// ✅ 안전함
<div>{userInput}</div>
```

**백엔드 확인**:

```python
# HTML 이스케이프
from html import escape

response = escape(user_input)
```

---

## 디버깅 도구

### 1. 로그 확인

```bash
# 백엔드 로그 (실시간)
tail -f backend/logs/app.log

# 에러만 필터링
tail -f backend/logs/app.log | grep ERROR

# 특정 사용자 로그
tail -f backend/logs/app.log | grep "user_id=123"

# Docker 로그
docker-compose logs -f backend
docker-compose logs -f postgres
docker-compose logs -f milvus-standalone
```

### 2. 데이터베이스 디버깅

```bash
# PostgreSQL 접속
docker exec -it rag-postgres psql -U raguser -d rag_platform

# 테이블 확인
\dt

# 데이터 확인
SELECT * FROM users LIMIT 10;

# 쿼리 실행 계획
EXPLAIN ANALYZE SELECT * FROM documents WHERE user_id = 1;
```

### 3. Milvus 디버깅

```bash
# Attu UI 사용 (추천)
# http://localhost:8080

# Python으로 확인
python3 << EOF
from app.db.milvus_client import get_milvus_client

client = get_milvus_client()

# Collection 리스트
print("Collections:", client.list_collections())

# Collection 정보
from pymilvus import Collection
collection = Collection("rag_documents")
print("Count:", collection.num_entities)
print("Schema:", collection.schema)
EOF
```

### 4. API 디버깅

```bash
# Swagger UI
# http://localhost:8000/docs

# ReDoc
# http://localhost:8000/redoc

# curl로 API 테스트
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test@example.com","password":"test123"}' \
  -v  # Verbose 모드
```

### 5. 성능 프로파일링

```bash
# Python 프로파일링
pip install py-spy

# 실행 중인 프로세스 프로파일링
py-spy top --pid <uvicorn-pid>

# 화염 그래프 생성
py-spy record -o profile.svg --pid <uvicorn-pid>
```

### 6. 네트워크 디버깅

```bash
# Docker 네트워크 확인
docker network inspect rag-platform_rag-network

# 컨테이너 간 통신 테스트
docker exec -it rag-backend ping postgres
docker exec -it rag-backend curl http://milvus-standalone:19530

# 포트 확인
netstat -tuln | grep -E "(5432|19530|11434|8080)"
```

---

## 빠른 참조

### 자주 사용하는 명령어

```bash
# 모든 서비스 재시작
docker-compose restart

# 로그 확인 (최근 100줄)
docker-compose logs --tail=100

# 특정 서비스 재시작
docker-compose restart postgres
docker-compose restart milvus-standalone
docker-compose restart ollama

# 백엔드 재시작
pkill -f uvicorn
cd backend && source venv/bin/activate
uvicorn app.main:app --reload

# 프론트엔드 재시작
cd frontend
npm run dev
```

### 체크리스트

문제 발생 시 순서대로 확인:

1. [ ] Docker 서비스 실행 중인지 확인 (`docker-compose ps`)
2. [ ] 로그에서 에러 확인 (`docker-compose logs`)
3. [ ] 환경 변수 확인 (`cat .env`)
4. [ ] 네트워크 연결 확인 (`docker network inspect`)
5. [ ] 포트 충돌 확인 (`lsof -i :PORT`)
6. [ ] 디스크 공간 확인 (`df -h`)
7. [ ] 메모리 확인 (`free -h`)

---

## 관련 문서

- [Deployment Guide](./deployment-guide.md) - 배포 가이드
- [Monitoring Guide](./monitoring.md) - 모니터링 및 로그 확인
- [Backup & Restore](./backup-restore.md) - 백업 및 복원 절차

---

**문제 해결이 안 되면 로그를 확인하세요!** 🔍
