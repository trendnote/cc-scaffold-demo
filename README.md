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
