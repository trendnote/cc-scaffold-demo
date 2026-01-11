#!/bin/bash
# Locust 부하 테스트 실행
# Task 4.3c: 성능 테스트

set -e

echo "=== Locust 부하 테스트 ==="
echo "목표: 동시 사용자 100명, 에러율 < 1%"
echo ""

# 백엔드 서버 확인
if ! curl -s http://localhost:8000/health > /dev/null; then
    echo "✗ 백엔드 서버가 실행되지 않았습니다"
    echo "uvicorn app.main:app --host 0.0.0.0 --port 8000 을 먼저 실행하세요"
    exit 1
fi

echo "✓ 백엔드 서버 정상"
echo ""

# 테스트 디렉토리로 이동
cd "$(dirname "$0")/.."

# Locust 실행 (헤드리스 모드)
echo "🚀 Locust 실행 중..."
echo "   - 사용자: 100명"
echo "   - 증가율: 10명/초"
echo "   - 실행 시간: 5분"
echo ""

locust \
    -f tests/performance/locustfile.py \
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
echo ""

# 결과 분석
if [ -f "load-test_stats.csv" ]; then
    echo "📊 결과 분석 중..."
    python3 tests/performance/analyze_results.py load-test_stats.csv
fi
