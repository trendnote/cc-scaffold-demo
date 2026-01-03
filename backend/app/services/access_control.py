"""
권한 기반 접근 제어 서비스

사용자의 access_level과 부서 정보를 기반으로
Milvus 필터 표현식을 생성하고 문서 접근 권한을 검증합니다.
"""

import logging
from app.schemas.user import UserContext

logger = logging.getLogger(__name__)


class AccessControlService:
    """
    권한 기반 접근 제어 서비스

    [HARD RULE] 권한 없는 문서는 절대 노출 금지
    """

    @staticmethod
    def build_filter_expression(user: UserContext) -> str:
        """
        사용자 권한 기반 Milvus 필터 표현식 생성

        Args:
            user: 사용자 컨텍스트

        Returns:
            str: Milvus filter expression

        권한 규칙:
        - Management: 모든 문서 접근 (L1, L2, L3)
        - L1 사용자: Public 문서만 (L1)
        - L2 사용자: Public + 자부서 Internal (L1 + 자부서 L2)
        - L3 사용자 (비Management): Public + 자부서 모든 문서 (L1 + 자부서 L2/L3)
        """
        logger.info(
            f"필터 표현식 생성: user_id={user.user_id}, "
            f"access_level={user.access_level}, "
            f"department={user.department}"
        )

        # Case 1: Management는 모든 문서 접근
        if user.department == "Management":
            filter_expr = 'metadata["access_level"] >= 1'
            logger.debug(f"Management 전체 접근: {filter_expr}")
            return filter_expr

        # Case 2: L1 사용자는 Public만
        if user.access_level == 1:
            filter_expr = 'metadata["access_level"] == 1'
            logger.debug(f"L1 Public 접근: {filter_expr}")
            return filter_expr

        # Case 3: L2 사용자는 Public + 자부서 Internal
        if user.access_level == 2:
            filter_expr = (
                f'(metadata["access_level"] == 1) or '
                f'(metadata["access_level"] == 2 and metadata["department"] == "{user.department}")'
            )
            logger.debug(f"L2 부서별 접근: {filter_expr}")
            return filter_expr

        # Case 4: L3 사용자 (Management 제외)는 Public + 자부서 모든 문서
        if user.access_level == 3:
            filter_expr = (
                f'(metadata["access_level"] == 1) or '
                f'(metadata["department"] == "{user.department}")'
            )
            logger.debug(f"L3 부서별 전체 접근: {filter_expr}")
            return filter_expr

        # 기본값: Public만 (안전한 기본값)
        logger.warning(
            f"알 수 없는 access_level={user.access_level}, Public만 허용"
        )
        return 'metadata["access_level"] == 1'

    @staticmethod
    def can_access_document(
        user: UserContext,
        document_access_level: int,
        document_department: str
    ) -> bool:
        """
        사용자가 특정 문서에 접근 가능한지 확인

        Args:
            user: 사용자 컨텍스트
            document_access_level: 문서 접근 레벨 (1-3)
            document_department: 문서 부서

        Returns:
            bool: 접근 가능 여부

        [HARD RULE] 권한 없는 문서는 절대 노출 금지
        """
        logger.debug(
            f"문서 접근 검증: user={user.user_id}, "
            f"doc_level={document_access_level}, "
            f"doc_dept={document_department}"
        )

        # Public 문서는 모두 접근 가능
        if document_access_level == 1:
            logger.debug("Public 문서 → 접근 허용")
            return True

        # Management는 모두 접근 가능
        if user.department == "Management":
            logger.debug("Management 사용자 → 접근 허용")
            return True

        # Internal 문서는 같은 부서 + access_level >= 2
        if document_access_level == 2:
            can_access = (
                user.access_level >= 2 and
                user.department == document_department
            )
            logger.debug(
                f"Internal 문서 → "
                f"{'접근 허용' if can_access else '접근 거부'}"
            )
            return can_access

        # Confidential 문서는 같은 부서 + access_level >= 3
        if document_access_level == 3:
            can_access = (
                user.access_level >= 3 and
                user.department == document_department
            )
            logger.debug(
                f"Confidential 문서 → "
                f"{'접근 허용' if can_access else '접근 거부'}"
            )
            return can_access

        # 기본값: 거부 (안전한 기본값)
        logger.warning(
            f"알 수 없는 document_access_level={document_access_level} → 접근 거부"
        )
        return False

    @staticmethod
    def validate_filter_expression(filter_expr: str) -> bool:
        """
        Milvus 필터 표현식 유효성 검증

        Args:
            filter_expr: Milvus 필터 표현식

        Returns:
            bool: 유효 여부
        """
        # 기본 검증: 빈 문자열 체크
        if not filter_expr or not filter_expr.strip():
            logger.error("빈 필터 표현식")
            return False

        # 필수 키워드 포함 검증
        required_keywords = ["access_level"]
        if not any(keyword in filter_expr for keyword in required_keywords):
            logger.error(f"필수 키워드 누락: {required_keywords}")
            return False

        # SQL Injection 방어: 위험한 키워드 체크
        dangerous_keywords = ["DROP", "DELETE", "INSERT", "UPDATE", "--", ";"]
        for keyword in dangerous_keywords:
            if keyword.lower() in filter_expr.lower():
                logger.error(f"위험한 키워드 감지: {keyword}")
                return False

        return True
