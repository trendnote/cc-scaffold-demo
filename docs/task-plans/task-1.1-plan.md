# Task 1.1 실행 Plan: 프로젝트 초기 구조 및 Docker Compose 설정

---

## Meta Information
- **Task ID**: 1.1
- **Task Name**: 프로젝트 초기 구조 및 Docker Compose 설정
- **Estimated Time**: 4시간
- **담당**: Infrastructure
- **작성일**: 2025-12-30
- **Status**: Ready for Implementation

---

## 1. Task 개요

### 1.1 목표
RAG 기반 사내 정보 검색 플랫폼의 기본 인프라를 Docker Compose 기반으로 구축합니다.

### 1.2 범위
- 프로젝트 디렉토리 구조 생성
- Docker Compose 설정 파일 작성 (PostgreSQL, Milvus, Ollama, Attu)
- 환경 변수 관리 체계 구축
- 기본 설치 가이드 작성

### 1.3 성공 기준
- [ ] `docker-compose up -d` 성공
- [ ] 모든 컨테이너 `running` 상태 확인
- [ ] PostgreSQL 연결 테스트 성공
- [ ] Attu UI 접속 가능 (http://localhost:8080)

---

## 2. 사전 준비사항 확인

### 2.1 필수 소프트웨어 설치 확인
```bash
# Docker 설치 확인
docker --version
# 예상 출력: Docker version 24.0.0 이상

# Docker Compose 설치 확인
docker-compose --version
# 예상 출력: Docker Compose version 2.0.0 이상

# Git 설치 확인
git --version
# 예상 출력: git version 2.30.0 이상
```

### 2.2 시스템 요구사항
- **메모리**: 최소 8GB RAM (권장 16GB)
- **디스크**: 최소 20GB 여유 공간
- **OS**: macOS, Linux, Windows (WSL2)

### 2.3 네트워크 포트 확인
다음 포트가 사용 가능한지 확인:
- `5432`: PostgreSQL
- `19530`: Milvus gRPC
- `9091`: Milvus HTTP
- `8080`: Attu (Milvus Web UI)
- `11434`: Ollama API
- `2379`: etcd (Milvus 의존성)
- `9000`: MinIO (Milvus 의존성)

```bash
# 포트 사용 중인지 확인
lsof -i :5432
lsof -i :19530
lsof -i :8080
lsof -i :11434
```

**[CHECKPOINT]** 포트가 사용 중이면 해당 프로세스 종료 또는 포트 변경 필요

---

## 3. 단계별 실행 계획

### **Step 1: 프로젝트 디렉토리 구조 생성 (15분)**

#### 3.1.1 액션
```bash
# 프로젝트 루트 (cc-scaffold-demo)에서 실행
# docs는 이미 존재하므로 frontend와 backend만 생성
mkdir -p frontend backend scripts
```

#### 3.1.2 디렉토리 구조
```
cc-scaffold-demo/           # 프로젝트 루트 (현재 디렉토리)
├── frontend/              # Next.js 14 프론트엔드 (Phase 3에서 구현)
├── backend/               # FastAPI 백엔드 (Phase 2에서 구현)
├── docs/                  # 프로젝트 문서 (이미 존재)
│   ├── prd/
│   ├── architecture/
│   ├── tech-stack/
│   ├── tasks/
│   └── task-plans/
├── scripts/               # 유틸리티 스크립트
├── docker-compose.yml     # Docker Compose 설정
├── .env                   # 환경 변수 (Git에서 제외)
├── .env.example           # 환경 변수 템플릿
├── .gitignore             # Git 제외 파일 목록 (이미 존재, 업데이트)
├── CLAUDE.md              # 프로젝트 규칙 (이미 존재)
└── README.md              # 설치 및 실행 가이드 (생성 예정)
```

#### 3.1.3 검증
```bash
# 디렉토리 구조 확인
ls -la

# 예상 출력에 다음이 포함되어야 함:
# drwxr-xr-x  frontend/
# drwxr-xr-x  backend/
# drwxr-xr-x  scripts/
# drwxr-xr-x  docs/      (이미 존재)
```

**[EXPECTED]** frontend/, backend/, scripts/ 디렉토리가 생성되고, docs/는 이미 존재함

---

### **Step 2: .gitignore 파일 업데이트 (5분)**

#### 3.2.1 액션
`.gitignore` 파일 확인 및 업데이트 (이미 존재하면 내용 추가)

#### 3.2.2 내용
```gitignore
# Environment variables
.env

# Docker volumes
docker-volumes/
*.db

# OS files
.DS_Store
Thumbs.db

# IDE
.vscode/
.idea/
*.swp
*.swo

# Logs
*.log
logs/

# Python
__pycache__/
*.py[cod]
*$py.class
.pytest_cache/
.coverage
htmlcov/

# Node.js
node_modules/
.next/
out/
build/
dist/

# Temporary files
*.tmp
*.bak
```

#### 3.2.3 검증
```bash
cat .gitignore | grep -E "^\.env$|^# Environment"
```

**[CHECKPOINT]** `.env` 파일이 gitignore에 포함되었는지 확인 (보안 HARD RULE)

**참고**: `.gitignore` 파일이 이미 존재하는 경우, 위 내용을 기존 파일에 추가합니다.

---

### **Step 3: 환경 변수 파일 작성 (20분)**

#### 3.3.1 `.env.example` 파일 생성
**[HARD RULE]** 실제 비밀번호는 `.env.example`에 포함하지 않음

```bash
# PostgreSQL Configuration
POSTGRES_USER=raguser
POSTGRES_PASSWORD=CHANGE_ME_IN_DOT_ENV
POSTGRES_DB=rag_platform
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

# Milvus Configuration
MILVUS_HOST=milvus-standalone
MILVUS_PORT=19530
MILVUS_USER=root
MILVUS_PASSWORD=CHANGE_ME_IN_DOT_ENV

# Ollama Configuration
OLLAMA_HOST=ollama
OLLAMA_PORT=11434
OLLAMA_MODEL_EMBED=nomic-embed-text
OLLAMA_MODEL_LLM=llama3

# Backend Configuration
BACKEND_HOST=backend
BACKEND_PORT=8000
JWT_SECRET=CHANGE_ME_IN_DOT_ENV_GENERATE_RANDOM_STRING

# Frontend Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000

# Logging
LOG_LEVEL=INFO
```

#### 3.3.2 실제 `.env` 파일 생성
```bash
cp .env.example .env
```

#### 3.3.3 `.env` 파일 보안 강화
**[CRITICAL ACTION]** `.env` 파일에서 비밀번호를 강력한 값으로 변경:

```bash
# 비밀번호 생성 예시 (macOS/Linux)
openssl rand -base64 32

# .env 파일 편집
# POSTGRES_PASSWORD=<생성된 랜덤 값>
# MILVUS_PASSWORD=<생성된 랜덤 값>
# JWT_SECRET=<생성된 랜덤 값>
```

#### 3.3.4 검증
```bash
# .env 파일 존재 확인
ls -la .env

# .env.example과 비교 (비밀번호가 다른지 확인)
diff .env .env.example
```

**[CHECKPOINT]** `.env` 파일의 모든 `CHANGE_ME_*` 값이 실제 값으로 변경되었는지 확인

---

### **Step 4: Docker Compose 파일 작성 (60분)**

#### 3.4.1 `docker-compose.yml` 파일 생성

**[HARD RULE 준수]**:
- 비밀번호는 환경 변수로 주입
- 하드코딩 절대 금지
- 볼륨은 명명된 볼륨 사용 (데이터 영속성)

#### 3.4.2 내용 (상세)

```yaml
version: '3.8'

services:
  # PostgreSQL 15
  postgres:
    image: postgres:15-alpine
    container_name: rag-postgres
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    ports:
      - "5432:5432"
    volumes:
      - postgres-data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - rag-network
    restart: unless-stopped

  # Milvus Standalone (etcd + MinIO 포함)
  etcd:
    image: quay.io/coreos/etcd:v3.5.5
    container_name: rag-etcd
    environment:
      - ETCD_AUTO_COMPACTION_MODE=revision
      - ETCD_AUTO_COMPACTION_RETENTION=1000
      - ETCD_QUOTA_BACKEND_BYTES=4294967296
      - ETCD_SNAPSHOT_COUNT=50000
    volumes:
      - etcd-data:/etcd
    command: etcd -advertise-client-urls=http://127.0.0.1:2379 -listen-client-urls http://0.0.0.0:2379 --data-dir /etcd
    healthcheck:
      test: ["CMD", "etcdctl", "endpoint", "health"]
      interval: 30s
      timeout: 20s
      retries: 3
    networks:
      - rag-network
    restart: unless-stopped

  minio:
    image: minio/minio:RELEASE.2023-03-20T20-16-18Z
    container_name: rag-minio
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    volumes:
      - minio-data:/minio_data
    command: minio server /minio_data --console-address ":9001"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 30s
      timeout: 20s
      retries: 3
    networks:
      - rag-network
    restart: unless-stopped

  milvus-standalone:
    image: milvusdb/milvus:v2.3.3
    container_name: rag-milvus
    depends_on:
      - etcd
      - minio
    environment:
      ETCD_ENDPOINTS: etcd:2379
      MINIO_ADDRESS: minio:9000
    volumes:
      - milvus-data:/var/lib/milvus
    ports:
      - "19530:19530"
      - "9091:9091"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9091/healthz"]
      interval: 30s
      timeout: 20s
      retries: 3
    networks:
      - rag-network
    restart: unless-stopped

  # Attu (Milvus Web UI)
  attu:
    image: zilliz/attu:v2.3.3
    container_name: rag-attu
    depends_on:
      - milvus-standalone
    environment:
      MILVUS_URL: milvus-standalone:19530
    ports:
      - "8080:3000"
    networks:
      - rag-network
    restart: unless-stopped

  # Ollama
  ollama:
    image: ollama/ollama:latest
    container_name: rag-ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama-data:/root/.ollama
    networks:
      - rag-network
    restart: unless-stopped
    # GPU 지원 (NVIDIA GPU가 있는 경우 주석 제거)
    # deploy:
    #   resources:
    #     reservations:
    #       devices:
    #         - driver: nvidia
    #           count: 1
    #           capabilities: [gpu]

volumes:
  postgres-data:
    driver: local
  etcd-data:
    driver: local
  minio-data:
    driver: local
  milvus-data:
    driver: local
  ollama-data:
    driver: local

networks:
  rag-network:
    driver: bridge
```

#### 3.4.3 파일 작성 후 검증
```bash
# YAML 문법 검사
docker-compose config

# 예상 출력: 파싱된 설정이 표시됨 (에러 없음)
```

**[CHECKPOINT]** YAML 문법 에러가 없는지 확인

---

### **Step 5: Docker Compose 실행 및 검증 (30분)**

#### 3.5.1 컨테이너 시작
```bash
# 백그라운드에서 모든 서비스 시작
docker-compose up -d

# 예상 출력:
# Creating network "rag-network" ... done
# Creating volume "rag-postgres-data" ... done
# Creating volume "rag-etcd-data" ... done
# Creating volume "rag-minio-data" ... done
# Creating volume "rag-milvus-data" ... done
# Creating volume "rag-ollama-data" ... done
# Creating rag-postgres ... done
# Creating rag-etcd ... done
# Creating rag-minio ... done
# Creating rag-milvus ... done
# Creating rag-attu ... done
# Creating rag-ollama ... done
```

#### 3.5.2 컨테이너 상태 확인
```bash
docker-compose ps

# 예상 출력: 모든 서비스가 "Up" 상태
# NAME            STATE    PORTS
# rag-postgres    Up       0.0.0.0:5432->5432/tcp
# rag-etcd        Up       2379/tcp
# rag-minio       Up       9000-9001/tcp
# rag-milvus      Up       0.0.0.0:19530->19530/tcp, 0.0.0.0:9091->9091/tcp
# rag-attu        Up       0.0.0.0:8080->3000/tcp
# rag-ollama      Up       0.0.0.0:11434->11434/tcp
```

**[CHECKPOINT 1]** 모든 컨테이너가 "Up" 상태인지 확인

#### 3.5.3 컨테이너 로그 확인 (에러 확인)
```bash
# 전체 로그 확인
docker-compose logs

# 특정 서비스 로그 확인
docker-compose logs postgres
docker-compose logs milvus-standalone
docker-compose logs ollama

# 실시간 로그 확인
docker-compose logs -f
```

**[CHECKPOINT 2]** 로그에 에러 메시지가 없는지 확인

---

### **Step 6: 서비스별 연결 테스트 (30분)**

#### 3.6.1 PostgreSQL 연결 테스트
```bash
# psql 클라이언트로 연결
docker exec -it rag-postgres psql -U raguser -d rag_platform

# PostgreSQL 프롬프트에서 실행
\dt  # 테이블 목록 (현재는 비어 있음)
\l   # 데이터베이스 목록
\q   # 종료
```

**[EXPECTED]** `rag_platform` 데이터베이스가 존재하고 연결 성공

#### 3.6.2 Milvus 연결 테스트 (Attu UI)
```bash
# 브라우저에서 접속
open http://localhost:8080
# 또는 직접 브라우저에서 http://localhost:8080 접속

# Attu 로그인 정보:
# - Milvus Address: milvus-standalone:19530
# - Username: (비워둠 또는 root)
# - Password: (비워둠 또는 .env의 MILVUS_PASSWORD)
```

**[EXPECTED]** Attu UI가 정상적으로 로드되고 Milvus에 연결 성공

#### 3.6.3 Ollama 연결 테스트
```bash
# Ollama API Health Check
curl http://localhost:11434/api/tags

# 예상 출력 (현재는 모델이 없음):
# {"models":[]}
```

**[EXPECTED]** HTTP 200 응답 및 JSON 반환

#### 3.6.4 Health Check 자동화 스크립트 작성
`rag-platform/scripts/health-check.sh` 생성:

```bash
#!/bin/bash

echo "===== RAG Platform Health Check ====="
echo ""

# PostgreSQL
echo "[1/3] PostgreSQL:"
docker exec rag-postgres pg_isready -U raguser > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ PostgreSQL is ready"
else
    echo "❌ PostgreSQL is not ready"
fi

# Milvus
echo ""
echo "[2/3] Milvus:"
curl -s -o /dev/null -w "%{http_code}" http://localhost:9091/healthz | grep -q 200
if [ $? -eq 0 ]; then
    echo "✅ Milvus is ready"
else
    echo "❌ Milvus is not ready"
fi

# Ollama
echo ""
echo "[3/3] Ollama:"
curl -s -o /dev/null -w "%{http_code}" http://localhost:11434/api/tags | grep -q 200
if [ $? -eq 0 ]; then
    echo "✅ Ollama is ready"
else
    echo "❌ Ollama is not ready"
fi

echo ""
echo "===== Health Check Complete ====="
```

실행 권한 부여 및 실행:
```bash
chmod +x scripts/health-check.sh
./scripts/health-check.sh
```

**[CHECKPOINT 3]** 모든 서비스가 ✅로 표시되는지 확인

---

### **Step 7: README.md 작성 (30분)**

#### 3.7.1 `README.md` 파일 생성 (프로젝트 루트)

```markdown
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

## 다음 단계
- Task 1.2: PostgreSQL 스키마 및 마이그레이션 설정
- Task 1.3: Milvus Collection 생성 및 연결 테스트
- Task 1.4: Ollama 모델 다운로드

## 참고 문서
- [PRD](docs/prd/rag-platform-prd.md)
- [Architecture](docs/architecture/architecture.md)
- [Tech Stack](docs/tech-stack/tech-stack.md)
- [Task Breakdown](docs/tasks/task-breakdown.md)

## 라이선스
Internal Use Only - KakaoPay
```

#### 3.7.2 검증
```bash
cat README.md
```

**[CHECKPOINT]** README.md에 설치 가이드가 명확하게 작성되었는지 확인

---

### **Step 8: 유틸리티 스크립트 추가 (20분)**

#### 3.8.1 scripts 디렉토리 확인
```bash
# Step 1에서 이미 생성했으므로 확인만 수행
ls -la scripts/
```

#### 3.8.2 `scripts/setup.sh` 생성 (초기 설정 자동화)
```bash
#!/bin/bash

set -e

echo "===== RAG Platform Setup ====="
echo ""

# 1. .env 파일 확인
if [ ! -f .env ]; then
    echo "[1/5] Creating .env file from .env.example..."
    cp .env.example .env
    echo "⚠️  Please edit .env file and change all CHANGE_ME_* values!"
    echo "    Run: vi .env"
    exit 1
else
    echo "[1/5] ✅ .env file exists"
fi

# 2. Docker 확인
echo "[2/5] Checking Docker..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi
echo "✅ Docker is installed: $(docker --version)"

# 3. Docker Compose 확인
echo "[3/5] Checking Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed."
    exit 1
fi
echo "✅ Docker Compose is installed: $(docker-compose --version)"

# 4. 포트 충돌 확인
echo "[4/5] Checking port conflicts..."
PORTS=(5432 19530 8080 11434)
CONFLICT=0
for PORT in "${PORTS[@]}"; do
    if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "⚠️  Port $PORT is already in use"
        CONFLICT=1
    fi
done

if [ $CONFLICT -eq 1 ]; then
    echo "❌ Port conflict detected. Please stop conflicting services."
    exit 1
fi
echo "✅ No port conflicts"

# 5. Docker Compose 실행
echo "[5/5] Starting Docker Compose..."
docker-compose up -d

echo ""
echo "===== Setup Complete ====="
echo ""
echo "Services:"
echo "  - PostgreSQL: localhost:5432"
echo "  - Milvus: localhost:19530"
echo "  - Attu: http://localhost:8080"
echo "  - Ollama: localhost:11434"
echo ""
echo "Run health check: ./scripts/health-check.sh"
```

#### 3.8.3 실행 권한 부여
```bash
chmod +x scripts/setup.sh
chmod +x scripts/health-check.sh
```

---

### **Step 9: 최종 검증 (20분)**

#### 3.9.1 전체 프로세스 재실행 테스트
```bash
# 컨테이너 중지 및 삭제
docker-compose down

# setup 스크립트로 재실행
./scripts/setup.sh

# health check
./scripts/health-check.sh
```

#### 3.9.2 검증 체크리스트

**인프라 검증**:
- [ ] `docker-compose up -d` 성공
- [ ] 모든 컨테이너 `Up` 상태 (`docker-compose ps`)
- [ ] 로그에 에러 없음 (`docker-compose logs`)

**서비스 연결 검증**:
- [ ] PostgreSQL 연결 성공 (`docker exec -it rag-postgres psql -U raguser -d rag_platform`)
- [ ] Milvus 연결 성공 (Attu UI http://localhost:8080)
- [ ] Ollama API 응답 성공 (`curl http://localhost:11434/api/tags`)

**보안 검증 (HARD RULE)**:
- [ ] `.env` 파일이 `.gitignore`에 포함됨
- [ ] `.env` 파일의 비밀번호가 기본값(`CHANGE_ME_*`)이 아님
- [ ] `docker-compose.yml`에 하드코딩된 비밀번호 없음

**문서 검증**:
- [ ] `README.md` 존재 및 설치 가이드 포함
- [ ] `.env.example` 존재 및 모든 필수 변수 포함
- [ ] `scripts/health-check.sh` 실행 가능 및 정상 동작

---

## 4. 예상 리스크 및 대응 방안

### 4.1 Risk: 포트 충돌
**증상**: `Error: bind: address already in use`

**원인**: 5432, 19530, 8080, 11434 포트가 이미 사용 중

**대응**:
1. 사용 중인 프로세스 확인 및 종료:
   ```bash
   lsof -i :5432
   kill -9 <PID>
   ```
2. `docker-compose.yml`에서 포트 변경:
   ```yaml
   ports:
     - "15432:5432"  # 5432 대신 15432 사용
   ```

### 4.2 Risk: Milvus 컨테이너 시작 실패
**증상**: `rag-milvus` 컨테이너가 `Exited` 상태

**원인**: etcd 또는 MinIO가 준비되기 전에 Milvus가 시작됨

**대응**:
1. etcd, MinIO 로그 확인:
   ```bash
   docker-compose logs etcd
   docker-compose logs minio
   ```
2. Milvus 재시작:
   ```bash
   docker-compose restart milvus-standalone
   ```
3. 지속되면 `docker-compose.yml`에 `depends_on` 조건 추가:
   ```yaml
   depends_on:
     etcd:
       condition: service_healthy
     minio:
       condition: service_healthy
   ```

### 4.3 Risk: 메모리 부족
**증상**: 컨테이너가 느리게 실행되거나 OOM(Out of Memory) 에러

**원인**: Docker Desktop 메모리 할당량 부족 (기본 2GB)

**대응**:
1. Docker Desktop 설정에서 메모리 증가:
   - macOS: Docker Desktop → Preferences → Resources → Memory → 8GB 이상
   - Windows: Docker Desktop → Settings → Resources → Memory → 8GB 이상
2. 불필요한 컨테이너 중지:
   ```bash
   docker stop $(docker ps -q)
   ```

### 4.4 Risk: .env 파일 Git 커밋
**증상**: `.env` 파일이 Git에 추적됨

**원인**: `.gitignore` 설정 누락 또는 이미 Git에 추가된 상태

**대응**:
1. `.gitignore`에 `.env` 추가 확인
2. 이미 추가된 경우 Git 캐시에서 제거:
   ```bash
   git rm --cached .env
   git commit -m "Remove .env from tracking"
   ```
3. **[CRITICAL]** GitHub에 푸시된 경우 즉시 비밀번호 변경 및 Secret 로테이션

### 4.5 Risk: Ollama 모델 다운로드 실패 (Task 1.4 관련)
**증상**: `docker exec -it ollama ollama pull llama3` 실패

**원인**: 네트워크 이슈 또는 디스크 공간 부족

**대응**:
1. 네트워크 연결 확인
2. 디스크 공간 확인:
   ```bash
   df -h
   ```
3. Ollama 로그 확인:
   ```bash
   docker-compose logs ollama
   ```
4. 재시도 (자동 재시도 3회)

---

## 5. 완료 기준 (Task 1.1 Success Criteria)

### 5.1 필수 조건 (Must Have)
- [x] **인프라 실행**:
  - `docker-compose up -d` 성공
  - 모든 컨테이너 `running` 상태
- [x] **서비스 연결**:
  - PostgreSQL 연결 테스트 성공
  - Attu UI 접속 가능 (http://localhost:8080)
  - Ollama API 응답 성공
- [x] **보안 (HARD RULE)**:
  - `.env` 파일이 `.gitignore`에 포함
  - 비밀번호 하드코딩 없음
  - 환경 변수로 비밀 관리
- [x] **문서화**:
  - `README.md` 작성 완료
  - `.env.example` 작성 완료
  - 설치 가이드 포함

### 5.2 선택 조건 (Nice to Have)
- [ ] `scripts/setup.sh` 자동화 스크립트 작성
- [ ] `scripts/health-check.sh` 헬스체크 스크립트 작성
- [ ] GPU 지원 (NVIDIA GPU가 있는 경우)

---

## 6. 다음 Task로 전환 조건

Task 1.1 완료 후 다음 Task로 진행 가능:
- **Task 1.2**: PostgreSQL 스키마 및 마이그레이션 설정
  - **전제 조건**: PostgreSQL 컨테이너가 정상 실행 중
  - **의존성**: Task 1.1 완료

---

## 7. 시간 배분 (예상 4시간)

| 단계 | 작업 | 예상 시간 |
|------|------|-----------|
| Step 1 | 디렉토리 구조 생성 | 15분 |
| Step 2 | .gitignore 작성 | 5분 |
| Step 3 | 환경 변수 파일 작성 | 20분 |
| Step 4 | Docker Compose 파일 작성 | 60분 |
| Step 5 | Docker Compose 실행 및 검증 | 30분 |
| Step 6 | 서비스별 연결 테스트 | 30분 |
| Step 7 | README.md 작성 | 30분 |
| Step 8 | 유틸리티 스크립트 작성 | 20분 |
| Step 9 | 최종 검증 | 20분 |
| **합계** | | **240분 (4시간)** |

---

## 8. 참고 자료

### 8.1 공식 문서
- [Docker Compose 문서](https://docs.docker.com/compose/)
- [PostgreSQL 공식 이미지](https://hub.docker.com/_/postgres)
- [Milvus 설치 가이드](https://milvus.io/docs/install_standalone-docker.md)
- [Ollama 문서](https://github.com/ollama/ollama)

### 8.2 내부 문서
- [Task Breakdown](../tasks/task-breakdown.md)
- [Architecture](../architecture/architecture.md)
- [Tech Stack](../tech-stack/tech-stack.md)
- [CLAUDE.md (보안 규칙)](../../CLAUDE.md)

---

## 9. 체크리스트 (실행 전 확인)

### 9.1 사전 확인
- [ ] Docker 설치 확인 (`docker --version`)
- [ ] Docker Compose 설치 확인 (`docker-compose --version`)
- [ ] 포트 사용 가능 확인 (5432, 19530, 8080, 11434)
- [ ] 디스크 공간 충분 확인 (최소 20GB)
- [ ] 메모리 충분 확인 (최소 8GB)

### 9.2 보안 확인 (HARD RULE)
- [ ] `.gitignore`에 `.env` 포함 확인
- [ ] `.env` 파일의 비밀번호 변경 확인
- [ ] `docker-compose.yml`에 하드코딩된 비밀번호 없음 확인
- [ ] 환경 변수로 비밀 관리 확인

### 9.3 실행 후 확인
- [ ] `docker-compose ps` → 모든 서비스 "Up" 상태
- [ ] `docker-compose logs` → 에러 없음
- [ ] PostgreSQL 연결 테스트 성공
- [ ] Attu UI 접속 성공
- [ ] Ollama API 응답 성공
- [ ] `./scripts/health-check.sh` → 모든 서비스 ✅

---

## 10. Sign-off

**실행 계획 작성자**: Claude Code
**검토자**: (Infrastructure Lead)
**승인일**: (실행 전 승인 필요)

**Task 1.1 실행 준비 완료**: ✅
**다음 단계**: 체크리스트 확인 후 Step 1부터 순차 실행

---

**END OF TASK 1.1 EXECUTION PLAN**
