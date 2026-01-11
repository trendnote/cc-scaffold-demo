# 개발 환경 설정 (Development Setup)

## 목차

1. [Prerequisites](#prerequisites)
2. [로컬 개발 환경](#로컬-개발-환경)
3. [IDE 설정](#ide-설정)
4. [Git 워크플로우](#git-워크플로우)
5. [디버깅 설정](#디버깅-설정)

---

## Prerequisites

### 1. 필수 소프트웨어

```bash
# Docker & Docker Compose
docker --version         # 20.10+
docker-compose --version # 2.0+

# Git
git --version           # 2.30+

# Python (백엔드)
python3 --version       # 3.11+
pip --version          # 최신

# Node.js (프론트엔드)
node --version          # 20+
npm --version           # 10+
```

### 2. 추천 도구

```bash
# Python 개발
pip install ipython        # Interactive Python
pip install black          # Code formatter
pip install flake8         # Linter
pip install mypy           # Type checker
pip install pytest-watch   # Auto test runner

# Node.js 개발
npm install -g typescript  # TypeScript
npm install -g eslint      # Linter
npm install -g prettier    # Formatter
```

### 3. OS별 설치 가이드

#### macOS

```bash
# Homebrew 설치
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 패키지 설치
brew install docker docker-compose git python@3.11 node
```

#### Ubuntu/Debian

```bash
# Docker
sudo apt-get update
sudo apt-get install docker.io docker-compose

# Python
sudo apt-get install python3.11 python3.11-venv python3-pip

# Node.js
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs
```

#### Windows (WSL2)

```powershell
# WSL2 설치
wsl --install

# Ubuntu 22.04 설치
wsl --install -d Ubuntu-22.04

# WSL 내에서 위의 Ubuntu 가이드 따르기
```

---

## 로컬 개발 환경

### 1. 프로젝트 클론

```bash
# 저장소 클론
git clone https://github.com/your-org/cc-scaffold-demo.git
cd cc-scaffold-demo

# 브랜치 확인
git branch -a

# 개발 브랜치로 전환 (있는 경우)
git checkout develop
```

### 2. 환경 변수 설정

```bash
# .env 파일 생성
cp .env.example .env

# .env 파일 수정
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

# LLM Provider (개발용 Ollama)
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL_LLM=llama3.2:1b       # 작은 모델로 빠른 테스트
OLLAMA_MODEL_EMBED=nomic-embed-text

# JWT Secret (개발용)
JWT_SECRET=dev_secret_key_not_for_production
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=480  # 8시간 (개발 편의성)

# CORS (localhost 허용)
BACKEND_CORS_ORIGINS=["http://localhost:3000","http://localhost:8000"]

# Logging (개발 시 DEBUG)
LOG_LEVEL=DEBUG
```

### 3. 인프라 시작

```bash
# Docker Compose로 인프라 시작
docker-compose up -d

# 서비스 상태 확인
docker-compose ps

# Ollama 모델 다운로드
docker exec -it rag-ollama ollama pull llama3.2:1b
docker exec -it rag-ollama ollama pull nomic-embed-text

# 모델 확인
docker exec -it rag-ollama ollama list
```

### 4. 백엔드 설정

```bash
cd backend

# Python 가상환경 생성
python3 -m venv venv

# 가상환경 활성화
# macOS/Linux:
source venv/bin/activate

# Windows (Git Bash):
# source venv/Scripts/activate

# 의존성 설치
pip install --upgrade pip
pip install -r requirements.txt

# 개발 전용 의존성 설치
pip install pytest pytest-cov pytest-asyncio httpx black flake8 mypy

# 데이터베이스 마이그레이션
alembic upgrade head

# Milvus Collection 초기화
python -m app.db.init_milvus

# 개발 서버 시작 (hot-reload)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**백엔드 확인**:

```bash
# 새 터미널에서
curl http://localhost:8000/health
curl http://localhost:8000/docs  # Swagger UI
```

### 5. 프론트엔드 설정

```bash
cd frontend

# Node.js 의존성 설치
npm install

# 또는 (더 빠름)
npm ci

# 환경 변수 설정
cp .env.example .env.local

# .env.local 수정
vi .env.local
```

**.env.local 설정**:

```env
# API URL (백엔드)
NEXT_PUBLIC_API_URL=http://localhost:8000

# Environment
NEXT_PUBLIC_ENV=development
```

**개발 서버 시작**:

```bash
# 개발 서버 시작 (hot-reload)
npm run dev

# 터보 모드 (더 빠름)
npm run dev --turbo
```

**프론트엔드 확인**:

```
브라우저에서: http://localhost:3000
```

---

## IDE 설정

### 1. Visual Studio Code

#### 필수 확장 프로그램

```json
// .vscode/extensions.json

{
  "recommendations": [
    // Python
    "ms-python.python",
    "ms-python.vscode-pylance",
    "ms-python.black-formatter",

    // TypeScript/React
    "dbaeumer.vscode-eslint",
    "esbenp.prettier-vscode",
    "bradlc.vscode-tailwindcss",

    // Docker
    "ms-azuretools.vscode-docker",

    // Git
    "eamodio.gitlens",

    // 기타
    "streetsidesoftware.code-spell-checker",
    "redhat.vscode-yaml"
  ]
}
```

#### 워크스페이스 설정

```json
// .vscode/settings.json

{
  // Python
  "python.defaultInterpreterPath": "${workspaceFolder}/backend/venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "python.formatting.blackArgs": ["--line-length=88"],
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["backend/tests"],

  // TypeScript
  "typescript.tsdk": "frontend/node_modules/typescript/lib",
  "typescript.enablePromptUseWorkspaceTsdk": true,

  // Formatting
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": true
  },

  // Files
  "files.exclude": {
    "**/__pycache__": true,
    "**/.pytest_cache": true,
    "**/node_modules": true,
    "**/.next": true
  },

  // Tailwind CSS
  "tailwindCSS.experimental.classRegex": [
    ["cva\\(([^)]*)\\)", "[\"'`]([^\"'`]*).*?[\"'`]"]
  ]
}
```

#### 디버깅 설정

```json
// .vscode/launch.json

{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "app.main:app",
        "--reload",
        "--host",
        "0.0.0.0",
        "--port",
        "8000"
      ],
      "cwd": "${workspaceFolder}/backend",
      "env": {
        "PYTHONPATH": "${workspaceFolder}/backend"
      },
      "console": "integratedTerminal"
    },
    {
      "name": "Next.js: debug server-side",
      "type": "node-terminal",
      "request": "launch",
      "command": "npm run dev",
      "cwd": "${workspaceFolder}/frontend",
      "serverReadyAction": {
        "pattern": "started server on .+, url: (https?://.+)",
        "uriFormat": "%s",
        "action": "debugWithChrome"
      }
    }
  ]
}
```

### 2. PyCharm

#### 프로젝트 설정

1. **Python Interpreter 설정**:
   - File → Settings → Project → Python Interpreter
   - Add Interpreter → Existing Environment
   - `/path/to/backend/venv/bin/python` 선택

2. **Run Configuration (FastAPI)**:
   - Run → Edit Configurations → Add New (Python)
   - Script path: `/path/to/venv/bin/uvicorn`
   - Parameters: `app.main:app --reload --host 0.0.0.0 --port 8000`
   - Working directory: `/path/to/backend`

3. **Code Style (Black)**:
   - File → Settings → Tools → Black
   - Enable Black formatter
   - Line length: 88

---

## Git 워크플로우

### 1. 브랜치 전략

```
main (production)
  ↑
develop (development)
  ↑
feature/ISSUE-123-feature-name (feature)
  ↑
your-local-branch
```

### 2. 브랜치 생성

```bash
# develop 브랜치에서 시작
git checkout develop
git pull origin develop

# 새 feature 브랜치 생성
git checkout -b feature/ISSUE-123-add-search-filter

# 브랜치 이름 규칙:
# - feature/ISSUE-{number}-{brief-description}
# - bugfix/ISSUE-{number}-{brief-description}
# - hotfix/ISSUE-{number}-{brief-description}
```

### 3. 커밋 규칙

```bash
# Conventional Commits 사용

# 타입:
# - feat: 새로운 기능
# - fix: 버그 수정
# - docs: 문서 변경
# - style: 코드 스타일 변경 (포매팅 등)
# - refactor: 코드 리팩토링
# - test: 테스트 추가
# - chore: 빌드/설정 변경

# 예시:
git commit -m "feat: Add search filter for documents

- Add filter by date range
- Add filter by department
- Add filter by access level

Closes #123"

# 또는 /commit 스킬 사용 (자동 포매팅)
```

### 4. Pull Request

```bash
# 변경사항 푸시
git push origin feature/ISSUE-123-add-search-filter

# PR 생성 (GitHub CLI)
gh pr create \
  --title "feat: Add search filter for documents" \
  --body "## Summary
- Add filter by date range
- Add filter by department
- Add filter by access level

## Test Plan
- [x] Unit tests pass
- [x] E2E tests pass
- [x] Manual testing completed

Closes #123"
```

### 5. 코드 리뷰

**리뷰어 체크리스트**:

- [ ] 코드가 요구사항을 충족하는가?
- [ ] 테스트가 충분한가?
- [ ] 코딩 표준을 따르는가?
- [ ] 보안 취약점이 없는가?
- [ ] 성능 문제가 없는가?
- [ ] 문서화가 되어 있는가?

### 6. 머지 후 정리

```bash
# develop으로 전환
git checkout develop

# 최신 상태로 업데이트
git pull origin develop

# 로컬 feature 브랜치 삭제
git branch -d feature/ISSUE-123-add-search-filter

# 원격 브랜치 삭제 (자동으로 되지 않은 경우)
git push origin --delete feature/ISSUE-123-add-search-filter
```

---

## 디버깅 설정

### 1. 백엔드 디버깅

#### ipdb 사용

```python
# 코드에 브레이크포인트 추가
def search_query(query: str):
    import ipdb; ipdb.set_trace()  # 디버거 시작

    # 코드 실행이 여기서 멈춤
    results = search_service.search(query)
    return results
```

#### 로깅 활용

```python
import structlog

logger = structlog.get_logger(__name__)

def search_query(query: str):
    logger.debug("search_query_start", query=query)

    results = search_service.search(query)

    logger.debug(
        "search_query_complete",
        query=query,
        result_count=len(results),
    )

    return results
```

#### 프로파일링

```bash
# py-spy로 프로파일링
pip install py-spy

# 실행 중인 프로세스 프로파일링
PID=$(pgrep -f "uvicorn app.main:app")
py-spy top --pid $PID

# 화염 그래프 생성
py-spy record -o profile.svg --pid $PID --duration 60
```

### 2. 프론트엔드 디버깅

#### React Developer Tools

```bash
# Chrome Extension 설치
# https://chrome.google.com/webstore/detail/react-developer-tools
```

#### Console Logging

```typescript
// 조건부 로깅 (개발 환경만)
if (process.env.NODE_ENV === 'development') {
  console.log('Search query:', query);
  console.log('Results:', results);
}

// 구조화된 로깅
console.group('Search Query');
console.log('Query:', query);
console.log('Filters:', filters);
console.table(results);
console.groupEnd();
```

#### 네트워크 디버깅

```typescript
// Axios/Fetch 인터셉터
import axios from 'axios';

axios.interceptors.request.use((config) => {
  console.log('Request:', config.method?.toUpperCase(), config.url);
  console.log('Data:', config.data);
  return config;
});

axios.interceptors.response.use(
  (response) => {
    console.log('Response:', response.status, response.data);
    return response;
  },
  (error) => {
    console.error('Error:', error.response?.status, error.message);
    return Promise.reject(error);
  }
);
```

### 3. 데이터베이스 디버깅

```bash
# PostgreSQL 쿼리 로그 활성화
docker exec -it rag-postgres psql -U raguser -c "
  ALTER SYSTEM SET log_statement = 'all';
  ALTER SYSTEM SET log_min_duration_statement = 0;
"

# 설정 리로드
docker exec -it rag-postgres psql -U raguser -c "SELECT pg_reload_conf();"

# 로그 확인
docker-compose logs -f postgres
```

---

## 유용한 스크립트

### 개발 환경 초기화

```bash
#!/bin/bash
# scripts/dev_setup.sh

set -e

echo "=== Development Environment Setup ==="

# 1. 인프라 시작
echo "1. Starting infrastructure..."
docker-compose up -d

# 2. Ollama 모델 다운로드
echo "2. Downloading Ollama models..."
docker exec -it rag-ollama ollama pull llama3.2:1b
docker exec -it rag-ollama ollama pull nomic-embed-text

# 3. 백엔드 설정
echo "3. Setting up backend..."
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
python -m app.db.init_milvus

# 4. 프론트엔드 설정
echo "4. Setting up frontend..."
cd ../frontend
npm install

echo ""
echo "=== Setup Complete! ==="
echo "Start backend: cd backend && source venv/bin/activate && uvicorn app.main:app --reload"
echo "Start frontend: cd frontend && npm run dev"
```

### 전체 재시작

```bash
#!/bin/bash
# scripts/dev_restart.sh

set -e

echo "Restarting development environment..."

# 인프라 재시작
docker-compose restart

# 백엔드 재시작 (PID 찾아서 종료)
pkill -f "uvicorn app.main:app" || true

# 프론트엔드 재시작
pkill -f "next dev" || true

echo "Restart complete!"
echo "Start backend: cd backend && uvicorn app.main:app --reload"
echo "Start frontend: cd frontend && npm run dev"
```

---

## 관련 문서

- [Testing Guide](./testing-guide.md) - 테스트 작성 및 실행
- [Coding Standards](./coding-standards.md) - 코딩 규칙 및 스타일 가이드
- [Deployment Guide](../operations/deployment-guide.md) - 배포 가이드

---

**행복한 코딩 되세요!** 🚀
