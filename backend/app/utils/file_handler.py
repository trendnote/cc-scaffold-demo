"""
파일 핸들러 설정

Task 4.2: 기본 모니터링 로그 설정

로그 파일 저장 및 로테이션 관리
- app.log: 일반 로그 (90일 보관)
- error.log: 에러 로그만 (365일 보관)
"""
import os
import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import Optional

from app.core.config import settings


def setup_file_handlers(
    logger: logging.Logger,
    log_file_path: Optional[str] = None,
    error_log_file_path: Optional[str] = None
) -> None:
    """
    파일 핸들러 설정

    Args:
        logger: Logger 인스턴스
        log_file_path: 일반 로그 파일 경로 (기본: settings.LOG_FILE_PATH)
        error_log_file_path: 에러 로그 파일 경로 (기본: app.log → error.log)
    """
    # 로그 파일 경로 결정
    if log_file_path is None:
        log_file_path = settings.LOG_FILE_PATH

    if error_log_file_path is None:
        # app.log → error.log로 변환
        error_log_file_path = log_file_path.replace("app.log", "error.log")

    # 로그 디렉토리 생성
    log_dir = Path(log_file_path).parent
    log_dir.mkdir(parents=True, exist_ok=True)

    # [핸들러 1] 일반 로그 (INFO 이상, 90일 보관)
    app_handler = TimedRotatingFileHandler(
        filename=log_file_path,
        when="midnight",  # 매일 자정에 로테이션
        interval=1,       # 1일 간격
        backupCount=settings.LOG_RETENTION_DAYS,  # 90일 보관
        encoding="utf-8",
        delay=False,
        utc=True
    )
    app_handler.setLevel(logging.INFO)
    app_handler.setFormatter(logging.Formatter("%(message)s"))  # structlog이 이미 포맷팅
    app_handler.suffix = "%Y-%m-%d"  # 백업 파일명: app.log.2025-01-11

    # [핸들러 2] 에러 로그 (ERROR 이상, 365일 보관)
    error_handler = TimedRotatingFileHandler(
        filename=error_log_file_path,
        when="midnight",
        interval=1,
        backupCount=settings.ERROR_LOG_RETENTION_DAYS,  # 365일 보관
        encoding="utf-8",
        delay=False,
        utc=True
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(logging.Formatter("%(message)s"))
    error_handler.suffix = "%Y-%m-%d"  # 백업 파일명: error.log.2025-01-11

    # Logger에 핸들러 추가
    logger.addHandler(app_handler)
    logger.addHandler(error_handler)

    logger.info(
        f"파일 핸들러 설정 완료: "
        f"app_log={log_file_path}, "
        f"error_log={error_log_file_path}"
    )


def cleanup_old_logs(log_dir: str, retention_days: int) -> int:
    """
    보관 기간 초과 로그 파일 삭제

    Args:
        log_dir: 로그 디렉토리
        retention_days: 보관 일수

    Returns:
        int: 삭제된 파일 수
    """
    import time
    from datetime import datetime, timedelta

    log_path = Path(log_dir)

    if not log_path.exists():
        return 0

    # 삭제 기준 시간 (현재 - retention_days)
    cutoff_time = time.time() - (retention_days * 24 * 60 * 60)
    deleted_count = 0

    # 로그 파일 순회 (*.log.YYYY-MM-DD 패턴)
    for log_file in log_path.glob("*.log.*"):
        # 파일 수정 시간 확인
        file_mtime = log_file.stat().st_mtime

        if file_mtime < cutoff_time:
            try:
                log_file.unlink()  # 파일 삭제
                deleted_count += 1
                logging.info(f"오래된 로그 삭제: {log_file}")
            except Exception as e:
                logging.error(f"로그 삭제 실패: {log_file}, {e}")

    if deleted_count > 0:
        logging.info(
            f"로그 정리 완료: {deleted_count}개 파일 삭제 "
            f"(기준: {retention_days}일 초과)"
        )

    return deleted_count


def get_log_file_size(log_file_path: str) -> int:
    """
    로그 파일 크기 확인 (바이트)

    Args:
        log_file_path: 로그 파일 경로

    Returns:
        int: 파일 크기 (바이트), 파일 없으면 0
    """
    log_path = Path(log_file_path)

    if not log_path.exists():
        return 0

    return log_path.stat().st_size


def get_log_stats(log_dir: str) -> dict:
    """
    로그 디렉토리 통계

    Args:
        log_dir: 로그 디렉토리

    Returns:
        dict: {
            "total_files": int,
            "total_size_bytes": int,
            "oldest_log": str,
            "newest_log": str
        }
    """
    log_path = Path(log_dir)

    if not log_path.exists():
        return {
            "total_files": 0,
            "total_size_bytes": 0,
            "oldest_log": None,
            "newest_log": None
        }

    # 모든 .log 파일 수집
    log_files = list(log_path.glob("*.log*"))

    if not log_files:
        return {
            "total_files": 0,
            "total_size_bytes": 0,
            "oldest_log": None,
            "newest_log": None
        }

    # 통계 계산
    total_size = sum(f.stat().st_size for f in log_files)
    log_files_sorted = sorted(log_files, key=lambda f: f.stat().st_mtime)

    return {
        "total_files": len(log_files),
        "total_size_bytes": total_size,
        "total_size_mb": round(total_size / (1024 * 1024), 2),
        "oldest_log": str(log_files_sorted[0].name),
        "newest_log": str(log_files_sorted[-1].name)
    }
