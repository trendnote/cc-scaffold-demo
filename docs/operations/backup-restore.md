# 백업 및 복원 가이드 (Backup & Restore Guide)

## 목차

1. [백업 전략](#백업-전략)
2. [PostgreSQL 백업](#postgresql-백업)
3. [Milvus 백업](#milvus-백업)
4. [파일 시스템 백업](#파일-시스템-백업)
5. [복원 절차](#복원-절차)
6. [재해 복구](#재해-복구)

---

## 백업 전략

### 1. 백업 정책

#### 백업 유형

| 유형 | 주기 | 보관 기간 | 우선순위 |
|------|------|-----------|----------|
| **Full Backup** | 매일 | 30일 | 높음 |
| **Incremental** | 6시간마다 | 7일 | 중간 |
| **Point-in-Time** | 실시간 (WAL) | 7일 | 높음 |

#### 백업 대상

1. **PostgreSQL 데이터베이스**
   - 사용자 정보
   - 문서 메타데이터
   - 검색 히스토리
   - 인증 정보

2. **Milvus 벡터 데이터**
   - 문서 임베딩
   - Collection 메타데이터
   - 인덱스 정보

3. **파일 시스템**
   - 로그 파일
   - 설정 파일 (.env)
   - 업로드된 문서 (있는 경우)

#### 백업 저장소

```bash
backups/
├── postgres/
│   ├── daily/
│   │   ├── backup-20260111.sql.gz
│   │   ├── backup-20260112.sql.gz
│   │   └── ...
│   └── incremental/
│       ├── backup-20260111-00.sql.gz
│       ├── backup-20260111-06.sql.gz
│       └── ...
├── milvus/
│   ├── backup-20260111.tar.gz
│   ├── backup-20260112.tar.gz
│   └── ...
├── logs/
│   ├── logs-20260111.tar.gz
│   └── ...
└── config/
    ├── .env.backup
    ├── docker-compose.yml.backup
    └── ...
```

### 2. 자동 백업 스케줄

```bash
# crontab -e

# PostgreSQL Full Backup (매일 02:00)
0 2 * * * /path/to/scripts/backup_postgres_full.sh

# PostgreSQL Incremental (6시간마다)
0 */6 * * * /path/to/scripts/backup_postgres_incremental.sh

# Milvus Backup (매일 03:00)
0 3 * * * /path/to/scripts/backup_milvus.sh

# 로그 백업 (매주 일요일 04:00)
0 4 * * 0 /path/to/scripts/backup_logs.sh

# 설정 파일 백업 (매일 01:00)
0 1 * * * /path/to/scripts/backup_config.sh

# 오래된 백업 삭제 (매일 05:00)
0 5 * * * /path/to/scripts/cleanup_old_backups.sh
```

---

## PostgreSQL 백업

### 1. Full Backup (전체 백업)

#### 수동 백업

```bash
#!/bin/bash
# scripts/backup_postgres_full.sh

set -e

BACKUP_DIR="backups/postgres/daily"
TIMESTAMP=$(date +%Y%m%d)
BACKUP_FILE="${BACKUP_DIR}/backup-${TIMESTAMP}.sql"

# 백업 디렉토리 생성
mkdir -p $BACKUP_DIR

# PostgreSQL 덤프
echo "Starting PostgreSQL full backup..."
docker exec rag-postgres pg_dump -U raguser -d rag_platform > $BACKUP_FILE

# 압축
echo "Compressing backup..."
gzip -f $BACKUP_FILE

# 백업 확인
if [ -f "${BACKUP_FILE}.gz" ]; then
  SIZE=$(du -h "${BACKUP_FILE}.gz" | cut -f1)
  echo "✓ Backup completed: ${BACKUP_FILE}.gz (${SIZE})"
else
  echo "✗ Backup failed"
  exit 1
fi

# S3 업로드 (선택)
# aws s3 cp "${BACKUP_FILE}.gz" s3://your-bucket/backups/postgres/
```

#### 실행

```bash
# 권한 부여
chmod +x scripts/backup_postgres_full.sh

# 실행
./scripts/backup_postgres_full.sh
```

### 2. Custom Format Backup (권장)

```bash
#!/bin/bash
# scripts/backup_postgres_custom.sh

set -e

BACKUP_DIR="backups/postgres/daily"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/backup-${TIMESTAMP}.dump"

mkdir -p $BACKUP_DIR

# Custom format으로 백업 (병렬 처리 가능, 압축 자동)
echo "Starting PostgreSQL custom format backup..."
docker exec rag-postgres pg_dump \
  -U raguser \
  -d rag_platform \
  -F custom \
  -f /tmp/backup.dump

# 백업 파일 복사
docker cp rag-postgres:/tmp/backup.dump $BACKUP_FILE

# 백업 확인
if [ -f "$BACKUP_FILE" ]; then
  SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
  echo "✓ Backup completed: ${BACKUP_FILE} (${SIZE})"
else
  echo "✗ Backup failed"
  exit 1
fi
```

### 3. Incremental Backup (증분 백업)

#### WAL (Write-Ahead Logging) 설정

```bash
# PostgreSQL 설정 수정
docker exec -it rag-postgres psql -U raguser -c "
  ALTER SYSTEM SET wal_level = 'replica';
  ALTER SYSTEM SET archive_mode = 'on';
  ALTER SYSTEM SET archive_command = 'test ! -f /backups/wal/%f && cp %p /backups/wal/%f';
"

# PostgreSQL 재시작
docker-compose restart postgres
```

#### WAL 백업

```bash
#!/bin/bash
# scripts/backup_postgres_incremental.sh

set -e

BACKUP_DIR="backups/postgres/incremental"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)

mkdir -p $BACKUP_DIR

# Base Backup (첫 실행 시)
if [ ! -f "$BACKUP_DIR/base.tar.gz" ]; then
  echo "Creating base backup..."
  docker exec rag-postgres pg_basebackup \
    -U raguser \
    -D /tmp/basebackup \
    -F tar \
    -z \
    -P

  docker cp rag-postgres:/tmp/basebackup/base.tar.gz $BACKUP_DIR/
fi

# WAL 아카이브 백업
echo "Backing up WAL archives..."
docker cp rag-postgres:/backups/wal $BACKUP_DIR/wal-${TIMESTAMP}

echo "✓ Incremental backup completed"
```

### 4. 스키마만 백업

```bash
# 스키마만 백업 (데이터 제외)
docker exec rag-postgres pg_dump \
  -U raguser \
  -d rag_platform \
  --schema-only \
  > backups/postgres/schema-$(date +%Y%m%d).sql

# 데이터만 백업 (스키마 제외)
docker exec rag-postgres pg_dump \
  -U raguser \
  -d rag_platform \
  --data-only \
  > backups/postgres/data-$(date +%Y%m%d).sql
```

### 5. 특정 테이블만 백업

```bash
# 단일 테이블 백업
docker exec rag-postgres pg_dump \
  -U raguser \
  -d rag_platform \
  -t users \
  > backups/postgres/users-$(date +%Y%m%d).sql

# 여러 테이블 백업
docker exec rag-postgres pg_dump \
  -U raguser \
  -d rag_platform \
  -t users \
  -t documents \
  -t search_history \
  > backups/postgres/tables-$(date +%Y%m%d).sql
```

---

## Milvus 백업

### 1. 볼륨 백업 (권장)

```bash
#!/bin/bash
# scripts/backup_milvus.sh

set -e

BACKUP_DIR="backups/milvus"
TIMESTAMP=$(date +%Y%m%d)
BACKUP_FILE="${BACKUP_DIR}/backup-${TIMESTAMP}.tar.gz"

mkdir -p $BACKUP_DIR

# Milvus 컨테이너 중지
echo "Stopping Milvus..."
docker-compose stop milvus-standalone

# 볼륨 백업
echo "Backing up Milvus volumes..."
docker run --rm \
  -v rag-platform_milvus-data:/data \
  -v $(pwd)/$BACKUP_DIR:/backup \
  alpine \
  tar czf /backup/backup-${TIMESTAMP}.tar.gz -C /data .

# Milvus 재시작
echo "Restarting Milvus..."
docker-compose start milvus-standalone

# 백업 확인
if [ -f "$BACKUP_FILE" ]; then
  SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
  echo "✓ Milvus backup completed: ${BACKUP_FILE} (${SIZE})"
else
  echo "✗ Backup failed"
  exit 1
fi
```

### 2. Milvus Backup 유틸리티 사용

```bash
# Milvus Backup 도구 설치
# https://github.com/zilliztech/milvus-backup

# 백업 생성
milvus-backup create \
  --milvus-address=localhost:19530 \
  --backup-name=backup-$(date +%Y%m%d)

# 백업 리스트 확인
milvus-backup list

# 백업 정보 확인
milvus-backup get --backup-name=backup-20260111
```

### 3. Collection별 백업

```python
# scripts/backup_milvus_collection.py

from pymilvus import connections, Collection, utility
import json

# Milvus 연결
connections.connect(host="localhost", port="19530")

# Collection 백업
collection_name = "rag_documents"
collection = Collection(collection_name)

# Collection 정보 저장
backup_info = {
    "name": collection_name,
    "schema": collection.schema.to_dict(),
    "num_entities": collection.num_entities,
    "indexes": [index.params for index in collection.indexes],
}

with open(f"backups/milvus/{collection_name}-info.json", "w") as f:
    json.dump(backup_info, f, indent=2)

print(f"✓ Collection info backed up: {collection_name}")

# 데이터 백업 (작은 Collection만)
# 큰 Collection은 볼륨 백업 사용
if collection.num_entities < 100000:
    results = collection.query(expr="", output_fields=["*"])
    with open(f"backups/milvus/{collection_name}-data.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"✓ Collection data backed up: {collection.num_entities} entities")
```

---

## 파일 시스템 백업

### 1. 로그 백업

```bash
#!/bin/bash
# scripts/backup_logs.sh

set -e

BACKUP_DIR="backups/logs"
TIMESTAMP=$(date +%Y%m%d)
BACKUP_FILE="${BACKUP_DIR}/logs-${TIMESTAMP}.tar.gz"

mkdir -p $BACKUP_DIR

# 로그 압축
echo "Backing up logs..."
tar czf $BACKUP_FILE \
  backend/logs/ \
  logs/

# 백업 확인
if [ -f "$BACKUP_FILE" ]; then
  SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
  echo "✓ Logs backup completed: ${BACKUP_FILE} (${SIZE})"
else
  echo "✗ Backup failed"
  exit 1
fi
```

### 2. 설정 파일 백업

```bash
#!/bin/bash
# scripts/backup_config.sh

set -e

BACKUP_DIR="backups/config"
TIMESTAMP=$(date +%Y%m%d)

mkdir -p $BACKUP_DIR

# .env 백업 (시크릿 포함 주의!)
echo "Backing up configuration files..."
cp .env "${BACKUP_DIR}/.env.${TIMESTAMP}"

# docker-compose.yml 백업
cp docker-compose.yml "${BACKUP_DIR}/docker-compose.yml.${TIMESTAMP}"

# 백엔드 설정
cp backend/alembic.ini "${BACKUP_DIR}/alembic.ini.${TIMESTAMP}"

# 프론트엔드 설정
cp frontend/.env.local "${BACKUP_DIR}/frontend.env.${TIMESTAMP}" 2>/dev/null || true

echo "✓ Configuration backup completed"

# 설정 파일은 암호화 권장
# gpg --symmetric --cipher-algo AES256 "${BACKUP_DIR}/.env.${TIMESTAMP}"
```

### 3. 전체 프로젝트 백업

```bash
#!/bin/bash
# scripts/backup_full_project.sh

set -e

BACKUP_DIR="backups/full"
TIMESTAMP=$(date +%Y%m%d)
BACKUP_FILE="${BACKUP_DIR}/project-${TIMESTAMP}.tar.gz"

mkdir -p $BACKUP_DIR

echo "Creating full project backup..."
tar czf $BACKUP_FILE \
  --exclude=node_modules \
  --exclude=venv \
  --exclude=.venv \
  --exclude=__pycache__ \
  --exclude=.next \
  --exclude=dist \
  --exclude=build \
  --exclude=.git \
  .

# 백업 확인
if [ -f "$BACKUP_FILE" ]; then
  SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
  echo "✓ Full project backup completed: ${BACKUP_FILE} (${SIZE})"
else
  echo "✗ Backup failed"
  exit 1
fi
```

---

## 복원 절차

### 1. PostgreSQL 복원

#### SQL 파일에서 복원

```bash
# 1. 백업 파일 압축 해제
gunzip backups/postgres/daily/backup-20260111.sql.gz

# 2. 데이터베이스 삭제 및 재생성 (주의!)
docker exec -it rag-postgres psql -U raguser -c "
  DROP DATABASE IF EXISTS rag_platform;
  CREATE DATABASE rag_platform;
"

# 3. 복원
cat backups/postgres/daily/backup-20260111.sql | \
  docker exec -i rag-postgres psql -U raguser -d rag_platform

# 4. 복원 확인
docker exec -it rag-postgres psql -U raguser -d rag_platform -c "
  SELECT count(*) FROM users;
  SELECT count(*) FROM documents;
"
```

#### Custom Format에서 복원

```bash
# 1. 백업 파일을 컨테이너로 복사
docker cp backups/postgres/daily/backup-20260111.dump rag-postgres:/tmp/

# 2. 데이터베이스 재생성
docker exec -it rag-postgres psql -U raguser -c "
  DROP DATABASE IF EXISTS rag_platform;
  CREATE DATABASE rag_platform;
"

# 3. 복원 (병렬 처리)
docker exec -it rag-postgres pg_restore \
  -U raguser \
  -d rag_platform \
  -j 4 \
  /tmp/backup-20260111.dump

# 4. 복원 확인
docker exec -it rag-postgres psql -U raguser -d rag_platform -c "\dt"
```

#### Point-in-Time Recovery (PITR)

```bash
# 1. Base Backup 복원
docker exec -it rag-postgres pg_basebackup \
  -U raguser \
  -D /var/lib/postgresql/data \
  -F tar

# 2. WAL 아카이브 복사
docker cp backups/postgres/incremental/wal-20260111/ rag-postgres:/var/lib/postgresql/wal_archive/

# 3. recovery.conf 생성
docker exec -it rag-postgres bash -c "cat > /var/lib/postgresql/data/recovery.conf <<EOF
restore_command = 'cp /var/lib/postgresql/wal_archive/%f %p'
recovery_target_time = '2026-01-11 14:00:00'
EOF"

# 4. PostgreSQL 재시작
docker-compose restart postgres
```

### 2. Milvus 복원

#### 볼륨 복원

```bash
#!/bin/bash
# scripts/restore_milvus.sh

set -e

BACKUP_FILE="backups/milvus/backup-20260111.tar.gz"

if [ ! -f "$BACKUP_FILE" ]; then
  echo "✗ Backup file not found: $BACKUP_FILE"
  exit 1
fi

# 1. Milvus 중지
echo "Stopping Milvus..."
docker-compose stop milvus-standalone

# 2. 기존 볼륨 삭제 (주의!)
echo "Removing old volume..."
docker volume rm rag-platform_milvus-data

# 3. 새 볼륨 생성
docker volume create rag-platform_milvus-data

# 4. 백업 복원
echo "Restoring backup..."
docker run --rm \
  -v rag-platform_milvus-data:/data \
  -v $(pwd)/backups/milvus:/backup \
  alpine \
  tar xzf /backup/backup-20260111.tar.gz -C /data

# 5. Milvus 재시작
echo "Restarting Milvus..."
docker-compose start milvus-standalone

# 6. 복원 확인
sleep 10
curl http://localhost:9091/healthz

echo "✓ Milvus restore completed"
```

#### Milvus Backup 유틸리티로 복원

```bash
# 백업 리스트 확인
milvus-backup list

# 복원
milvus-backup restore \
  --milvus-address=localhost:19530 \
  --backup-name=backup-20260111

# Collection 확인
milvus-backup get --backup-name=backup-20260111
```

### 3. 설정 파일 복원

```bash
# .env 복원
cp backups/config/.env.20260111 .env

# docker-compose.yml 복원
cp backups/config/docker-compose.yml.20260111 docker-compose.yml

# 복원 확인
cat .env | grep -v PASSWORD | grep -v SECRET
```

---

## 재해 복구

### 1. 전체 시스템 복구 절차

```bash
#!/bin/bash
# scripts/disaster_recovery.sh

set -e

echo "=== Disaster Recovery ==="
echo ""

# 1. 인프라 시작
echo "1. Starting infrastructure..."
docker-compose up -d
sleep 30

# 2. PostgreSQL 복원
echo "2. Restoring PostgreSQL..."
./scripts/restore_postgres.sh backups/postgres/daily/backup-20260111.sql.gz

# 3. Milvus 복원
echo "3. Restoring Milvus..."
./scripts/restore_milvus.sh backups/milvus/backup-20260111.tar.gz

# 4. 설정 파일 복원
echo "4. Restoring configuration..."
cp backups/config/.env.20260111 .env
cp backups/config/docker-compose.yml.20260111 docker-compose.yml

# 5. 서비스 재시작
echo "5. Restarting services..."
docker-compose restart

# 6. Health Check
echo "6. Running health checks..."
sleep 10
./scripts/health_check.sh

echo ""
echo "=== Recovery Completed ==="
```

### 2. 복구 시간 목표 (RTO/RPO)

| 항목 | 목표 | 설명 |
|------|------|------|
| **RTO** | 2시간 | Recovery Time Objective (복구 시간) |
| **RPO** | 6시간 | Recovery Point Objective (데이터 손실 허용) |

**복구 우선순위**:

1. **Critical (30분)**:
   - PostgreSQL 복원
   - 인증 시스템 복원

2. **High (1시간)**:
   - Milvus 복원
   - 검색 기능 복원

3. **Medium (2시간)**:
   - 프론트엔드 복원
   - 로그 복원

---

## 백업 검증

### 1. 백업 무결성 확인

```bash
#!/bin/bash
# scripts/verify_backup.sh

BACKUP_FILE="backups/postgres/daily/backup-20260111.sql.gz"

echo "Verifying backup: $BACKUP_FILE"

# 1. 파일 존재 확인
if [ ! -f "$BACKUP_FILE" ]; then
  echo "✗ Backup file not found"
  exit 1
fi

# 2. 압축 파일 무결성 확인
if gzip -t "$BACKUP_FILE"; then
  echo "✓ Compression OK"
else
  echo "✗ Compression corrupted"
  exit 1
fi

# 3. SQL 파일 구문 확인
gunzip -c "$BACKUP_FILE" | head -100 | grep -q "CREATE TABLE"
if [ $? -eq 0 ]; then
  echo "✓ SQL syntax OK"
else
  echo "✗ SQL syntax error"
  exit 1
fi

echo "✓ Backup verification passed"
```

### 2. 복원 테스트 (권장)

```bash
#!/bin/bash
# scripts/test_restore.sh

set -e

echo "=== Backup Restore Test ==="

# 1. 테스트 데이터베이스 생성
docker exec -it rag-postgres psql -U raguser -c "
  DROP DATABASE IF EXISTS rag_platform_test;
  CREATE DATABASE rag_platform_test;
"

# 2. 백업 복원
gunzip -c backups/postgres/daily/backup-20260111.sql.gz | \
  docker exec -i rag-postgres psql -U raguser -d rag_platform_test

# 3. 데이터 확인
USERS_COUNT=$(docker exec -it rag-postgres psql -U raguser -d rag_platform_test -t -c "SELECT count(*) FROM users;")

echo "Users count: $USERS_COUNT"

if [ $USERS_COUNT -gt 0 ]; then
  echo "✓ Restore test passed"
else
  echo "✗ Restore test failed"
  exit 1
fi

# 4. 테스트 데이터베이스 삭제
docker exec -it rag-postgres psql -U raguser -c "DROP DATABASE rag_platform_test;"
```

---

## 백업 클린업

### 1. 오래된 백업 삭제

```bash
#!/bin/bash
# scripts/cleanup_old_backups.sh

set -e

echo "Cleaning up old backups..."

# 30일 이상 된 PostgreSQL 백업 삭제
find backups/postgres/daily -name "*.sql.gz" -mtime +30 -delete

# 7일 이상 된 Incremental 백업 삭제
find backups/postgres/incremental -mtime +7 -delete

# 30일 이상 된 Milvus 백업 삭제
find backups/milvus -name "*.tar.gz" -mtime +30 -delete

# 90일 이상 된 로그 백업 삭제
find backups/logs -name "*.tar.gz" -mtime +90 -delete

echo "✓ Cleanup completed"

# 디스크 공간 확인
df -h backups/
```

### 2. 백업 크기 모니터링

```bash
# 백업 디렉토리 크기
du -sh backups/

# 항목별 크기
du -sh backups/*/

# 큰 파일 찾기 (1GB 이상)
find backups/ -size +1G -exec ls -lh {} \;
```

---

## 체크리스트

### 백업 전

- [ ] 백업 스토리지 용량 확인 (최소 50GB 여유)
- [ ] 백업 스크립트 권한 확인 (chmod +x)
- [ ] Cron 스케줄 설정 확인
- [ ] 알림 설정 (백업 성공/실패)

### 백업 후

- [ ] 백업 파일 생성 확인
- [ ] 백업 파일 크기 확인
- [ ] 백업 무결성 검증
- [ ] 원격 스토리지 업로드 (S3 등)
- [ ] 복원 테스트 (월 1회)

### 복원 전

- [ ] 백업 파일 확인
- [ ] 복원 계획 수립
- [ ] 현재 상태 백업 (롤백용)
- [ ] 관련자 통지

### 복원 후

- [ ] 데이터 무결성 확인
- [ ] 서비스 Health Check
- [ ] 로그 확인
- [ ] 사용자 테스트

---

## 관련 문서

- [Deployment Guide](./deployment-guide.md) - 배포 가이드
- [Troubleshooting Guide](./troubleshooting.md) - 문제 해결 가이드
- [Monitoring Guide](./monitoring.md) - 모니터링 및 로그 확인

---

**백업은 보험입니다. 필요할 때 없으면 후회합니다!** 💾
