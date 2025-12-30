# Issue Create

## 🎯 역할

**Task Breakdown의 작업 단위 또는 새로운 요청을 GitHub Issue로 생성합니다.**

### 두 가지 사용 방식

**1. Task 기반 (구조화된 개발)**
```
PRD → Task Breakdown → /issue-create 1.1
→ Task 1.1을 자동으로 Issue로 변환
```

**2. 자유 요청 (빠른 Issue 생성)**
```
/issue-create "Add Redis caching layer"
→ 요청을 분석하여 적절한 Issue 생성
```

### 왜 Issue를 만드나요?

```
✅ 작업 추적
   무엇을 할지 명확히 기록

✅ 팀 협업
   누가 무엇을 하는지 공유

✅ 브랜치 연결
   feature/issue-1-docker-setup
   커밋: Ref: #1, PR: Closes #1

✅ 히스토리
   진행 상황과 완료 시점 기록
```

---

## Usage

```bash
# Task 기반 (Task Breakdown 사용)
/issue-create [task-id]
/issue-create [task-id] --dry-run          # 미리보기만
/issue-create [task-id] --assign-me
/issue-create [task-id] --file docs/tasks/custom.md

# 자유 요청 (빠른 생성)
/issue-create "[요청 내용]"
/issue-create "[요청]" --dry-run           # 미리보기만
/issue-create "[요청]" --priority high

# 자연어 (유연한 사용)
/issue-create Task 1.1을 docs/tasks/custom.md에서 읽어서 생성
```

**파라미터:**
- `task-id` - Task ID (예: 1.1, 2.3)
- `"요청 내용"` - 자유 형식 요청
- `--assign-me` - 자신에게 할당
- `--priority` - high/medium/low (기본: medium)
- `--dry-run` - 미리보기만 (생성 안 함)
- `--file` - 커스텀 Task Breakdown 파일

## Examples

```bash
# Task 기반
/issue-create 1.1
/issue-create 1.1 --dry-run --assign-me

# 커스텀 파일
/issue-create 1.1 --file docs/tasks/phase-1.md

# 자유 요청
/issue-create "Add Redis caching layer"
/issue-create "Fix login bug" --priority high --dry-run

# 자연어
/issue-create Task 1.1을 생성해주세요
```

---

## 프로젝트 라벨링 시스템

**CLAUDE.md 표준 라벨 적용**

### 작업 유형 (Type)

| 라벨 | 설명 | 사용 시 |
|------|------|---------|
| `✨ feature` | 새로운 기능 추가 | 새 API, 새 페이지, 새 기능 |
| `🐛 bug` | 버그 수정 | 오류, 예외, 작동 안 함 |
| `🔧 refactor` | 코드 리팩토링 | 구조 개선, 중복 제거 |
| `🎨 ui/ux` | UI/UX 개선 | 디자인, 사용성 개선 |
| `🗑️ cleanup` | 코드 정리 | 불필요한 코드 제거 |
| `🔄 enhancement` | 기능 개선 | 기존 기능 향상 |
| `📝 docs` | 문서화 | README, 주석, 가이드 |
| `🧪 test` | 테스트 추가 | 단위/통합 테스트 |

### 우선순위 (Priority)

| 라벨 | 설명 | 처리 시간 |
|------|------|-----------|
| `🔥 high-priority` | 긴급/중요 | 즉시 처리 |
| `📋 medium-priority` | 보통 | 1-2주 내 |
| `🔖 low-priority` | 낮음 | 시간 날 때 |

### 상태 (Status)

| 라벨 | 설명 |
|------|------|
| `💡 idea` | 제안/아이디어 |
| `🚧 in-progress` | 진행 중 |
| `🔍 needs-review` | 리뷰 필요 |
| `✅ ready` | 준비 완료 |

### Phase 라벨

| 라벨 | 설명 |
|------|------|
| `phase-1` | Phase 1 작업 |
| `phase-2` | Phase 2 작업 |
| `phase-3` | Phase 3 작업 |

---

## Instructions for Claude

### Execution Method

Claude uses the bash tool to execute these commands step by step.
Each bash code block should be executed sequentially.

**Important:** 
- This is NOT a single shell script
- Execute each Step separately using bash tool
- Parse natural language parameters when needed

---

## 모드 1: Task 기반 Issue 생성

### Step 1: Parameter Validation & Parsing

```bash
# ===== 파라미터 초기화 =====
TASK_ID=""
REQUEST=""
ASSIGN_ME=false
DRY_RUN=false
PRIORITY_ARG=""
CUSTOM_FILE=""
MODE=""

# ===== 첫 번째 인자 확인 =====
FIRST_ARG="$1"

if [[ -z "$FIRST_ARG" ]]; then
  echo "❌ 파라미터가 필요합니다."
  echo ""
  echo "사용법:"
  echo "  /issue-create 1.1"
  echo "  /issue-create \"Add Redis caching\""
  echo "  /issue-create Task 1.1을 생성해주세요"
  exit 1
fi

# ===== Task ID 형식 검증 (숫자.숫자) =====
if [[ "$FIRST_ARG" =~ ^[0-9]+\.[0-9]+$ ]]; then
  # Task 모드
  TASK_ID="$FIRST_ARG"
  MODE="task"
  shift
  
elif [[ "$*" =~ Task[[:space:]]+([0-9]+\.[0-9]+) ]]; then
  # 자연어에서 Task ID 추출
  TASK_ID="${BASH_REMATCH[1]}"
  MODE="task"
  
else
  # 자유 요청 모드
  REQUEST="$*"
  MODE="freeform"
fi

# ===== 나머지 옵션 파싱 =====
while [[ $# -gt 0 ]]; do
  case $1 in
    --assign-me)
      ASSIGN_ME=true
      shift
      ;;
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    --priority)
      PRIORITY_ARG="$2"
      shift 2
      ;;
    --file)
      CUSTOM_FILE="$2"
      shift 2
      ;;
    *)
      shift
      ;;
  esac
done

# ===== 모드 확인 =====
echo "🎯 실행 모드: ${MODE}"
[ "$MODE" = "task" ] && echo "   Task ID: ${TASK_ID}"
[ "$MODE" = "freeform" ] && echo "   요청: ${REQUEST}"
[ "$DRY_RUN" = true ] && echo "   ⚠️  Dry Run: 미리보기만 (생성 안 함)"
echo ""
```

### Step 2: Task Breakdown 파일 찾기 (Task 모드)

```bash
# Task 모드가 아니면 건너뛰기
if [ "$MODE" != "task" ]; then
  echo "ℹ️  자유 요청 모드 - Task Breakdown 건너뛰기"
else
  # ===== 파일 경로 결정 =====
  if [ -n "$CUSTOM_FILE" ]; then
    # 사용자 지정 파일
    TASK_BREAKDOWN_FILE="$CUSTOM_FILE"
    echo "📖 Task Breakdown: ${TASK_BREAKDOWN_FILE} (사용자 지정)"
    
  elif [[ "$*" =~ (docs/[^ ]+\.md) ]]; then
    # 자연어에서 파일 경로 추출
    TASK_BREAKDOWN_FILE="${BASH_REMATCH[1]}"
    echo "📖 Task Breakdown: ${TASK_BREAKDOWN_FILE} (자연어 추출)"
    
  else
    # 자동 탐색
    TASK_BREAKDOWN_FILE=$(find docs/tasks -type f \( \
      -name "phase-*-tasks.md" -o \
      -name "task-breakdown.md" -o \
      -name "*breakdown.md" -o \
      -name "*tasks.md" \
    \) 2>/dev/null | head -1)
    
    if [ -z "$TASK_BREAKDOWN_FILE" ]; then
      echo "❌ Task Breakdown 파일을 찾을 수 없습니다."
      echo ""
      echo "다음 위치에 파일이 있어야 합니다:"
      echo "  - docs/tasks/task-breakdown.md"
      echo "  - docs/tasks/phase-1-tasks.md"
      echo ""
      echo "또는 --file 옵션으로 파일을 지정하세요:"
      echo "  /issue-create 1.1 --file docs/tasks/custom.md"
      exit 1
    fi
    
    echo "📖 Task Breakdown: ${TASK_BREAKDOWN_FILE} (자동 탐색)"
  fi
  
  # ===== 파일 존재 확인 =====
  if [ ! -f "$TASK_BREAKDOWN_FILE" ]; then
    echo "❌ 파일이 존재하지 않습니다: ${TASK_BREAKDOWN_FILE}"
    exit 1
  fi
  
  echo "✅ Task Breakdown 파일 확인 완료"
  echo ""
fi
```

### Step 3: Task 정보 추출 (Task 모드)

```bash
# Task 모드가 아니면 건너뛰기
if [ "$MODE" != "task" ]; then
  echo "ℹ️  자유 요청 모드 - Task 추출 건너뛰기"
else
  echo "📄 Task ${TASK_ID} 정보 추출 중..."

  # ===== Task 섹션 추출 (개선된 패턴 매칭) =====
  # 지원 형식:
  #   - ### Task 1.1: Title
  #   - #### Task 1.1: Title
  #   - #### **Task 1.1: Title**
  #   - ## Task 1.1: Title
  #   - **Task 1.1**: Title

  # 먼저 파일에서 실제 Task 패턴 찾기 (디버깅용)
  TASK_LINE=$(grep -n "Task ${TASK_ID}[:\*]" "$TASK_BREAKDOWN_FILE" | head -1)

  if [ -z "$TASK_LINE" ]; then
    echo "❌ Task ${TASK_ID}를 찾을 수 없습니다."
    echo ""
    echo "확인 사항:"
    echo "  - 파일: ${TASK_BREAKDOWN_FILE}"
    echo "  - 검색 패턴: Task ${TASK_ID}"
    echo ""
    echo "📋 파일에 있는 Task 목록:"
    grep -E "Task [0-9]+\.[0-9]+" "$TASK_BREAKDOWN_FILE" | head -10
    echo ""
    exit 1
  fi

  # Task 시작 라인 번호
  TASK_START_LINE=$(echo "$TASK_LINE" | cut -d':' -f1)

  # 다음 Task 또는 구분선(---)까지 추출
  TASK_SECTION=$(awk -v start="$TASK_START_LINE" '
    NR == start { in_task=1 }
    in_task {
      # 다음 Task나 구분선을 만나면 중지
      if (NR > start && (/^#{2,4} .*Task [0-9]+\.[0-9]+/ || /^---$/)) {
        exit
      }
      print
    }
  ' "$TASK_BREAKDOWN_FILE")

  # ===== Task 존재 확인 =====
  if [ -z "$TASK_SECTION" ]; then
    echo "❌ Task ${TASK_ID} 섹션을 추출할 수 없습니다."
    echo ""
    echo "발견된 라인: ${TASK_LINE}"
    exit 1
  fi

  # ===== 각 필드 추출 =====

  # 1. Title 추출 (모든 마크다운 형식 제거)
  TASK_TITLE=$(echo "$TASK_SECTION" | head -1 | \
    sed 's/^####* *//' | \
    sed 's/\*\*//g' | \
    sed 's/^Task [0-9.]*: *//')

  # 2. Estimate 추출 (시간 또는 Estimate 필드)
  ESTIMATE=$(echo "$TASK_SECTION" | \
    grep -iE "^- \*\*(시간|Estimate)" | \
    sed 's/.*: *//' | \
    head -1)

  # 3. Description 추출 (Description 필드 또는 작업 내용)
  DESCRIPTION=$(echo "$TASK_SECTION" | \
    grep -iE "^- \*\*(Description|작업 내용)" | \
    sed 's/.*: *//' | \
    head -1)

  # Description이 없으면 Title을 Description으로 사용
  if [ -z "$DESCRIPTION" ]; then
    DESCRIPTION="$TASK_TITLE"
  fi

  # 4. Phase 추출 (Task ID에서 - 1.1 → Phase 1)
  PHASE=$(echo "$TASK_ID" | cut -d'.' -f1)

  # 5. Deliverables 추출 (출력물 또는 Deliverables)
  DELIVERABLES=$(echo "$TASK_SECTION" | \
    sed -n '/\*\*\(출력물\|Deliverables\)\*\*/,/^- \*\*[^출]/p' | \
    grep "^  -" | sed 's/^  //')

  # 6. Acceptance Criteria 추출 (검증 기준 또는 Acceptance Criteria)
  ACCEPTANCE_CRITERIA=$(echo "$TASK_SECTION" | \
    sed -n '/\*\*\(검증 기준\|Acceptance Criteria\)\*\*/,/^- \*\*/p' | \
    grep "^  - \[" | sed 's/^  //')

  # 7. Files to Create 추출 (선택 필드)
  FILES_TO_CREATE=$(echo "$TASK_SECTION" | \
    sed -n '/\*\*Files to Create\*\*/,/^$/p' | \
    grep "^  -" | sed 's/^  //')

  # ===== 추출 결과 확인 =====
  echo "✅ Task 정보 추출 완료:"
  echo ""
  echo "   Title: ${TASK_TITLE}"
  echo "   Estimate: ${ESTIMATE:-없음}"
  echo "   Phase: ${PHASE}"

  DELIVERABLES_COUNT=$(echo "$DELIVERABLES" | grep -c "^-" || echo "0")
  echo "   Deliverables: ${DELIVERABLES_COUNT}개 항목"

  CRITERIA_COUNT=$(echo "$ACCEPTANCE_CRITERIA" | grep -c "^-" || echo "0")
  echo "   Acceptance Criteria: ${CRITERIA_COUNT}개 조건"

  if [ -n "$FILES_TO_CREATE" ]; then
    FILES_COUNT=$(echo "$FILES_TO_CREATE" | grep -c "^-" || echo "0")
    echo "   Files to Create: ${FILES_COUNT}개 파일"
  fi

  echo ""
fi
```

### Step 4: 작업 유형 자동 판단 (Task 모드)

```bash
# Task 모드가 아니면 건너뛰기
if [ "$MODE" != "task" ]; then
  echo "ℹ️  자유 요청 모드 - 라벨은 나중에 결정"
else
  echo "🏷️  라벨 자동 판단 중..."
  
  # ===== 키워드 기반 작업 유형 판단 =====
  CONTENT=$(echo "${TASK_TITLE} ${DESCRIPTION}" | tr '[:upper:]' '[:lower:]')
  
  # 작업 유형 결정
  if echo "$CONTENT" | grep -qE "bug|fix|error|issue|crash"; then
    TYPE_LABEL="🐛 bug"
  elif echo "$CONTENT" | grep -qE "refactor|restructure|reorganize"; then
    TYPE_LABEL="🔧 refactor"
  elif echo "$CONTENT" | grep -qE "ui|ux|design|style|layout"; then
    TYPE_LABEL="🎨 ui/ux"
  elif echo "$CONTENT" | grep -qE "cleanup|remove|delete|unused"; then
    TYPE_LABEL="🗑️ cleanup"
  elif echo "$CONTENT" | grep -qE "enhance|improve|optimize|better"; then
    TYPE_LABEL="🔄 enhancement"
  elif echo "$CONTENT" | grep -qE "test|testing|coverage"; then
    TYPE_LABEL="🧪 test"
  elif echo "$CONTENT" | grep -qE "doc|documentation|readme"; then
    TYPE_LABEL="📝 docs"
  else
    TYPE_LABEL="✨ feature"
  fi
  
  # ===== Phase별 우선순위 자동 설정 =====
  case $PHASE in
    1)
      PRIORITY_LABEL="🔥 high-priority"
      CATEGORY_LABEL="infrastructure"
      ;;
    2)
      PRIORITY_LABEL="📋 medium-priority"
      CATEGORY_LABEL="backend"
      ;;
    3)
      PRIORITY_LABEL="📋 medium-priority"
      CATEGORY_LABEL="frontend"
      ;;
    *)
      PRIORITY_LABEL="📋 medium-priority"
      CATEGORY_LABEL=""
      ;;
  esac
  
  # 우선순위 옵션 오버라이드
  case "$PRIORITY_ARG" in
    high)
      PRIORITY_LABEL="🔥 high-priority"
      ;;
    medium)
      PRIORITY_LABEL="📋 medium-priority"
      ;;
    low)
      PRIORITY_LABEL="🔖 low-priority"
      ;;
  esac
  
  # ===== 라벨 조합 =====
  LABELS="${TYPE_LABEL},${PRIORITY_LABEL},phase-${PHASE}"
  [ -n "$CATEGORY_LABEL" ] && LABELS="${LABELS},${CATEGORY_LABEL}"
  
  echo "   Type: ${TYPE_LABEL}"
  echo "   Priority: ${PRIORITY_LABEL}"
  echo "   Phase: phase-${PHASE}"
  [ -n "$CATEGORY_LABEL" ] && echo "   Category: ${CATEGORY_LABEL}"
  echo ""
fi
```

### Step 5: Issue 본문 생성 (Task 모드)

```bash
# Task 모드가 아니면 건너뛰기
if [ "$MODE" != "task" ]; then
  echo "ℹ️  자유 요청 모드 - Issue 본문은 나중에 생성"
else
  echo "📝 Issue 본문 생성 중..."
  
  # ===== Issue Title =====
  ISSUE_TITLE="[Task ${TASK_ID}] ${TASK_TITLE}"
  
  # ===== Issue Body =====
  ISSUE_BODY=$(cat << EOF
## Task Information

- **Task ID**: ${TASK_ID}
- **Estimate**: ${ESTIMATE:-TBD}
- **Phase**: ${PHASE}

## Description

${DESCRIPTION}

## Deliverables

${DELIVERABLES}

## Acceptance Criteria

${ACCEPTANCE_CRITERIA}

$([ -n "$FILES_TO_CREATE" ] && cat << FILESEOF

## Files to Create

${FILES_TO_CREATE}
FILESEOF
)

---

**Task Breakdown**: [${TASK_BREAKDOWN_FILE}](../blob/main/${TASK_BREAKDOWN_FILE})
EOF
)
  
  echo "✅ Issue 본문 생성 완료"
  echo ""
fi
```

---

## 모드 2: 자유 요청 Issue 생성

### Step 1: 요청 분석 (자유 요청 모드)

```bash
# 자유 요청 모드가 아니면 건너뛰기
if [ "$MODE" != "freeform" ]; then
  echo "ℹ️  Task 모드 - 요청 분석 건너뛰기"
else
  echo "🤔 요청 분석 중..."
  echo "   \"${REQUEST}\""
  echo ""
fi
```

**Claude의 수행 (자유 요청 모드):**

1. **요청 분석**
   - 키워드 추출 (add, fix, refactor 등)
   - 대상 식별 (Redis, API, UI 등)
   - 범위 파악

2. **프로젝트 컨텍스트 파악**
   - README.md 읽기 (프로젝트 구조)
   - 관련 파일 확인 (해당되는 경우)
   - 기술 스택 파악

3. **Issue 구조화**
   - 명확한 제목 생성
   - 구조화된 본문 작성
   - 테스트 가능한 조건 제시

### Step 2: 작업 유형 판단 (자유 요청 모드)

```bash
# 자유 요청 모드가 아니면 건너뛰기
if [ "$MODE" != "freeform" ]; then
  echo "ℹ️  Task 모드 - 라벨 이미 결정됨"
else
  echo "🏷️  라벨 자동 판단 중..."
  
  # ===== 요청을 소문자로 변환 =====
  REQUEST_LOWER=$(echo "$REQUEST" | tr '[:upper:]' '[:lower:]')
  
  # ===== 작업 유형 판단 =====
  if echo "$REQUEST_LOWER" | grep -qE "bug|fix|error|crash|broken|issue|fail"; then
    TYPE_LABEL="🐛 bug"
    PRIORITY_LABEL="🔥 high-priority"  # 버그는 높은 우선순위
    
  elif echo "$REQUEST_LOWER" | grep -qE "refactor|restructure|reorganize|clean code"; then
    TYPE_LABEL="🔧 refactor"
    PRIORITY_LABEL="📋 medium-priority"
    
  elif echo "$REQUEST_LOWER" | grep -qE "ui|ux|design|style|layout|theme"; then
    TYPE_LABEL="🎨 ui/ux"
    PRIORITY_LABEL="📋 medium-priority"
    
  elif echo "$REQUEST_LOWER" | grep -qE "cleanup|remove|delete|unused"; then
    TYPE_LABEL="🗑️ cleanup"
    PRIORITY_LABEL="🔖 low-priority"
    
  elif echo "$REQUEST_LOWER" | grep -qE "enhance|improve|optimize|better"; then
    TYPE_LABEL="🔄 enhancement"
    PRIORITY_LABEL="📋 medium-priority"
    
  elif echo "$REQUEST_LOWER" | grep -qE "test|testing|coverage"; then
    TYPE_LABEL="🧪 test"
    PRIORITY_LABEL="📋 medium-priority"
    
  elif echo "$REQUEST_LOWER" | grep -qE "doc|documentation|readme|comment"; then
    TYPE_LABEL="📝 docs"
    PRIORITY_LABEL="🔖 low-priority"
    
  elif echo "$REQUEST_LOWER" | grep -qE "urgent|critical|asap|immediately"; then
    TYPE_LABEL="✨ feature"
    PRIORITY_LABEL="🔥 high-priority"
    
  else
    TYPE_LABEL="✨ feature"
    PRIORITY_LABEL="📋 medium-priority"
  fi
  
  # ===== 우선순위 옵션 오버라이드 =====
  case "$PRIORITY_ARG" in
    high)
      PRIORITY_LABEL="🔥 high-priority"
      ;;
    medium)
      PRIORITY_LABEL="📋 medium-priority"
      ;;
    low)
      PRIORITY_LABEL="🔖 low-priority"
      ;;
  esac
  
  # ===== 아이디어 라벨 추가 =====
  STATUS_LABEL=""
  if echo "$REQUEST_LOWER" | grep -qE "idea|suggestion|propose|consider|maybe"; then
    STATUS_LABEL="💡 idea"
    LABELS="${TYPE_LABEL},${PRIORITY_LABEL},${STATUS_LABEL}"
  else
    LABELS="${TYPE_LABEL},${PRIORITY_LABEL}"
  fi
  
  echo "   Type: ${TYPE_LABEL}"
  echo "   Priority: ${PRIORITY_LABEL}"
  [ -n "$STATUS_LABEL" ] && echo "   Status: ${STATUS_LABEL}"
  echo ""
fi
```

### Step 3: Issue 제목 & 본문 생성 (자유 요청 모드)

**Claude가 수행:**

```
요청을 분석하여:
1. 명확한 제목 생성
   - 작업 유형 이모지 포함
   - 명확한 동작 동사
   - 구체적인 대상

2. 구조화된 본문 작성
   - Overview (1-2문장)
   - Objectives (bullet points)
   - Technical Details (필요시)
   - Acceptance Criteria (테스트 가능한 조건)

3. 프로젝트 컨텍스트 반영
   - 기술 스택 고려
   - 기존 패턴 참조
   - 관련 파일/컴포넌트 언급
```

**예시:**

```bash
# 요청: "Add Redis caching layer"

ISSUE_TITLE="✨ Add Redis caching layer for API responses"

ISSUE_BODY=$(cat << EOF
## 📋 Overview

Implement Redis caching to improve API response times and reduce database load.

## 🎯 Objectives

- Integrate Redis client library
- Implement caching middleware
- Define cache invalidation strategy
- Add cache configuration

## 📝 Technical Details

**Suggested approach:**
- Use \`ioredis\` for Node.js or \`redis-py\` for Python
- Cache GET endpoints with TTL
- Invalidate on POST/PUT/DELETE
- Configure Redis connection pool

**Files to modify:**
- \`backend/config/cache.js\` (new)
- \`backend/middleware/cache.js\` (new)
- \`backend/routes/*.js\` (add caching)

## ✅ Acceptance Criteria

- [ ] Redis client connected and configured
- [ ] GET /api/* endpoints cached
- [ ] Cache hit rate > 70%
- [ ] Cache invalidation working
- [ ] Unit tests for caching middleware
- [ ] Documentation updated

## 🔗 Related

- Related to: Performance optimization
- Depends on: Redis server setup

---

*This issue was automatically created from request: "${REQUEST}"*
EOF
)
```

---

## 공통: GitHub CLI 확인 & Issue 생성

### Step: GitHub CLI 확인

```bash
# ===== GitHub CLI 설치 확인 =====
if ! command -v gh &> /dev/null; then
  echo "❌ GitHub CLI가 설치되어 있지 않습니다."
  echo ""
  echo "설치 방법:"
  echo "  macOS: brew install gh"
  echo "  Ubuntu: sudo apt-get install gh"
  echo "  Windows: winget install GitHub.cli"
  echo ""
  echo "공식 사이트: https://cli.github.com"
  exit 1
fi

# ===== GitHub 인증 확인 =====
if ! gh auth status &> /dev/null; then
  echo "❌ GitHub 인증이 필요합니다."
  echo ""
  echo "인증 방법:"
  echo "  gh auth login"
  echo ""
  echo "인증 후 다시 시도하세요."
  exit 1
fi

echo "✅ GitHub CLI 확인 완료"
echo ""
```

### Step: Dry-run Preview (선택)

```bash
# ===== Dry-run 모드 처리 =====
if [ "$DRY_RUN" = true ]; then
  echo ""
  echo "=========================================="
  echo "📋 Issue Preview (Dry Run)"
  echo "=========================================="
  echo ""
  echo "Title:"
  echo "  ${ISSUE_TITLE}"
  echo ""
  echo "Labels:"
  echo "  ${LABELS}"
  echo ""
  [ "$ASSIGN_ME" = true ] && echo "Assignee: @me"
  [ "$ASSIGN_ME" = true ] && echo ""
  echo "Body:"
  echo "---"
  echo "${ISSUE_BODY}"
  echo "---"
  echo ""
  echo "💡 이 Issue를 생성하려면 --dry-run을 제거하세요:"
  
  if [ "$MODE" = "task" ]; then
    echo "   /issue-create ${TASK_ID}"
  else
    echo "   /issue-create \"${REQUEST}\""
  fi
  
  echo ""
  exit 0
fi
```

### Step: Issue 생성

```bash
echo "🚀 GitHub Issue 생성 중..."
echo ""

# ===== Issue 생성 (에러 캡처) =====
ASSIGN_FLAG=""
[ "$ASSIGN_ME" = true ] && ASSIGN_FLAG="--assignee @me"

# Issue 생성 실행
ISSUE_RESULT=$(gh issue create \
  --title "$ISSUE_TITLE" \
  --body "$ISSUE_BODY" \
  --label "$LABELS" \
  $ASSIGN_FLAG \
  2>&1)

# ===== 결과 확인 =====
if echo "$ISSUE_RESULT" | grep -q "https://github.com"; then
  # 성공
  ISSUE_URL=$(echo "$ISSUE_RESULT" | grep "https://github.com")
  ISSUE_NUMBER=$(echo "$ISSUE_URL" | grep -oE '[0-9]+$')
  
  echo ""
  echo "=========================================="
  echo "✅ Issue 생성 완료!"
  echo "=========================================="
  echo ""
  echo "📌 Issue #${ISSUE_NUMBER}"
  echo "🔗 ${ISSUE_URL}"
  echo ""
  echo "📋 정보:"
  echo "   제목: ${ISSUE_TITLE}"
  echo "   라벨: ${LABELS}"
  [ "$ASSIGN_ME" = true ] && echo "   담당: @me"
  echo ""
  echo "🚀 다음 단계:"
  echo "   1. /branch-create ${ISSUE_NUMBER}"
  echo "      또는"
  echo "      /worktree-create ${ISSUE_NUMBER}"
  echo ""
  
else
  # 실패 - 상세 에러 분석
  echo "❌ Issue 생성 실패"
  echo ""
  
  # 에러 원인별 메시지
  if echo "$ISSUE_RESULT" | grep -qE "auth|authentication"; then
    echo "❌ 원인: GitHub 인증 실패"
    echo ""
    echo "해결 방법:"
    echo "  1. gh auth login"
    echo "  2. 인증 완료 후 다시 시도"
    
  elif echo "$ISSUE_RESULT" | grep -qE "rate limit"; then
    echo "❌ 원인: API 속도 제한 (Rate Limit)"
    echo ""
    echo "해결 방법:"
    echo "  - 잠시 후 다시 시도 (1시간 대기)"
    echo "  - gh api rate_limit (제한 확인)"
    
  elif echo "$ISSUE_RESULT" | grep -qE "not found|404"; then
    echo "❌ 원인: 저장소를 찾을 수 없음"
    echo ""
    echo "해결 방법:"
    echo "  1. Git 저장소 확인: git remote -v"
    echo "  2. GitHub 저장소 존재 확인"
    echo "  3. 원격 저장소 연결 확인"
    
  elif echo "$ISSUE_RESULT" | grep -qE "permission|forbidden"; then
    echo "❌ 원인: 권한 부족"
    echo ""
    echo "해결 방법:"
    echo "  1. 저장소 접근 권한 확인"
    echo "  2. Collaborator 권한 요청"
    echo "  3. gh repo view (권한 확인)"
    
  elif echo "$ISSUE_RESULT" | grep -qE "network|connection"; then
    echo "❌ 원인: 네트워크 연결 실패"
    echo ""
    echo "해결 방법:"
    echo "  1. 인터넷 연결 확인"
    echo "  2. VPN 설정 확인"
    echo "  3. 방화벽 설정 확인"
    
  else
    echo "❌ 원인: 알 수 없는 오류"
    echo ""
    echo "상세 에러:"
    echo "$ISSUE_RESULT"
  fi
  
  echo ""
  echo "🔍 확인 사항:"
  echo "   1. GitHub 인증: gh auth status"
  echo "   2. 저장소 정보: gh repo view"
  echo "   3. 네트워크: ping github.com"
  echo ""
  
  exit 1
fi
```

---

## 라벨링 예시

### Task 기반 예시

```bash
/issue-create 1.1
# Task: "Docker Compose 설정"
# Phase: 1

자동 라벨:
→ ✨ feature (기본 작업)
→ 🔥 high-priority (Phase 1)
→ phase-1
→ infrastructure
```

```bash
/issue-create 2.1
# Task: "Fix PostgreSQL connection"
# Phase: 2

자동 라벨:
→ 🐛 bug (fix 키워드)
→ 📋 medium-priority (Phase 2)
→ phase-2
→ backend
```

### 자유 요청 예시

```bash
/issue-create "Add Redis caching layer"

자동 분석:
→ ✨ feature (새 기능)
→ 📋 medium-priority (일반)

Issue:
Title: ✨ Add Redis caching layer for API responses
Body: [상세한 설명 + Acceptance Criteria]
```

```bash
/issue-create "Fix login authentication failure" --priority high

자동 분석:
→ 🐛 bug (fix 키워드)
→ 🔥 high-priority (옵션 지정)

Issue:
Title: 🐛 Fix login authentication failure
Body: [버그 설명 + 재현 방법 + 수정 조건]
```

```bash
/issue-create "Consider implementing GraphQL" 

자동 분석:
→ ✨ feature
→ 📋 medium-priority
→ 💡 idea (consider 키워드)

Issue:
Title: 💡 Consider implementing GraphQL API
Labels: ✨ feature, 📋 medium-priority, 💡 idea
```

---

## Error Handling

### 파라미터 없음

```bash
if [[ -z "$FIRST_ARG" ]]; then
  echo "❌ 파라미터가 필요합니다."
  echo "사용법: /issue-create 1.1"
  exit 1
fi
```

### Task Breakdown 없음 (Task 모드)

```bash
if [ -z "$TASK_BREAKDOWN_FILE" ]; then
  echo "❌ Task Breakdown 파일을 찾을 수 없습니다."
  echo "위치: docs/tasks/"
  exit 1
fi
```

### Task 정보 없음 (Task 모드)

```bash
if [ "$TASK_SECTION" = "TASK_NOT_FOUND" ]; then
  echo "❌ Task ${TASK_ID}를 찾을 수 없습니다."
  exit 1
fi
```

### GitHub CLI 없음

```bash
if ! command -v gh &> /dev/null; then
  echo "❌ GitHub CLI 미설치"
  echo "설치: brew install gh"
  exit 1
fi
```

### GitHub 인증 없음

```bash
if ! gh auth status &> /dev/null; then
  echo "❌ GitHub 인증 필요"
  echo "인증: gh auth login"
  exit 1
fi
```

### Issue 생성 실패

```bash
# 에러 원인별 상세 메시지
if echo "$ISSUE_RESULT" | grep -q "auth"; then
  echo "원인: 인증 실패"
elif echo "$ISSUE_RESULT" | grep -q "rate limit"; then
  echo "원인: API 제한"
# ...
fi
```

---

## Notes

### 자동 라벨링 규칙

**작업 유형 키워드:**
```
bug, fix → 🐛 bug
refactor → 🔧 refactor
ui, ux → 🎨 ui/ux
cleanup, remove → 🗑️ cleanup
enhance, improve → 🔄 enhancement
test → 🧪 test
doc → 📝 docs
기본 → ✨ feature
```

**우선순위 규칙:**
```
Task 기반:
- Phase 1 → 🔥 high-priority
- Phase 2-3 → 📋 medium-priority

자유 요청:
- bug, urgent → 🔥 high-priority
- 일반 → 📋 medium-priority
- cleanup, docs → 🔖 low-priority
```

**상태 라벨:**
```
idea, suggest, consider → 💡 idea
```

### Dry-run 활용

```bash
# 미리보기로 확인
/issue-create 1.1 --dry-run

# 확인 후 생성
/issue-create 1.1
```

### 파일 경로 지정

```bash
# 자동 탐색 (기본)
/issue-create 1.1

# 수동 지정 (구조화)
/issue-create 1.1 --file docs/tasks/phase-1.md

# 수동 지정 (자연어)
/issue-create Task 1.1을 docs/tasks/custom.md에서 생성
```

---

## Related Commands

- `/branch-create [issue-number]` - Issue 기반 브랜치 생성
- `/worktree-create [issue-number]` - Issue 기반 Worktree 생성
- `/commit` - Issue 참조 커밋
- `/pr-create` - Issue 닫는 PR 생성

---

## 워크플로우 예시

### Task 기반 워크플로우

```bash
# 1. Task Breakdown 작성 (수동)
vim docs/tasks/task-breakdown.md

# 2. Issue 미리보기
/issue-create 1.1 --dry-run

# 3. Issue 생성
/issue-create 1.1
# → Issue #1 (✨ feature, 🔥 high-priority, phase-1)

# 4. 개발 진행
/branch-create 1
```

### 자유 요청 워크플로우

```bash
# 1. 빠른 Issue 미리보기
/issue-create "Add Redis caching" --dry-run

# 2. Issue 생성
/issue-create "Add Redis caching layer"
# → Issue #5 (✨ feature, 📋 medium-priority)

# 3. 긴급 버그
/issue-create "Fix payment timeout" --priority high
# → Issue #6 (🐛 bug, 🔥 high-priority)

# 4. 개발 진행
/branch-create 5
```

---

**표준화된 라벨과 안전한 Issue 생성!** 🚀
