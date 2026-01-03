# Task 2.4: 권한 기반 필터링 로직 - 실행 계획

---

## 📋 Meta

- **Task ID**: 2.4
- **Task명**: 권한 기반 필터링 로직
- **예상 시간**: 6시간
- **담당**: Backend
- **작성일**: 2026-01-03
- **상태**: Ready for Implementation
- **버전**: 1.0.0

---

## 1. Executive Summary

### 1.1 목표
사용자의 access_level과 부서 정보를 기반으로 접근 가능한 문서만 검색 결과에 포함시킵니다.

### 1.2 핵심 요구사항
- **보안**: [HARD RULE] 권한 없는 문서는 절대 노출 금지
- **기능**: Access level (1-3) 및 부서 기반 필터링
- **성능**: 필터링으로 인한 검색 성능 저하 < 10%
- **안정성**: 권한 테스트 10개 시나리오 100% 통과

### 1.3 성공 기준
- [ ] Level 1 사용자는 Level 2/3 문서 접근 불가
- [ ] Level 2 사용자는 타부서 Level 2 문서 접근 불가
- [ ] Level 2 사용자는 자부서 Level 2 문서 접근 가능
- [ ] Management는 모든 문서 접근 가능
- [ ] 권한 테스트 10개 케이스 100% 통과

### 1.4 Why This Task Matters
**정보 보안의 핵심**:
- **데이터 유출 방지**: 권한 없는 문서 노출 차단
- **컴플라이언스**: 회사 보안 정책 준수
- **사용자 신뢰**: 안전한 정보 접근 환경 제공

---

## 2. 선행 조건 검증

### 2.1 환경 검증
```bash
# Task 1.2 완료 확인 (documents 테이블 access_level 컬럼)
psql -d rag_platform -c "\d documents"

# Task 2.3 완료 확인 (VectorSearchService)
ls -la backend/app/services/vector_search.py
```

### 2.2 의존성 확인
- [x] **Task 1.2**: PostgreSQL 스키마 완료 (documents.access_level)
- [x] **Task 1.3**: Milvus Collection 완료 (metadata 필드에 access_level 포함)
- [x] **Task 2.3**: VectorSearchService 구현 완료

---

## 3. 접근 제어 모델 설계

### 3.1 Access Level 정의

```python
class AccessLevel:
    PUBLIC = 1        # 모든 사용자 접근 가능
    INTERNAL = 2      # 같은 부서만 접근 (또는 Management)
    CONFIDENTIAL = 3  # Management만 접근
```

### 3.2 권한 규칙

| 사용자 레벨 | 부서 | 접근 가능 문서 |
|------------|------|--------------|
| L1 (Public) | Any | L1 문서만 |
| L2 (Internal) | Marketing | L1 + Marketing L2 |
| L2 (Internal) | Engineering | L1 + Engineering L2 |
| L3 (Confidential) | Management | 모든 문서 (L1, L2, L3) |

### 3.3 Milvus 필터 표현식 생성 로직

```python
def build_filter_expr(user: User) -> str:
    """
    사용자 권한 기반 Milvus 필터 표현식 생성

    Returns:
        str: Milvus filter expression (예: "access_level == 1")
    """
    # Case 1: Management (L3)는 모든 문서 접근
    if user.department == "Management":
        return "access_level >= 1"  # 모든 문서

    # Case 2: L1 사용자는 Public 문서만
    if user.access_level == 1:
        return "access_level == 1"

    # Case 3: L2 사용자는 Public + 자부서 Internal 문서
    if user.access_level == 2:
        return (
            f"(access_level == 1) or "
            f"(access_level == 2 and department == '{user.department}')"
        )

    # Case 4: L3 사용자 (Management 제외)는 Public + 자부서 모든 문서
    if user.access_level == 3:
        return (
            f"(access_level == 1) or "
            f"(department == '{user.department}')"
        )

    # 기본값: Public만
    return "access_level == 1"
```

---

## 4. 구현 단계별 상세 계획

### 4.1 Step 1: 사용자 정보 모델 정의 (60분)

#### 작업 내용
**`backend/app/schemas/user.py` 작성**:

```python
from pydantic import BaseModel, Field
from typing import Optional


class User(BaseModel):
    """사용자 정보 스키마"""

    user_id: str = Field(..., description="사용자 고유 ID")
    access_level: int = Field(..., ge=1, le=3, description="접근 레벨 (1-3)")
    department: str = Field(..., description="부서명")
    email: Optional[str] = Field(None, description="이메일")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user_001",
                "access_level": 2,
                "department": "Engineering",
                "email": "user@example.com"
            }
        }


class UserContext:
    """사용자 컨텍스트 (JWT에서 추출)"""

    def __init__(self, user_id: str, access_level: int, department: str):
        self.user_id = user_id
        self.access_level = access_level
        self.department = department

    @staticmethod
    def from_token(token: str) -> "UserContext":
        """
        JWT에서 사용자 정보 추출

        [NOTE] Task 3.x에서 실제 JWT 파싱 구현
        현재는 Mock 데이터 사용
        """
        # TODO: JWT 파싱 로직 구현
        return UserContext(
            user_id="user_test",
            access_level=2,
            department="Engineering"
        )
```

---

### 4.2 Step 2: Access Control 서비스 구현 (120분)

#### 작업 내용
**`backend/app/services/access_control.py` 작성**:

```python
import logging
from typing import Optional
from app.schemas.user import UserContext

logger = logging.getLogger(__name__)


class AccessControlService:
    """권한 기반 접근 제어 서비스"""

    @staticmethod
    def build_filter_expression(user: UserContext) -> str:
        """
        사용자 권한 기반 Milvus 필터 표현식 생성

        Args:
            user: 사용자 컨텍스트

        Returns:
            str: Milvus filter expression

        [HARD RULE] 권한 없는 문서는 절대 노출 금지
        """
        logger.info(
            f"필터 표현식 생성: user_id={user.user_id}, "
            f"access_level={user.access_level}, "
            f"department={user.department}"
        )

        # Management는 모든 문서 접근
        if user.department == "Management":
            filter_expr = "access_level >= 1"
            logger.debug(f"Management 전체 접근: {filter_expr}")
            return filter_expr

        # L1 사용자: Public만
        if user.access_level == 1:
            filter_expr = "access_level == 1"
            logger.debug(f"L1 Public 접근: {filter_expr}")
            return filter_expr

        # L2 사용자: Public + 자부서 Internal
        if user.access_level == 2:
            filter_expr = (
                f"(access_level == 1) or "
                f"(access_level == 2 and department == '{user.department}')"
            )
            logger.debug(f"L2 부서별 접근: {filter_expr}")
            return filter_expr

        # L3 사용자 (Management 제외): Public + 자부서 모든 문서
        if user.access_level == 3:
            filter_expr = (
                f"(access_level == 1) or "
                f"(department == '{user.department}')"
            )
            logger.debug(f"L3 부서별 전체 접근: {filter_expr}")
            return filter_expr

        # 기본값: Public만 (안전한 기본값)
        logger.warning(
            f"알 수 없는 access_level={user.access_level}, Public만 허용"
        )
        return "access_level == 1"

    @staticmethod
    def can_access_document(user: UserContext, document_access_level: int, document_department: str) -> bool:
        """
        사용자가 특정 문서에 접근 가능한지 확인

        Args:
            user: 사용자 컨텍스트
            document_access_level: 문서 접근 레벨
            document_department: 문서 부서

        Returns:
            bool: 접근 가능 여부
        """
        # Public 문서는 모두 접근 가능
        if document_access_level == 1:
            return True

        # Management는 모두 접근 가능
        if user.department == "Management":
            return True

        # Internal 문서는 같은 부서만
        if document_access_level == 2:
            return user.access_level >= 2 and user.department == document_department

        # Confidential 문서는 Management만 (이미 위에서 체크)
        if document_access_level == 3:
            return False

        # 기본값: 거부
        return False
```

---

### 4.3 Step 3: VectorSearchService 통합 (90분)

#### 작업 내용
**`backend/app/services/vector_search.py` 수정**:

```python
from app.schemas.user import UserContext
from app.services.access_control import AccessControlService

class VectorSearchService:
    # ... 기존 코드 ...

    def search(
        self,
        query: str,
        top_k: int = 5,
        user: Optional[UserContext] = None  # 추가
    ) -> List[SearchResult]:
        """
        벡터 유사도 검색 실행 (권한 필터링 포함)

        Args:
            query: 검색어
            top_k: 반환할 최대 결과 수
            user: 사용자 컨텍스트 (권한 필터링용)

        Returns:
            List[SearchResult]: 검색 결과 (권한 필터링 완료)
        """
        self._ensure_collection()

        # Step 1: 권한 필터 표현식 생성
        filter_expr = None
        if user:
            access_control = AccessControlService()
            filter_expr = access_control.build_filter_expression(user)
            logger.info(f"권한 필터 적용: {filter_expr}")

        # Step 2: 쿼리 임베딩 생성
        query_embedding = self.embedding_service.embed_query(query)

        # Step 3: Milvus 검색 (필터 포함)
        try:
            search_results = self.collection.search(
                data=[query_embedding],
                anns_field="embedding",
                param=self.search_params,
                limit=top_k,
                expr=filter_expr,  # 권한 필터 적용
                output_fields=[
                    "document_id",
                    "chunk_index",
                    "content",
                    "page_number",
                    "metadata"
                ]
            )

            results = self._parse_results(search_results[0])

            logger.info(
                f"권한 필터링 검색 완료: found={len(results)}, "
                f"user={user.user_id if user else 'anonymous'}"
            )

            return results

        except Exception as e:
            logger.error(f"권한 기반 벡터 검색 실패: {e}")
            raise ValueError(f"벡터 검색 실패: {e}")
```

---

### 4.4 Step 4: 통합 테스트 (90분)

#### 작업 내용
**`backend/tests/test_access_control.py` 작성**:

```python
import pytest
from app.services.access_control import AccessControlService
from app.schemas.user import UserContext


def test_management_access_all():
    """TC01: Management는 모든 문서 접근 가능"""
    user = UserContext(user_id="mgr_001", access_level=3, department="Management")

    filter_expr = AccessControlService.build_filter_expression(user)

    assert "access_level >= 1" in filter_expr


def test_l1_user_public_only():
    """TC02: L1 사용자는 Public만 접근"""
    user = UserContext(user_id="user_001", access_level=1, department="Engineering")

    filter_expr = AccessControlService.build_filter_expression(user)

    assert filter_expr == "access_level == 1"


def test_l2_user_same_department():
    """TC03: L2 사용자는 Public + 자부서 Internal 접근"""
    user = UserContext(user_id="user_002", access_level=2, department="Engineering")

    filter_expr = AccessControlService.build_filter_expression(user)

    assert "access_level == 1" in filter_expr
    assert "access_level == 2" in filter_expr
    assert "department == 'Engineering'" in filter_expr


def test_l2_user_cannot_access_other_department():
    """TC04: L2 사용자는 타부서 Internal 접근 불가"""
    user = UserContext(user_id="user_003", access_level=2, department="Marketing")

    can_access = AccessControlService.can_access_document(
        user,
        document_access_level=2,
        document_department="Engineering"
    )

    assert can_access is False


def test_l2_user_can_access_same_department():
    """TC05: L2 사용자는 자부서 Internal 접근 가능"""
    user = UserContext(user_id="user_004", access_level=2, department="Marketing")

    can_access = AccessControlService.can_access_document(
        user,
        document_access_level=2,
        document_department="Marketing"
    )

    assert can_access is True


def test_l3_user_non_management():
    """TC06: L3 사용자 (비Management)는 자부서 모든 문서 접근"""
    user = UserContext(user_id="user_005", access_level=3, department="Engineering")

    can_access_l3_same_dept = AccessControlService.can_access_document(
        user,
        document_access_level=3,
        document_department="Engineering"
    )

    assert can_access_l3_same_dept is True


# ... 4개 추가 테스트 케이스 (총 10개)
```

---

## 5. 테스트 계획

### 5.1 단위 테스트
```bash
pytest backend/tests/test_access_control.py -v
# 예상: 10 passed
```

### 5.2 통합 테스트
```bash
pytest backend/tests/integration/test_search_permissions.py -v
# 예상: 5 passed (End-to-End 권한 검증)
```

---

## 6. 검증 기준

### 6.1 필수 체크리스트

- [ ] L1 사용자는 L2/L3 문서 접근 불가
- [ ] L2 사용자는 타부서 L2 문서 접근 불가
- [ ] L2 사용자는 자부서 L2 문서 접근 가능
- [ ] Management는 모든 문서 접근 가능
- [ ] Milvus 필터 표현식 문법 오류 없음
- [ ] 단위 테스트 10개 케이스 통과
- [ ] 통합 테스트 5개 시나리오 통과

### 6.2 성능 기준

- [ ] 필터링으로 인한 검색 성능 저하 < 10%

---

## 7. 출력물

### 7.1 생성될 파일

1. `backend/app/schemas/user.py` - 사용자 정보 스키마
2. `backend/app/services/access_control.py` - 권한 제어 서비스
3. `backend/tests/test_access_control.py` - 단위 테스트 (10개)
4. `backend/tests/integration/test_search_permissions.py` - 통합 테스트 (5개)

### 7.2 수정될 파일

1. `backend/app/services/vector_search.py` - 권한 필터 통합
2. `backend/app/services/search_service.py` - UserContext 파라미터 추가

---

## 8. 참고 문서

- Task Breakdown: `docs/tasks/task-breakdown.md`
- Task 1.2 Plan: PostgreSQL 스키마 (access_level 컬럼)
- Milvus Filter Expressions: https://milvus.io/docs/boolean.md

---

**작성자**: Claude Code (Sonnet 4.5)
**작성일**: 2026-01-03
