# Logging Guide

**Task 4.2: 기본 모니터링 로그 설정**

RAG Platform의 구조화된 로깅 시스템 사용 가이드

---

## 📋 목차

1. [로그 레벨](#로그-레벨)
2. [로그 사용법](#로그-사용법)
3. [개인정보 마스킹](#개인정보-마스킹)
4. [로그 파일 관리](#로그-파일-관리)
5. [모니터링 및 분석](#모니터링-및-분석)
6. [Best Practices](#best-practices)

---

## 로그 레벨

### 레벨 정의

| 레벨 | 사용 시점 | 예시 |
|------|----------|------|
| **DEBUG** | 개발/디버깅 시 상세 정보 | 변수 값, 함수 호출 흐름 |
| **INFO** | 일반적인 정보성 이벤트 | 서버 시작, 요청 처리 완료 |
| **WARNING** | 주의가 필요한 상황 (정상 동작) | 느린 응답, 임계치 근접 |
| **ERROR** | 에러 발생 (일부 기능 실패) | API 호출 실패, DB 연결 오류 |

### 레벨 설정

환경 변수 또는 `.env` 파일에서 설정:

```bash
# .env
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
```

운영 환경 권장: `INFO` 또는 `WARNING`

---

## 로그 사용법

### 기본 사용법

```python
from app.utils.logger import get_logger

logger = get_logger(__name__)

# INFO 레벨
logger.info("서버 시작", port=8000, version="1.0.0")

# ERROR 레벨
logger.error("DB 연결 실패", error=str(e), database="postgres")

# WARNING 레벨
logger.warning("느린 응답", response_time_ms=5000, threshold_ms=3000)
```

### 구조화된 로깅 (Structured Logging)

**✅ 권장: 구조화된 필드 사용**

```python
logger.info(
    "search_request",
    user_id="user_12345",
    query="연차 사용 방법",
    results_count=5,
    response_time_ms=1234
)
```

**출력 (JSON)**:
```json
{
  "event": "search_request",
  "user_id": "user_12345",
  "query": "연차 사용 방법",
  "results_count": 5,
  "response_time_ms": 1234,
  "timestamp": "2025-01-11T10:30:00.123Z",
  "level": "info",
  "logger": "app.routers.search"
}
```

**❌ 비권장: 일반 문자열 로깅**

```python
# Bad
logger.info(f"User {user_id} searched for {query}")

# Good
logger.info("user_search", user_id=user_id, query=query)
```

---

## 개인정보 마스킹

**[HARD RULE]** 로그에 개인정보를 기록할 때는 **자동 마스킹**이 적용됩니다.

### 자동 마스킹 대상

#### 1. 이메일 주소

```python
logger.info("user_login", email="user@example.com")

# 출력: email="u***@example.com"
```

**패턴**: `local@domain` → `l***@domain`

#### 2. IP 주소

```python
logger.info("api_request", client_ip="192.168.1.100")

# 출력: client_ip="192.168.*.*"
```

**패턴**: `192.168.1.100` → `192.168.*.*`

#### 3. 민감 검색어

```python
logger.info("search_query", query="급여명세서 조회")

# 출력: query="a3f5c8d2e1b9f7a4", query_masked=true
```

**민감 키워드**: 급여, 연봉, 인사, 기밀, 비밀, 급여명세서, 성과급

민감 키워드 포함 시 **SHA-256 해시(16자)** 로 변환됩니다.

#### 4. 개인정보 패턴

```python
logger.info("user_input", query="주민번호 123456-1234567")

# 출력: query="주민번호 [주민번호]"
```

**자동 마스킹 패턴**:
- 주민번호: `123456-1234567` → `[주민번호]`
- 계좌번호: `123-456-789012` → `[계좌번호]`
- 전화번호: `010-1234-5678` → `[전화번호]`
- 이메일: `user@example.com` → `[이메일]`

### 마스킹 검증

```python
# 테스트 코드 예시
from app.utils.logger import mask_email, mask_ip

assert mask_email("user@example.com") == "u***@example.com"
assert mask_ip("192.168.1.1") == "192.168.*.*"
```

---

## 로그 파일 관리

### 파일 위치

```
/var/log/rag-platform/
├── app.log          # 일반 로그 (INFO 이상)
├── error.log        # 에러 로그 (ERROR 이상)
├── app.log.2025-01-10   # 로테이션된 백업
└── error.log.2025-01-09
```

### 로테이션 정책

| 파일 | 로테이션 | 보관 기간 |
|------|----------|-----------|
| `app.log` | 매일 자정 | 90일 |
| `error.log` | 매일 자정 | 365일 |

**자동 로테이션**: 매일 자정(UTC)에 새 파일 생성
**백업 파일명**: `app.log.YYYY-MM-DD`

### 로그 확인

```bash
# 실시간 로그 확인
tail -f /var/log/rag-platform/app.log

# 최근 100줄
tail -100 /var/log/rag-platform/app.log

# 에러 로그만
tail -f /var/log/rag-platform/error.log

# 특정 날짜 로그
cat /var/log/rag-platform/app.log.2025-01-11
```

### 로그 검색 (jq 활용)

로그가 JSON 형식이므로 `jq`로 쉽게 파싱 가능:

```bash
# 검색 요청만 필터링
cat app.log | jq 'select(.event == "search_request")'

# 에러만 필터링
cat app.log | jq 'select(.level == "error")'

# 응답 시간 1초 이상
cat app.log | jq 'select(.response_time_ms > 1000)'

# 특정 사용자
cat app.log | jq 'select(.user_id == "user_12345")'
```

---

## 모니터링 및 분석

### 주요 지표 로깅

#### 1. API 요청/응답

```python
logger.info(
    "api_request",
    method="POST",
    path="/api/v1/search",
    status_code=200,
    response_time_ms=1234,
    user_id="user_12345",
    client_ip="192.168.1.1"
)
```

#### 2. 검색 성능

```python
logger.info(
    "search_performance",
    query="연차 사용",
    embedding_time_ms=100,
    vector_search_time_ms=50,
    llm_time_ms=2000,
    total_time_ms=2150,
    results_count=5
)
```

#### 3. 에러 추적

```python
logger.error(
    "llm_generation_failed",
    error_type="TimeoutError",
    error_message=str(e),
    query="데이터브릭스 설명",
    timeout_seconds=60,
    retry_count=3
)
```

#### 4. 스케줄러 작업

```python
logger.info(
    "scheduler_job_start",
    job_name="document_indexing",
    scheduled_time="2025-01-11T02:00:00Z"
)

logger.info(
    "scheduler_job_complete",
    job_name="document_indexing",
    duration_ms=15000,
    indexed_documents=10,
    failed_documents=0
)
```

### 로그 분석 예시

#### 응답 시간 분포 확인

```bash
cat app.log | jq -r '.response_time_ms' | \
  awk '{sum+=$1; count++} END {print "평균:", sum/count, "ms"}'
```

#### 에러 빈도 확인

```bash
cat error.log | jq -r '.error_type' | sort | uniq -c | sort -rn
```

#### 시간대별 요청 수

```bash
cat app.log | jq -r '.timestamp' | \
  cut -d'T' -f2 | cut -d':' -f1 | sort | uniq -c
```

---

## Best Practices

### ✅ DO

1. **구조화된 로깅 사용**
   ```python
   logger.info("user_action", user_id=user_id, action="search")
   ```

2. **의미 있는 이벤트 이름**
   ```python
   # Good
   logger.info("search_completed", ...)
   logger.error("database_connection_failed", ...)

   # Bad
   logger.info("done")
   logger.error("error")
   ```

3. **중요한 메트릭 기록**
   ```python
   logger.info(
       "search_request",
       response_time_ms=1234,  # 성능 모니터링
       results_count=5,        # 품질 모니터링
       user_id="user_12345"    # 추적
   )
   ```

4. **에러는 ERROR 레벨 사용**
   ```python
   try:
       result = do_something()
   except Exception as e:
       logger.error("operation_failed", error=str(e), context="...")
       raise
   ```

5. **개인정보는 자동 마스킹 필드 사용**
   ```python
   logger.info("user_login", email=email, client_ip=ip)
   # email, client_ip는 자동 마스킹됨
   ```

### ❌ DON'T

1. **민감 정보를 직접 로깅하지 말 것**
   ```python
   # Bad
   logger.info("user", password=password)
   logger.info("query", ssn="123456-1234567")
   ```

2. **과도한 DEBUG 로깅**
   ```python
   # Bad (운영 환경)
   for item in items:
       logger.debug(f"Processing {item}")  # 수천 줄 로그 생성
   ```

3. **로그에 에러를 숨기지 말 것**
   ```python
   # Bad
   try:
       critical_operation()
   except:
       pass  # 에러 무시!

   # Good
   try:
       critical_operation()
   except Exception as e:
       logger.error("critical_operation_failed", error=str(e))
       raise
   ```

4. **일반 문자열 포맷팅 사용**
   ```python
   # Bad
   logger.info(f"User {user_id} completed action")

   # Good
   logger.info("user_action_completed", user_id=user_id)
   ```

---

## 설정 참고

### 환경 변수 (.env)

```bash
# 로그 레벨
LOG_LEVEL=INFO

# 로그 파일 경로
LOG_FILE_PATH=/var/log/rag-platform/app.log

# JSON 포맷 사용
LOG_JSON_FORMAT=true

# 보관 기간
LOG_RETENTION_DAYS=90
ERROR_LOG_RETENTION_DAYS=365
```

### 코드 설정 (config.py)

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    LOG_LEVEL: str = "INFO"
    LOG_FILE_PATH: str = "/var/log/rag-platform/app.log"
    LOG_JSON_FORMAT: bool = True
    LOG_RETENTION_DAYS: int = 90
    ERROR_LOG_RETENTION_DAYS: int = 365
```

---

## 문제 해결

### Q1: 로그 파일이 생성되지 않아요

**확인 사항**:
1. 디렉토리 권한 확인:
   ```bash
   sudo mkdir -p /var/log/rag-platform
   sudo chown $USER:$USER /var/log/rag-platform
   ```

2. 설정 확인:
   ```python
   from app.core.config import settings
   print(settings.LOG_FILE_PATH)
   ```

### Q2: 로그가 너무 많이 쌓여요

**해결책**:
1. 로그 레벨 상향:
   ```bash
   LOG_LEVEL=WARNING  # INFO 대신 WARNING
   ```

2. 보관 기간 단축:
   ```bash
   LOG_RETENTION_DAYS=30  # 90일 → 30일
   ```

3. 불필요한 로그 제거:
   ```python
   # 빈번한 INFO 로그를 DEBUG로 변경
   logger.debug("minor_event", ...)  # 운영에서는 출력 안 됨
   ```

### Q3: 개인정보 마스킹이 작동하지 않아요

**확인 사항**:
1. 필드 이름 확인:
   ```python
   # Good (자동 마스킹)
   logger.info("event", email=email)

   # Bad (마스킹 안 됨)
   logger.info("event", user_email_address=email)
   ```

2. 마스킹 프로세서 활성화 확인:
   ```python
   from app.utils.logger import configure_logging
   configure_logging()  # 앱 시작 시 호출되어야 함
   ```

---

## 참고 자료

- **structlog 문서**: https://www.structlog.org/
- **Python logging**: https://docs.python.org/3/library/logging.html
- **jq 매뉴얼**: https://stedolan.github.io/jq/manual/

---

**작성일**: 2025-01-11
**작성자**: Task 4.2 (기본 모니터링 로그 설정)
**버전**: 1.0.0
