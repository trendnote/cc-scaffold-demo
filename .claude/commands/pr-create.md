# PR Create

## 🎯 역할

**현재 브랜치의 변경사항을 Pull Request로 생성합니다.**

### Pull Request란?

```
Pull Request (PR):
- 코드 리뷰 요청
- 변경사항 병합 제안
- 팀 협업의 핵심
- CI/CD 트리거
```

### 언제 사용하나요?

```
✅ 기능 개발 완료
   테스트 통과
   코드 리뷰 준비 완료

✅ 버그 수정 완료
   재현 확인
   수정 검증

✅ 문서 작성 완료
   가독성 확인
   정확성 검증
```

---

## Usage

```bash
# 기본 사용 (자동 감지)
/pr-create

# Draft PR 생성
/pr-create --draft

# Base 브랜치 지정
/pr-create --base develop

# 옵션
/pr-create --draft --base main
/pr-create --reviewers user1,user2
```

**파라미터:**
- `--draft` - Draft PR로 생성 (기본: ready)
- `--base` - Base 브랜치 (기본: main)
- `--reviewers` - 리뷰어 지정 (쉼표 구분)

## Examples

```bash
# 기본 PR 생성
/pr-create
# → Issue 자동 감지
# → PR 템플릿 자동 생성
# → Ready for Review

# Draft PR
/pr-create --draft
# → 작업 진행 중
# → gh pr ready로 전환

# Develop으로 병합
/pr-create --base develop

# 리뷰어 지정
/pr-create --reviewers alice,bob
```

---

## Instructions for Claude

### Execution Method

Claude uses the bash tool to execute these commands step by step.

**Important Notes:**
- 현재 브랜치의 Issue 자동 감지
- PR 템플릿 자동 생성
- Conventional Commits 형식 제목
- PR-Agent 연동 준비

---

## PR 템플릿 구조

### 표준 템플릿

```markdown
## Issue

- resolve: #[ISSUE_NUMBER]

## Why is this change needed?

[DESCRIPTION]

## What would you like reviewers to focus on?

- [FOCUS_POINT_1]
- [FOCUS_POINT_2]

## Testing Verification

[TESTING_DETAILS]

## What was done

pr_agent:summary

## Detailed Changes

pr_agent:walkthrough

## Additional Notes

[ADDITIONAL_NOTES]
```

### 섹션 설명

```
Issue:
- PR이 해결하는 Issue 번호
- "resolve: #1" → Issue #1 자동 닫힘

Why is this change needed?:
- 변경 이유 설명
- 문제 상황 및 해결 방안

What would you like reviewers to focus on?:
- 리뷰 포인트
- 중요 변경사항
- 의사결정 사항

Testing Verification:
- 테스트 방법
- 검증 결과
- 재현 방법

What was done:
- pr_agent:summary
- PR-Agent가 자동 생성

Detailed Changes:
- pr_agent:walkthrough
- PR-Agent가 자동 생성

Additional Notes:
- 추가 정보
- 향후 작업
- 알려진 이슈
```

---

### Step 1: Git Repository 확인

```bash
# ===== Git 저장소 확인 =====
if ! git rev-parse --is-inside-work-tree &> /dev/null; then
  echo "❌ Git 저장소가 아닙니다."
  echo ""
  echo "현재 위치: $(pwd)"
  exit 1
fi

# ===== 현재 브랜치 확인 =====
CURRENT_BRANCH=$(git branch --show-current)

if [ -z "$CURRENT_BRANCH" ]; then
  echo "❌ 브랜치를 확인할 수 없습니다."
  exit 1
fi

# ===== Main/Master 브랜치 확인 =====
if [[ "$CURRENT_BRANCH" =~ ^(main|master|develop)$ ]]; then
  echo "❌ ${CURRENT_BRANCH} 브랜치에서는 PR을 생성할 수 없습니다."
  echo ""
  echo "Feature 브랜치를 먼저 생성하세요:"
  echo "  /branch-create [issue-number]"
  exit 1
fi

echo "🌿 Current Branch: ${CURRENT_BRANCH}"
echo ""
```

### Step 2: Dependencies 확인

```bash
# ===== jq 확인 =====
if ! command -v jq &> /dev/null; then
  echo "❌ jq가 설치되어 있지 않습니다."
  echo ""
  echo "설치 방법:"
  echo "  macOS: brew install jq"
  echo "  Ubuntu: sudo apt-get install jq"
  echo "  Windows: winget install jqlang.jq"
  echo ""
  exit 1
fi

# ===== GitHub CLI 확인 =====
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
  exit 1
fi

echo "✅ Dependencies 확인 완료"
echo ""
```

### Step 3: 파라미터 파싱

```bash
# ===== 파라미터 초기화 =====
DRAFT_MODE=false
BASE_BRANCH="main"
REVIEWERS=""

# ===== 옵션 파싱 =====
while [[ $# -gt 0 ]]; do
  case $1 in
    --draft)
      DRAFT_MODE=true
      shift
      ;;
    --base)
      BASE_BRANCH="$2"
      shift 2
      ;;
    --reviewers)
      REVIEWERS="$2"
      shift 2
      ;;
    *)
      echo "⚠️  알 수 없는 옵션: $1"
      shift
      ;;
  esac
done

# ===== 설정 확인 =====
echo "📋 PR 생성 설정"
echo "   Branch: ${CURRENT_BRANCH}"
echo "   Base: ${BASE_BRANCH}"
[ "$DRAFT_MODE" = true ] && echo "   Mode: Draft"
[ -n "$REVIEWERS" ] && echo "   Reviewers: ${REVIEWERS}"
echo ""
```

### Step 4: 커밋 확인

```bash
# ===== 커밋 존재 확인 =====
if ! git log -1 &> /dev/null; then
  echo "❌ 커밋이 없습니다."
  echo ""
  echo "먼저 커밋을 생성하세요:"
  echo "  /commit [type] \"message\""
  exit 1
fi

# ===== Base 브랜치 존재 확인 =====
if ! git rev-parse --verify "origin/${BASE_BRANCH}" &> /dev/null 2>&1; then
  echo "❌ Base 브랜치 'origin/${BASE_BRANCH}'가 존재하지 않습니다."
  echo ""
  echo "사용 가능한 브랜치:"
  git branch -r | grep -v HEAD
  exit 1
fi

# ===== 커밋 차이 확인 =====
COMMIT_COUNT=$(git rev-list --count "origin/${BASE_BRANCH}..HEAD")

if [ "$COMMIT_COUNT" -eq 0 ]; then
  echo "❌ Base 브랜치(${BASE_BRANCH})와 차이가 없습니다."
  echo ""
  echo "현재 브랜치에 새로운 커밋이 필요합니다."
  echo ""
  echo "확인:"
  echo "  git log origin/${BASE_BRANCH}..HEAD"
  exit 1
fi

echo "✅ ${COMMIT_COUNT}개의 새로운 커밋 확인"
echo ""

# ===== Push 확인 =====
if ! git rev-parse --verify "origin/${CURRENT_BRANCH}" &> /dev/null 2>&1; then
  echo "⚠️  원격 브랜치가 없습니다."
  echo ""
  echo "브랜치를 Push하는 중..."
  
  if git push -u origin "$CURRENT_BRANCH"; then
    echo "✅ Push 완료"
  else
    echo "❌ Push 실패"
    exit 1
  fi
  echo ""
fi

# ===== 최신 상태 확인 =====
LOCAL_COMMIT=$(git rev-parse HEAD)
REMOTE_COMMIT=$(git rev-parse "origin/${CURRENT_BRANCH}")

if [ "$LOCAL_COMMIT" != "$REMOTE_COMMIT" ]; then
  echo "⚠️  로컬 커밋이 원격과 다릅니다."
  echo ""
  echo "Push하는 중..."
  
  if git push; then
    echo "✅ Push 완료"
  else
    echo "❌ Push 실패"
    exit 1
  fi
  echo ""
fi

echo "✅ 브랜치가 최신 상태입니다."
echo ""
```

### Step 5: Issue 번호 추출

```bash
# ===== Issue 번호 추출 =====
echo "🔍 Issue 번호 추출 중..."

# 브랜치명에서 Issue 번호 추출
# 예: feature/issue-1-docker-setup → 1
if [[ "$CURRENT_BRANCH" =~ issue-([0-9]+) ]]; then
  ISSUE_NUMBER="${BASH_REMATCH[1]}"
  echo "   Issue #${ISSUE_NUMBER} (브랜치명에서 추출)"
elif [[ "$CURRENT_BRANCH" =~ ([0-9]+)- ]]; then
  # 예: feature/1-docker-setup → 1
  ISSUE_NUMBER="${BASH_REMATCH[1]}"
  echo "   Issue #${ISSUE_NUMBER} (브랜치명에서 추출)"
else
  echo "   ℹ️  브랜치명에 Issue 번호가 없습니다."
  ISSUE_NUMBER=""
fi

echo ""
```

### Step 6: Issue 정보 확인

```bash
# ===== Issue 정보 확인 =====
if [ -n "$ISSUE_NUMBER" ]; then
  echo "📋 Issue 정보 확인 중..."
  
  if ISSUE_INFO=$(gh issue view "$ISSUE_NUMBER" --json title,labels,body 2>&1); then
    ISSUE_TITLE=$(echo "$ISSUE_INFO" | jq -r '.title')
    ISSUE_LABELS=$(echo "$ISSUE_INFO" | jq -r '.labels[].name' | tr '\n' ', ' | sed 's/,$//')
    ISSUE_BODY=$(echo "$ISSUE_INFO" | jq -r '.body')
    
    echo "   #${ISSUE_NUMBER}: ${ISSUE_TITLE}"
    [ -n "$ISSUE_LABELS" ] && echo "   Labels: ${ISSUE_LABELS}"
  else
    echo "   ⚠️  Issue #${ISSUE_NUMBER}를 찾을 수 없습니다."
    ISSUE_TITLE=""
    ISSUE_LABELS=""
    ISSUE_BODY=""
  fi
  echo ""
fi
```

### Step 7: PR 제목 생성

```bash
# ===== PR 제목 생성 =====
echo "📝 PR 제목 생성 중..."

# 브랜치 타입에서 emoji 추출 (우선순위 높음)
BRANCH_TYPE=$(echo "$CURRENT_BRANCH" | cut -d'/' -f1)
PR_TYPE=""
PR_EMOJI=""

case "$BRANCH_TYPE" in
  feature)
    PR_TYPE="feat"
    PR_EMOJI="✨"
    ;;
  bugfix|fix)
    PR_TYPE="fix"
    PR_EMOJI="🐛"
    ;;
  hotfix)
    PR_TYPE="fix"
    PR_EMOJI="🚑"
    ;;
  docs)
    PR_TYPE="docs"
    PR_EMOJI="📝"
    ;;
  refactor)
    PR_TYPE="refactor"
    PR_EMOJI="♻️"
    ;;
  perf|performance)
    PR_TYPE="perf"
    PR_EMOJI="⚡"
    ;;
  test)
    PR_TYPE="test"
    PR_EMOJI="✅"
    ;;
  chore)
    PR_TYPE="chore"
    PR_EMOJI="🔧"
    ;;
  style)
    PR_TYPE="style"
    PR_EMOJI="💄"
    ;;
  *)
    # Issue 라벨에서 타입 추출 (폴백)
    PR_TYPE="feat"
    PR_EMOJI="✨"

    if [ -n "$ISSUE_LABELS" ]; then
      if echo "$ISSUE_LABELS" | grep -qi "bug"; then
        PR_TYPE="fix"
        PR_EMOJI="🐛"
      elif echo "$ISSUE_LABELS" | grep -qi "refactor"; then
        PR_TYPE="refactor"
        PR_EMOJI="♻️"
      elif echo "$ISSUE_LABELS" | grep -qi "docs"; then
        PR_TYPE="docs"
        PR_EMOJI="📝"
      elif echo "$ISSUE_LABELS" | grep -qi "test"; then
        PR_TYPE="test"
        PR_EMOJI="✅"
      elif echo "$ISSUE_LABELS" | grep -qi "feature"; then
        PR_TYPE="feat"
        PR_EMOJI="✨"
      fi
    fi
    ;;
esac

# Scope 추출 (브랜치명 또는 Issue 제목에서)
PR_SCOPE=""
if [ -n "$ISSUE_TITLE" ]; then
  # Issue 제목의 첫 단어를 scope로 사용
  PR_SCOPE=$(echo "$ISSUE_TITLE" | awk '{print tolower($1)}' | sed 's/[^a-z0-9-]//g')
fi

# PR 제목 생성
if [ -n "$ISSUE_TITLE" ]; then
  if [ -n "$PR_SCOPE" ]; then
    PR_TITLE="${PR_EMOJI}(${PR_SCOPE}): ${ISSUE_TITLE}"
  else
    PR_TITLE="${PR_EMOJI}: ${ISSUE_TITLE}"
  fi
else
  # Issue 정보가 없으면 브랜치명 사용
  BRANCH_DESC=$(echo "$CURRENT_BRANCH" | sed 's/^[^/]*\///' | sed 's/-/ /g')
  PR_TITLE="${PR_EMOJI}: ${BRANCH_DESC}"
fi

echo "   ${PR_TITLE}"
echo ""
```

### Step 8: PR 본문 생성

```bash
# ===== PR 본문 생성 =====
echo "📝 PR 본문 생성 중..."
echo ""

# ===== 커밋 정보 수집 =====
COMMIT_MESSAGES=$(git log "origin/${BASE_BRANCH}..HEAD" --pretty=format:"- %s" | head -20)
COMMIT_DETAILS=$(git log "origin/${BASE_BRANCH}..HEAD" --pretty=format:"%h - %s (%an)" | head -10)

# ===== 파일 변경사항 수집 =====
CHANGED_FILES=$(git diff --name-only "origin/${BASE_BRANCH}..HEAD")
CHANGED_FILES_COUNT=$(echo "$CHANGED_FILES" | wc -l | tr -d ' ')
FILE_STATS=$(git diff --stat "origin/${BASE_BRANCH}..HEAD" | tail -1)

# ===== 주요 변경 파일 (상위 10개) =====
TOP_CHANGED_FILES=$(git diff --stat "origin/${BASE_BRANCH}..HEAD" | head -10 | sed 's/^/- /')

# ===== Issue 관련 정보 추출 =====
ISSUE_SECTION=""
if [ -n "$ISSUE_NUMBER" ]; then
  ISSUE_SECTION="- resolve: #${ISSUE_NUMBER}"
else
  ISSUE_SECTION="- N/A"
fi

# ===== Why is this change needed? 생성 =====
WHY_SECTION=""
if [ -n "$ISSUE_BODY" ]; then
  # Issue body의 첫 3줄 사용
  WHY_SECTION=$(echo "$ISSUE_BODY" | head -3)
else
  WHY_SECTION="This PR includes ${COMMIT_COUNT} commit(s) with the following changes:

${COMMIT_MESSAGES}

Please refer to the commit messages and code changes for details."
fi

# ===== 리뷰 포인트 자동 생성 =====
REVIEW_FOCUS=""

# 파일 타입별 분석
if echo "$CHANGED_FILES" | grep -q "\.sql$\|migration\|alembic"; then
  REVIEW_FOCUS="${REVIEW_FOCUS}- Database schema changes and migration scripts
"
fi

if echo "$CHANGED_FILES" | grep -q "\.env\|config\|settings"; then
  REVIEW_FOCUS="${REVIEW_FOCUS}- Configuration changes and environment variables
"
fi

if echo "$CHANGED_FILES" | grep -q "test_\|\.test\.\|spec\."; then
  REVIEW_FOCUS="${REVIEW_FOCUS}- Test coverage and test cases
"
fi

if echo "$CHANGED_FILES" | grep -q "requirements\.txt\|package\.json\|go\.mod"; then
  REVIEW_FOCUS="${REVIEW_FOCUS}- Dependency updates and compatibility
"
fi

if echo "$CHANGED_FILES" | grep -q "Dockerfile\|docker-compose\|\.yaml$"; then
  REVIEW_FOCUS="${REVIEW_FOCUS}- Docker and infrastructure configuration
"
fi

# 기본 리뷰 포인트
if [ -z "$REVIEW_FOCUS" ]; then
  REVIEW_FOCUS="- Code quality and best practices
- Error handling and edge cases
- Performance implications"
else
  REVIEW_FOCUS="${REVIEW_FOCUS}- Overall code quality and implementation approach"
fi

# ===== 테스트 섹션 생성 =====
TESTING_SECTION=""

if echo "$CHANGED_FILES" | grep -q "test_\|\.test\.\|spec\."; then
  TEST_FILES=$(echo "$CHANGED_FILES" | grep "test_\|\.test\.\|spec\." | sed 's/^/- /')
  TESTING_SECTION="### Tests Added/Updated:
${TEST_FILES}

### Manual Testing:
- [ ] Verified on local development environment
- [ ] Tested happy path scenarios
- [ ] Tested error cases"
else
  TESTING_SECTION="- [ ] Manual testing completed
- [ ] Verified on local development environment
- [ ] No automated tests added (consider adding if applicable)"
fi

# ===== PR 본문 생성 =====
cat > /tmp/pr_body.md << EOF
## Issue

${ISSUE_SECTION}

## Why is this change needed?

${WHY_SECTION}

## What would you like reviewers to focus on?

${REVIEW_FOCUS}

## Testing Verification

${TESTING_SECTION}

## What was done

pr_agent:summary

## Detailed Changes

pr_agent:walkthrough

## Additional Notes

**Commits (${COMMIT_COUNT}):**
${COMMIT_DETAILS}

**Files Changed (${CHANGED_FILES_COUNT}):**
${TOP_CHANGED_FILES}

**Stats:** ${FILE_STATS}

---
🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF

echo "✅ PR 본문 생성 완료"
echo ""
```

### Step 9: PR 생성

```bash
# ===== PR 본문 파일 사용 =====
PR_BODY_FILE="/tmp/pr_body.md"

# ===== PR 생성 옵션 설정 =====
PR_OPTIONS=(
  "--title" "$PR_TITLE"
  "--body-file" "$PR_BODY_FILE"
  "--base" "$BASE_BRANCH"
)

# Draft 모드
if [ "$DRAFT_MODE" = true ]; then
  PR_OPTIONS+=("--draft")
fi

# Reviewers
if [ -n "$REVIEWERS" ]; then
  PR_OPTIONS+=("--reviewer" "$REVIEWERS")
fi

# ===== PR 생성 실행 =====
echo "🚀 Pull Request 생성 중..."
echo ""

if PR_URL=$(gh pr create "${PR_OPTIONS[@]}" 2>&1); then
  # PR 번호 추출
  PR_NUMBER=$(echo "$PR_URL" | grep -oE '[0-9]+$')
  
  echo ""
  echo "=========================================="
  echo "✅ Pull Request 생성 완료!"
  echo "=========================================="
  echo ""
  echo "📌 PR #${PR_NUMBER}"
  echo "🔗 ${PR_URL}"
  echo ""
  echo "📋 정보:"
  echo "   제목: ${PR_TITLE}"
  [ -n "$ISSUE_NUMBER" ] && echo "   Issue: #${ISSUE_NUMBER}"
  echo "   Base: ${BASE_BRANCH}"
  echo "   Branch: ${CURRENT_BRANCH}"
  [ "$DRAFT_MODE" = true ] && echo "   상태: Draft"
  [ -n "$REVIEWERS" ] && echo "   Reviewers: ${REVIEWERS}"
  echo ""
  
  echo "🎯 다음 단계:"
  echo ""
  
  if [ "$DRAFT_MODE" = true ]; then
    echo "1. 추가 작업 완료"
    echo "   - 코드 정리"
    echo "   - 테스트 추가"
    echo "   - 문서 업데이트"
    echo ""
    echo "2. Ready for Review로 전환:"
    echo "   gh pr ready ${PR_NUMBER}"
    echo ""
    echo "3. 리뷰 요청:"
    echo "   gh pr edit ${PR_NUMBER} --add-reviewer user1,user2"
  else
    echo "1. 코드 리뷰 대기"
    echo "   - PR-Agent 자동 분석 확인"
    echo "   - 리뷰어 피드백 대응"
    echo ""
    echo "2. 승인 후 병합:"
    echo "   gh pr merge ${PR_NUMBER} --squash"
    echo ""
    echo "3. 정리:"
    echo "   /pr-cleanup"
  fi
  echo ""
  
  # 임시 파일 삭제
  rm -f "$PR_BODY_FILE"
  
else
  # PR 생성 실패
  echo ""
  echo "❌ Pull Request 생성 실패"
  echo ""
  
  # 에러 분석
  if echo "$PR_URL" | grep -q "already exists"; then
    echo "원인: PR이 이미 존재합니다."
    echo ""
    echo "확인 방법:"
    echo "  gh pr list --head ${CURRENT_BRANCH}"
    
  elif echo "$PR_URL" | grep -q "No commits"; then
    echo "원인: Base 브랜치와 차이가 없습니다."
    echo ""
    echo "확인 방법:"
    echo "  git log origin/${BASE_BRANCH}..HEAD"
    
  elif echo "$PR_URL" | grep -q "authentication"; then
    echo "원인: GitHub 인증 실패"
    echo ""
    echo "해결 방법:"
    echo "  gh auth login"
    
  else
    echo "원인: 알 수 없는 오류"
    echo ""
    echo "상세 에러:"
    echo "$PR_URL"
  fi
  
  echo ""
  
  # 임시 파일 삭제
  rm -f "$PR_BODY_FILE"
  
  exit 1
fi
```

---

## PR 제목 규칙

### Conventional Commits + Emoji

```
형식:
[emoji](scope): description

예시:
✨(api): Add user authentication endpoints
🐛(auth): Fix token expiration issue
🔧(db): Refactor database connection pool
📝(readme): Update installation guide
🧪(test): Add integration tests for API
```

### Emoji 가이드

| Emoji | Type | 설명 |
|-------|------|------|
| ✨ | feat | 새 기능 |
| 🐛 | fix | 버그 수정 |
| 🔧 | refactor | 리팩토링 |
| 📝 | docs | 문서 |
| 🧪 | test | 테스트 |
| 🎨 | style | 스타일 |
| ⚡ | perf | 성능 |
| 🔒 | security | 보안 |

### Scope 가이드

```
기능별:
- api: API 엔드포인트
- auth: 인증/인가
- db: 데이터베이스
- ui: 사용자 인터페이스
- config: 설정

파일별:
- readme: README
- docker: Docker 관련
- ci: CI/CD
```

---

## PR 본문 예시

### 완성된 PR 본문

```markdown
## Issue

- resolve: #1

## Why is this change needed?

This change implements the Docker Compose setup for local development environment. 
Currently, developers need to manually install and configure PostgreSQL, Redis, 
and Milvus, which leads to inconsistent development environments and setup issues.

With Docker Compose, all services can be started with a single command, ensuring 
consistent environments across the team.

## What would you like reviewers to focus on?

- PostgreSQL configuration and volume mounting strategy
- Redis persistence settings
- Milvus vector database initialization
- Environment variable management in .env.example
- Health check configurations for all services

## Testing Verification

- ✅ All services start successfully with `docker-compose up`
- ✅ PostgreSQL accepts connections and creates test database
- ✅ Redis persists data after container restart
- ✅ Milvus collection creation works correctly
- ✅ Health checks pass for all services
- ✅ Tested on macOS and Linux environments

Manual testing steps:
1. `docker-compose up -d`
2. Verify all services: `docker-compose ps`
3. Test database connection: `psql -h localhost -U postgres`
4. Test Redis: `redis-cli ping`

## What was done

pr_agent:summary

## Detailed Changes

pr_agent:walkthrough

## Additional Notes

**Breaking Changes:** None

**Migration Steps:** 
- Copy `.env.example` to `.env`
- Update database credentials if needed

**Future Improvements:**
- Add pgAdmin for database management
- Consider adding development seed data
- Explore docker-compose profiles for different environments
```

---

## Error Handling

### GitHub CLI 없음

```bash
if ! command -v gh; then
  echo "❌ GitHub CLI 미설치"
  echo "설치: brew install gh"
  exit 1
fi
```

### 인증 실패

```bash
if ! gh auth status; then
  echo "❌ GitHub 인증 필요"
  echo "인증: gh auth login"
  exit 1
fi
```

### Main 브랜치에서 실행

```bash
if [ "$CURRENT_BRANCH" = "main" ]; then
  echo "❌ Main에서 PR 불가"
  echo "Feature 브랜치 필요"
  exit 1
fi
```

### 커밋 없음

```bash
if ! git log -1; then
  echo "❌ 커밋이 없습니다"
  exit 1
fi
```

### PR 이미 존재

```bash
if gh pr list --head "$CURRENT_BRANCH" | grep -q .; then
  echo "⚠️  PR이 이미 존재합니다"
  gh pr list --head "$CURRENT_BRANCH"
  exit 1
fi
```

---

## Notes

### PR-Agent 통합

```
PR 본문의 특수 태그:
- pr_agent:summary
- pr_agent:walkthrough

→ PR-Agent가 자동으로:
  - 요약 생성
  - 상세 변경사항 분석
  - 코드 리뷰 포인트 제시
```

### Draft vs Ready

```
Draft PR:
✅ 작업 진행 중
✅ 피드백 받기
✅ CI 테스트
❌ 병합 불가

Ready for Review:
✅ 작업 완료
✅ 리뷰 요청
✅ 병합 가능
```

### Base 브랜치 선택

```
main:
- 프로덕션 배포
- Hotfix
- 안정 버전

develop:
- 기능 개발 (기본)
- 통합 테스트
- 다음 릴리스

release/*:
- 릴리스 준비
- 버전 정리
```

---

## Related Commands

- `/branch-create [issue-number]` - 브랜치 생성
- `/commit [type] "message"` - 커밋
- `/pr-cleanup` - PR 병합 후 정리
- `gh pr ready [number]` - Draft → Ready
- `gh pr merge [number]` - PR 병합

---

## 워크플로우 예시

### 일반 개발

```bash
# 1. Issue 생성
/issue-create 1.1

# 2. 브랜치 생성
/branch-create 1

# 3. 개발
# TDD로 개발...

# 4. 커밋
/commit feat "Add feature"

# 5. PR 생성
/pr-create
# → Issue #1 자동 링크
# → PR 템플릿 자동 생성
# → Ready for Review

# 6. 리뷰 & 병합
# ...

# 7. 정리
/pr-cleanup
```

### Draft 워크플로우

```bash
# 1. Draft PR 생성 (작업 중)
/pr-create --draft

# 2. CI 확인 & 추가 작업

# 3. Ready로 전환
gh pr ready [PR_NUMBER]

# 4. 리뷰어 추가
gh pr edit [PR_NUMBER] --add-reviewer alice,bob

# 5. 리뷰 & 병합

# 6. 정리
/pr-cleanup
```

### Hotfix 워크플로우

```bash
# 1. Main에서 Hotfix 브랜치
/branch-create 99 --base main

# 2. 버그 수정

# 3. 커밋
/commit fix "Fix critical bug"

# 4. Main으로 PR
/pr-create --base main

# 5. 긴급 병합

# 6. Develop에도 반영
git checkout develop
git cherry-pick [COMMIT]
```

---

**자동화된 PR 생성으로 효율적인 협업!** 🚀
