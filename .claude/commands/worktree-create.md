# Worktree Create

## 🎯 역할

**Issue 기반으로 Git Worktree를 생성하여 병렬 작업 환경을 구축합니다.**

### Worktree란?

```
일반 브랜치 (Feature Branch):
- 하나의 작업 디렉토리
- 브랜치 전환 시 파일 변경
- 순차적 작업

Git Worktree:
- 여러 작업 디렉토리 동시 존재
- 각 디렉토리가 다른 브랜치
- 병렬 작업 가능
```

### 언제 사용하나요?

```
✅ 병렬 작업
   Task 1.1 작업 중 긴급 버그 수정

✅ 빠른 전환
   브랜치 전환 없이 디렉토리만 이동

✅ 비교 작업
   두 브랜치 코드를 동시에 비교

✅ CI/CD 대기
   PR 생성 후 다른 Task 즉시 시작
```

### 디렉토리 구조

```
workspace/
├── project/                ← Main 작업 디렉토리
│   ├── .git/
│   ├── src/
│   └── docs/
│
└── project-wt/             ← Worktree 디렉토리 (프로젝트 밖!)
    ├── issue-1/            ← Task 1.1 작업
    │   ├── .git           (worktree 링크)
    │   ├── src/
    │   └── docs/
    ├── issue-2/            ← Task 1.2 작업
    │   ├── src/
    │   └── docs/
    └── hotfix/             ← 긴급 수정
        ├── src/
        └── docs/
```

**중요: Worktree는 프로젝트 밖에 생성됩니다!**
```
이유:
✅ 실수로 Main에 커밋 불가능
✅ .gitignore 설정 불필요
✅ 프로젝트 디렉토리 깔끔
✅ IDE 작업 공간 분리
```

---

## Usage

```bash
# Issue 기반 생성
/worktree-create [issue-number]

# 커스텀 이름으로 생성
/worktree-create [issue-number] [custom-name]

# Base 브랜치 지정
/worktree-create [issue-number] --base develop

# 옵션
/worktree-create 1 --dry-run           # 미리보기
/worktree-create 1 --fetch             # 원격 브랜치 fetch 후 생성
```

**파라미터:**
- `issue-number` - GitHub Issue 번호 (필수)
- `custom-name` - 커스텀 디렉토리명 (선택)
- `--base` - Base 브랜치 (기본: 자동 감지 - main/master/develop)
- `--dry-run` - 미리보기만
- `--fetch` - 원격 브랜치 최신화

## Examples

```bash
# 기본 사용
/worktree-create 1
# → project-wt/issue-1 생성
# → feature/issue-1-... 브랜치
# → Base: 자동 감지 (main/master/develop)

# 커스텀 이름
/worktree-create 1 hotfix
# → project-wt/hotfix 생성

# Base 브랜치 명시적 지정
/worktree-create 2 --base main
# → main에서 분기

# 미리보기
/worktree-create 1 --dry-run
# → 생성 전 확인

# 원격 최신화 후 생성
/worktree-create 1 --fetch
# → fetch 후 최신 코드로 생성
```

---

## Instructions for Claude

### Execution Method

Claude uses the bash tool to execute these commands step by step.

**Important Notes:**
- Worktree는 병렬 작업을 위한 독립 작업 디렉토리
- 각 Worktree는 별도 브랜치 체크아웃
- 디렉토리 구조: `worktree/issue-{number}` 또는 커스텀명
- Claude Code 실행 시 디렉토리 이동은 사용자가 수동으로

---

### Step 1: Parameter Validation & Parsing

```bash
# ===== 파라미터 초기화 =====
ISSUE_NUMBER=""
CUSTOM_NAME=""
BASE_BRANCH=""  # 자동 감지
DRY_RUN=false
DO_FETCH=false

# ===== 첫 번째 인자 확인 (Issue Number) =====
FIRST_ARG="$1"

if [[ -z "$FIRST_ARG" ]]; then
  echo "❌ Issue 번호가 필요합니다."
  echo ""
  echo "사용법:"
  echo "  /worktree-create [issue-number]"
  echo "  /worktree-create 1"
  echo "  /worktree-create 1 hotfix"
  exit 1
fi

# ===== Issue Number 검증 =====
if [[ "$FIRST_ARG" =~ ^[0-9]+$ ]]; then
  ISSUE_NUMBER="$FIRST_ARG"
  shift
else
  echo "❌ Issue 번호는 숫자여야 합니다: ${FIRST_ARG}"
  echo "예시: /worktree-create 1"
  exit 1
fi

# ===== 두 번째 인자 확인 (Custom Name - 선택) =====
if [[ -n "$1" ]] && [[ ! "$1" =~ ^-- ]]; then
  CUSTOM_NAME="$1"
  shift
fi

# ===== 옵션 파싱 =====
while [[ $# -gt 0 ]]; do
  case $1 in
    --base)
      BASE_BRANCH="$2"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    --fetch)
      DO_FETCH=true
      shift
      ;;
    *)
      echo "⚠️  알 수 없는 옵션: $1"
      shift
      ;;
  esac
done

# ===== Base 브랜치 자동 감지 (옵션으로 지정 안 된 경우) =====
if [ -z "$BASE_BRANCH" ]; then
  # origin/HEAD에서 기본 브랜치 확인
  DEFAULT_BRANCH=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@')

  if [ -z "$DEFAULT_BRANCH" ]; then
    # origin/HEAD가 없으면 일반적인 이름 시도
    if git show-ref --verify --quiet refs/heads/main; then
      DEFAULT_BRANCH="main"
    elif git show-ref --verify --quiet refs/heads/master; then
      DEFAULT_BRANCH="master"
    elif git show-ref --verify --quiet refs/heads/develop; then
      DEFAULT_BRANCH="develop"
    else
      # 최후의 수단: 현재 브랜치
      DEFAULT_BRANCH=$(git branch --show-current)
    fi
  fi

  BASE_BRANCH="${DEFAULT_BRANCH}"
fi

# ===== 설정 확인 =====
echo "🎯 Worktree 생성 설정"
echo "   Issue: #${ISSUE_NUMBER}"
[ -n "$CUSTOM_NAME" ] && echo "   Custom Name: ${CUSTOM_NAME}"
echo "   Base Branch: ${BASE_BRANCH} (자동 감지)"
[ "$DRY_RUN" = true ] && echo "   ⚠️  Dry Run: 미리보기만"
[ "$DO_FETCH" = true ] && echo "   📥 Fetch: 원격 최신화"
echo ""
```

### Step 2: Git Repository 확인

```bash
# ===== Git 저장소 확인 =====
if ! git rev-parse --is-inside-work-tree &> /dev/null; then
  echo "❌ Git 저장소가 아닙니다."
  echo ""
  echo "현재 위치: $(pwd)"
  echo "Git 저장소 루트로 이동하세요."
  exit 1
fi

# ===== Repository Root 확인 =====
REPO_ROOT=$(git rev-parse --show-toplevel)
echo "📁 Repository: ${REPO_ROOT}"

# ===== 현재 브랜치 확인 =====
CURRENT_BRANCH=$(git branch --show-current)
echo "🌿 Current Branch: ${CURRENT_BRANCH}"
echo ""
```

### Step 3: Issue 정보 확인

```bash
# ===== GitHub CLI 확인 =====
if ! command -v gh &> /dev/null; then
  echo "⚠️  GitHub CLI가 없습니다."
  echo "   Issue 정보를 확인할 수 없지만 계속 진행합니다."
  echo ""
  ISSUE_TITLE="issue-${ISSUE_NUMBER}"
else
  # ===== Issue 정보 가져오기 (타임아웃 포함) =====
  echo "📋 Issue 정보 확인 중..."

  # jq 사용 가능 여부 확인
  if command -v jq &> /dev/null; then
    # jq 있음 - JSON 파싱
    if ISSUE_INFO=$(timeout 5 gh issue view "$ISSUE_NUMBER" --json title,state 2>&1); then
      ISSUE_TITLE=$(echo "$ISSUE_INFO" | jq -r '.title')
      ISSUE_STATE=$(echo "$ISSUE_INFO" | jq -r '.state')
    else
      EXIT_CODE=$?
      if [ $EXIT_CODE -eq 124 ]; then
        echo "⚠️  GitHub API 타임아웃 - 기본값 사용"
      else
        echo "⚠️  Issue #${ISSUE_NUMBER}를 찾을 수 없습니다."
      fi
      ISSUE_TITLE="issue-${ISSUE_NUMBER}"
      ISSUE_STATE="UNKNOWN"
    fi
  else
    # jq 없음 - 텍스트 파싱
    if ISSUE_INFO=$(timeout 5 gh issue view "$ISSUE_NUMBER" 2>&1); then
      ISSUE_TITLE=$(echo "$ISSUE_INFO" | grep -m1 "^title:" | sed 's/^title:[[:space:]]*//')
      ISSUE_STATE=$(echo "$ISSUE_INFO" | grep -m1 "^state:" | sed 's/^state:[[:space:]]*//')
    else
      EXIT_CODE=$?
      if [ $EXIT_CODE -eq 124 ]; then
        echo "⚠️  GitHub API 타임아웃 - 기본값 사용"
      else
        echo "⚠️  Issue #${ISSUE_NUMBER}를 찾을 수 없습니다."
      fi
      ISSUE_TITLE="issue-${ISSUE_NUMBER}"
      ISSUE_STATE="UNKNOWN"
    fi
  fi

  # Issue 정보 표시
  if [ "$ISSUE_TITLE" != "issue-${ISSUE_NUMBER}" ]; then
    echo "   Title: ${ISSUE_TITLE}"
    echo "   State: ${ISSUE_STATE}"

    # Issue가 닫혀있으면 경고
    if [ "$ISSUE_STATE" = "CLOSED" ]; then
      echo ""
      echo "⚠️  경고: Issue #${ISSUE_NUMBER}가 이미 닫혀있습니다."
      echo "   계속 진행할까요? (이미 작업된 Issue일 수 있습니다)"
      echo ""
    fi
  else
    echo "   계속 진행합니다."
  fi
  echo ""
fi
```

### Step 4: 브랜치 이름 생성

```bash
# ===== 브랜치 이름 생성 =====
# GitHub Issue 제목에서 slug 생성
if [ -n "$ISSUE_TITLE" ] && [ "$ISSUE_TITLE" != "issue-${ISSUE_NUMBER}" ]; then
  # Title 정제 (prefix 제거)
  # 예: "[Task 1.1] PostgreSQL 스키마" → "PostgreSQL 스키마"
  CLEAN_TITLE=$(echo "$ISSUE_TITLE" | \
    sed 's/\[Task [0-9.]*\][[:space:]]*//' | \
    sed 's/^\*\**[[:space:]]*//' | \
    sed 's/[[:space:]]*\*\**$//')

  # Slug 생성 (영문/숫자만 사용)
  # 한글 및 특수문자는 제거하여 깔끔한 브랜치명 생성
  SLUG=$(echo "$CLEAN_TITLE" | \
    tr '[:upper:]' '[:lower:]' | \
    sed 's/[^a-z0-9-]/-/g' | \
    sed 's/--*/-/g' | \
    sed 's/^-//' | \
    sed 's/-$//' | \
    cut -c1-40)

  # 빈 slug 방지
  if [ -z "$SLUG" ] || [ "$SLUG" = "-" ]; then
    SLUG="task"
  fi

  BRANCH_NAME="feature/issue-${ISSUE_NUMBER}-${SLUG}"
else
  BRANCH_NAME="feature/issue-${ISSUE_NUMBER}"
fi

echo "🌿 브랜치 이름: ${BRANCH_NAME}"
echo ""
```

### Step 5: Worktree 디렉토리 결정

```bash
# ===== Repository 정보 =====
REPO_ROOT=$(git rev-parse --show-toplevel)
REPO_NAME=$(basename "$REPO_ROOT")

# ===== Worktree Base 디렉토리 (프로젝트 밖!) =====
# 예: /workspace/project → /workspace/project-wt
WORKTREE_BASE=$(dirname "$REPO_ROOT")/${REPO_NAME}-wt

# ===== Worktree 이름 결정 =====
if [ -n "$CUSTOM_NAME" ]; then
  # 커스텀 이름 사용
  WORKTREE_NAME="$CUSTOM_NAME"
else
  # 기본: issue-{number}
  WORKTREE_NAME="issue-${ISSUE_NUMBER}"
fi

# ===== 최종 Worktree 경로 =====
WORKTREE_PATH="${WORKTREE_BASE}/${WORKTREE_NAME}"

echo "📂 Worktree 구조:"
echo "   Main: ${REPO_ROOT}"
echo "   Worktrees: ${WORKTREE_BASE}"
echo "   This: ${WORKTREE_PATH}"
echo ""

# ===== 디렉토리 존재 확인 =====
if [ -d "$WORKTREE_PATH" ]; then
  echo "⚠️  경고: Worktree 디렉토리가 이미 존재합니다."
  echo "   경로: ${WORKTREE_PATH}"
  echo ""
  
  # 기존 worktree인지 확인
  if git worktree list | grep -q "$WORKTREE_PATH"; then
    echo "   이미 등록된 Worktree입니다."
    echo ""
    echo "Worktree 목록:"
    git worktree list
    echo ""
    echo "계속하려면 먼저 제거하세요:"
    echo "  /worktree-cleanup ${WORKTREE_NAME}"
    exit 1
  else
    echo "   Git Worktree가 아닌 일반 디렉토리입니다."
    echo "   수동으로 삭제 후 다시 시도하세요:"
    echo "   rm -rf ${WORKTREE_PATH}"
    exit 1
  fi
fi
```

### Step 6: Base 브랜치 확인

```bash
# ===== Base 브랜치 존재 확인 =====
echo "🔍 Base 브랜치 확인: ${BASE_BRANCH}"

if ! git show-ref --verify --quiet "refs/heads/${BASE_BRANCH}"; then
  # 로컬에 없으면 원격 확인
  if git show-ref --verify --quiet "refs/remotes/origin/${BASE_BRANCH}"; then
    echo "   로컬에 없음 - 원격에서 가져옵니다."
    git branch --track "$BASE_BRANCH" "origin/$BASE_BRANCH"
  else
    echo "❌ Base 브랜치가 존재하지 않습니다: ${BASE_BRANCH}"
    echo ""
    echo "사용 가능한 브랜치:"
    git branch -a | head -10
    exit 1
  fi
fi

echo "✅ Base 브랜치 확인 완료"
echo ""
```

### Step 7: Fetch (선택)

```bash
# ===== 원격 브랜치 최신화 (--fetch 옵션) =====
if [ "$DO_FETCH" = true ]; then
  echo "📥 원격 저장소 최신화 중..."

  if git fetch origin; then
    echo "✅ Fetch 완료"

    # Base 브랜치 최신화 (checkout 없이)
    if git show-ref --verify --quiet "refs/heads/${BASE_BRANCH}"; then
      echo "   ${BASE_BRANCH} 최신화 중..."

      # checkout 없이 직접 업데이트 (더 안전)
      if git fetch origin "${BASE_BRANCH}:${BASE_BRANCH}" 2>/dev/null; then
        echo "   ✅ ${BASE_BRANCH} 최신화 완료"
      else
        # 실패 시 (브랜치가 체크아웃 중이거나 dirty한 경우)
        echo "   ⚠️  ${BASE_BRANCH} 최신화 실패 - 현재 상태 유지"
        echo "      (브랜치가 현재 사용 중일 수 있습니다)"
      fi
    fi
  else
    echo "⚠️  Fetch 실패 - 계속 진행합니다."
  fi
  echo ""
fi
```

### Step 8: 브랜치 존재 확인

```bash
# ===== 브랜치 존재 확인 =====
echo "🔍 브랜치 확인: ${BRANCH_NAME}"

BRANCH_EXISTS=false
REMOTE_BRANCH=false

# ===== 브랜치가 다른 Worktree에서 사용 중인지 확인 (사전 검증) =====
if git worktree list | grep -q "$BRANCH_NAME"; then
  echo ""
  echo "❌ 브랜치가 이미 다른 Worktree에서 사용 중입니다."
  echo ""
  echo "현재 Worktree 목록:"
  git worktree list
  echo ""
  echo "해결 방법:"
  echo "  1. 다른 브랜치명 사용"
  echo "  2. 기존 Worktree 제거 후 재시도"
  echo ""
  exit 1
fi

# ===== 브랜치 존재 여부 확인 =====
if git show-ref --verify --quiet "refs/heads/${BRANCH_NAME}"; then
  echo "   ✅ 로컬 브랜치 존재"
  BRANCH_EXISTS=true
elif git show-ref --verify --quiet "refs/remotes/origin/${BRANCH_NAME}"; then
  echo "   ✅ 원격 브랜치 존재 (로컬로 체크아웃)"
  BRANCH_EXISTS=true
  REMOTE_BRANCH=true
else
  echo "   ℹ️  브랜치가 없음 - 새로 생성합니다."
  BRANCH_EXISTS=false
fi

echo ""
```

### Step 9: Dry-run Preview (선택)

```bash
# ===== Dry-run 모드 =====
if [ "$DRY_RUN" = true ]; then
  echo ""
  echo "=========================================="
  echo "📋 Worktree Preview (Dry Run)"
  echo "=========================================="
  echo ""
  echo "Issue:"
  echo "  #${ISSUE_NUMBER}: ${ISSUE_TITLE}"
  echo ""
  echo "Worktree:"
  echo "  경로: ${WORKTREE_PATH}"
  echo "  이름: ${WORKTREE_NAME}"
  echo ""
  echo "브랜치:"
  echo "  이름: ${BRANCH_NAME}"
  echo "  Base: ${BASE_BRANCH}"
  
  if [ "$BRANCH_EXISTS" = true ]; then
    echo "  상태: 기존 브랜치 사용"
  else
    echo "  상태: 새 브랜치 생성"
  fi
  
  echo ""
  echo "실행될 명령:"
  
  if [ "$BRANCH_EXISTS" = true ]; then
    if [ "$REMOTE_BRANCH" = true ]; then
      echo "  git worktree add ${WORKTREE_PATH} origin/${BRANCH_NAME}"
    else
      echo "  git worktree add ${WORKTREE_PATH} ${BRANCH_NAME}"
    fi
  else
    echo "  git worktree add -b ${BRANCH_NAME} ${WORKTREE_PATH} ${BASE_BRANCH}"
  fi
  
  echo ""
  echo "💡 실제 생성하려면 --dry-run을 제거하세요:"
  echo "   /worktree-create ${ISSUE_NUMBER}"
  echo ""
  exit 0
fi
```

### Step 10: Worktree 생성

```bash
# ===== Worktree Base 디렉토리 준비 =====
echo "📁 Worktree 디렉토리 생성 중..."

# Worktree Base 디렉토리 생성 (프로젝트 밖)
mkdir -p "$WORKTREE_BASE"

echo "   Base: ${WORKTREE_BASE}"
echo ""

# ===== Worktree 생성 =====
echo "🚀 Worktree 생성 중..."
echo ""

if [ "$BRANCH_EXISTS" = true ]; then
  # 기존 브랜치로 Worktree 생성
  if [ "$REMOTE_BRANCH" = true ]; then
    # 원격 브랜치에서 생성
    if git worktree add "$WORKTREE_PATH" "origin/${BRANCH_NAME}"; then
      CREATION_SUCCESS=true
    else
      CREATION_SUCCESS=false
    fi
  else
    # 로컬 브랜치로 생성
    if git worktree add "$WORKTREE_PATH" "$BRANCH_NAME"; then
      CREATION_SUCCESS=true
    else
      CREATION_SUCCESS=false
    fi
  fi
else
  # 새 브랜치로 Worktree 생성
  if git worktree add -b "$BRANCH_NAME" "$WORKTREE_PATH" "$BASE_BRANCH"; then
    CREATION_SUCCESS=true
  else
    CREATION_SUCCESS=false
  fi
fi

# ===== 생성 결과 확인 =====
if [ "$CREATION_SUCCESS" = true ]; then
  echo ""
  echo "=========================================="
  echo "✅ Worktree 생성 완료!"
  echo "=========================================="
  echo ""
  echo "📍 Issue #${ISSUE_NUMBER}: ${ISSUE_TITLE}"
  echo ""
  echo "📂 Worktree 경로:"
  echo "   ${WORKTREE_PATH}"
  echo ""
  echo "🌿 브랜치:"
  echo "   ${BRANCH_NAME}"
  echo ""

  # Worktree 목록 표시
  echo "📋 현재 Worktree 목록:"
  git worktree list
  echo ""

  # ===== 상대 경로 계산 =====
  CURRENT_DIR=$(pwd)
  if command -v realpath &> /dev/null; then
    REL_PATH=$(realpath --relative-to="$CURRENT_DIR" "$WORKTREE_PATH" 2>/dev/null || echo "$WORKTREE_PATH")
  else
    # realpath 없으면 간단한 계산
    REL_PATH=$(python3 -c "import os.path; print(os.path.relpath('$WORKTREE_PATH', '$CURRENT_DIR'))" 2>/dev/null || echo "$WORKTREE_PATH")
  fi

  echo "🚀 다음 단계:"
  echo ""
  echo "1. Worktree 디렉토리로 이동:"
  echo "   cd ${REL_PATH}"
  echo ""
  if [ "$REL_PATH" != "$WORKTREE_PATH" ]; then
    echo "   (절대 경로: ${WORKTREE_PATH})"
    echo ""
  fi
  echo "2. 개발 시작:"
  echo "   - TDD로 개발"
  echo "   - /commit으로 커밋"
  echo "   - /pr-create로 PR 생성"
  echo ""
  echo "3. 작업 완료 후:"
  echo "   cd ${REPO_ROOT}"
  echo "   /worktree-cleanup ${WORKTREE_NAME}"
  echo ""
  
  # 추가 팁
  echo "💡 팁:"
  echo "   - Main 작업과 병렬 진행 가능"
  echo "   - Claude Code는 각 디렉토리에서 독립 실행"
  echo "   - 긴급 수정 시 언제든 다른 Worktree 생성"
  echo ""
  
else
  # 생성 실패
  echo ""
  echo "❌ Worktree 생성 실패"
  echo ""
  echo "가능한 원인:"
  echo "  1. 브랜치가 이미 다른 Worktree에서 사용 중"
  echo "  2. 경로에 문제가 있음"
  echo "  3. Git 권한 문제"
  echo ""
  echo "확인 방법:"
  echo "  - 현재 Worktree 목록: git worktree list"
  echo "  - 경로 확인: ls -la ${REPO_ROOT}/worktree/"
  echo ""
  exit 1
fi
```

---

## Worktree 디렉토리 구조

### 생성 전

```
workspace/
└── project/
    ├── .git/
    ├── src/
    ├── docs/
    └── README.md
```

### 생성 후

```
workspace/
├── project/                ← Main 작업 디렉토리 (develop)
│   ├── .git/
│   ├── src/
│   ├── docs/
│   └── README.md
│
└── project-wt/       ← Worktree 디렉토리 (프로젝트 밖!)
    ├── issue-1/            ← Issue #1 작업
    │   ├── .git           (파일 - worktree 링크)
    │   ├── src/
    │   ├── docs/
    │   └── README.md
    └── issue-2/            ← Issue #2 작업
        ├── .git
        ├── src/
        ├── docs/
        └── README.md
```

### 왜 프로젝트 밖인가?

```
✅ 실수로 Main에 커밋 불가능
   git add . 해도 Worktree 내용 포함 안 됨

✅ .gitignore 설정 불필요
   구조적으로 분리되어 있음

✅ IDE 작업 공간 분리
   Main과 Worktree를 별도로 열 수 있음

✅ 검색 결과 깔끔
   Main에서 검색 시 Worktree 내용 안 나옴
```

### 각 Worktree는 독립적

```
project-wt/issue-1/:
- 브랜치: feature/issue-1-docker-setup
- 작업: Docker Compose 설정
- 커밋: 독립적으로 관리
- Main에 영향 없음

project-wt/issue-2/:
- 브랜치: feature/issue-2-db-schema
- 작업: PostgreSQL 스키마
- 커밋: 독립적으로 관리
- Main에 영향 없음
```

---

## 사용 시나리오

### 시나리오 1: 순차 작업 → 병렬 작업

```bash
# Main에서 Task 1.1 작업 중
cd ~/workspace/project/
/issue-create 1.1
/branch-create 1
# 개발 중...

# 긴급 버그 발견!
/issue-create 99 --priority high
/worktree-create 99 hotfix
# → ~/workspace/project-wt/hotfix 생성

# Hotfix 작업
cd ../project-wt/hotfix
# 버그 수정
/commit fix "Fix critical bug"
/pr-create

# Main 작업으로 복귀
cd ../../project/
# Task 1.1 계속 작업
```

### 시나리오 2: 여러 Task 병렬 진행

```bash
# Task 1.1 시작
cd ~/workspace/project/
/worktree-create 1
cd ../project-wt/issue-1
# 개발...

# Task 1.2 동시 시작 (CI 대기 중)
cd ../../project/
/worktree-create 2
cd ../project-wt/issue-2
# 개발...

# 두 Task를 번갈아가며 작업
cd ../issue-1  # Task 1.1
cd ../issue-2  # Task 1.2
```

### 시나리오 3: 코드 비교

```bash
# 새 구현 vs 기존 구현 비교
cd ~/workspace/project/
/worktree-create 5 new-impl
/worktree-create 5 old-impl --base main

# 두 디렉토리를 IDE로 동시 열기
code ../project-wt/new-impl
code ../project-wt/old-impl

# 비교 후 결정
```

---

## Error Handling

### Issue 번호 없음

```bash
if [[ -z "$FIRST_ARG" ]]; then
  echo "❌ Issue 번호가 필요합니다."
  exit 1
fi
```

### Issue 번호 형식 오류

```bash
if [[ ! "$FIRST_ARG" =~ ^[0-9]+$ ]]; then
  echo "❌ Issue 번호는 숫자여야 합니다."
  exit 1
fi
```

### Git 저장소 아님

```bash
if ! git rev-parse --is-inside-work-tree; then
  echo "❌ Git 저장소가 아닙니다."
  exit 1
fi
```

### Worktree 이미 존재

```bash
if [ -d "$WORKTREE_PATH" ]; then
  echo "⚠️  Worktree가 이미 존재합니다."
  echo "제거: /worktree-cleanup"
  exit 1
fi
```

### Base 브랜치 없음

```bash
if ! git show-ref --verify --quiet "refs/heads/${BASE_BRANCH}"; then
  echo "❌ Base 브랜치가 없습니다."
  exit 1
fi
```

### 브랜치 이미 사용 중

```bash
# Worktree 생성 실패 시
echo "❌ 브랜치가 이미 다른 Worktree에서 사용 중"
git worktree list
```

---

## Notes

### Worktree vs Branch 비교

| 항목 | Feature Branch | Worktree |
|------|---------------|----------|
| 작업 디렉토리 | 1개 (공유) | 여러 개 (독립) |
| 브랜치 전환 | `git checkout` | `cd` 명령 |
| 병렬 작업 | 불가 | 가능 |
| 파일 변경 | 전환 시 변경됨 | 독립적 |
| IDE 설정 | 공유 | 독립 가능 |
| 사용 난이도 | 쉬움 | 보통 |

### Worktree 사용 팁

```
✅ 장점:
- 병렬 작업 가능
- 빠른 전환 (checkout 불필요)
- 독립적인 환경
- CI/CD 대기 중 다른 작업

⚠️ 주의사항:
- 디스크 공간 더 사용
- 각 Worktree마다 node_modules 필요
- 정리 필수 (완료 후 삭제)

💡 권장:
- 긴급 수정 시
- 병렬 개발 필요 시
- 코드 비교 필요 시
```

### Claude Code와 Worktree

```
각 Worktree에서 독립 실행:
cd ~/workspace/project-wt/issue-1
claude code

→ 각 디렉토리가 독립적인 프로젝트처럼 작동
→ 설정, 의존성, 환경 모두 독립
```

### 프로젝트 밖 구조의 장점

```
✅ 실수 방지:
   Main에서 git add . 해도
   Worktree 내용이 포함되지 않음!

✅ .gitignore 불필요:
   프로젝트 밖이므로
   자동으로 Git 추적 대상 아님

✅ IDE 깔끔:
   Main 프로젝트 인덱싱 시
   Worktree 파일 제외됨

✅ 검색 깔끔:
   Main에서 grep 시
   Worktree 결과 안 나옴
```

### 정리의 중요성

```
작업 완료 후 반드시 정리:

cd ~/workspace/project/
/worktree-cleanup issue-1

이유:
- 디스크 공간 확보
- 혼란 방지
- Git 저장소 깔끔 유지

정리 후:
~/workspace/project-wt/issue-1 삭제됨
```

---

## Related Commands

- `/issue-create [task-id]` - Issue 생성
- `/branch-create [issue-number]` - 일반 브랜치 생성
- `/worktree-cleanup [name]` - Worktree 정리
- `/commit` - 커밋
- `/pr-create` - PR 생성

---

## 워크플로우 예시

### 일반 개발 (Feature Branch)

```bash
cd ~/workspace/project/
/issue-create 1.1
/branch-create 1
# 개발...
/commit
/pr-create
/pr-cleanup
```

### 병렬 개발 (Worktree)

```bash
# Task 1.1
cd ~/workspace/project/
/issue-create 1.1
/worktree-create 1
cd ../project-wt/issue-1
# 개발...
/commit
/pr-create

# Task 1.2 (병렬)
cd ../../project/
/worktree-create 2
cd ../project-wt/issue-2
# 개발...

# 정리
cd ../../project/
/worktree-cleanup issue-1
/worktree-cleanup issue-2
```

---

**병렬 작업으로 생산성 극대화!** 🚀
