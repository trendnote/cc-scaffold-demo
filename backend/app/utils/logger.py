"""
구조화된 로깅 설정

Task 4.2: 기본 모니터링 로그 설정

[HARD RULE] 개인정보 마스킹:
- 이메일: user@example.com → u***@example.com
- 민감 검색어: 마스킹 또는 해시
- IP 주소: 192.168.1.1 → 192.168.*.*
"""
import structlog
import logging
import re
import hashlib
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


def mask_sensitive_data(logger, method_name, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    민감 데이터 마스킹 프로세서

    [HARD RULE] 마스킹 대상:
    - email, user_email: u***@example.com
    - client_ip: 192.168.*.*
    - query: 민감 키워드 해시 (급여, 연봉, 인사, 기밀, 비밀)

    Args:
        logger: Logger 인스턴스
        method_name: 로그 메서드 이름
        event_dict: 이벤트 딕셔너리

    Returns:
        Dict: 마스킹된 이벤트 딕셔너리
    """
    # 이메일 마스킹
    if 'email' in event_dict:
        event_dict['email'] = mask_email(str(event_dict['email']))

    if 'user_email' in event_dict:
        event_dict['user_email'] = mask_email(str(event_dict['user_email']))

    # IP 마스킹
    if 'client_ip' in event_dict:
        event_dict['client_ip'] = mask_ip(str(event_dict['client_ip']))

    # 검색어 해시 (민감한 검색어 보호)
    if 'query' in event_dict:
        query = str(event_dict['query'])
        # 민감 키워드 체크
        sensitive_keywords = ['급여', '연봉', '인사', '기밀', '비밀', '급여명세서', '성과급']
        if any(keyword in query for keyword in sensitive_keywords):
            event_dict['query'] = hashlib.sha256(
                query.encode()
            ).hexdigest()[:16]
            event_dict['query_masked'] = True

    # 개인정보 패턴 마스킹
    if 'query' in event_dict and 'query_masked' not in event_dict:
        query = str(event_dict['query'])

        # 주민번호 패턴 (123456-1234567)
        query = re.sub(r'\d{6}-\d{7}', '[주민번호]', query)

        # 계좌번호 패턴 (123-456-789012)
        query = re.sub(r'\d{3}-\d{3}-\d{6,}', '[계좌번호]', query)

        # 전화번호 패턴 (010-1234-5678)
        query = re.sub(r'\d{3}-\d{4}-\d{4}', '[전화번호]', query)

        # 휴대폰 번호 패턴 (01012345678)
        query = re.sub(r'010\d{8}', '[전화번호]', query)

        # 이메일 주소 마스킹
        query = re.sub(
            r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            '[이메일]',
            query
        )

        event_dict['query'] = query

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
