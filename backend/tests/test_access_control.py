"""
권한 제어 서비스 단위 테스트

AccessControlService의 필터 표현식 생성 및 문서 접근 검증을 테스트합니다.
"""

import pytest
from app.services.access_control import AccessControlService
from app.schemas.user import UserContext


def test_management_access_all():
    """TC01: Management는 모든 문서 접근 가능"""
    user = UserContext(
        user_id="mgr_001",
        access_level=3,
        department="Management"
    )

    filter_expr = AccessControlService.build_filter_expression(user)

    assert 'metadata["access_level"] >= 1' in filter_expr
    assert "Management" not in filter_expr  # Management는 부서 필터 불필요


def test_l1_user_public_only():
    """TC02: L1 사용자는 Public만 접근"""
    user = UserContext(
        user_id="user_001",
        access_level=1,
        department="Engineering"
    )

    filter_expr = AccessControlService.build_filter_expression(user)

    assert filter_expr == 'metadata["access_level"] == 1'


def test_l2_user_same_department():
    """TC03: L2 사용자는 Public + 자부서 Internal 접근"""
    user = UserContext(
        user_id="user_002",
        access_level=2,
        department="Engineering"
    )

    filter_expr = AccessControlService.build_filter_expression(user)

    assert 'metadata["access_level"] == 1' in filter_expr
    assert 'metadata["access_level"] == 2' in filter_expr
    assert 'metadata["department"] == "Engineering"' in filter_expr


def test_l2_user_cannot_access_other_department():
    """TC04: L2 사용자는 타부서 Internal 접근 불가"""
    user = UserContext(
        user_id="user_003",
        access_level=2,
        department="Marketing"
    )

    can_access = AccessControlService.can_access_document(
        user,
        document_access_level=2,
        document_department="Engineering"
    )

    assert can_access is False


def test_l2_user_can_access_same_department():
    """TC05: L2 사용자는 자부서 Internal 접근 가능"""
    user = UserContext(
        user_id="user_004",
        access_level=2,
        department="Marketing"
    )

    can_access = AccessControlService.can_access_document(
        user,
        document_access_level=2,
        document_department="Marketing"
    )

    assert can_access is True


def test_l3_user_non_management():
    """TC06: L3 사용자 (비Management)는 자부서 모든 문서 접근"""
    user = UserContext(
        user_id="user_005",
        access_level=3,
        department="Engineering"
    )

    # 자부서 L3 문서 접근 가능
    can_access_l3_same_dept = AccessControlService.can_access_document(
        user,
        document_access_level=3,
        document_department="Engineering"
    )

    assert can_access_l3_same_dept is True

    # 타부서 L3 문서 접근 불가
    can_access_l3_other_dept = AccessControlService.can_access_document(
        user,
        document_access_level=3,
        document_department="Marketing"
    )

    assert can_access_l3_other_dept is False


def test_public_document_access_all():
    """TC07: Public 문서는 모든 사용자 접근 가능"""
    users = [
        UserContext("user_l1", 1, "Engineering"),
        UserContext("user_l2", 2, "Marketing"),
        UserContext("user_l3", 3, "Engineering"),
        UserContext("mgr", 3, "Management"),
    ]

    for user in users:
        can_access = AccessControlService.can_access_document(
            user,
            document_access_level=1,
            document_department="Any"
        )
        assert can_access is True, f"{user.user_id} should access Public documents"


def test_management_access_all_documents():
    """TC08: Management는 모든 레벨, 모든 부서 문서 접근 가능"""
    user = UserContext(
        user_id="mgr_002",
        access_level=3,
        department="Management"
    )

    test_cases = [
        (1, "Engineering"),
        (2, "Marketing"),
        (3, "Finance"),
    ]

    for doc_level, doc_dept in test_cases:
        can_access = AccessControlService.can_access_document(
            user,
            document_access_level=doc_level,
            document_department=doc_dept
        )
        assert can_access is True, \
            f"Management should access L{doc_level} {doc_dept} documents"


def test_l1_user_cannot_access_internal():
    """TC09: L1 사용자는 Internal/Confidential 접근 불가"""
    user = UserContext(
        user_id="user_006",
        access_level=1,
        department="Engineering"
    )

    # 자부서 L2 문서도 접근 불가
    can_access_l2 = AccessControlService.can_access_document(
        user,
        document_access_level=2,
        document_department="Engineering"
    )

    assert can_access_l2 is False

    # 자부서 L3 문서도 접근 불가
    can_access_l3 = AccessControlService.can_access_document(
        user,
        document_access_level=3,
        document_department="Engineering"
    )

    assert can_access_l3 is False


def test_filter_expression_validation():
    """TC10: 필터 표현식 유효성 검증"""
    valid_user = UserContext("user_007", 2, "Engineering")

    filter_expr = AccessControlService.build_filter_expression(valid_user)

    # 유효성 검증
    is_valid = AccessControlService.validate_filter_expression(filter_expr)

    assert is_valid is True
    assert "access_level" in filter_expr

    # 빈 필터 표현식은 유효하지 않음
    is_valid_empty = AccessControlService.validate_filter_expression("")
    assert is_valid_empty is False

    # 위험한 키워드 포함 시 유효하지 않음
    dangerous_filter = "access_level == 1; DROP TABLE users"
    is_valid_dangerous = AccessControlService.validate_filter_expression(dangerous_filter)
    assert is_valid_dangerous is False


def test_l2_user_filter_expression_structure():
    """TC11 (Bonus): L2 사용자 필터 표현식 구조 검증"""
    user = UserContext("user_008", 2, "Marketing")

    filter_expr = AccessControlService.build_filter_expression(user)

    # OR 조건 포함
    assert " or " in filter_expr

    # Public 조건
    assert '(metadata["access_level"] == 1)' in filter_expr

    # 부서별 Internal 조건
    assert '(metadata["access_level"] == 2 and metadata["department"] == "Marketing")' in filter_expr


def test_l3_user_filter_expression_structure():
    """TC12 (Bonus): L3 사용자 (비Management) 필터 표현식 구조 검증"""
    user = UserContext("user_009", 3, "Finance")

    filter_expr = AccessControlService.build_filter_expression(user)

    # OR 조건 포함
    assert " or " in filter_expr

    # Public 조건
    assert '(metadata["access_level"] == 1)' in filter_expr

    # 부서 조건 (모든 레벨)
    assert '(metadata["department"] == "Finance")' in filter_expr
