# Task Plan

개별 Task의 구체적인 실행 계획을 작성합니다.

## Usage

```
/task-plan [task-id]
```

Examples:
```
/task-plan 1.1
/task-plan 2.3
/task-plan 3.5
```

## What This Command Does

1. **Task 정보 읽기** - Task Breakdown에서 추출
2. **조사 및 설계** - 기술 조사, 설계 결정
3. **구현 단계 분해** - 30분-1시간 Step으로
4. **테스트 계획** - 구체적 케이스 나열
5. **리스크 식별** - 예상 어려움 및 대응
6. **실행 계획 문서** - `docs/task-plans/task-[ID]-plan.md`

## Instructions for Claude

### Step 1: Task Breakdown 읽기

```bash
TASK_ID="$1"

# Task Breakdown 파일 찾기
# 여러 패턴 시도: *tasks.md, *task-breakdown.md, *breakdown.md
TASK_BREAKDOWN_FILE=""

if [ -d "docs/tasks" ]; then
  # 패턴 우선순위:
  # 1. phase-X-tasks.md (권장 패턴)
  # 2. task-breakdown.md (사용자 업로드)
  # 3. 기타 *tasks.md, *breakdown.md
  TASK_BREAKDOWN_FILE=$(find docs/tasks -type f \( \
    -name "phase-*-tasks.md" -o \
    -name "task-breakdown.md" -o \
    -name "*breakdown.md" -o \
    -name "*tasks.md" \
  \) | head -1)
fi

if [ -z "$TASK_BREAKDOWN_FILE" ] || [ ! -f "$TASK_BREAKDOWN_FILE" ]; then
  echo "❌ Task Breakdown 파일을 찾을 수 없습니다"
  echo ""
  echo "다음 위치를 확인하세요:"
  echo "  - docs/tasks/phase-*-tasks.md"
  echo "  - docs/tasks/task-breakdown.md"
  echo "  - docs/tasks/*breakdown.md"
  echo ""
  echo "또는 먼저 /task-breakdown 명령어로 Task를 분해하세요"
  exit 1
fi

# 특정 Task 섹션 추출
echo "📖 Task $TASK_ID 정보 읽는 중..."
echo "📁 파일: $TASK_BREAKDOWN_FILE"
echo ""

# Task ID 패턴 여러 형식 지원:
# - Task 1.1:
# - **Task 1.1**:
# - Task 1.1 -
# - #### Task 1.1
grep -E -A 50 "(Task ${TASK_ID}[:\-]|Task ${TASK_ID}\*\*|#### .*Task ${TASK_ID})" "$TASK_BREAKDOWN_FILE"
```

### Step 2: task-planner Skill 활성화

task-planner 스킬의 프로세스 따름:
1. Task 정보 확인 및 사용자 동의
2. 조사 및 설계 (필요 시)
3. 구현 단계 분해 (30분-1h Step)
4. 테스트 계획 (구체적 케이스)
5. 리스크 식별
6. 문서 생성

### Step 3: 문서 생성

```bash
mkdir -p docs/task-plans

OUTPUT_FILE="docs/task-plans/task-${TASK_ID}-plan.md"

cat > "$OUTPUT_FILE" << 'EOFPLAN'
# Task Execution Plan: [ID] - [Name]

[템플릿 기반으로 채우기]

## 1. Task Overview
[Task Breakdown에서 가져온 정보]

## 2. Research & Design
[조사 결과]
[설계 결정]

## 3. Implementation Steps

### Step 1: [Name] (Xh)
[상세 작업]

### Step 2: [Name] (Xh)
[상세 작업]

[... 모든 Step ...]

## 4. Testing Plan
[5개 테스트 케이스]

## 5. Risks & Mitigation
[2-3개 리스크]

## 6. Definition of Done
[체크리스트]

EOFPLAN

echo "✅ 실행 계획 생성: $OUTPUT_FILE"
```

### Step 4: 품질 체크

```
✅ 품질 검증:
- [ ] Step 크기 적절 (30분-1h)
- [ ] 시간 배분 합리적
  - 조사: 15-20%
  - 구현: 60-70%
  - 테스트: 15-20%
- [ ] 테스트 케이스 구체적
- [ ] 리스크 파악됨
- [ ] Definition of Done 명확

⚠️ 경고:
- 총 시간이 Task Breakdown과 50% 이상 차이
  → 재검토 필요
- Step이 2시간 초과
  → 더 작게 분해 권장
```

### Step 5: 최종 요약

"🎉 실행 계획 완료!

📁 docs/task-plans/task-[ID]-plan.md

## 계획 요약

**Task**: [ID] - [Name]
**Original Estimate**: [6h from Task Breakdown]
**Planned Time**: [6h]

**Implementation Steps** ([N] Steps):
1. [Step 1 Name] ([Xh])
2. [Step 2 Name] ([Xh])
3. [Step 3 Name] ([Xh])
...

**Time Breakdown**:
```
Research: [1h] (17%)
Implementation: [4h] (67%)
Testing: [1h] (17%)
```

**Testing**: [5] test cases
**Risks**: [2] identified (with mitigation)

**Coverage**:
- ✅ All Acceptance Criteria addressedTask: [ID] - [Name]
**Original Estimate**: [6h]
**Revised Estimate**: [6.5h]
**Variance**: +0.5h (조사 시간 추가)

**구현 단계** ([N] Steps):
- Step 1: [Name] ([X]h)
- Step 2: [Name] ([X]h)
- Step 3: [Name] ([X]h)
...

**시간 배분**:
- Research/Design: [%]
- Implementation: [%]
- Testing: [%]

**테스트 계획**:
- Unit Tests: [N]개
- Integration Tests: [N]개 (if any)
- Coverage Target: >80%

**리스크** ([N]개):
- High Priority: [N]
- Medium Priority: [N]
- All have mitigation plans

## 품질 체크

✅ Step 크기 적절 (0.5-2h)
✅ 시간 추정 합리적
✅ 테스트 계획 충분
✅ 리스크 파악됨
✅ Definition of Done 명확

## 다음 단계

1. ✅ Peer 리뷰 요청
   - [팀원]에게 공유
   - 피드백 수렴 (15분)

2. ✅ Lead 승인
   - Tech Lead 검토
   - 승인 받기

3. ✅ 구현 시작
   - Step 1부터 순차 진행
   - 진행 상황 기록

Peer 리뷰를 요청할까요?"
```

## Best Practices

### DO:
- ✅ Task 착수 직전 작성 (당일 아침)
- ✅ 30분 이내 작성
- ✅ Peer 리뷰 받기
- ✅ 테스트 케이스 구체적으로
- ✅ 리스크 솔직하게

### DON'T:
- ❌ 완벽한 계획 추구
- ❌ 2시간+ 소요 (Analysis Paralysis)
- ❌ 너무 상세 (10분 단위)
- ❌ 혼자 결정 (피드백 없이)
- ❌ 계획 무시하고 구현

## Example Usage

```
사용자: /task-plan 1.1

Claude: 📖 Task 1.1 읽는 중...

"Task 1.1: 프로젝트 초기 구조 및 Docker Compose 설정

**Task 정보:**
- ID: 1.1
- Estimate: 4h
- Description: Docker Compose 환경 구축

**Acceptance Criteria:**
- [ ] docker-compose up -d 성공
- [ ] 모든 컨테이너 running
- [ ] PostgreSQL 연결 확인
- [ ] Attu UI 접속 (http://localhost:8080)

이 Task의 실행 계획을 작성할까요?"

사용자: "네"

Claude: "조사가 필요한 부분이 있습니다.

**조사 항목:**
1. Milvus Docker 이미지 버전
2. etcd + MinIO 설정 요구사항
3. 네트워크 설정

10분 조사를 진행할까요?"

사용자: "네"

[웹 검색 수행]

Claude: "조사 완료!

**발견 사항:**
- Milvus 2.3.3 (최신 stable)
- etcd 3.5.0 + MinIO 필요
- 별도 네트워크 설정 필요 (milvus-network)

**구현 단계 제안:**

**Step 1: 프로젝트 구조 생성** (0.5h)
- 디렉토리 구조 생성
- .gitignore, README.md

**Step 2: Docker Compose 기본 설정** (1h)
- PostgreSQL 15 설정
- 환경 변수 관리
- 네트워크 설정

**Step 3: Milvus 스택 추가** (1.5h)
- Milvus Standalone
- etcd 설정
- MinIO 설정
- Attu (Web UI)

**Step 4: 검증 및 테스트** (1h)
- 모든 컨테이너 실행
- 연결 테스트
- 문서 작성

**총 예상: 4h**

**테스트 계획:**
1. test_docker_compose_up()
2. test_postgresql_connection()
3. test_milvus_health_check()
4. test_attu_ui_accessible()

**리스크:**
Risk 1: Milvus 메모리 요구사항 높음
- Impact: Medium
- Mitigation: docker-compose.yml에 리소스 제한 설정

진행할까요?"

사용자: "네"

Claude: "✅ 실행 계획 생성 완료!

📁 docs/task-plans/task-1.1-plan.md

[상세 요약 출력]

다음: Peer 리뷰 요청"
```

## Related Commands

- `/task-breakdown [prd] [phase]` - Task 분해 (이전 단계)
- `/prd-review [prd]` - PRD 검토
- `/architecture-design [prd]` - 아키텍처 설계
