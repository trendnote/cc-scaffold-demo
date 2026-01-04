"""
구조화된 로깅 (Structlog)

Task 2.9: 성능 최적화 및 로깅

[HARD RULE] 개인정보 마스킹:
- user_id: 뒤 4자리만 표시
- email: @ 앞 2자만 표시
- query: 민감 키워드 마스킹 (주민번호, 계좌번호, 전화번호)
"""

import structlog
import logging
import sys
from typing import Any, Dict
import re


def configure_logging(log_level: str = "INFO"):
    """
    Structlog 구조화된 로깅 설정

    [HARD RULE] 개인정보 마스킹:
    - user_id: 뒤 4자리만 표시
    - email: @ 앞 2자만 표시
    - query: 민감 키워드 마스킹

    Args:
        log_level: 로그 레벨 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            _mask_sensitive_data,  # 커스텀 프로세서
            structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelName(log_level)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )


def _mask_sensitive_data(logger, method_name, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    개인정보 마스킹 프로세서

    [HARD RULE] 마스킹 대상:
    - user_id: user_1234 → user_****1234
    - email: user@example.com → us**@example.com
    - query: 민감 키워드 (주민번호, 계좌번호, 전화번호 패턴)

    Args:
        logger: Logger 인스턴스
        method_name: 로그 메서드 이름
        event_dict: 이벤트 딕셔너리

    Returns:
        Dict[str, Any]: 마스킹된 이벤트 딕셔너리
    """
    # user_id 마스킹
    if "user_id" in event_dict:
        user_id = str(event_dict["user_id"])
        if len(user_id) > 4:
            masked_part = "*" * (len(user_id) - 4)
            event_dict["user_id"] = f"{masked_part}{user_id[-4:]}"

    # email 마스킹
    if "email" in event_dict:
        email = str(event_dict["email"])
        if "@" in email:
            local, domain = email.split("@", 1)
            if len(local) > 2:
                masked_local = local[:2] + "**"
            else:
                masked_local = "**"
            event_dict["email"] = f"{masked_local}@{domain}"

    # query 민감 정보 마스킹
    if "query" in event_dict:
        query = str(event_dict["query"])

        # 주민번호 패턴 (123456-1234567)
        query = re.sub(r"\d{6}-\d{7}", "[주민번호]", query)

        # 계좌번호 패턴 (123-456-789012)
        query = re.sub(r"\d{3}-\d{3}-\d{6,}", "[계좌번호]", query)

        # 전화번호 패턴 (010-1234-5678)
        query = re.sub(r"\d{3}-\d{4}-\d{4}", "[전화번호]", query)

        # 휴대폰 번호 패턴 (01012345678)
        query = re.sub(r"010\d{8}", "[전화번호]", query)

        # 이메일 주소 마스킹
        query = re.sub(
            r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
            "[이메일]",
            query
        )

        event_dict["query"] = query

    return event_dict


def get_logger(name: str):
    """
    구조화된 로거 생성

    Args:
        name: 로거 이름 (보통 __name__ 사용)

    Returns:
        structlog.BoundLogger: 구조화된 로거

    Usage:
        logger = get_logger(__name__)
        logger.info(
            "search_request",
            user_id="user_12345",
            query="연차 사용 방법",
            response_time_ms=1234
        )
    """
    return structlog.get_logger(name)
