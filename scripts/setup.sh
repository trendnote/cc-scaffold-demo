#!/bin/bash

set -e

echo "===== RAG Platform Setup ====="
echo ""

# 1. .env 파일 확인
if [ ! -f .env ]; then
    echo "[1/5] Creating .env file from .env.example..."
    cp .env.example .env
    echo "⚠️  Please edit .env file and change all CHANGE_ME_* values!"
    echo "    Run: vi .env"
    exit 1
else
    echo "[1/5] ✅ .env file exists"
fi

# 2. Docker 확인
echo "[2/5] Checking Docker..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi
echo "✅ Docker is installed: $(docker --version)"

# 3. Docker Compose 확인
echo "[3/5] Checking Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed."
    exit 1
fi
echo "✅ Docker Compose is installed: $(docker-compose --version)"

# 4. 포트 충돌 확인
echo "[4/5] Checking port conflicts..."
PORTS=(5432 19530 8080 11434)
CONFLICT=0
for PORT in "${PORTS[@]}"; do
    if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "⚠️  Port $PORT is already in use"
        CONFLICT=1
    fi
done

if [ $CONFLICT -eq 1 ]; then
    echo "❌ Port conflict detected. Please stop conflicting services."
    exit 1
fi
echo "✅ No port conflicts"

# 5. Docker Compose 실행
echo "[5/5] Starting Docker Compose..."
docker-compose up -d

echo ""
echo "===== Setup Complete ====="
echo ""
echo "Services:"
echo "  - PostgreSQL: localhost:5432"
echo "  - Milvus: localhost:19530"
echo "  - Attu: http://localhost:8080"
echo "  - Ollama: localhost:11434"
echo ""
echo "Run health check: ./scripts/health-check.sh"
