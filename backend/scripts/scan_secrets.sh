#!/bin/bash
# Secret Scanning Script
# Task 4.3b: Security & Permission Testing

set -e

echo "=========================================="
echo "Secret Scanning (Hardcoded Credentials)"
echo "=========================================="
echo ""

# 스캔할 디렉토리
SCAN_DIR="${1:-.}"

echo "Scanning directory: $SCAN_DIR"
echo ""

# 시크릿 패턴 정의
declare -a PATTERNS=(
    # API Keys
    "sk-[a-zA-Z0-9]{20,}"
    "api[_-]?key['\"]?\s*[:=]\s*['\"][a-zA-Z0-9]{16,}['\"]"

    # Passwords
    "password['\"]?\s*[:=]\s*['\"][^'\"]{8,}['\"]"
    "passwd['\"]?\s*[:=]\s*['\"][^'\"]{8,}['\"]"
    "pwd['\"]?\s*[:=]\s*['\"][^'\"]{8,}['\"]"

    # Database URLs
    "postgresql://[^:]+:[^@]+@"
    "mysql://[^:]+:[^@]+@"
    "mongodb://[^:]+:[^@]+@"

    # AWS Keys
    "AKIA[0-9A-Z]{16}"
    "aws[_-]?secret[_-]?access[_-]?key"

    # JWT Secrets
    "jwt[_-]?secret['\"]?\s*[:=]\s*['\"][^'\"]{16,}['\"]"
    "secret[_-]?key['\"]?\s*[:=]\s*['\"][^'\"]{16,}['\"]"

    # GitHub tokens
    "ghp_[a-zA-Z0-9]{36}"
    "gho_[a-zA-Z0-9]{36}"

    # Private keys
    "-----BEGIN (RSA |EC )?PRIVATE KEY-----"
)

# 제외할 파일/디렉토리
EXCLUDE_DIRS=(
    ".git"
    "node_modules"
    "__pycache__"
    ".pytest_cache"
    "venv"
    ".venv"
    "env"
    ".env"
    "build"
    "dist"
)

# 제외 패턴 생성
EXCLUDE_PATTERN=""
for dir in "${EXCLUDE_DIRS[@]}"; do
    EXCLUDE_PATTERN="$EXCLUDE_PATTERN --exclude-dir=$dir"
done

# 스캔 실행
FOUND_SECRETS=0
REPORT_FILE="secret-scan-report.txt"

echo "🔍 Scanning for hardcoded secrets..."
echo "" > "$REPORT_FILE"

for pattern in "${PATTERNS[@]}"; do
    # grep으로 패턴 검색
    RESULTS=$(grep -rn -E "$pattern" $EXCLUDE_PATTERN "$SCAN_DIR" 2>/dev/null || true)

    if [ ! -z "$RESULTS" ]; then
        echo "⚠️  Pattern found: $pattern"
        echo "$RESULTS"
        echo ""

        # 리포트에 저장
        echo "Pattern: $pattern" >> "$REPORT_FILE"
        echo "$RESULTS" >> "$REPORT_FILE"
        echo "" >> "$REPORT_FILE"

        FOUND_SECRETS=$((FOUND_SECRETS + 1))
    fi
done

echo ""
echo "=========================================="
echo "Results"
echo "=========================================="

if [ $FOUND_SECRETS -gt 0 ]; then
    echo "⚠️  Found $FOUND_SECRETS potential secret patterns"
    echo "Review $REPORT_FILE for details"
    echo ""
    echo "⚠️  WARNING: Review all matches carefully!"
    echo "False positives may occur (e.g., comments, examples)"
    exit 1
else
    echo "✓ No hardcoded secrets found"
    rm -f "$REPORT_FILE"
fi

echo ""
echo "=========================================="
echo "Secret Scan Complete"
echo "=========================================="
