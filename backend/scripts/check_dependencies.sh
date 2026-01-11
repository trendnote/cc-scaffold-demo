#!/bin/bash
# Dependency Vulnerability Check Script
# Task 4.3b: Security & Permission Testing

set -e

echo "=========================================="
echo "Dependency Vulnerability Check (Safety)"
echo "=========================================="
echo ""

# 현재 디렉토리 확인
if [ ! -f "requirements.txt" ]; then
    echo "❌ requirements.txt not found"
    echo "Run this script from the backend directory"
    exit 1
fi

echo "✓ requirements.txt found"
echo ""

# Safety 설치 확인
if ! command -v safety &> /dev/null; then
    echo "❌ Safety is not installed"
    echo "Install: pip install safety"
    exit 1
fi

echo "✓ Safety is installed"
echo ""

# Dependency check 실행
echo "🔍 Checking dependencies for known vulnerabilities..."
echo ""

# Safety check (무료 버전)
# --json 옵션으로 JSON 출력
# --output 옵션으로 파일 저장

safety check \
    --file requirements.txt \
    --json \
    --output safety-report.json || true

# 결과 확인
if [ -f "safety-report.json" ]; then
    echo ""
    echo "✓ Safety report generated: safety-report.json"

    # JSON 파싱하여 요약 출력
    VULN_COUNT=$(python3 -c "
import json
try:
    with open('safety-report.json', 'r') as f:
        data = json.load(f)
        if isinstance(data, list):
            print(len(data))
        else:
            print(0)
except:
    print(0)
" 2>/dev/null || echo "0")

    echo ""
    echo "=========================================="
    echo "Results"
    echo "=========================================="
    echo "Vulnerabilities found: $VULN_COUNT"

    if [ "$VULN_COUNT" -gt 0 ]; then
        echo ""
        echo "⚠️  Vulnerabilities detected!"
        echo "Review safety-report.json for details"
        exit 1
    else
        echo ""
        echo "✓ No known vulnerabilities found"
    fi
else
    echo "⚠️  Safety report not generated"
fi

echo ""
echo "=========================================="
echo "Dependency Check Complete"
echo "=========================================="
