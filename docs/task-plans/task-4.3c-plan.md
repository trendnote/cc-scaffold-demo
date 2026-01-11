# Task 4.3c 실행 계획: 성능 테스트

## 📋 작업 정보
- **Task ID**: 4.3c
- **Task명**: 성능 테스트
- **예상 시간**: 3시간
- **담당**: Backend + Infrastructure
- **의존성**: Task 2.9 (성능 최적화 및 로깅)
- **GitHub Issue**: #34

---

## 🎯 작업 목표

시스템 성능을 측정하고 NFR(Non-Functional Requirements) 달성 여부를 검증

---

## 📐 성능 목표 (NFR)

- **응답 시간**: P95 < 30초
- **동시 사용자**: 100명 처리 가능
- **에러율**: < 1%
- **처리량**: 최소 10 req/sec

---

## 🏗️ 테스트 아키텍처

```
┌──────────────────────────────────────────────────────────────┐
│              Performance Testing Architecture                 │
├──────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌──────────────────────────────────────────┐                │
│  │  Load Generator (Locust)                 │                │
│  │  - 가상 사용자 생성                        │                │
│  │  - 동시 요청 시뮬레이션                    │                │
│  └──────────────────┬───────────────────────┘                │
│                     │                                          │
│                     ▼                                          │
│  ┌──────────────────────────────────────────┐                │
│  │  Test Scenarios                           │                │
│  │  - 응답 시간 테스트 (100회)                │                │
│  │  - 동시 사용자 테스트 (100명)              │                │
│  │  - 부하 테스트 (증가 패턴)                 │                │
│  └──────────────────┬───────────────────────┘                │
│                     │                                          │
│                     ▼                                          │
│  ┌──────────────────────────────────────────┐                │
│  │  Backend API                              │                │
│  │  (FastAPI + PostgreSQL + Milvus)         │                │
│  └──────────────────┬───────────────────────┘                │
│                     │                                          │
│                     ▼                                          │
│  ┌──────────────────────────────────────────┐                │
│  │  Metrics Collection                       │                │
│  │  - Response Times (P50, P95, P99)        │                │
│  │  - Error Rates                            │                │
│  │  - Throughput (req/sec)                  │                │
│  │  - Resource Usage (CPU, Memory)          │                │
│  └──────────────────┬───────────────────────┘                │
│                     │                                          │
│                     ▼                                          │
│  ┌──────────────────────────────────────────┐                │
│  │  Performance Report                       │                │
│  │  - HTML Report (Graphs)                  │                │
│  │  - CSV Data                              │                │
│  │  - JSON Results                          │                │
│  └──────────────────────────────────────────┘                │
│                                                                │
└──────────────────────────────────────────────────────────────┘
```

---

## 📝 구현 계획

### Phase 1: Locust 설정 (0.5시간)

#### 1.1 Locust 설치
**파일**: `backend/requirements-dev.txt`
```python
locust==2.16.1
```

```bash
pip install locust
```

#### 1.2 Locust 파일 작성
**파일**: `backend/tests/performance/locustfile.py`
```python
"""
성능 테스트 시나리오

목표:
- P95 응답 시간 < 30초
- 동시 사용자 100명 처리
- 에러율 < 1%
"""
from locust import HttpUser, task, between
import random


class RAGPlatformUser(HttpUser):
    """RAG 플랫폼 사용자 시뮬레이션"""

    wait_time = between(1, 3)  # 1-3초 대기
    host = "http://localhost:8000"

    def on_start(self):
        """테스트 시작 시 로그인"""
        # 로그인하여 토큰 얻기
        response = self.client.post(
            "/api/v1/auth/login",
            json={
                "email": "user@example.com",
                "password": "password123"
            }
        )

        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access_token")
        else:
            raise Exception("Login failed")

    @task(10)
    def search_query(self):
        """검색 쿼리 (가장 빈번한 작업)"""
        queries = [
            "연차 사용 방법",
            "휴가 신청 절차",
            "급여 지급일",
            "출퇴근 시간",
            "회의실 예약 방법",
            "복지 제도",
            "재택 근무 정책",
            "교육 지원 제도",
        ]

        query = random.choice(queries)

        self.client.post(
            "/api/v1/search/",
            json={"query": query, "limit": 5},
            headers={"Authorization": f"Bearer {self.token}"},
            name="/api/v1/search/ (검색)"
        )

    @task(3)
    def view_history(self):
        """히스토리 조회"""
        self.client.get(
            "/api/v1/users/me/history?page=1&page_size=10",
            headers={"Authorization": f"Bearer {self.token}"},
            name="/api/v1/users/me/history (히스토리)"
        )

    @task(1)
    def submit_feedback(self):
        """피드백 제출"""
        self.client.post(
            "/api/v1/feedback/",
            json={
                "query_id": "test_query_123",
                "rating": random.randint(1, 5),
                "comment": "테스트 피드백"
            },
            headers={"Authorization": f"Bearer {self.token}"},
            name="/api/v1/feedback/ (피드백)"
        )
```

---

### Phase 2: 응답 시간 테스트 (1시간)

#### 2.1 응답 시간 측정 스크립트
**파일**: `backend/tests/performance/test_response_time.py`
```python
"""
응답 시간 테스트

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
```

**실행**:
```bash
python backend/tests/performance/test_response_time.py
```

---

### Phase 3: 동시 사용자 테스트 (1시간)

#### 3.1 Locust 실행 스크립트
**파일**: `backend/scripts/run_load_test.sh`
```bash
#!/bin/bash
# Locust 부하 테스트 실행

echo "=== Locust 부하 테스트 ==="
echo "목표: 동시 사용자 100명, 에러율 < 1%"
echo ""

# 백엔드 서버 확인
if ! curl -s http://localhost:8000/health > /dev/null; then
    echo "✗ 백엔드 서버가 실행되지 않았습니다"
    echo "docker-compose up -d를 먼저 실행하세요"
    exit 1
fi

echo "✓ 백엔드 서버 정상"
echo ""

# Locust 실행 (헤드리스 모드)
locust \
    -f backend/tests/performance/locustfile.py \
    --headless \
    --users 100 \
    --spawn-rate 10 \
    --run-time 5m \
    --html=load-test-report.html \
    --csv=load-test \
    --host=http://localhost:8000

echo ""
echo "=== 테스트 완료 ==="
echo "리포트: load-test-report.html"
echo "데이터: load-test_stats.csv"
```

**실행**:
```bash
bash backend/scripts/run_load_test.sh
```

#### 3.2 Locust 웹 UI 모드
```bash
# 웹 UI로 실행 (대화형)
locust -f backend/tests/performance/locustfile.py

# 브라우저에서 http://localhost:8089 접속
# 사용자 수와 증가율 설정
```

---

### Phase 4: 성능 분석 및 리포트 (0.5시간)

#### 4.1 결과 분석 스크립트
**파일**: `backend/tests/performance/analyze_results.py`
```python
"""
성능 테스트 결과 분석
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
```

**실행**:
```bash
python backend/tests/performance/analyze_results.py load-test_stats.csv
```

---

## 🧪 테스트 시나리오

### 시나리오 1: 응답 시간 테스트
**목표**: P95 < 30초

```bash
# 실행
python backend/tests/performance/test_response_time.py

# 예상 결과
# P50: 15,000 ms (15 s)
# P95: 25,000 ms (25 s)  ← 목표 달성
# P99: 28,000 ms (28 s)
```

### 시나리오 2: 동시 사용자 100명
**목표**: 에러율 < 1%

```bash
# 실행 (5분간)
bash backend/scripts/run_load_test.sh

# 예상 결과
# 총 요청: 3,000
# 실패: 15
# 에러율: 0.5%  ← 목표 달성
```

### 시나리오 3: 램프업 테스트
**목표**: 점진적 부하 증가 시 안정성 확인

```bash
# 웹 UI로 실행
locust -f backend/tests/performance/locustfile.py

# 설정:
# - 사용자: 200
# - 증가율: 5/sec
# - 실행 시간: 10분

# 확인 사항:
# - 사용자 수 증가에 따른 응답 시간 추이
# - 임계점 확인 (응답 시간이 급격히 증가하는 지점)
```

---

## ✅ 검증 기준

### 성능 목표 달성
- [ ] **P95 응답 시간 < 30초**
  - 100회 테스트 실행
  - 95회 이상 30초 이내

- [ ] **동시 사용자 100명 처리**
  - 5분간 안정적 처리
  - 에러율 < 1%

- [ ] **처리량 >= 10 req/s**
  - 지속 가능한 처리량

### 리포트 생성
- [ ] HTML 리포트 (그래프 포함)
- [ ] CSV 데이터 (상세 분석용)
- [ ] JSON 요약 (CI/CD 연동용)

---

## 📂 파일 구조

```
backend/
├── tests/
│   └── performance/
│       ├── locustfile.py
│       ├── test_response_time.py
│       └── analyze_results.py
├── scripts/
│   └── run_load_test.sh
└── performance-reports/        # 성능 리포트 (gitignore)
    ├── load-test-report.html
    ├── load-test_stats.csv
    ├── response_times.csv
    └── performance_summary.json
```

---

## 📊 예상 결과

### 응답 시간 분포
```
┌────────────────────────────────────────┐
│  Response Time Distribution            │
├────────────────────────────────────────┤
│  P50:  15.2s  ████████████░░░░░░░░░    │
│  P75:  20.5s  ████████████████░░░░░    │
│  P90:  24.8s  ███████████████████░░    │
│  P95:  27.1s  ████████████████████░    │
│  P99:  29.3s  █████████████████████    │
│  Max:  32.5s  ██████████████████████   │
└────────────────────────────────────────┘
```

### 부하 테스트 결과
```
┌────────────────────────────────────────┐
│  Load Test Summary                     │
├────────────────────────────────────────┤
│  Duration: 5 minutes                   │
│  Users: 100 (concurrent)               │
│  Total Requests: 3,245                 │
│  Failures: 18                          │
│  Error Rate: 0.55%  ✓                  │
│  Requests/sec: 10.8  ✓                 │
└────────────────────────────────────────┘
```

---

## 🔧 성능 최적화 팁

### 병목 지점 식별
1. **벡터 검색 느림** (> 2초)
   - HNSW 파라미터 조정 (ef: 64 → 32)
   - 인덱스 재구성

2. **LLM 호출 느림** (> 25초)
   - Ollama → OpenAI 전환 (3배 빠름)
   - 프롬프트 최적화 (토큰 절약)

3. **DB 쿼리 느림** (> 1초)
   - Connection Pool 증가
   - 인덱스 추가
   - 쿼리 최적화

### 캐싱 전략
```python
# 검색 결과 캐싱 (Redis)
from functools import lru_cache

@lru_cache(maxsize=100)
def get_cached_search_result(query: str):
    # 동일 검색어 캐싱
    pass
```

---

## 🔄 향후 개선 사항

### Phase 4 이후
1. **스트레스 테스트**
   - 시스템 한계 테스트
   - 200명, 500명, 1000명

2. **Soak 테스트**
   - 장시간 부하 테스트 (24시간)
   - 메모리 누수 확인

3. **스파이크 테스트**
   - 급격한 부하 증가 시뮬레이션
   - Auto-scaling 검증

4. **분산 부하 테스트**
   - 여러 머신에서 동시 테스트
   - Locust Master-Worker 모드

---

## 📚 참고 자료

- [Locust Documentation](https://docs.locust.io/)
- [Performance Testing Best Practices](https://martinfowler.com/articles/practical-test-pyramid.html#PerformanceTests)
- [HTTP Load Testing](https://github.com/rakyll/hey)

---

**작성자**: Task Planner
**작성일**: 2026-01-10
**버전**: 1.0.0
