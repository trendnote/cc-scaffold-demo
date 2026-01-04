"""
성능 측정 타이머

Task 2.6: 출처 추적 및 응답 구성
"""

import time
from contextlib import contextmanager
from typing import Dict
import logging

logger = logging.getLogger(__name__)


class PerformanceTimer:
    """
    성능 측정 타이머

    Usage:
        timer = PerformanceTimer()

        with timer.measure("embedding"):
            # 임베딩 생성 코드
            pass

        with timer.measure("search"):
            # 검색 코드
            pass

        embedding_time = timer.get("embedding")  # 밀리초
        total_time = timer.get_total()  # 모든 측정의 합
    """

    def __init__(self):
        """타이머 초기화"""
        self.timings: Dict[str, int] = {}

    @contextmanager
    def measure(self, operation: str):
        """
        컨텍스트 매니저로 성능 측정

        Args:
            operation: 측정할 작업명

        Yields:
            None

        Example:
            with timer.measure("embedding"):
                embed_query(query)
        """
        start_time = time.time()

        try:
            yield
        finally:
            elapsed_ms = int((time.time() - start_time) * 1000)
            self.timings[operation] = elapsed_ms
            logger.debug(f"[Performance] {operation}: {elapsed_ms}ms")

    def get(self, operation: str) -> int:
        """
        특정 작업의 소요 시간 조회 (밀리초)

        Args:
            operation: 작업명

        Returns:
            int: 소요 시간 (밀리초), 없으면 0
        """
        return self.timings.get(operation, 0)

    def get_all(self) -> Dict[str, int]:
        """
        모든 성능 측정 데이터 조회

        Returns:
            dict: {operation: time_ms} 딕셔너리
        """
        return self.timings.copy()

    def get_total(self) -> int:
        """
        전체 소요 시간 (밀리초)

        Returns:
            int: 모든 측정값의 합
        """
        return sum(self.timings.values())

    def reset(self):
        """모든 측정 데이터 초기화"""
        self.timings.clear()
        logger.debug("[Performance] Timer reset")
