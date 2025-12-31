#!/bin/bash

echo "===== RAG Platform Health Check ====="
echo ""

# PostgreSQL
echo "[1/3] PostgreSQL:"
docker exec rag-postgres pg_isready -U raguser > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ PostgreSQL is ready"
else
    echo "❌ PostgreSQL is not ready"
fi

# Milvus
echo ""
echo "[2/3] Milvus:"
curl -s -o /dev/null -w "%{http_code}" http://localhost:9091/healthz | grep -q 200
if [ $? -eq 0 ]; then
    echo "✅ Milvus is ready"
else
    echo "❌ Milvus is not ready"
fi

# Ollama
echo ""
echo "[3/3] Ollama:"
curl -s -o /dev/null -w "%{http_code}" http://localhost:11434/api/tags | grep -q 200
if [ $? -eq 0 ]; then
    echo "✅ Ollama is ready"
else
    echo "❌ Ollama is not ready"
fi

echo ""
echo "===== Health Check Complete ====="
