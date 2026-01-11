# 모니터링 가이드 (Monitoring Guide)

## 목차

1. [로그 관리](#로그-관리)
2. [서비스 모니터링](#서비스-모니터링)
3. [성능 모니터링](#성능-모니터링)
4. [보안 모니터링](#보안-모니터링)
5. [알림 설정](#알림-설정)
6. [대시보드](#대시보드)

---

## 로그 관리

### 1. 백엔드 로그

#### 로그 파일 위치

```bash
backend/
├── logs/
│   ├── app.log          # 일반 로그 (INFO 이상)
│   └── error.log        # 에러 로그 (ERROR 이상)
```

#### 실시간 로그 확인

```bash
# 일반 로그 (실시간)
tail -f backend/logs/app.log

# 에러 로그 (실시간)
tail -f backend/logs/error.log

# 최근 100줄
tail -n 100 backend/logs/app.log

# 특정 시간대
grep "2026-01-11 14:" backend/logs/app.log
```

#### 로그 레벨별 필터링

```bash
# INFO 로그만
grep "INFO" backend/logs/app.log

# WARNING 로그만
grep "WARNING" backend/logs/app.log

# ERROR 로그만
grep "ERROR" backend/logs/app.log

# CRITICAL 로그만
grep "CRITICAL" backend/logs/app.log
```

#### 로그 포맷

**Structured Logging (JSON 형식)**:

```json
{
  "timestamp": "2026-01-11T14:30:45.123456Z",
  "level": "INFO",
  "logger": "app.routers.search",
  "event": "search_query_received",
  "user_id": "user123",
  "query": "How to deploy FastAPI",
  "request_id": "req-abc123"
}
```

**PII 마스킹 적용**:

```json
{
  "timestamp": "2026-01-11T14:30:45.123456Z",
  "level": "INFO",
  "event": "user_login",
  "email": "t***@e***.com",  // 마스킹됨
  "ip_address": "192.***.***.***",  // 마스킹됨
  "request_id": "req-abc123"
}
```

#### 로그 검색

```bash
# 특정 사용자의 로그
grep '"user_id": "user123"' backend/logs/app.log

# 특정 이벤트
grep '"event": "search_query"' backend/logs/app.log

# Request ID로 추적
grep '"request_id": "req-abc123"' backend/logs/app.log

# 에러 메시지 검색
grep -A 10 "ERROR" backend/logs/app.log  # 에러 이후 10줄
```

#### 로그 로테이션

```bash
# 로그 파일 크기 확인
du -h backend/logs/*

# 로그 파일 정리 (7일 이상 된 파일 삭제)
find backend/logs -name "*.log" -mtime +7 -delete

# 압축된 백업 보관
tar -czf logs-backup-$(date +%Y%m%d).tar.gz backend/logs/
mv logs-backup-*.tar.gz backups/
```

**자동 로그 로테이션 설정** (Linux):

```bash
# /etc/logrotate.d/rag-platform

/path/to/backend/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0644 user group
}
```

### 2. Docker 로그

#### 컨테이너 로그 확인

```bash
# 모든 컨테이너 로그
docker-compose logs

# 특정 서비스 로그
docker-compose logs backend
docker-compose logs postgres
docker-compose logs milvus-standalone
docker-compose logs ollama

# 실시간 로그 (팔로우)
docker-compose logs -f backend

# 최근 100줄
docker-compose logs --tail=100 backend

# 특정 시간 이후
docker-compose logs --since 2026-01-11T10:00:00 backend

# 특정 시간 범위
docker-compose logs --since 2026-01-11T10:00:00 --until 2026-01-11T11:00:00 backend
```

#### Docker 로그 설정

```yaml
# docker-compose.yml

services:
  backend:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### 3. PostgreSQL 로그

```bash
# PostgreSQL 로그 확인
docker-compose logs postgres

# 느린 쿼리 로그 활성화
docker exec -it rag-postgres psql -U raguser -c "
  ALTER SYSTEM SET log_min_duration_statement = 1000;  -- 1초 이상
  ALTER SYSTEM SET log_statement = 'all';
"

# 설정 리로드
docker exec -it rag-postgres psql -U raguser -c "SELECT pg_reload_conf();"

# 로그 확인
docker exec -it rag-postgres cat /var/lib/postgresql/data/log/postgresql-*.log
```

### 4. Milvus 로그

```bash
# Milvus 로그
docker-compose logs milvus-standalone

# 특정 에러 검색
docker-compose logs milvus-standalone | grep ERROR

# Attu UI에서 로그 확인
# http://localhost:8080 → System View → Logs
```

---

## 서비스 모니터링

### 1. Health Check

#### 백엔드 Health Check

```bash
# Health Check API
curl http://localhost:8000/health

# 예상 응답:
# {
#   "status": "healthy",
#   "database": "connected",
#   "milvus": "connected",
#   "llm": "available",
#   "timestamp": "2026-01-11T14:30:45.123456Z"
# }
```

**Health Check 스크립트**:

```bash
#!/bin/bash
# scripts/health_check.sh

echo "=== Health Check ==="

# 백엔드
echo -n "Backend: "
if curl -sf http://localhost:8000/health > /dev/null; then
  echo "✓ OK"
else
  echo "✗ FAIL"
fi

# PostgreSQL
echo -n "PostgreSQL: "
if docker exec rag-postgres pg_isready -U raguser > /dev/null 2>&1; then
  echo "✓ OK"
else
  echo "✗ FAIL"
fi

# Milvus
echo -n "Milvus: "
if curl -sf http://localhost:9091/healthz > /dev/null; then
  echo "✓ OK"
else
  echo "✗ FAIL"
fi

# Ollama
echo -n "Ollama: "
if curl -sf http://localhost:11434/api/tags > /dev/null; then
  echo "✓ OK"
else
  echo "✗ FAIL"
fi
```

#### 정기적 Health Check (Cron)

```bash
# crontab -e

# 5분마다 Health Check 실행
*/5 * * * * /path/to/scripts/health_check.sh >> /var/log/health_check.log 2>&1

# 실패 시 알림
*/5 * * * * /path/to/scripts/health_check_with_alert.sh
```

### 2. 서비스 상태 모니터링

```bash
# Docker 컨테이너 상태
docker-compose ps

# 리소스 사용량
docker stats

# 특정 컨테이너만
docker stats rag-backend rag-postgres rag-milvus

# 1회만 출력 (스크립트용)
docker stats --no-stream
```

### 3. 프로세스 모니터링

```bash
# 백엔드 프로세스 확인
ps aux | grep uvicorn

# 프론트엔드 프로세스
ps aux | grep next

# 리소스 사용량 상위 10개
ps aux --sort=-%mem | head -11
ps aux --sort=-%cpu | head -11
```

---

## 성능 모니터링

### 1. 응답 시간 모니터링

#### API 응답 시간 측정

```bash
# 단일 요청
time curl http://localhost:8000/api/v1/search/query \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "test"}'

# 여러 요청 (평균 측정)
for i in {1..10}; do
  time curl -s http://localhost:8000/health > /dev/null
done
```

#### 로그에서 응답 시간 분석

```bash
# 백엔드 로그에서 응답 시간 추출
grep "request_duration" backend/logs/app.log | \
  jq -r '.request_duration' | \
  awk '{sum+=$1; count++} END {print "Average:", sum/count, "ms"}'

# P95, P99 계산
grep "request_duration" backend/logs/app.log | \
  jq -r '.request_duration' | \
  sort -n | \
  awk '{a[NR]=$1} END {
    print "P95:", a[int(NR*0.95)]
    print "P99:", a[int(NR*0.99)]
  }'
```

### 2. 데이터베이스 성능

```bash
# PostgreSQL 활성 쿼리
docker exec -it rag-postgres psql -U raguser -d rag_platform -c "
  SELECT pid, age(clock_timestamp(), query_start), usename, query
  FROM pg_stat_activity
  WHERE query != '<IDLE>' AND query NOT ILIKE '%pg_stat_activity%'
  ORDER BY query_start DESC;
"

# 느린 쿼리 확인
docker exec -it rag-postgres psql -U raguser -d rag_platform -c "
  SELECT query, calls, total_time, mean_time, max_time
  FROM pg_stat_statements
  ORDER BY mean_time DESC
  LIMIT 10;
"

# 데이터베이스 크기
docker exec -it rag-postgres psql -U raguser -d rag_platform -c "
  SELECT pg_size_pretty(pg_database_size('rag_platform'));
"

# 테이블별 크기
docker exec -it rag-postgres psql -U raguser -d rag_platform -c "
  SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
  FROM pg_tables
  WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
  ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
"
```

### 3. Milvus 성능

```bash
# Collection 통계 (Attu UI)
# http://localhost:8080 → Collections → Statistics

# Python으로 확인
python3 << EOF
from app.db.milvus_client import get_milvus_client
from pymilvus import Collection

client = get_milvus_client()
collection = Collection("rag_documents")

print(f"Total entities: {collection.num_entities}")
print(f"Index info: {collection.index().params}")

# 검색 성능 테스트
import time
start = time.time()
results = collection.search(
    data=[[0.1] * 384],
    anns_field="embedding",
    param={"metric_type": "IP", "params": {"nprobe": 10}},
    limit=10,
)
end = time.time()
print(f"Search time: {(end-start)*1000:.2f} ms")
EOF
```

### 4. LLM 성능

```bash
# Ollama 모델별 응답 시간 테스트
time docker exec -it rag-ollama ollama run llama3.2:1b "Hello"

# API 응답 시간
time curl http://localhost:11434/api/generate -d '{
  "model": "llama3.2:1b",
  "prompt": "Hello",
  "stream": false
}'
```

### 5. 시스템 리소스

```bash
# CPU 사용률
top -bn1 | grep "Cpu(s)"

# 메모리 사용량
free -h

# 디스크 사용량
df -h

# 디스크 I/O
iostat -x 1 10

# 네트워크 트래픽
ifstat -i eth0 1 10
```

---

## 보안 모니터링

### 1. 인증 실패 모니터링

```bash
# 로그인 실패 확인
grep '"event": "login_failed"' backend/logs/app.log

# 실패 횟수 집계
grep '"event": "login_failed"' backend/logs/app.log | \
  jq -r '.email' | sort | uniq -c | sort -rn

# 시간대별 실패 횟수
grep '"event": "login_failed"' backend/logs/app.log | \
  jq -r '.timestamp' | cut -d'T' -f1,2 | cut -d':' -f1 | \
  sort | uniq -c
```

### 2. 비정상 접근 탐지

```bash
# 비정상적으로 많은 요청 (DoS 의심)
grep '"event": "request"' backend/logs/app.log | \
  jq -r '.ip_address' | sort | uniq -c | sort -rn | head -10

# 403 Forbidden 응답
grep '"status_code": 403' backend/logs/app.log

# 401 Unauthorized 응답
grep '"status_code": 401' backend/logs/app.log
```

### 3. 보안 스캔 로그

```bash
# Bandit 보안 스캔
cd backend
bandit -r app/ -f json -o security-scan.json

# 심각도별 집계
cat security-scan.json | jq '.results[] | .issue_severity' | sort | uniq -c

# Safety 의존성 취약점 스캔
safety check --json > safety-report.json

# 취약점 개수
cat safety-report.json | jq '.vulnerabilities | length'
```

### 4. 시크릿 노출 감지

```bash
# Git 히스토리에서 시크릿 검색
git log -p | grep -E "(API_KEY|SECRET|PASSWORD|TOKEN)" --color=always

# 파일에서 하드코딩된 시크릿 검색
grep -r -E "(sk-[a-zA-Z0-9]{48}|ghp_[a-zA-Z0-9]{36})" . --exclude-dir={node_modules,venv,.git}

# detect-secrets 도구 사용
pip install detect-secrets
detect-secrets scan --baseline .secrets.baseline
```

---

## 알림 설정

### 1. Slack 알림

```bash
# Slack Webhook으로 알림 전송
SLACK_WEBHOOK="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

# 에러 발생 시 알림
tail -f backend/logs/app.log | grep "ERROR" | while read line; do
  curl -X POST $SLACK_WEBHOOK \
    -H 'Content-Type: application/json' \
    -d "{\"text\": \"🚨 Backend Error: $line\"}"
done
```

### 2. 이메일 알림

```bash
# mailutils 설치 (Ubuntu)
sudo apt-get install mailutils

# 에러 발생 시 이메일
tail -f backend/logs/app.log | grep "ERROR" | while read line; do
  echo "$line" | mail -s "RAG Platform Error" admin@example.com
done
```

### 3. PagerDuty 알림

```python
# scripts/alert_pagerduty.py

import requests

def send_pagerduty_alert(message, severity="error"):
    url = "https://events.pagerduty.com/v2/enqueue"
    payload = {
        "routing_key": "YOUR_ROUTING_KEY",
        "event_action": "trigger",
        "payload": {
            "summary": message,
            "severity": severity,
            "source": "rag-platform",
        }
    }
    requests.post(url, json=payload)

# 사용
send_pagerduty_alert("Database connection failed", "critical")
```

### 4. 모니터링 스크립트

```bash
#!/bin/bash
# scripts/monitor_and_alert.sh

# Health Check 실패 시 알림
if ! curl -sf http://localhost:8000/health > /dev/null; then
  curl -X POST $SLACK_WEBHOOK \
    -H 'Content-Type: application/json' \
    -d '{"text": "🚨 Backend Health Check Failed!"}'
fi

# 디스크 사용량 80% 이상 시 알림
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
  curl -X POST $SLACK_WEBHOOK \
    -H 'Content-Type: application/json' \
    -d "{\"text\": \"⚠️ Disk usage: ${DISK_USAGE}%\"}"
fi

# 메모리 사용량 80% 이상 시 알림
MEM_USAGE=$(free | awk 'NR==2 {printf "%.0f", $3/$2*100}')
if [ $MEM_USAGE -gt 80 ]; then
  curl -X POST $SLACK_WEBHOOK \
    -H 'Content-Type: application/json' \
    -d "{\"text\": \"⚠️ Memory usage: ${MEM_USAGE}%\"}"
fi
```

---

## 대시보드

### 1. Grafana + Prometheus (선택)

#### Prometheus 설정

```yaml
# docker-compose.yml에 추가

services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3001:3000"
    volumes:
      - grafana-data:/var/lib/grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin

volumes:
  prometheus-data:
  grafana-data:
```

#### Prometheus 설정 파일

```yaml
# monitoring/prometheus.yml

global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'backend'
    static_configs:
      - targets: ['backend:8000']

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres:5432']
```

#### Grafana 대시보드

```
1. Grafana 접속: http://localhost:3001
2. 로그인: admin / admin
3. Data Source 추가: Prometheus (http://prometheus:9090)
4. Dashboard Import: Node Exporter, PostgreSQL Dashboard
```

### 2. 간단한 웹 대시보드

```python
# scripts/dashboard.py

from flask import Flask, jsonify
import psutil
import requests

app = Flask(__name__)

@app.route('/status')
def status():
    # 시스템 리소스
    cpu = psutil.cpu_percent()
    memory = psutil.virtual_memory().percent
    disk = psutil.disk_usage('/').percent

    # 서비스 상태
    try:
        backend = requests.get('http://localhost:8000/health', timeout=5).ok
    except:
        backend = False

    return jsonify({
        'system': {
            'cpu': cpu,
            'memory': memory,
            'disk': disk,
        },
        'services': {
            'backend': backend,
        },
    })

if __name__ == '__main__':
    app.run(port=5000)
```

---

## 모니터링 체크리스트

### 일일 체크

- [ ] 모든 Docker 컨테이너 실행 중인지 확인
- [ ] 백엔드 Health Check API 응답 확인
- [ ] 에러 로그 확인 (backend/logs/error.log)
- [ ] 디스크 사용량 확인 (80% 이하 유지)

### 주간 체크

- [ ] 로그 파일 크기 확인 및 정리
- [ ] 데이터베이스 백업 확인
- [ ] 성능 지표 확인 (응답 시간, 처리량)
- [ ] 보안 스캔 실행 (Bandit, Safety)

### 월간 체크

- [ ] 시스템 업데이트 확인
- [ ] Docker 이미지 업데이트 확인
- [ ] Python/Node.js 의존성 업데이트 확인
- [ ] 로그 백업 및 아카이빙
- [ ] 용량 계획 검토

---

## 관련 문서

- [Deployment Guide](./deployment-guide.md) - 배포 가이드
- [Troubleshooting Guide](./troubleshooting.md) - 문제 해결 가이드
- [Backup & Restore](./backup-restore.md) - 백업 및 복원 절차

---

**모니터링은 문제를 예방하는 최선의 방법입니다!** 📊
