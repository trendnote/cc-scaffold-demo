# Branch Create

## 🎯 역할

**Issue 기반으로 Feature 브랜치를 생성하고 자동으로 체크아웃합니다.**

### 언제 사용하나요?

```
✅ 일반 개발 (순차 작업)
   한 번에 하나의 작업만
   빠른 브랜치 전환

✅ 단순한 Task
   짧은 개발 시간
   병렬 작업 불필요

✅ 브랜치만 필요
   Worktree 오버헤드 불필요
```

### Branch vs Worktree 비교

| 항목 | Branch (이 명령) | Worktree |
|------|------------------|----------|
| 작업 디렉토리 | 1개 (공유) | 여러 개 (독립) |
| 전환 | `git checkout` | `cd` 명령 |
| 병렬 작업 | ❌ 불가 | ✅ 가능 |
| 디스크 사용 | ✅ 적음 | ⚠️ 많음 |
| 사용 난이도 | ✅ 쉬움 | ⚠️ 보통 |
| 권장 상황 | 순차 개발 | 병렬 개발 |

---

## Usage

```bash
# Issue 기반 생성
/branch-create [issue-number]

# Base 브랜치 지정
/branch-create [issue-number] --base develop

# 옵션
/branch-create 1 --dry-run           # 미리보기
/branch-create 1 --fetch             # 원격 브랜치 최신화
```

**파라미터:**
- `issue-number` - GitHub Issue 번호 (필수)
- `--base` - Base 브랜치 (기본: main)
- `--dry-run` - 미리보기만
- `--fetch` - 원격 브랜치 최신화

## Examples

```bash
# 기본 사용
/branch-create 1
# → feature/issue-1-docker-setup 생성 및 체크아웃
# (Issue #1에 레이블이 없으면 feature 타입)

# 버그 수정 (Issue에 "bug" 레이블이 있는 경우)
/branch-create 2
# → bugfix/issue-2-login-error 생성
# (레이블 기반 자동 감지)

# 긴급 수정 (Issue에 "hotfix" 레이블이 있는 경우)
/branch-create 3
# → hotfix/issue-3-security-fix 생성

# Base 브랜치 지정
/branch-create 4 --base develop
# → develop에서 분기

# 미리보기
/branch-create 1 --dry-run
# → 생성될 브랜치 확인 (타입 포함)

# 원격 최신화 후 생성
/branch-create 1 --fetch
# → git fetch 후 브랜치 생성
```

---

## Instructions for Claude

### Execution Method

Claude uses the bash tool to execute these commands step by step.

**Important Notes:**
- 현재 디렉토리에서 작업
- 브랜치 생성 후 자동 체크아웃
- 작업 중인 변경사항 확인
- GitHub Issue 정보로 브랜치명 생성

---

### Step 1: Parameter Validation & Parsing

```bash
# ===== 파라미터 초기화 =====
ISSUE_NUMBER=""
BASE_BRANCH="main"
DRY_RUN=false
DO_FETCH=false

# ===== 첫 번째 인자 확인 (Issue Number) =====
FIRST_ARG="$1"

if [[ -z "$FIRST_ARG" ]]; then
  echo "❌ Issue 번호가 필요합니다."
  echo ""
  echo "사용법:"
  echo "  /branch-create [issue-number]"
  echo "  /branch-create 1"
  echo "  /branch-create 1 --base develop"
  exit 1
fi

# ===== Issue Number 검증 =====
if [[ "$FIRST_ARG" =~ ^[0-9]+$ ]]; then
  ISSUE_NUMBER="$FIRST_ARG"
  shift
else
  echo "❌ Issue 번호는 숫자여야 합니다: ${FIRST_ARG}"
  echo "예시: /branch-create 1"
  exit 1
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

# ===== 설정 확인 =====
echo "🎯 브랜치 생성 설정"
echo "   Issue: #${ISSUE_NUMBER}"
echo "   Base Branch: ${BASE_BRANCH}"
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

# ===== Protected 브랜치 확인 (CLAUDE.md Git Safety Protocol) =====
PROTECTED_BRANCHES=("main" "master" "develop" "production")
for PROTECTED in "${PROTECTED_BRANCHES[@]}"; do
  if [ "$CURRENT_BRANCH" = "$PROTECTED" ]; then
    echo ""
    echo "❌ 보호된 브랜치에서는 직접 작업할 수 없습니다: ${CURRENT_BRANCH}"
    echo ""
    echo "이유:"
    echo "  - CLAUDE.md Git Safety Protocol 위반"
    echo "  - 프로덕션 안정성 보호"
    echo ""
    echo "해결 방법:"
    echo "  1. Feature 브랜치 생성: /branch-create [issue-number]"
    echo "  2. 임시 브랜치로 전환: git checkout -b temp-work"
    echo ""
    echo "워크플로우:"
    echo "  ${CURRENT_BRANCH} (보호됨)"
    echo "  └─ feature/issue-X (여기서 작업)"
    echo "     └─ PR 생성 후 병합"
    echo ""
    exit 1
  fi
done

echo ""
```

### Step 3: 작업 중인 변경사항 확인

```bash
# ===== Uncommitted Changes 확인 =====
if ! git diff-index --quiet HEAD -- 2>/dev/null; then
  echo "⚠️  경고: 커밋되지 않은 변경사항이 있습니다."
  echo ""
  
  # 변경된 파일 목록
  echo "변경된 파일:"
  git status --short | head -10
  
  # 10개 이상이면 표시
  CHANGES_COUNT=$(git status --short | wc -l)
  if [ "$CHANGES_COUNT" -gt 10 ]; then
    echo "... 외 $(($CHANGES_COUNT - 10))개 파일"
  fi
  
  echo ""
  echo "브랜치를 전환하면 변경사항이 손실될 수 있습니다."
  echo ""
  echo "권장 조치:"
  echo "  1. 변경사항 커밋: /commit"
  echo "  2. 변경사항 임시 저장: git stash"
  echo "  3. 변경사항 버리기: git reset --hard"
  echo ""
  echo "❌ 브랜치 생성을 중단합니다."
  exit 1
fi

echo "✅ 작업 디렉토리 깨끗함"
echo ""
```

### Step 4: Issue 정보 확인

```bash
# ===== GitHub CLI 확인 =====
if ! command -v gh &> /dev/null; then
  echo "⚠️  GitHub CLI가 없습니다."
  echo "   Issue 정보를 확인할 수 없지만 계속 진행합니다."
  echo ""
  echo "설치 방법:"
  echo "  macOS:   brew install gh"
  echo "  Linux:   https://github.com/cli/cli#installation"
  echo "  Windows: https://github.com/cli/cli#installation"
  echo ""
  ISSUE_TITLE="issue-${ISSUE_NUMBER}"
  BRANCH_TYPE="feature"  # 기본값
else
  # ===== GitHub CLI 인증 확인 =====
  if ! gh auth status &> /dev/null; then
    echo "⚠️  GitHub CLI 인증이 필요합니다."
    echo "   Issue 정보를 확인할 수 없지만 계속 진행합니다."
    echo ""
    echo "인증 방법:"
    echo "  1. 인증 시작: gh auth login"
    echo "  2. 브라우저 또는 토큰 선택"
    echo "  3. 인증 완료 후 재시도"
    echo ""
    echo "확인 방법:"
    echo "  gh auth status"
    echo ""
    ISSUE_TITLE="issue-${ISSUE_NUMBER}"
    BRANCH_TYPE="feature"  # 기본값
  else
  # ===== Issue 정보 가져오기 =====
  echo "📋 Issue 정보 확인 중..."
  
  if ISSUE_INFO=$(gh issue view "$ISSUE_NUMBER" --json title,state,labels 2>&1); then
    ISSUE_TITLE=$(echo "$ISSUE_INFO" | jq -r '.title')
    ISSUE_STATE=$(echo "$ISSUE_INFO" | jq -r '.state')
    ISSUE_LABELS=$(echo "$ISSUE_INFO" | jq -r '.labels[].name' | tr '\n' ', ' | sed 's/,$//')

    echo "   #${ISSUE_NUMBER}: ${ISSUE_TITLE}"
    echo "   State: ${ISSUE_STATE}"
    [ -n "$ISSUE_LABELS" ] && echo "   Labels: ${ISSUE_LABELS}"

    # ===== Label 기반 브랜치 타입 자동 감지 =====
    BRANCH_TYPE="feature"  # 기본값

    if echo "$ISSUE_LABELS" | grep -qi "bug\|bugfix\|fix"; then
      BRANCH_TYPE="bugfix"
      echo "   🐛 Type: Bugfix (자동 감지)"
    elif echo "$ISSUE_LABELS" | grep -qi "hotfix\|critical\|urgent"; then
      BRANCH_TYPE="hotfix"
      echo "   🔥 Type: Hotfix (자동 감지)"
    elif echo "$ISSUE_LABELS" | grep -qi "enhancement\|feature"; then
      BRANCH_TYPE="feature"
      echo "   ✨ Type: Feature (자동 감지)"
    elif echo "$ISSUE_LABELS" | grep -qi "docs\|documentation"; then
      BRANCH_TYPE="docs"
      echo "   📝 Type: Documentation (자동 감지)"
    elif echo "$ISSUE_LABELS" | grep -qi "refactor"; then
      BRANCH_TYPE="refactor"
      echo "   ♻️  Type: Refactor (자동 감지)"
    else
      echo "   ✨ Type: Feature (기본값)"
    fi

    # Issue가 닫혀있으면 경고
    if [ "$ISSUE_STATE" = "CLOSED" ]; then
      echo ""
      echo "⚠️  경고: Issue #${ISSUE_NUMBER}가 이미 닫혀있습니다."
      echo "   이미 완료된 작업일 수 있습니다."
      echo ""
    fi
  else
    echo "⚠️  Issue #${ISSUE_NUMBER}를 찾을 수 없습니다."
    echo ""
    echo "가능한 원인:"
    echo "  1. Issue가 존재하지 않음"
    echo "  2. 저장소 권한 부족"
    echo "  3. 잘못된 저장소"
    echo ""
    echo "확인 방법:"
    echo "  gh issue list | grep ${ISSUE_NUMBER}"
    echo "  gh repo view"
    echo ""
    echo "⚠️  기본 브랜치명으로 계속 진행합니다."
    ISSUE_TITLE="issue-${ISSUE_NUMBER}"
    BRANCH_TYPE="feature"  # 기본값
  fi
  echo ""
  fi
fi
```

### Step 5: 브랜치 이름 생성

```bash
# ===== 브랜치 이름 생성 =====
echo "🏷️  브랜치 이름 생성 중..."

# GitHub Issue 제목에서 slug 생성
if [ -n "$ISSUE_TITLE" ] && [ "$ISSUE_TITLE" != "issue-${ISSUE_NUMBER}" ]; then
  # Title을 slug로 변환
  # 예: "Docker Compose 설정" → "docker-compose-setup"
  # 예: "Fix login bug" → "fix-login-bug"
  SLUG=$(echo "$ISSUE_TITLE" | \
    tr '[:upper:]' '[:lower:]' | \
    sed 's/[^a-z0-9가-힣]/-/g' | \
    sed 's/--*/-/g' | \
    sed 's/^-//' | \
    sed 's/-$//' | \
    cut -c1-50)

  # 감지된 브랜치 타입 사용 (feature/bugfix/hotfix/docs/refactor)
  BRANCH_NAME="${BRANCH_TYPE}/issue-${ISSUE_NUMBER}-${SLUG}"
else
  BRANCH_NAME="${BRANCH_TYPE}/issue-${ISSUE_NUMBER}"
fi

echo "   브랜치명: ${BRANCH_NAME}"
echo "   타입: ${BRANCH_TYPE}"
echo ""
```

### Step 6: 브랜치 존재 확인

```bash
# ===== 브랜치 존재 확인 =====
echo "🔍 브랜치 확인 중..."

# 로컬 브랜치 확인
if git show-ref --verify --quiet "refs/heads/${BRANCH_NAME}"; then
  echo "⚠️  브랜치가 이미 존재합니다: ${BRANCH_NAME}"
  echo ""
  
  # 브랜치 정보 표시
  BRANCH_COMMIT=$(git rev-parse --short "${BRANCH_NAME}")
  BRANCH_TIME=$(git log -1 --format=%cd --date=relative "${BRANCH_NAME}")
  
  echo "브랜치 정보:"
  echo "  Commit: ${BRANCH_COMMIT}"
  echo "  Updated: ${BRANCH_TIME}"
  echo ""
  
  # 현재 브랜치와 같은지 확인
  if [ "$CURRENT_BRANCH" = "$BRANCH_NAME" ]; then
    echo "✅ 이미 해당 브랜치에 있습니다."
    echo ""
    echo "개발을 시작하세요:"
    echo "  - TDD로 개발"
    echo "  - /commit으로 커밋"
    echo "  - /pr-create로 PR 생성"
    exit 0
  fi
  
  echo "다음 중 선택하세요:"
  echo "  1. 기존 브랜치로 전환: git checkout ${BRANCH_NAME}"
  echo "  2. 브랜치 삭제 후 재생성: git branch -D ${BRANCH_NAME}"
  echo ""
  echo "❌ 브랜치 생성을 중단합니다."
  exit 1
fi

# 원격 브랜치 확인
if git show-ref --verify --quiet "refs/remotes/origin/${BRANCH_NAME}"; then
  echo "ℹ️  원격 브랜치가 존재합니다: origin/${BRANCH_NAME}"

  # 로컬 브랜치가 있으면 동기화 상태 확인
  if git show-ref --verify --quiet "refs/heads/${BRANCH_NAME}"; then
    # 로컬과 원격 차이 확인
    LOCAL_HASH=$(git rev-parse "${BRANCH_NAME}" 2>/dev/null)
    REMOTE_HASH=$(git rev-parse "origin/${BRANCH_NAME}" 2>/dev/null)

    if [ "$LOCAL_HASH" = "$REMOTE_HASH" ]; then
      echo "   ✅ 로컬과 원격이 동기화됨"
    else
      AHEAD=$(git rev-list --count "origin/${BRANCH_NAME}..${BRANCH_NAME}" 2>/dev/null || echo 0)
      BEHIND=$(git rev-list --count "${BRANCH_NAME}..origin/${BRANCH_NAME}" 2>/dev/null || echo 0)

      if [ "$AHEAD" -gt 0 ] && [ "$BEHIND" -gt 0 ]; then
        echo "   ⚠️  로컬과 원격이 갈라짐 (diverged)"
        echo "      로컬 ahead: ${AHEAD} commits"
        echo "      로컬 behind: ${BEHIND} commits"
        echo ""
        echo "해결 방법:"
        echo "  1. Rebase: git rebase origin/${BRANCH_NAME}"
        echo "  2. Merge: git merge origin/${BRANCH_NAME}"
        echo "  3. Force push (위험): git push -f"
      elif [ "$AHEAD" -gt 0 ]; then
        echo "   📤 로컬이 최신 (ahead ${AHEAD} commits)"
        echo "      Push 필요: git push"
      elif [ "$BEHIND" -gt 0 ]; then
        echo "   📥 원격이 최신 (behind ${BEHIND} commits)"
        echo "      Pull 필요: git pull"
      fi
    fi
  fi

  echo "   원격 브랜치를 체크아웃합니다."
  REMOTE_BRANCH=true
else
  echo "✅ 새 브랜치를 생성합니다."
  REMOTE_BRANCH=false
fi

echo ""
```

### Step 7: Base 브랜치 확인

```bash
# ===== Base 브랜치 존재 확인 =====
echo "🔍 Base 브랜치 확인: ${BASE_BRANCH}"

if ! git show-ref --verify --quiet "refs/heads/${BASE_BRANCH}"; then
  # 로컬에 없으면 원격 확인
  if git show-ref --verify --quiet "refs/remotes/origin/${BASE_BRANCH}"; then
    echo "   로컬에 없음 - 원격에서 가져옵니다."
    git branch --track "$BASE_BRANCH" "origin/$BASE_BRANCH" &> /dev/null
  else
    echo "❌ Base 브랜치가 존재하지 않습니다: ${BASE_BRANCH}"
    echo ""
    echo "사용 가능한 브랜치:"
    git branch -a | grep -E "main|master|develop" | head -10
    exit 1
  fi
fi

echo "✅ Base 브랜치 확인 완료"
echo ""
```

### Step 8: Fetch (선택)

```bash
# ===== 원격 브랜치 최신화 (--fetch 옵션) =====
if [ "$DO_FETCH" = true ]; then
  echo "📥 원격 저장소 최신화 중..."
  
  if git fetch origin &> /dev/null; then
    echo "✅ Fetch 완료"
    
    # Base 브랜치 최신화
    if git show-ref --verify --quiet "refs/heads/${BASE_BRANCH}"; then
      CURRENT_SAVED=$(git branch --show-current)
      
      echo "   ${BASE_BRANCH} 최신화 중..."
      git checkout "$BASE_BRANCH" &> /dev/null
      git pull origin "$BASE_BRANCH" &> /dev/null
      
      # 원래 브랜치로 복귀
      if [ -n "$CURRENT_SAVED" ] && [ "$CURRENT_SAVED" != "$BASE_BRANCH" ]; then
        git checkout "$CURRENT_SAVED" &> /dev/null
      fi
      
      echo "   ✅ ${BASE_BRANCH} 최신화 완료"
    fi
  else
    echo "⚠️  Fetch 실패 - 계속 진행합니다."
  fi
  echo ""
fi
```

### Step 9: Dry-run Preview (선택)

```bash
# ===== Dry-run 모드 =====
if [ "$DRY_RUN" = true ]; then
  echo ""
  echo "=========================================="
  echo "📋 브랜치 Preview (Dry Run)"
  echo "=========================================="
  echo ""
  echo "Issue:"
  echo "  #${ISSUE_NUMBER}: ${ISSUE_TITLE}"
  echo ""
  echo "브랜치:"
  echo "  이름: ${BRANCH_NAME}"
  echo "  Base: ${BASE_BRANCH}"
  
  if [ "$REMOTE_BRANCH" = true ]; then
    echo "  타입: 원격 브랜치 체크아웃"
  else
    echo "  타입: 새 브랜치 생성"
  fi
  
  echo ""
  echo "실행될 명령:"
  
  if [ "$REMOTE_BRANCH" = true ]; then
    echo "  git checkout -b ${BRANCH_NAME} origin/${BRANCH_NAME}"
  else
    echo "  git checkout -b ${BRANCH_NAME} ${BASE_BRANCH}"
  fi
  
  echo ""
  echo "💡 실제 생성하려면 --dry-run을 제거하세요:"
  echo "   /branch-create ${ISSUE_NUMBER}"
  echo ""
  exit 0
fi
```

### Step 10: 브랜치 생성 및 체크아웃

```bash
echo "🚀 브랜치 생성 중..."
echo ""

# ===== 브랜치 생성 =====
if [ "$REMOTE_BRANCH" = true ]; then
  # 원격 브랜치 체크아웃
  if git checkout -b "$BRANCH_NAME" "origin/${BRANCH_NAME}" 2>&1; then
    CREATION_SUCCESS=true
  else
    CREATION_SUCCESS=false
  fi
else
  # 새 브랜치 생성
  if git checkout -b "$BRANCH_NAME" "$BASE_BRANCH" 2>&1; then
    CREATION_SUCCESS=true
  else
    CREATION_SUCCESS=false
  fi
fi

# ===== 생성 결과 확인 =====
if [ "$CREATION_SUCCESS" = true ]; then
  # 현재 브랜치 확인
  NEW_BRANCH=$(git branch --show-current)
  CURRENT_COMMIT=$(git rev-parse --short HEAD)
  
  echo ""
  echo "=========================================="
  echo "✅ 브랜치 생성 완료!"
  echo "=========================================="
  echo ""
  echo "📍 Issue #${ISSUE_NUMBER}: ${ISSUE_TITLE}"
  echo ""
  echo "🌿 브랜치:"
  echo "   이름: ${NEW_BRANCH}"
  echo "   Base: ${BASE_BRANCH}"
  echo "   Commit: ${CURRENT_COMMIT}"
  echo ""
  
  # 브랜치 목록 (최근 5개)
  echo "📋 최근 브랜치:"
  git branch --sort=-committerdate | head -5
  echo ""
  
  echo "🚀 다음 단계:"
  echo ""
  echo "1. 개발 시작:"
  echo "   - TDD로 개발 (Red-Green-Refactor)"
  echo "   - 테스트 작성 → 구현 → 리팩토링"
  echo ""
  echo "2. 커밋:"
  echo "   /commit [type] \"메시지\""
  echo "   예: /commit feat \"Add Docker Compose\""
  echo ""
  echo "3. PR 생성:"
  echo "   /pr-create"
  echo ""
  echo "4. 완료 후 정리:"
  echo "   /pr-cleanup"
  echo ""
  
  # 추가 팁
  echo "💡 팁:"
  echo "   - Issue #${ISSUE_NUMBER} 참조하여 개발"
  echo "   - 커밋 메시지에 'Ref: #${ISSUE_NUMBER}' 자동 포함"
  echo "   - PR 생성 시 'Closes #${ISSUE_NUMBER}' 자동 포함"
  echo ""
  
else
  # 생성 실패
  echo ""
  echo "❌ 브랜치 생성 실패"
  echo ""
  echo "가능한 원인:"
  echo "  1. Base 브랜치에 문제가 있음"
  echo "  2. 브랜치명에 문제가 있음"
  echo "  3. Git 권한 문제"
  echo ""
  echo "확인 방법:"
  echo "  - 현재 브랜치: git branch"
  echo "  - Base 브랜치 확인: git log ${BASE_BRANCH} -1"
  echo "  - Git 상태: git status"
  echo ""
  exit 1
fi
```

---

## 브랜치 명명 규칙

### 표준 형식

```
{type}/issue-{number}-{slug}

예시:
feature/issue-1-docker-compose-setup
bugfix/issue-2-login-error
hotfix/issue-3-critical-security-fix
docs/issue-4-api-documentation
refactor/issue-5-database-layer
```

### 브랜치 타입 자동 감지

Issue 레이블을 기반으로 브랜치 타입이 자동으로 결정됩니다:

| Issue Label | Branch Type | 사용 예시 |
|-------------|-------------|-----------|
| `bug`, `bugfix`, `fix` | `bugfix/` | 버그 수정 |
| `hotfix`, `critical`, `urgent` | `hotfix/` | 긴급 수정 |
| `feature`, `enhancement` | `feature/` | 새 기능 |
| `docs`, `documentation` | `docs/` | 문서 작업 |
| `refactor` | `refactor/` | 리팩토링 |
| (레이블 없음) | `feature/` | 기본값 |

### Slug 생성 규칙

```
1. Issue Title → 소문자 변환
2. 특수문자 → 하이픈(-)
3. 연속 하이픈 → 단일 하이픈
4. 앞뒤 하이픈 제거
5. 최대 50자 제한

영문 예시:
"Docker Compose Setup" → "docker-compose-setup"
"Fix login bug" → "fix-login-bug"
"Add API endpoints" → "add-api-endpoints"

한글 예시:
"로그인 버그 수정" → "로그인-버그-수정"
"사용자 인증 기능 추가" → "사용자-인증-기능-추가"
"데이터베이스 스키마 설계" → "데이터베이스-스키마-설계"

혼합 예시:
"Docker Compose 설정" → "docker-compose-설정"
"Fix 로그인 버그" → "fix-로그인-버그"
```

**한글 처리:**
- 한글 문자(가-힣)는 그대로 유지됩니다
- Git 브랜치명에서 한글은 완전히 지원됩니다
- 원격 저장소(GitHub, GitLab)에서도 정상 작동합니다
- 영문으로 변환하려면 Issue 제목을 영문으로 작성하세요

---

## Error Handling

### Issue 번호 없음

```bash
if [[ -z "$FIRST_ARG" ]]; then
  echo "❌ Issue 번호가 필요합니다."
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

### 작업 중인 변경사항

```bash
if ! git diff-index --quiet HEAD --; then
  echo "⚠️  커밋되지 않은 변경사항이 있습니다."
  echo "권장: /commit 또는 git stash"
  exit 1
fi
```

### 브랜치 이미 존재

```bash
if git show-ref --verify --quiet "refs/heads/${BRANCH_NAME}"; then
  echo "⚠️  브랜치가 이미 존재합니다."
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

---

## Notes

### Branch vs Worktree 선택 가이드

**Branch 사용 (이 명령):**
```
✅ 순차 개발
   - 하나씩 작업
   - 빠른 전환

✅ 단순 작업
   - 짧은 개발
   - 병렬 불필요

✅ 리소스 절약
   - 디스크 공간
   - 의존성 설치
```

**Worktree 사용:**
```
✅ 병렬 개발
   - 여러 Task 동시
   - CI 대기 중 작업

✅ 긴급 수정
   - 작업 중 버그 발견
   - 빠른 전환 필요

✅ 코드 비교
   - 두 구현 비교
   - 독립 환경 필요
```

### 브랜치 전환 시 주의사항

```
⚠️ 변경사항 확인
   - git status로 확인
   - 커밋 또는 stash

⚠️ 의존성 변경
   - package.json 변경 시 npm install
   - requirements.txt 변경 시 pip install

⚠️ 데이터베이스
   - 마이그레이션 확인
   - DB 스키마 변경 주의
```

### 브랜치 전략

```
Git Flow 기반:
main       - 프로덕션
develop    - 개발 통합 (Base)
feature/*  - 기능 개발 (이 명령)
hotfix/*   - 긴급 수정
release/*  - 릴리스 준비
```

---

## Troubleshooting

### 문제: "GitHub CLI가 없습니다"

**증상:**
```
⚠️  GitHub CLI가 없습니다.
```

**원인:**
- GitHub CLI (gh)가 설치되지 않음

**해결 방법:**
```bash
# macOS
brew install gh

# Linux (Debian/Ubuntu)
sudo apt install gh

# Linux (Fedora/CentOS)
sudo dnf install gh

# Windows
winget install GitHub.cli
# 또는
choco install gh
```

**확인:**
```bash
gh --version
```

---

### 문제: "GitHub CLI 인증이 필요합니다"

**증상:**
```
⚠️  GitHub CLI 인증이 필요합니다.
```

**원인:**
- GitHub CLI 인증이 완료되지 않음

**해결 방법:**
```bash
# 1. 인증 시작
gh auth login

# 2. 선택사항
#    - GitHub.com 선택
#    - HTTPS 선택
#    - 브라우저 또는 토큰 선택
#    - 인증 완료

# 3. 확인
gh auth status
```

**예상 출력:**
```
✓ Logged in to github.com as [username]
```

---

### 문제: "보호된 브랜치에서는 직접 작업할 수 없습니다"

**증상:**
```
❌ 보호된 브랜치에서는 직접 작업할 수 없습니다: main
```

**원인:**
- main/master/develop 등 보호된 브랜치에서 직접 작업 시도
- CLAUDE.md Git Safety Protocol 위반

**해결 방법:**
```bash
# 1. Issue 기반 브랜치 생성 (권장)
/branch-create [issue-number]

# 2. 또는 직접 브랜치 생성
git checkout -b feature/my-work

# 3. 또는 기존 브랜치로 전환
git checkout feature/existing-branch
```

---

### 문제: "커밋되지 않은 변경사항이 있습니다"

**증상:**
```
⚠️  경고: 커밋되지 않은 변경사항이 있습니다.
```

**원인:**
- 현재 브랜치에 커밋되지 않은 변경사항 존재
- 브랜치 전환 시 변경사항 손실 위험

**해결 방법 1 (커밋):**
```bash
# 변경사항 커밋
/commit feat "작업 내용"

# 또는
git add .
git commit -m "feat: 작업 내용"
```

**해결 방법 2 (임시 저장):**
```bash
# 변경사항 임시 저장
git stash

# 브랜치 생성
/branch-create [issue-number]

# 나중에 복구
git stash pop
```

**해결 방법 3 (변경사항 버리기):**
```bash
# ⚠️ 주의: 변경사항 영구 삭제
git reset --hard
git clean -fd
```

---

### 문제: "브랜치가 이미 존재합니다"

**증상:**
```
⚠️  브랜치가 이미 존재합니다: feature/issue-1-xxx
```

**원인:**
- 동일한 브랜치가 이미 생성됨

**해결 방법 1 (기존 브랜치 사용):**
```bash
# 기존 브랜치로 전환
git checkout feature/issue-1-xxx
```

**해결 방법 2 (브랜치 삭제 후 재생성):**
```bash
# 브랜치 삭제 (병합되지 않은 경우 -D)
git branch -d feature/issue-1-xxx
# 또는
git branch -D feature/issue-1-xxx

# 브랜치 재생성
/branch-create 1
```

**해결 방법 3 (다른 브랜치명 사용):**
```bash
# 다른 Issue 번호 사용
/branch-create [다른-issue-number]
```

---

### 문제: "Base 브랜치가 존재하지 않습니다"

**증상:**
```
❌ Base 브랜치가 존재하지 않습니다: develop
```

**원인:**
- 지정한 Base 브랜치가 로컬 또는 원격에 없음

**해결 방법 1 (사용 가능한 브랜치 확인):**
```bash
# 로컬 브랜치 확인
git branch

# 원격 브랜치 확인
git branch -r

# 모든 브랜치 확인
git branch -a
```

**해결 방법 2 (Base 브랜치 변경):**
```bash
# main 브랜치 사용
/branch-create [issue-number] --base main

# 또는 master 사용
/branch-create [issue-number] --base master
```

**해결 방법 3 (원격 브랜치 가져오기):**
```bash
# 원격 브랜치 최신화
git fetch origin

# 원격 브랜치 체크아웃
git checkout -b develop origin/develop
```

---

### 문제: "Issue를 찾을 수 없습니다"

**증상:**
```
⚠️  Issue #123를 찾을 수 없습니다.
```

**원인:**
- Issue가 존재하지 않음
- 저장소 권한 부족
- 잘못된 저장소에서 실행

**해결 방법 1 (Issue 확인):**
```bash
# Issue 목록 확인
gh issue list

# 특정 Issue 확인
gh issue view 123

# 저장소 확인
gh repo view
```

**해결 방법 2 (저장소 확인):**
```bash
# 현재 저장소 확인
git remote -v

# 올바른 저장소인지 확인
gh repo view
```

**해결 방법 3 (Issue 생성):**
```bash
# Issue 생성
/issue-create [task-id]

# 또는
gh issue create --title "작업 제목" --body "작업 내용"
```

---

### 문제: "로컬과 원격이 갈라짐 (diverged)"

**증상:**
```
⚠️  로컬과 원격이 갈라짐 (diverged)
로컬 ahead: 3 commits
로컬 behind: 2 commits
```

**원인:**
- 로컬과 원격 브랜치의 커밋 히스토리가 다름
- 동일 브랜치에서 여러 곳에서 작업

**해결 방법 1 (Rebase - 권장):**
```bash
# 원격 기준으로 Rebase
git rebase origin/[branch-name]

# 충돌 해결 후
git rebase --continue

# Push (force with lease)
git push --force-with-lease
```

**해결 방법 2 (Merge):**
```bash
# 원격 변경사항 Merge
git merge origin/[branch-name]

# 충돌 해결 후
git commit

# Push
git push
```

**해결 방법 3 (로컬 변경사항 버리기):**
```bash
# ⚠️ 주의: 로컬 변경사항 영구 삭제
git reset --hard origin/[branch-name]
```

---

### 문제: "브랜치 생성 실패"

**증상:**
```
❌ 브랜치 생성 실패
```

**원인:**
- Base 브랜치 문제
- 브랜치명 문제
- Git 권한 문제

**해결 방법:**
```bash
# 1. Git 상태 확인
git status

# 2. Base 브랜치 확인
git log main -1
git log develop -1

# 3. 권한 확인
git config --list | grep user

# 4. 다시 시도
/branch-create [issue-number]

# 5. 디버깅 모드
/branch-create [issue-number] --dry-run
```

---

## Related Commands

- `/issue-create [task-id]` - Issue 생성
- `/worktree-create [issue-number]` - Worktree 생성 (병렬 작업)
- `/commit [type] "message"` - 커밋
- `/pr-create` - PR 생성
- `/pr-cleanup` - PR 병합 후 정리

---

## 워크플로우 예시

### 일반 개발 (Feature Branch)

```bash
# 1. Issue 생성
/issue-create 1.1
# → Issue #1 생성

# 2. 브랜치 생성
/branch-create 1
# → feature/issue-1-docker-setup
# → 자동 체크아웃

# 3. 개발
# TDD로 개발...

# 4. 커밋
/commit feat "Add Docker Compose setup"
# → Ref: #1 자동 포함

# 5. PR 생성
/pr-create
# → Closes #1 자동 포함

# 6. 정리
/pr-cleanup
# → 브랜치 삭제
```

### 긴급 수정 (Hotfix)

```bash
# 현재 작업 중...

# 긴급 버그 발견!
git stash  # 임시 저장

# Hotfix 브랜치
/branch-create 99 --base main
# → feature/issue-99-critical-fix

# 수정 후 PR
/commit fix "Fix critical bug"
/pr-create

# 원래 작업 복귀
git checkout feature/issue-1-docker-setup
git stash pop
```

### Base 브랜치 지정

```bash
# Develop에서 분기
/branch-create 1 --base develop

# Main에서 분기 (Hotfix)
/branch-create 99 --base main

# 특정 브랜치에서 분기
/branch-create 5 --base release/v1.0
```

---

**간단하고 빠른 브랜치 생성!** 🚀
