"""
응답 시간 테스트

Task 4.3c: 성능 테스트

목표: P95 < 30초
"""
import asyncio
import httpx
import statistics
import time
from typing import List


async def measure_search_response_time() -> List[float]:
    """
    100회 검색 요청 실행 및 응답 시간 측정

    Returns:
        List[float]: 응답 시간 리스트 (ms)
    """
    # 로그인
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "user@example.com",
                "password": "password123"
            }
        )
        token = login_response.json()["access_token"]

        # 100회 검색 요청
        response_times = []
        test_queries = [
            "연차 사용 방법",
            "휴가 신청 절차",
            "급여 지급일",
            "출퇴근 시간",
            "회의실 예약",
        ]

        for i in range(100):
            query = test_queries[i % len(test_queries)]

            start_time = time.time()

            response = await client.post(
                "/api/v1/search/",
                json={"query": query, "limit": 5},
                headers={"Authorization": f"Bearer {token}"},
                timeout=60.0
            )

            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000

            response_times.append(duration_ms)

            if (i + 1) % 10 == 0:
                print(f"Progress: {i + 1}/100")

        return response_times


def calculate_percentiles(data: List[float]) -> dict:
    """
    백분위수 계산

    Args:
        data: 응답 시간 리스트

    Returns:
        dict: P50, P95, P99
    """
    sorted_data = sorted(data)

    return {
        "p50": statistics.median(sorted_data),
        "p95": sorted_data[int(len(sorted_data) * 0.95)],
        "p99": sorted_data[int(len(sorted_data) * 0.99)],
        "min": min(sorted_data),
        "max": max(sorted_data),
        "mean": statistics.mean(sorted_data),
    }


async def main():
    """메인 테스트 실행"""
    print("=== 응답 시간 테스트 시작 ===")
    print("100회 검색 요청 실행 중...\n")

    response_times = await measure_search_response_time()

    print("\n=== 결과 ===")
    percentiles = calculate_percentiles(response_times)

    for key, value in percentiles.items():
        print(f"{key.upper()}: {value:.2f} ms ({value/1000:.2f} s)")

    # NFR 검증
    p95_seconds = percentiles["p95"] / 1000
    if p95_seconds < 30:
        print(f"\n✓ P95 응답 시간 목표 달성: {p95_seconds:.2f}s < 30s")
    else:
        print(f"\n✗ P95 응답 시간 목표 미달: {p95_seconds:.2f}s >= 30s")

    # CSV 저장
    import csv
    with open("response_times.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["request_number", "response_time_ms"])
        for i, rt in enumerate(response_times, 1):
            writer.writerow([i, rt])

    print("\n결과가 response_times.csv에 저장되었습니다.")


if __name__ == "__main__":
    asyncio.run(main())
