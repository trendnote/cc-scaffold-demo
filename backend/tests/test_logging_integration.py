"""
로깅 통합 테스트

Task 4.2: 기본 모니터링 로그 설정

전체 로깅 시스템 통합 검증:
- structlog 설정 확인
- 파일 핸들러 동작 확인
- JSON 포맷 출력 확인
- 타임스탬프 검증
"""
import pytest
import json
import tempfile
import logging
from pathlib import Path
from datetime import datetime

from app.utils.logger import configure_logging, get_logger, add_timestamp
from app.utils.file_handler import (
    setup_file_handlers,
    cleanup_old_logs,
    get_log_file_size,
    get_log_stats
)


class TestLoggingConfiguration:
    """로깅 설정 테스트"""

    def test_configure_logging_default(self):
        """기본 로깅 설정"""
        configure_logging()
        logger = get_logger(__name__)

        assert logger is not None
        assert hasattr(logger, 'info')
        assert hasattr(logger, 'error')
        assert hasattr(logger, 'warning')

    def test_configure_logging_debug_level(self):
        """DEBUG 레벨 설정"""
        configure_logging(log_level="DEBUG")
        logger = get_logger(__name__)

        # DEBUG 레벨 확인
        root_logger = logging.getLogger()
        assert root_logger.level == logging.DEBUG

    def test_get_logger_instance(self):
        """로거 인스턴스 가져오기"""
        logger1 = get_logger("test.module1")
        logger2 = get_logger("test.module2")

        assert logger1 is not None
        assert logger2 is not None
        # 캐시된 로거 확인
        assert get_logger("test.module1") is logger1


class TestTimestampProcessor:
    """타임스탬프 프로세서 테스트"""

    def test_add_timestamp(self):
        """타임스탬프 추가"""
        event_dict = {"event": "test"}
        result = add_timestamp(None, None, event_dict)

        assert "timestamp" in result
        # ISO 8601 포맷 확인
        timestamp = result["timestamp"]
        assert timestamp.endswith("Z")
        # 파싱 가능 여부 확인
        datetime.fromisoformat(timestamp.replace("Z", "+00:00"))


class TestFileHandlers:
    """파일 핸들러 테스트"""

    def test_setup_file_handlers(self):
        """파일 핸들러 설정"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = str(Path(tmpdir) / "app.log")
            error_file = str(Path(tmpdir) / "error.log")

            logger = logging.getLogger("test_file_handler")
            logger.handlers.clear()  # 기존 핸들러 제거

            setup_file_handlers(logger, log_file, error_file)

            # 핸들러 추가 확인
            assert len(logger.handlers) >= 2

    def test_file_handler_creates_log_file(self):
        """로그 파일 생성 확인"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = str(Path(tmpdir) / "app.log")

            logger = logging.getLogger("test_create_file")
            logger.handlers.clear()
            logger.setLevel(logging.INFO)

            setup_file_handlers(logger, log_file)

            # 로그 작성
            logger.info("Test message")

            # 파일 생성 확인
            assert Path(log_file).exists()

    def test_error_log_separation(self):
        """에러 로그 분리 확인"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = str(Path(tmpdir) / "app.log")
            error_file = str(Path(tmpdir) / "error.log")

            logger = logging.getLogger("test_error_separation")
            logger.handlers.clear()
            logger.setLevel(logging.INFO)

            setup_file_handlers(logger, log_file, error_file)

            # INFO와 ERROR 로그 작성
            logger.info("Info message")
            logger.error("Error message")

            # 두 파일 모두 생성 확인
            assert Path(log_file).exists()
            assert Path(error_file).exists()

            # 에러 로그에는 ERROR만 있어야 함
            error_content = Path(error_file).read_text()
            assert "Error message" in error_content


class TestLogFileManagement:
    """로그 파일 관리 테스트"""

    def test_cleanup_old_logs(self):
        """오래된 로그 파일 삭제"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 테스트 로그 파일 생성
            old_log = Path(tmpdir) / "app.log.2020-01-01"
            recent_log = Path(tmpdir) / "app.log.2025-01-10"

            old_log.write_text("old log")
            recent_log.write_text("recent log")

            # 90일 이상 된 파일 삭제
            deleted_count = cleanup_old_logs(tmpdir, retention_days=90)

            # old_log만 삭제되어야 함
            assert not old_log.exists()
            assert recent_log.exists()
            assert deleted_count == 1

    def test_get_log_file_size(self):
        """로그 파일 크기 확인"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"
            log_file.write_text("test content")

            size = get_log_file_size(str(log_file))
            assert size == len("test content")

    def test_get_log_file_size_not_exists(self):
        """존재하지 않는 파일"""
        size = get_log_file_size("/nonexistent/path/test.log")
        assert size == 0

    def test_get_log_stats(self):
        """로그 디렉토리 통계"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 테스트 로그 파일 생성
            (Path(tmpdir) / "app.log").write_text("content1")
            (Path(tmpdir) / "error.log").write_text("content2")
            (Path(tmpdir) / "app.log.2025-01-10").write_text("content3")

            stats = get_log_stats(tmpdir)

            assert stats["total_files"] == 3
            assert stats["total_size_bytes"] > 0
            assert stats["oldest_log"] is not None
            assert stats["newest_log"] is not None

    def test_get_log_stats_empty_dir(self):
        """빈 디렉토리"""
        with tempfile.TemporaryDirectory() as tmpdir:
            stats = get_log_stats(tmpdir)

            assert stats["total_files"] == 0
            assert stats["total_size_bytes"] == 0
            assert stats["oldest_log"] is None
            assert stats["newest_log"] is None


class TestStructuredLogging:
    """구조화된 로깅 테스트"""

    def test_structured_log_format(self, caplog):
        """구조화된 로그 포맷 확인"""
        configure_logging(log_level="INFO")
        logger = get_logger(__name__)

        with caplog.at_level(logging.INFO):
            logger.info(
                "test_event",
                user_id="user_123",
                action="search",
                count=5
            )

        # 로그가 기록되었는지 확인
        assert len(caplog.records) > 0

    def test_json_serialization(self):
        """JSON 직렬화 가능 여부"""
        configure_logging(log_level="INFO")
        logger = get_logger(__name__)

        # JSON 직렬화 가능한 데이터
        test_data = {
            "event": "test",
            "user_id": "user_123",
            "count": 5,
            "is_active": True,
            "timestamp": "2025-01-11T10:30:00Z"
        }

        # 예외 없이 로깅 가능해야 함
        logger.info("json_test", **test_data)


class TestLoggingIntegration:
    """통합 테스트"""

    def test_end_to_end_logging(self):
        """전체 로깅 파이프라인"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = str(Path(tmpdir) / "app.log")

            # 1. 로깅 설정
            configure_logging(log_level="INFO")

            # 2. 파일 핸들러 설정
            root_logger = logging.getLogger()
            root_logger.handlers.clear()
            setup_file_handlers(root_logger, log_file)

            # 3. 로거 가져오기
            logger = get_logger("integration_test")

            # 4. 로그 작성 (개인정보 포함)
            logger.info(
                "user_action",
                email="user@example.com",
                client_ip="192.168.1.1",
                query="연차 사용 방법"
            )

            # 5. 파일 생성 확인
            assert Path(log_file).exists()

            # 6. 로그 내용 확인
            log_content = Path(log_file).read_text()
            assert len(log_content) > 0

            # JSON 파싱 가능 여부 (각 줄이 JSON)
            for line in log_content.strip().split("\n"):
                if line:
                    log_entry = json.loads(line)
                    # 기본 필드 확인
                    assert "timestamp" in log_entry
                    assert "level" in log_entry

    def test_logging_with_error_level(self):
        """에러 레벨 로깅"""
        with tempfile.TemporaryDirectory() as tmpdir:
            error_file = str(Path(tmpdir) / "error.log")

            configure_logging(log_level="INFO")

            root_logger = logging.getLogger()
            root_logger.handlers.clear()
            setup_file_handlers(
                root_logger,
                log_file_path=str(Path(tmpdir) / "app.log"),
                error_log_file_path=error_file
            )

            logger = get_logger("error_test")

            # 에러 로그 작성
            logger.error(
                "test_error",
                error_type="ValueError",
                error_message="Something went wrong"
            )

            # 에러 파일 생성 확인
            assert Path(error_file).exists()

            # 에러 로그 내용 확인
            error_content = Path(error_file).read_text()
            assert "test_error" in error_content


class TestLoggingPerformance:
    """로깅 성능 테스트"""

    def test_logging_performance(self):
        """로깅 성능 (1000회)"""
        import time

        configure_logging(log_level="INFO")
        logger = get_logger("performance_test")

        start_time = time.time()

        for i in range(1000):
            logger.info(
                "performance_test",
                iteration=i,
                user_id=f"user_{i}",
                action="test"
            )

        elapsed_time = time.time() - start_time

        # 1000회 로깅이 1초 이내 (성능 기준)
        assert elapsed_time < 1.0, f"Logging too slow: {elapsed_time:.2f}s"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
