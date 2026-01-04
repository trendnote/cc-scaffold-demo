# Task 2.2: 검색어 전처리 및 유효성 검증 - 실행 계획

---

## 📋 Meta

- **Task ID**: 2.2
- **Task명**: 검색어 전처리 및 유효성 검증
- **예상 시간**: 3시간
- **담당**: Backend
- **작성일**: 2026-01-03
- **상태**: Ready for Implementation
- **버전**: 1.0.0

---

## 1. Executive Summary

### 1.1 목표
검색 API의 입력 데이터에 대한 철저한 검증 및 전처리 로직을 구현하여 보안과 데이터 품질을 보장합니다.

### 1.2 핵심 요구사항
- **기능**: Pydantic 스키마 기반 입력 검증, 검색어 전처리
- **보안**: [HARD RULE] SQL Injection 방지, XSS 방지, 특수문자 필터링
- **품질**: 길이 제한 (5-200자), 빈 값 거부
- **안정성**: 21개 테스트 케이스 100% 통과

### 1.3 성공 기준
- [ ] 유효한 검색어 통과
- [ ] 4자 이하 검색어 거부 (422 에러)
- [ ] 201자 이상 검색어 거부 (422 에러)
- [ ] SQL Injection 패턴 차단 (SELECT, UNION, DROP 등)
- [ ] XSS 공격 패턴 차단 (<script>, javascript: 등)
- [ ] 단위 테스트 21개 케이스 통과
- [ ] API 통합 테스트 4개 케이스 통과

### 1.4 Why This Task Matters
**보안의 첫 번째 방어선**:
- **공격 차단**: SQL Injection, XSS 공격 원천 차단
- **데이터 품질**: 무의미한 검색어 사전 필터링
- **사용자 경험**: 명확한 에러 메시지로 사용자 가이드
- **시스템 안정성**: 과도한 요청 방지

---

## 2. 선행 조건 검증

### 2.1 환경 검증
```bash
# Task 2.1 완료 확인
ls -la backend/app/main.py
ls -la backend/app/routers/search.py

# Pydantic 버전 확인 (2.0+)
python -c "import pydantic; print(pydantic.__version__)"
```

### 2.2 의존성 확인
- [x] **Task 2.1**: FastAPI 기본 구조 및 라우터 설정 완료

---

## 3. 기술 스택 선택

### 3.1 Pydantic을 사용한 검증

**선택 이유**:
- FastAPI 네이티브 통합
- 자동 OpenAPI 문서 생성
- 타입 안전성 보장
- 커스텀 Validator 지원

### 3.2 검증 전략

```
입력 검증 계층:

1. Pydantic 스키마 (자동 검증)
   ↓
2. 커스텀 Validator (비즈니스 로직)
   ↓
3. 전처리 (정규화, 공백 제거)
   ↓
4. 보안 검사 (SQL Injection, XSS)
```

---

## 4. 구현 단계별 상세 계획

### 4.1 Step 1: Pydantic 스키마 정의 (40분)

#### 디렉토리 구조
```bash
mkdir -p backend/app/schemas
touch backend/app/schemas/__init__.py
```

#### `backend/app/schemas/search.py` 작성

**핵심 스키마**:

1. **SearchQueryRequest**: 검색 요청
   - query: 5-200자, SQL Injection/XSS 검증
   - limit: 1-20 범위
   - user_id, session_id: 선택적

2. **SearchQueryResponse**: 검색 응답
   - query_id, answer, sources
   - response_time_ms, timestamp

3. **DocumentSource**: 출처 정보
   - document_id, title, source
   - chunk_content, page_number
   - relevance_score (0-1)

**보안 검증 로직**:
```python
@field_validator('query')
@classmethod
def validate_query(cls, v: str) -> str:
    # 1. 공백 정규화
    v = ' '.join(v.split())

    # 2. 빈 값 검사
    if not v.strip():
        raise ValueError("검색어는 빈 값일 수 없습니다.")

    # 3. SQL Injection 패턴 검사
    sql_patterns = [
        r"(\bunion\b|\bselect\b|\bdrop\b|\bdelete\b|\binsert\b|\bupdate\b)",
        r"(--|;|\/\*|\*\/)",
        r"(\bor\b\s+\d+\s*=\s*\d+)",
        r"(\band\b\s+\d+\s*=\s*\d+)",
    ]

    for pattern in sql_patterns:
        if re.search(pattern, v, re.IGNORECASE):
            raise ValueError(
                f"검색어에 허용되지 않는 패턴이 포함되어 있습니다"
            )

    # 4. XSS 공격 패턴 검사
    xss_patterns = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"onerror\s*=",
        r"onload\s*=",
    ]

    for pattern in xss_patterns:
        if re.search(pattern, v, re.IGNORECASE):
            raise ValueError("검색어에 허용되지 않는 스크립트가 포함되어 있습니다.")

    # 5. 허용된 문자만 포함 (한글, 영어, 숫자, 공백, 일부 특수문자)
    allowed_pattern = r'^[가-힣a-zA-Z0-9\s\?\.\,\!\-\(\)]+$'
    if not re.match(allowed_pattern, v):
        raise ValueError(
            "검색어는 한글, 영어, 숫자, 공백, 기본 문장부호만 포함할 수 있습니다."
        )

    return v
```

---

### 4.2 Step 2: 테스트 케이스 작성 (60분)

#### `backend/tests/test_search_validation.py`

**테스트 카테고리**:

1. **Happy Path** (4개):
   - 유효한 한글 검색어
   - 유효한 영어 검색어
   - 한글+영어+숫자 혼합
   - 허용된 특수문자 (?, ., !, -, 괄호)

2. **Edge Cases** (4개):
   - 최소 길이 (5자)
   - 최대 길이 (200자)
   - 공백 정규화 (여러 공백 → 하나)
   - limit 파라미터 범위

3. **Error Handling** (6개):
   - 너무 짧은 검색어 (4자 이하)
   - 너무 긴 검색어 (201자 이상)
   - 빈 문자열
   - 공백만 있는 검색어
   - limit 범위 초과 (0, 21)

4. **Security** (7개):
   - SQL Injection (SELECT, UNION, DROP)
   - XSS (<script>, javascript:)
   - 허용되지 않는 특수문자 (#, $, %, &)
   - Comment 기호 (--, /*)

**총 21개 테스트 케이스**

#### 테스트 실행
```bash
# 테스트 실행
pytest backend/tests/test_search_validation.py -v

# 커버리지 확인
pytest backend/tests/test_search_validation.py \
  --cov=backend/app/schemas \
  --cov-report=html
```

---

### 4.3 Step 3: Search 라우터 업데이트 (30분)

#### `backend/app/routers/search.py` 수정

**변경사항**:
1. SearchQueryRequest 스키마 적용
2. ValidationError 처리
3. 에러 응답 표준화
4. OpenAPI 문서 responses 추가

```python
from pydantic import ValidationError
from app.schemas.search import SearchQueryRequest, SearchQueryResponse

@router.post(
    "/",
    response_model=SearchQueryResponse,
    responses={
        422: {"description": "잘못된 검색어"},
        500: {"description": "서버 에러"}
    },
    summary="검색 실행",
    description="자연어 질문에 대한 답변 및 출처 반환"
)
async def search(request: SearchQueryRequest):
    try:
        # TODO: Task 2.3-2.6에서 실제 검색 로직 구현

        # 임시 응답 (스켈레톤)
        return SearchQueryResponse(
            query_id="qry_temp_123",
            query=request.query,
            answer="검색 기능은 Task 2.3-2.6에서 구현될 예정입니다.",
            sources=[],
            response_time_ms=0
        )

    except ValidationError as e:
        # Pydantic 검증 에러는 FastAPI가 자동으로 422 반환
        raise

    except Exception as e:
        # [HARD RULE] 에러 메시지에 민감 정보 포함 금지
        raise HTTPException(
            status_code=500,
            detail={
                "error": "InternalServerError",
                "message": "검색 처리 중 오류가 발생했습니다."
            }
        )
```

---

### 4.4 Step 4: 통합 테스트 (30분)

#### `backend/tests/test_search_api.py`

**API 레벨 테스트**:
1. 정상 검색어 → 200 OK
2. 짧은 검색어 → 422 Validation Error
3. SQL Injection → 422 Validation Error
4. XSS 공격 → 422 Validation Error

```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_search_api_valid_query():
    """정상 검색어 → 200 OK"""
    response = client.post(
        "/api/v1/search/",
        json={"query": "연차 사용 방법"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "연차 사용 방법"
    assert "answer" in data
    assert "sources" in data
```

---

## 5. 테스트 계획

### 5.1 단위 테스트
```bash
pytest backend/tests/test_search_validation.py -v
# 예상: 21 passed
```

### 5.2 통합 테스트
```bash
pytest backend/tests/test_search_api.py -v
# 예상: 4 passed
```

### 5.3 커버리지
```bash
pytest backend/tests/test_search_validation.py \
  --cov=backend/app/schemas \
  --cov-report=html
# 목표: ≥ 95%
```

---

## 6. 검증 기준

### 6.1 필수 체크리스트

- [ ] Pydantic 스키마 정의 완료 (`SearchQueryRequest`, `SearchQueryResponse`)
- [ ] 검색어 길이 검증 (5-200자)
- [ ] SQL Injection 패턴 차단 (SELECT, UNION, DROP 등)
- [ ] XSS 공격 패턴 차단 (<script>, javascript:)
- [ ] 공백 정규화 (여러 공백 → 하나로)
- [ ] 단위 테스트 21개 케이스 통과
- [ ] API 통합 테스트 4개 케이스 통과
- [ ] 코드 커버리지 ≥ 95%

### 6.2 품질 기준

- [ ] 모든 에러 케이스 명확한 메시지
- [ ] OpenAPI 문서 자동 생성 확인 (/docs)
- [ ] 에러 응답 표준화 (SearchValidationError)

---

## 7. 출력물

### 7.1 생성될 파일

1. `backend/app/schemas/__init__.py`
2. `backend/app/schemas/search.py` - 검색 요청/응답 스키마
3. `backend/tests/test_search_validation.py` - 검증 로직 테스트 (21개)
4. `backend/tests/test_search_api.py` - API 통합 테스트 (4개)

### 7.2 수정될 파일

1. `backend/app/routers/search.py` - 스키마 적용 및 에러 처리

---

## 8. 참고 문서

- Task Breakdown: `docs/tasks/task-breakdown.md`
- Task 2.1 Plan: `docs/task-plans/task-2.1-plan.md`
- Pydantic Validators: https://docs.pydantic.dev/latest/concepts/validators/
- OWASP Input Validation: https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html

---

**작성자**: Claude Code (Sonnet 4.5)
**작성일**: 2026-01-03
