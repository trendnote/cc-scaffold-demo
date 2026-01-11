"""
성능 테스트 결과 분석

Task 4.3c: 성능 테스트
"""
import csv
import json


def analyze_locust_results(stats_file: str) -> dict:
    """
    Locust 통계 파일 분석

    Args:
        stats_file: CSV 통계 파일 경로

    Returns:
        dict: 분석 결과
    """
    with open(stats_file, "r") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # 전체 통계 (마지막 Aggregated 행)
    aggregated = [r for r in rows if r["Name"] == "Aggregated"][0]

    total_requests = int(aggregated["Request Count"])
    total_failures = int(aggregated["Failure Count"])
    error_rate = (total_failures / total_requests * 100) if total_requests > 0 else 0

    return {
        "total_requests": total_requests,
        "total_failures": total_failures,
        "error_rate_percent": error_rate,
        "p50_ms": float(aggregated["50%"]),
        "p95_ms": float(aggregated["95%"]),
        "p99_ms": float(aggregated["99%"]),
        "requests_per_second": float(aggregated["Requests/s"]),
    }


def generate_report(results: dict):
    """
    성능 테스트 리포트 생성

    Args:
        results: 분석 결과
    """
    print("=" * 60)
    print("성능 테스트 결과 리포트")
    print("=" * 60)
    print()

    print(f"총 요청 수: {results['total_requests']:,}")
    print(f"실패 수: {results['total_failures']:,}")
    print(f"에러율: {results['error_rate_percent']:.2f}%")
    print()

    print("응답 시간:")
    print(f"  P50: {results['p50_ms']:.0f} ms ({results['p50_ms']/1000:.2f} s)")
    print(f"  P95: {results['p95_ms']:.0f} ms ({results['p95_ms']/1000:.2f} s)")
    print(f"  P99: {results['p99_ms']:.0f} ms ({results['p99_ms']/1000:.2f} s)")
    print()

    print(f"처리량: {results['requests_per_second']:.2f} req/s")
    print()

    # NFR 검증
    print("=" * 60)
    print("NFR 검증")
    print("=" * 60)

    nfr_passed = True

    # P95 < 30초
    p95_seconds = results['p95_ms'] / 1000
    if p95_seconds < 30:
        print(f"✓ P95 응답 시간: {p95_seconds:.2f}s < 30s")
    else:
        print(f"✗ P95 응답 시간: {p95_seconds:.2f}s >= 30s")
        nfr_passed = False

    # 에러율 < 1%
    if results['error_rate_percent'] < 1:
        print(f"✓ 에러율: {results['error_rate_percent']:.2f}% < 1%")
    else:
        print(f"✗ 에러율: {results['error_rate_percent']:.2f}% >= 1%")
        nfr_passed = False

    # 처리량 >= 10 req/s
    if results['requests_per_second'] >= 10:
        print(f"✓ 처리량: {results['requests_per_second']:.2f} >= 10 req/s")
    else:
        print(f"✗ 처리량: {results['requests_per_second']:.2f} < 10 req/s")
        nfr_passed = False

    print()
    if nfr_passed:
        print("✓ 모든 NFR 목표 달성")
    else:
        print("✗ 일부 NFR 목표 미달")

    # JSON 저장
    with open("performance_summary.json", "w") as f:
        json.dump(results, f, indent=2)

    print()
    print("상세 결과가 performance_summary.json에 저장되었습니다.")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python analyze_results.py <stats_file.csv>")
        sys.exit(1)

    stats_file = sys.argv[1]
    results = analyze_locust_results(stats_file)
    generate_report(results)
