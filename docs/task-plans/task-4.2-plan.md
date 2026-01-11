# Task 4.2 실행 계획: 기본 모니터링 로그 설정

## 📋 작업 정보
- **Task ID**: 4.2
- **Task명**: 기본 모니터링 로그 설정
- **예상 시간**: 4시간
- **담당**: Backend
- **의존성**: Task 2.9 (성능 최적화 및 로깅)
- **GitHub Issue**: #31

---

## 🎯 작업 목표

구조화된 로깅 시스템을 구현하여 운영 중 문제 추적 및 성능 모니터링 지원

---

## 📐 기술 스택

- **structlog**: 23.0+ (구조화된 로깅)
- **Python logging**: 표준 라이브러리
- **logrotate**: 로그 파일 로테이션 (시스템 레벨)
- **JSON**: 로그 출력 포맷

---

## 🏗️ 로깅 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                    Logging System                            │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────────────────────────────┐               │
│  │  Application Code                         │               │
│  │  (FastAPI, Services, etc.)               │               │
│  └──────────────────┬───────────────────────┘               │
│                     │                                         │
│                     ▼                                         │
│  ┌──────────────────────────────────────────┐               │
│  │  structlog Logger                         │               │
│  │  - 구조화된 컨텍스트                        │               │
│  │  - 개인정보 마스킹                          │               │
│  │  - 로그 레벨 필터링                         │               │
│  └──────────────────┬───────────────────────┘               │
│                     │                                         │
│           ┌─────────┴─────────┐                              │
│           ▼                   ▼                               │
│  ┌───────────────┐   ┌───────────────┐                      │
│  │  Console      │   │  JSON File    │                      │
│  │  (개발환경)    │   │  (운영환경)    │                      │
│  └───────────────┘   └───────┬───────┘                      │
│                               │                               │
│                               ▼                               │
│                      ┌───────────────┐                       │
│                      │  Log Rotation │                       │
│                      │  (Daily/Size) │                       │
│                      └───────────────┘                       │
│                                                               │
│  ┌──────────────────────────────────────────┐               │
│  │  Log Levels:                              │               │
│  │  - ERROR: LLM 실패, DB 실패               │               │
│  │  - WARNING: 응답 시간 > 25초              │               │
│  │  - INFO: 모든 검색 요청                   │               │
│  │  - DEBUG: 상세 디버깅 (개발만)            │               │
│  └──────────────────────────────────────────┘               │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 📝 구현 계획

### Phase 1: structlog 설정 (1.5시간)

#### 1.1 의존성 설치
**파일**: `backend/requirements.txt`
```python
structlog==23.2.0
python-json-logger==2.0.7
```

#### 1.2 structlog 설정
**파일**: `backend/app/utils/logger.py`
```python
"""
구조화된 로깅 설정

[HARD RULE] 개인정보 마스킹:
- 이메일: user@example.com → u***@example.com
- 민감 검색어: 마스킹 또는 해시
- IP 주소: 192.168.1.1 → 192.168.*.*
"""
import structlog
import logging
import re
from typing import Any, Dict
from datetime import datetime


def mask_email(email: str) -> str:
    """
    이메일 마스킹

    Args:
        email: 원본 이메일

    Returns:
        str: 마스킹된 이메일 (u***@example.com)
    """
    if not email or '@' not in email:
        return email

    local, domain = email.split('@', 1)
    if len(local) <= 1:
        masked_local = '*'
    else:
        masked_local = local[0] + '***'

    return f"{masked_local}@{domain}"


def mask_ip(ip: str) -> str:
    """
    IP 주소 마스킹

    Args:
        ip: 원본 IP

    Returns:
        str: 마스킹된 IP (192.168.*.*)
    """
    parts = ip.split('.')
    if len(parts) == 4:
        return f"{parts[0]}.{parts[1]}.*.*"
    return ip


def mask_sensitive_data(event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    민감 데이터 마스킹 프로세서

    Args:
        event_dict: 로그 이벤트 딕셔너리

    Returns:
        Dict: 마스킹된 이벤트 딕셔너리
    """
    # 이메일 마스킹
    if 'email' in event_dict:
        event_dict['email'] = mask_email(event_dict['email'])

    if 'user_email' in event_dict:
        event_dict['user_email'] = mask_email(event_dict['user_email'])

    # IP 마스킹
    if 'client_ip' in event_dict:
        event_dict['client_ip'] = mask_ip(event_dict['client_ip'])

    # 검색어 해시 (민감한 검색어 보호)
    if 'query' in event_dict:
        query = event_dict['query']
        # 민감 키워드 체크 (예: 급여, 인사, 기밀 등)
        sensitive_keywords = ['급여', '연봉', '인사', '기밀', '비밀']
        if any(keyword in query for keyword in sensitive_keywords):
            import hashlib
            event_dict['query'] = hashlib.sha256(
                query.encode()
            ).hexdigest()[:16]
            event_dict['query_masked'] = True

    return event_dict


def add_timestamp(logger, method_name, event_dict):
    """
    타임스탬프 추가 프로세서

    Args:
        logger: 로거
        method_name: 메서드명
        event_dict: 이벤트 딕셔너리

    Returns:
        Dict: 타임스탬프 추가된 딕셔너리
    """
    event_dict['timestamp'] = datetime.utcnow().isoformat() + 'Z'
    return event_dict


def configure_logging(log_level: str = "INFO"):
    """
    structlog 설정

    Args:
        log_level: 로그 레벨 (DEBUG, INFO, WARNING, ERROR)
    """
    # Python 기본 로깅 설정
    logging.basicConfig(
        format="%(message)s",
        level=getattr(logging, log_level.upper()),
    )

    # structlog 프로세서 체인
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            add_timestamp,
            mask_sensitive_data,  # [HARD RULE] 민감 데이터 마스킹
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),  # JSON 출력
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """
    구조화된 로거 가져오기

    Args:
        name: 로거 이름 (일반적으로 __name__)

    Returns:
        structlog.BoundLogger: 구조화된 로거
    """
    return structlog.get_logger(name)
```

#### 1.3 환경별 로그 설정
**파일**: `backend/app/core/config.py`
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # 기존 설정...

    # 로깅 설정
    LOG_LEVEL: str = "INFO"  # DEBUG, INFO, WARNING, ERROR
    LOG_FILE_PATH: str = "/var/log/rag-platform/app.log"
    LOG_JSON_FORMAT: bool = True  # JSON 포맷 사용 여부

    # 로그 보관 정책
    LOG_RETENTION_DAYS: int = 90  # 검색 로그 90일
    ERROR_LOG_RETENTION_DAYS: int = 365  # 에러 로그 1년

    class Config:
        env_file = ".env"


settings = Settings()
```

---

### Phase 2: 로그 레벨 및 포맷 정의 (1시간)

#### 2.1 로그 레벨 가이드라인
**파일**: `backend/docs/logging-guide.md`
```markdown
# 로깅 가이드라인

## 로그 레벨

### ERROR
- **사용 시점**: 시스템 오류, 복구 불가능한 에러
- **예시**:
  - LLM 호출 실패 (3회 재시도 후)
  - DB 연결 실패
  - Milvus 연결 실패
  - 파일 파싱 실패 (손상된 파일)
- **로그 예시**:
  ```python
  logger.error(
      "llm_call_failed",
      query_id=query_id,
      error=str(e),
      retry_count=3
  )
  ```

### WARNING
- **사용 시점**: 주의가 필요한 상황, 성능 저하
- **예시**:
  - 응답 시간 > 25초
  - DB 쿼리 시간 > 5초
  - 메모리 사용량 > 80%
  - Fallback 모드 진입
- **로그 예시**:
  ```python
  logger.warning(
      "slow_response",
      query_id=query_id,
      response_time_ms=27000,
      threshold_ms=25000
  )
  ```

### INFO
- **사용 시점**: 정상 작동, 중요 이벤트
- **예시**:
  - 모든 검색 요청
  - 문서 인덱싱 완료
  - 배치 작업 시작/완료
  - 사용자 로그인/로그아웃
- **로그 예시**:
  ```python
  logger.info(
      "search_request",
      query_id=query_id,
      user_id=user_id,
      query=query,
      response_time_ms=response_time,
      sources_count=len(sources)
  )
  ```

### DEBUG
- **사용 시점**: 상세 디버깅 (개발 환경만)
- **예시**:
  - 벡터 검색 상세 결과
  - 프롬프트 템플릿 내용
  - DB 쿼리 상세
- **로그 예시**:
  ```python
  logger.debug(
      "vector_search_details",
      query_vector=query_vector[:5],  # 처음 5개만
      search_params=search_params,
      results_count=len(results)
  )
  ```
```

#### 2.2 주요 이벤트 로깅
**파일**: `backend/app/services/search_service.py` (예시)
```python
from app.utils.logger import get_logger

logger = get_logger(__name__)


class SearchService:
    async def search(self, query: str, user_id: str):
        query_id = generate_query_id()

        # INFO: 검색 요청 시작
        logger.info(
            "search_started",
            query_id=query_id,
            user_id=user_id,
            query_length=len(query)
        )

        try:
            # 벡터 검색
            results = await self.vector_search(query)

            # DEBUG: 검색 결과 상세
            logger.debug(
                "vector_search_completed",
                query_id=query_id,
                results_count=len(results),
                top_score=results[0].score if results else 0
            )

            # LLM 답변 생성
            answer = await self.generate_answer(query, results)

            # INFO: 검색 완료
            logger.info(
                "search_completed",
                query_id=query_id,
                response_time_ms=response_time,
                sources_count=len(results),
                answer_length=len(answer)
            )

            return answer

        except Exception as e:
            # ERROR: 검색 실패
            logger.error(
                "search_failed",
                query_id=query_id,
                error=str(e),
                error_type=type(e).__name__
            )
            raise
```

---

### Phase 3: 로그 파일 관리 (1시간)

#### 3.1 파일 핸들러 설정
**파일**: `backend/app/utils/file_handler.py`
```python
"""
로그 파일 핸들러 설정
"""
import logging
from logging.handlers import TimedRotatingFileHandler, RotatingFileHandler
from pathlib import Path
from app.core.config import settings


def setup_file_handlers():
    """
    로그 파일 핸들러 설정

    - app.log: 모든 로그 (일별 로테이션, 90일 보관)
    - error.log: ERROR 이상 (일별 로테이션, 1년 보관)
    """
    # 로그 디렉토리 생성
    log_dir = Path(settings.LOG_FILE_PATH).parent
    log_dir.mkdir(parents=True, exist_ok=True)

    # 기본 로그 파일 핸들러 (일별 로테이션)
    app_handler = TimedRotatingFileHandler(
        filename=settings.LOG_FILE_PATH,
        when='midnight',
        interval=1,
        backupCount=settings.LOG_RETENTION_DAYS,
        encoding='utf-8'
    )
    app_handler.setLevel(logging.INFO)
    app_handler.suffix = "%Y%m%d"

    # 에러 로그 파일 핸들러 (일별 로테이션)
    error_log_path = log_dir / "error.log"
    error_handler = TimedRotatingFileHandler(
        filename=str(error_log_path),
        when='midnight',
        interval=1,
        backupCount=settings.ERROR_LOG_RETENTION_DAYS,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.suffix = "%Y%m%d"

    # 포맷터 설정 (JSON)
    formatter = logging.Formatter('%(message)s')
    app_handler.setFormatter(formatter)
    error_handler.setFormatter(formatter)

    # 루트 로거에 핸들러 추가
    root_logger = logging.getLogger()
    root_logger.addHandler(app_handler)
    root_logger.addHandler(error_handler)

    return app_handler, error_handler
```

#### 3.2 main.py 통합
**파일**: `backend/app/main.py`
```python
from app.utils.logger import configure_logging
from app.utils.file_handler import setup_file_handlers
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 시작/종료 시 실행"""
    # Startup
    # 로깅 설정
    configure_logging(log_level=settings.LOG_LEVEL)
    setup_file_handlers()

    logger.info(
        "server_startup",
        version="1.0.0",
        environment=settings.ENVIRONMENT,
        log_level=settings.LOG_LEVEL
    )

    yield

    # Shutdown
    logger.info("server_shutdown")
```

#### 3.3 로그 로테이션 설정
**파일**: `backend/scripts/logrotate.conf`
```conf
/var/log/rag-platform/*.log {
    daily
    rotate 90
    compress
    delaycompress
    missingok
    notifempty
    create 0644 www-data www-data
    sharedscripts
    postrotate
        systemctl reload rag-platform
    endscript
}

/var/log/rag-platform/error.log {
    daily
    rotate 365
    compress
    delaycompress
    missingok
    notifempty
    create 0644 www-data www-data
}
```

---

### Phase 4: 개인정보 마스킹 테스트 (0.5시간)

#### 4.1 마스킹 테스트
**파일**: `backend/tests/test_logger.py`
```python
import pytest
from app.utils.logger import mask_email, mask_ip, mask_sensitive_data


class TestDataMasking:
    """데이터 마스킹 테스트"""

    def test_mask_email(self):
        """이메일 마스킹 테스트"""
        assert mask_email("user@example.com") == "u***@example.com"
        assert mask_email("a@example.com") == "*@example.com"
        assert mask_email("john.doe@company.com") == "j***@company.com"

    def test_mask_ip(self):
        """IP 마스킹 테스트"""
        assert mask_ip("192.168.1.100") == "192.168.*.*"
        assert mask_ip("10.0.0.1") == "10.0.*.*"

    def test_mask_sensitive_query(self):
        """민감 검색어 마스킹 테스트"""
        event = {
            'query': '급여 인상 정책',
            'user_id': '123'
        }

        result = mask_sensitive_data(event)

        assert 'query_masked' in result
        assert result['query_masked'] is True
        assert len(result['query']) == 16  # 해시 값

    def test_normal_query_not_masked(self):
        """일반 검색어는 마스킹 안 함"""
        event = {
            'query': '휴가 신청 방법',
            'user_id': '123'
        }

        result = mask_sensitive_data(event)

        assert 'query_masked' not in result
        assert result['query'] == '휴가 신청 방법'
```

---

## 🧪 테스트 계획

### 단위 테스트
**파일**: `backend/tests/test_logging_integration.py`
```python
import pytest
import json
from app.utils.logger import configure_logging, get_logger


@pytest.fixture
def logger():
    """테스트용 로거"""
    configure_logging("DEBUG")
    return get_logger("test")


def test_structured_logging(logger, caplog):
    """구조화된 로깅 테스트"""
    logger.info(
        "test_event",
        user_id="123",
        action="search",
        duration_ms=150
    )

    # JSON 파싱 확인
    log_record = caplog.records[0]
    log_json = json.loads(log_record.message)

    assert log_json['event'] == 'test_event'
    assert log_json['user_id'] == '123'
    assert log_json['action'] == 'search'
    assert log_json['duration_ms'] == 150
    assert 'timestamp' in log_json


def test_log_levels(logger, caplog):
    """로그 레벨 테스트"""
    logger.debug("debug message")
    logger.info("info message")
    logger.warning("warning message")
    logger.error("error message")

    assert len(caplog.records) == 4
    assert caplog.records[0].levelname == 'DEBUG'
    assert caplog.records[1].levelname == 'INFO'
    assert caplog.records[2].levelname == 'WARNING'
    assert caplog.records[3].levelname == 'ERROR'


def test_email_masking_in_logs(logger, caplog):
    """로그 내 이메일 마스킹 테스트"""
    logger.info(
        "user_login",
        email="user@example.com",
        ip="192.168.1.100"
    )

    log_json = json.loads(caplog.records[0].message)

    assert log_json['email'] == 'u***@example.com'
    assert log_json['ip'] == '192.168.*.*'
```

---

## ✅ 검증 기준

### 기능 검증
- [ ] structlog 정상 설정 (JSON 출력)
- [ ] 로그 레벨 필터링 확인 (INFO, WARNING, ERROR)
- [ ] 파일 핸들러 동작 확인 (app.log, error.log)
- [ ] 로그 로테이션 확인 (일별)

### 보안 검증 ([HARD RULE])
- [ ] 이메일 마스킹 확인 (u***@example.com)
- [ ] IP 마스킹 확인 (192.168.*.*)
- [ ] 민감 검색어 해시 확인
- [ ] 에러 로그에 시스템 정보 노출 없음

### 성능 검증
- [ ] 로그 오버헤드 < 5ms (1000회 측정)
- [ ] 파일 I/O 블로킹 없음 (비동기 핸들러)

---

## 📂 파일 구조

```
backend/
├── app/
│   ├── utils/
│   │   ├── logger.py              # structlog 설정
│   │   └── file_handler.py        # 파일 핸들러
│   ├── core/
│   │   └── config.py              # 로그 설정 추가
│   └── main.py                     # 로깅 초기화
├── tests/
│   ├── test_logger.py             # 마스킹 테스트
│   └── test_logging_integration.py # 통합 테스트
├── scripts/
│   └── logrotate.conf             # 로그 로테이션 설정
├── docs/
│   └── logging-guide.md           # 로깅 가이드
├── logs/                           # 로그 파일 (gitignore)
│   ├── app.log
│   └── error.log
└── requirements.txt               # structlog 추가
```

---

## 🔒 보안 고려사항

### [HARD RULE] 개인정보 보호
1. **이메일 마스킹**
   - 첫 글자만 표시: `u***@example.com`
   - 전체 이메일 노출 금지

2. **IP 주소 마스킹**
   - 앞 2자리만 표시: `192.168.*.*`
   - 전체 IP 노출 금지

3. **민감 검색어 보호**
   - 키워드 기반 감지: 급여, 연봉, 인사, 기밀 등
   - SHA-256 해시로 변환 (16자 트렁케이트)
   - `query_masked: true` 플래그 추가

4. **에러 로그 안전화**
   - 스택 트레이스에서 파일 경로 제거
   - DB 연결 문자열 마스킹
   - API 키 노출 방지

---

## 📊 로그 예시

### 정상 검색 요청 (INFO)
```json
{
  "timestamp": "2026-01-10T12:34:56.789Z",
  "level": "info",
  "event": "search_request",
  "query_id": "qry_abc123",
  "user_id": "user_123",
  "user_email": "u***@example.com",
  "query": "연차 사용 방법",
  "response_time_ms": 2500,
  "sources_count": 5,
  "is_fallback": false
}
```

### 느린 응답 (WARNING)
```json
{
  "timestamp": "2026-01-10T12:35:00.123Z",
  "level": "warning",
  "event": "slow_response",
  "query_id": "qry_def456",
  "response_time_ms": 27000,
  "threshold_ms": 25000,
  "llm_time_ms": 24500,
  "vector_search_time_ms": 1200
}
```

### LLM 실패 (ERROR)
```json
{
  "timestamp": "2026-01-10T12:36:00.456Z",
  "level": "error",
  "event": "llm_call_failed",
  "query_id": "qry_ghi789",
  "error": "Timeout after 30 seconds",
  "error_type": "TimeoutError",
  "retry_count": 3,
  "fallback_used": true
}
```

---

## 📈 모니터링 메트릭

### 주요 메트릭
1. **에러율**
   - ERROR 로그 발생 빈도
   - 목표: < 1% (전체 요청 대비)

2. **응답 시간**
   - P50, P95, P99 측정
   - WARNING 발생 빈도 (> 25초)

3. **Fallback 비율**
   - Fallback 모드 진입 빈도
   - 목표: < 5%

### 대시보드 (추후 구현)
```
┌─────────────────────────────────────────┐
│  RAG Platform Monitoring Dashboard      │
├─────────────────────────────────────────┤
│  Last Hour                               │
│  - Total Requests: 1,234                │
│  - Error Rate: 0.5%                     │
│  - P95 Response Time: 18.5s             │
│  - Fallback Rate: 2.3%                  │
│                                          │
│  Top Errors (Last 24h)                  │
│  1. LLM Timeout: 15                     │
│  2. Milvus Connection: 3                │
│  3. DB Lock: 1                          │
└─────────────────────────────────────────┘
```

---

## 🔄 향후 개선 사항

### Phase 4 이후
1. **중앙 로그 수집**
   - ELK Stack (Elasticsearch, Logstash, Kibana)
   - Grafana Loki
   - AWS CloudWatch

2. **실시간 알림**
   - 에러율 > 5% → Slack 알림
   - P95 > 30초 → 이메일 알림
   - 서버 다운 → PagerDuty

3. **로그 분석**
   - 자주 검색되는 키워드 분석
   - 에러 패턴 분석
   - 사용자 행동 분석

4. **트레이싱**
   - OpenTelemetry 통합
   - 분산 트레이싱
   - 요청 흐름 추적

---

## 📚 참고 자료

- [structlog Documentation](https://www.structlog.org/)
- [Python Logging Cookbook](https://docs.python.org/3/howto/logging-cookbook.html)
- [12 Factor App: Logs](https://12factor.net/logs)
- [GDPR Logging Best Practices](https://gdpr.eu/data-processing/)

---

**작성자**: Task Planner
**작성일**: 2026-01-10
**버전**: 1.0.0
