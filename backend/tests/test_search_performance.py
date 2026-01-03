"""
성능 테스트: 벡터 검색 성능 검증

P95 < 1초 목표를 검증합니다.
"""

import pytest
import time
import statistics
from typing import List
from app.services.search_service import SearchService
from app.services.vector_search import VectorSearchService


# 성능 측정용 쿼리 세트
PERFORMANCE_QUERIES = [
    "연차 사용 방법은 무엇인가요",
    "급여 지급일은 언제인가요",
    "회의실 예약 절차를 알려주세요",
    "복리후생 제도에 대해 설명해주세요",
    "재택근무 정책은 어떻게 되나요",
    "야근 수당 계산 방법",
    "퇴직금 규정",
    "휴가 신청 절차",
    "경조사 휴가 일수",
    "건강검진 안내",
]


def measure_search_time(service: SearchService, query: str, limit: int = 5) -> float:
    """
    검색 실행 시간 측정 (ms)

    Returns:
        float: 실행 시간 (밀리초)
    """
    start_time = time.perf_counter()
    results = service.search_documents(query, limit=limit)
    end_time = time.perf_counter()

    elapsed_ms = (end_time - start_time) * 1000
    return elapsed_ms


def calculate_percentile(values: List[float], percentile: int) -> float:
    """
    백분위수 계산

    Args:
        values: 측정값 리스트
        percentile: 백분위 (95 for P95)

    Returns:
        float: 백분위수 값
    """
    if not values:
        return 0.0

    sorted_values = sorted(values)
    index = int(len(sorted_values) * (percentile / 100))

    # index가 범위를 벗어나지 않도록 조정
    if index >= len(sorted_values):
        index = len(sorted_values) - 1

    return sorted_values[index]


def test_single_search_latency():
    """TC01: 단일 검색 응답 시간"""
    service = SearchService()
    query = "연차 사용 방법"

    elapsed_ms = measure_search_time(service, query, limit=5)

    print(f"\n단일 검색 응답 시간: {elapsed_ms:.2f}ms")

    # 단일 검색은 2초 이내여야 함 (여유 있는 기준)
    assert elapsed_ms < 2000, f"단일 검색이 너무 느림: {elapsed_ms:.2f}ms"


def test_p95_latency_requirement():
    """TC02: P95 < 1초 검증 (HARD RULE)"""
    service = SearchService()

    # 100번 검색 실행
    latencies = []
    for i in range(100):
        query = PERFORMANCE_QUERIES[i % len(PERFORMANCE_QUERIES)]
        elapsed_ms = measure_search_time(service, query, limit=5)
        latencies.append(elapsed_ms)

    # 통계 계산
    p50 = calculate_percentile(latencies, 50)
    p95 = calculate_percentile(latencies, 95)
    p99 = calculate_percentile(latencies, 99)
    avg = statistics.mean(latencies)

    print(f"\n성능 통계 (100회 검색):")
    print(f"  평균: {avg:.2f}ms")
    print(f"  P50: {p50:.2f}ms")
    print(f"  P95: {p95:.2f}ms")
    print(f"  P99: {p99:.2f}ms")
    print(f"  최소: {min(latencies):.2f}ms")
    print(f"  최대: {max(latencies):.2f}ms")

    # HARD RULE: P95 < 1000ms
    assert p95 < 1000, f"P95 성능 목표 미달: {p95:.2f}ms (목표: < 1000ms)"


def test_vector_search_latency():
    """TC03: VectorSearchService 단독 성능"""
    service = VectorSearchService()

    latencies = []
    for i in range(50):
        query = PERFORMANCE_QUERIES[i % len(PERFORMANCE_QUERIES)]

        start_time = time.perf_counter()
        results = service.search(query, top_k=5)
        end_time = time.perf_counter()

        elapsed_ms = (end_time - start_time) * 1000
        latencies.append(elapsed_ms)

    p95 = calculate_percentile(latencies, 95)
    avg = statistics.mean(latencies)

    print(f"\nVectorSearchService 성능 (50회):")
    print(f"  평균: {avg:.2f}ms")
    print(f"  P95: {p95:.2f}ms")

    # VectorSearch P95 < 800ms (SearchService보다 여유)
    assert p95 < 800, f"VectorSearchService P95 목표 미달: {p95:.2f}ms"


def test_search_latency_with_different_top_k():
    """TC04: top_k 값에 따른 성능 변화"""
    service = SearchService()
    query = "급여 지급일은 언제인가요"

    results = {}

    for top_k in [1, 5, 10, 20]:
        latencies = []
        for _ in range(20):
            elapsed_ms = measure_search_time(service, query, limit=top_k)
            latencies.append(elapsed_ms)

        avg = statistics.mean(latencies)
        results[top_k] = avg

    print(f"\ntop_k별 평균 응답 시간:")
    for top_k, avg_time in results.items():
        print(f"  top_k={top_k}: {avg_time:.2f}ms")

    # 모든 top_k에서 평균 1.5초 이내
    for top_k, avg_time in results.items():
        assert avg_time < 1500, f"top_k={top_k} 평균 응답 시간 초과: {avg_time:.2f}ms"


def test_search_consistency():
    """TC05: 동일 쿼리 반복 검색 시 성능 일관성"""
    service = SearchService()
    query = "연차 사용 방법"

    latencies = []
    for _ in range(30):
        elapsed_ms = measure_search_time(service, query, limit=5)
        latencies.append(elapsed_ms)

    avg = statistics.mean(latencies)
    stdev = statistics.stdev(latencies) if len(latencies) > 1 else 0

    print(f"\n동일 쿼리 반복 검색 (30회):")
    print(f"  평균: {avg:.2f}ms")
    print(f"  표준편차: {stdev:.2f}ms")
    print(f"  변동계수: {(stdev / avg * 100):.1f}%")

    # 변동계수 < 50% (합리적인 일관성)
    cv = stdev / avg if avg > 0 else 0
    assert cv < 0.5, f"성능 변동이 너무 큼: CV={cv:.2%}"


def test_embedding_time_measurement():
    """TC06: 임베딩 생성 시간 측정"""
    from app.services.embedding_service import OllamaEmbeddingService

    service = OllamaEmbeddingService()

    latencies = []
    for query in PERFORMANCE_QUERIES[:20]:
        start_time = time.perf_counter()
        embedding = service.embed_query(query)
        end_time = time.perf_counter()

        elapsed_ms = (end_time - start_time) * 1000
        latencies.append(elapsed_ms)

    avg = statistics.mean(latencies)
    p95 = calculate_percentile(latencies, 95)

    print(f"\n임베딩 생성 시간 (20회):")
    print(f"  평균: {avg:.2f}ms")
    print(f"  P95: {p95:.2f}ms")

    # 임베딩 P95 < 500ms (reasonable for Ollama)
    assert p95 < 500, f"임베딩 생성이 너무 느림: {p95:.2f}ms"


def test_milvus_search_time():
    """TC07: Milvus 검색 시간 단독 측정"""
    service = VectorSearchService()
    service._ensure_collection()

    # 더미 임베딩으로 검색 (임베딩 시간 제외)
    dummy_embedding = [0.1] * 768

    latencies = []
    for _ in range(50):
        start_time = time.perf_counter()

        search_results = service.collection.search(
            data=[dummy_embedding],
            anns_field="embedding",
            param=service.search_params,
            limit=5,
            output_fields=["document_id", "chunk_index", "content", "page_number", "metadata"]
        )

        end_time = time.perf_counter()

        elapsed_ms = (end_time - start_time) * 1000
        latencies.append(elapsed_ms)

    avg = statistics.mean(latencies)
    p95 = calculate_percentile(latencies, 95)

    print(f"\nMilvus 검색 시간 (50회, 임베딩 제외):")
    print(f"  평균: {avg:.2f}ms")
    print(f"  P95: {p95:.2f}ms")

    # Milvus 검색 P95 < 200ms
    assert p95 < 200, f"Milvus 검색이 너무 느림: {p95:.2f}ms"


def test_search_performance_summary():
    """TC08: 성능 테스트 종합 요약"""
    service = SearchService()

    # 100번 검색으로 종합 통계
    latencies = []
    for i in range(100):
        query = PERFORMANCE_QUERIES[i % len(PERFORMANCE_QUERIES)]
        elapsed_ms = measure_search_time(service, query, limit=5)
        latencies.append(elapsed_ms)

    print(f"\n========== 성능 테스트 종합 요약 ==========")
    print(f"총 검색 횟수: {len(latencies)}")
    print(f"평균 응답 시간: {statistics.mean(latencies):.2f}ms")
    print(f"중앙값 (P50): {calculate_percentile(latencies, 50):.2f}ms")
    print(f"P95: {calculate_percentile(latencies, 95):.2f}ms")
    print(f"P99: {calculate_percentile(latencies, 99):.2f}ms")
    print(f"최소 응답 시간: {min(latencies):.2f}ms")
    print(f"최대 응답 시간: {max(latencies):.2f}ms")
    print(f"표준편차: {statistics.stdev(latencies):.2f}ms")
    print(f"==========================================")

    p95 = calculate_percentile(latencies, 95)
    assert p95 < 1000, f"종합 P95 목표 미달: {p95:.2f}ms"
