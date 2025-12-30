# Git Init

프로젝트의 Git 저장소를 초기화하고 기본 설정을 자동으로 구성합니다.

## 역할

- Git 저장소 초기화
- .gitignore 생성 (프로젝트 타입별)
- .gitattributes 생성
- 원격 저장소 연결
- 초기 README 생성
- 첫 커밋 및 푸시

## Usage

```bash
/git-init
/git-init [project-type]
/git-init [project-type] --skip-remote
```

**프로젝트 타입:**
- `python` - Python 프로젝트
- `nodejs` - Node.js 프로젝트
- `fullstack` - Python + Node.js (기본값)

**옵션:**
- `--skip-remote` - 원격 저장소 연결 건너뛰기

## Examples

```bash
# 기본 (fullstack, 원격 저장소 연결)
/git-init

# Python 프로젝트
/git-init python

# 원격 저장소 연결 건너뛰기
/git-init fullstack --skip-remote
```

## Instructions for Claude

### Important Notes

**대화형 입력 제한:**
- Claude Code의 bash 툴은 `read` 같은 대화형 입력을 지원하지 않습니다
- 대신 Claude가 사용자에게 직접 질문하고 답변을 받아 실행합니다
- 모든 사용자 확인은 Claude의 대화를 통해 처리합니다

**실행 방식:**
1. Claude가 현재 상태 확인
2. 사용자에게 확인 질문 (필요 시)
3. 사용자 답변에 따라 bash 명령 실행
4. 에러 발생 시 롤백 방법 안내

### Step 1: 현재 상태 확인

```bash
# Git 설치 확인
if ! command -v git &> /dev/null; then
  echo "❌ Git이 설치되어 있지 않습니다."
  echo ""
  echo "설치 방법:"
  echo "  macOS: brew install git"
  echo "  Ubuntu: sudo apt-get install git"
  exit 1
fi

# Git 저장소 여부 확인
if [ -d ".git" ]; then
  echo "⚠️  경고: 이미 Git 저장소가 초기화되어 있습니다."
  echo ""
  echo "기존 Git 히스토리:"
  git log --oneline -5 2>/dev/null || echo "  (빈 저장소)"
  echo ""
  # ⚠️ 여기서 중단하고 Claude가 사용자에게 물어봄
  # "기존 Git 저장소가 있습니다. 계속 진행하시겠습니까?"
  exit 1
fi

# Git 사용자 정보 확인
GIT_USER=$(git config user.name)
GIT_EMAIL=$(git config user.email)

if [ -z "$GIT_USER" ] || [ -z "$GIT_EMAIL" ]; then
  echo "❌ Git 사용자 정보가 설정되지 않았습니다."
  echo ""
  echo "다음 명령어로 설정하세요:"
  echo "  git config --global user.name \"Your Name\""
  echo "  git config --global user.email \"your@email.com\""
  exit 1
fi

echo "✅ Git 설치 확인: $(git --version)"
echo "✅ Git 사용자: ${GIT_USER} <${GIT_EMAIL}>"

# GitHub CLI 확인 (선택사항)
if ! command -v gh &> /dev/null; then
  echo "ℹ️  GitHub CLI가 설치되어 있지 않습니다."
  echo "   원격 저장소 연결을 위해 설치를 권장합니다."
fi
```

**Claude의 처리:**
- 기존 `.git`이 있으면 사용자에게 확인 요청
- 사용자가 "yes"면 다음 단계 진행
- 사용자가 "no"면 중단

### Step 2: 프로젝트 타입 및 옵션 확인

```bash
PROJECT_TYPE="${1:-fullstack}"
SKIP_REMOTE=false

# 인자 파싱
for arg in "$@"; do
  case $arg in
    --skip-remote)
      SKIP_REMOTE=true
      shift
      ;;
    python|nodejs|fullstack)
      PROJECT_TYPE=$arg
      shift
      ;;
  esac
done

echo ""
echo "🚀 Git 저장소 초기화"
echo ""
echo "프로젝트 타입: ${PROJECT_TYPE}"
echo "원격 저장소 연결: $([ "$SKIP_REMOTE" = true ] && echo "건너뛰기" || echo "진행")"
echo ""
```

### Step 3: Git 초기화

```bash
# Git 초기화
if [ ! -d ".git" ]; then
  if git init; then
    echo "✅ Git 저장소 초기화"
  else
    echo "❌ Git 초기화 실패"
    exit 1
  fi
else
  echo "ℹ️  기존 Git 저장소 사용"
fi
```

### Step 4: .gitignore 생성

```bash
# .gitignore 생성
if [ "$PROJECT_TYPE" = "python" ]; then
  cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual Environment
venv/
env/
ENV/
.venv
env.bak/
venv.bak/

# Environment Variables
.env
.env.local
.env.*.local
*.env

# IDE
.vscode/
.idea/
*.swp
*.swo
*~
.project
.pydevproject

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Logs
*.log
logs/
pip-log.txt

# Testing
.coverage
htmlcov/
.pytest_cache/
.tox/
.hypothesis/
.nox/
coverage.xml
*.cover

# Database
*.db
*.sqlite
*.sqlite3

# Jupyter
.ipynb_checkpoints
*.ipynb

# mypy
.mypy_cache/
.dmypy.json
dmypy.json

# Pyre
.pyre/

# pytype
.pytype/

# Claude Code (로컬 설정만)
.claude/local/
settings.local.json

# Docker
docker-compose.override.yml

# Temporary
temp/
tmp/
*.tmp
EOF

elif [ "$PROJECT_TYPE" = "nodejs" ]; then
  cat > .gitignore << 'EOF'
# Node
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
lerna-debug.log*
.npm
.yarn-integrity
.pnp.*
.yarn/*
!.yarn/patches
!.yarn/plugins
!.yarn/releases
!.yarn/sdks
!.yarn/versions

# Build
dist/
build/
.next/
out/
.nuxt/
.cache/
.parcel-cache/

# Environment Variables
.env
.env.local
.env.development.local
.env.test.local
.env.production.local
.env.*.local
*.env

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Logs
*.log
logs/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Testing
coverage/
.nyc_output/
.jest/

# Database
*.db
*.sqlite
*.sqlite3

# Claude Code (로컬 설정만)
.claude/local/
settings.local.json

# Docker
docker-compose.override.yml

# Temporary
temp/
tmp/
*.tmp
EOF

else  # fullstack
  cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
.venv/
venv/
*.egg-info/
.pytest_cache/

# Node
node_modules/
npm-debug.log*
.next/
dist/
build/
.cache/

# Environment Variables
.env
.env.local
.env.*.local
*.env

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Logs
*.log
logs/

# Testing
.coverage
htmlcov/
coverage/

# Database
*.db
*.sqlite
*.sqlite3

# Claude Code (로컬 설정만)
.claude/local/
settings.local.json

# Docker
docker-compose.override.yml

# Temporary
temp/
tmp/
*.tmp
.cache/

# Misc
.DS_Store
EOF
fi

echo "✅ .gitignore 생성 (${PROJECT_TYPE})"
```

### Step 5: .gitattributes 생성

```bash
cat > .gitattributes << 'EOF'
# Auto detect text files and perform LF normalization
* text=auto

# Text files - normalize line endings to LF
*.py text eol=lf
*.js text eol=lf
*.jsx text eol=lf
*.ts text eol=lf
*.tsx text eol=lf
*.json text eol=lf
*.md text eol=lf
*.yml text eol=lf
*.yaml text eol=lf
*.sh text eol=lf
*.bash text eol=lf
*.html text eol=lf
*.css text eol=lf
*.scss text eol=lf

# Configuration files
.gitignore text eol=lf
.gitattributes text eol=lf
Dockerfile text eol=lf
Makefile text eol=lf
*.toml text eol=lf
*.ini text eol=lf

# Binary files
*.png binary
*.jpg binary
*.jpeg binary
*.gif binary
*.ico binary
*.pdf binary
*.zip binary
*.gz binary
*.tar binary
*.woff binary
*.woff2 binary
*.ttf binary
*.eot binary
*.otf binary
*.pyc binary
*.pyo binary
*.db binary
*.sqlite binary
*.sqlite3 binary
EOF

echo "✅ .gitattributes 생성"
```

### Step 6: README 생성 (없는 경우)

```bash
if [ ! -f "README.md" ]; then
  PROJECT_NAME=$(basename "$(pwd)")
  
  cat > README.md << EOF
# ${PROJECT_NAME}

## 프로젝트 개요

<!-- 프로젝트 설명을 작성하세요 -->

## 기술 스택

<!-- 사용 기술을 나열하세요 -->

## 시작하기

### Prerequisites

\`\`\`bash
# 필요한 도구들
\`\`\`

### 설치

\`\`\`bash
# 설치 명령어
\`\`\`

### 실행

\`\`\`bash
# 실행 명령어
\`\`\`

## 개발

### 브랜치 전략

- \`main\` - Production
- \`develop\` - Integration

### 개발 워크플로우

\`\`\`bash
/issue-create → /branch-create → 개발 → /commit → /pr-create → /pr-cleanup
\`\`\`

## 라이선스

<!-- 라이선스 정보 -->
EOF

  echo "✅ README.md 생성"
else
  echo "ℹ️  README.md 이미 존재 (건너뜀)"
fi
```

### Step 7: 기존 .DS_Store 등 제거

```bash
# .gitignore에 있는 파일들 중 이미 존재하는 것 제거
echo ""
echo "🧹 불필요한 파일 정리 중..."

# .DS_Store 제거 (macOS)
find . -name ".DS_Store" -type f -delete 2>/dev/null && \
  echo "  - .DS_Store 파일 제거" || true

# __pycache__ 제거 (Python)
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null && \
  echo "  - __pycache__ 디렉토리 제거" || true

# node_modules 경고 (용량 큰 경우)
if [ -d "node_modules" ]; then
  echo "  ⚠️  node_modules 폴더가 있습니다 (.gitignore에 포함됨)"
fi

echo "✅ 파일 정리 완료"
```

### Step 8: 초기 커밋

```bash
echo ""
echo "📦 초기 커밋 준비 중..."

# Git에 추가할 파일 확인
git add .gitignore .gitattributes README.md

# CLAUDE.md가 있으면 추가
[ -f "CLAUDE.md" ] && git add CLAUDE.md && echo "  - CLAUDE.md 추가"

# docs/ 폴더가 있으면 추가
if [ -d "docs" ]; then
  git add docs/
  echo "  - docs/ 추가"
fi

# .claude/ 폴더가 있으면 추가 (local/ 제외)
if [ -d ".claude" ]; then
  git add .claude/
  echo "  - .claude/ 추가"
fi

# 추가된 파일 확인
echo ""
echo "추가될 파일:"
git diff --cached --name-only | sed 's/^/  - /'
echo ""

# 초기 커밋 (에러 처리 포함)
if git commit -m "chore: Initial commit

- Git 저장소 초기화
- .gitignore 추가 (${PROJECT_TYPE})
- .gitattributes 추가
- README.md 추가"; then
  echo "✅ 초기 커밋 완료"
else
  echo "❌ 커밋 실패"
  echo ""
  echo "롤백 방법:"
  echo "  rm -rf .git"
  echo ""
  echo "상태 확인:"
  echo "  git status"
  exit 1
fi
```

### Step 9: 원격 저장소 연결

```bash
# --skip-remote 옵션이 있으면 건너뛰기
if [ "$SKIP_REMOTE" = true ]; then
  echo ""
  echo "ℹ️  원격 저장소 연결 건너뛰기 (--skip-remote)"
  # Step 10으로 이동
else
  echo ""
  # ⚠️ 여기서 Claude가 사용자에게 물어봄
  # "원격 저장소를 연결하시겠습니까?"
  # 사용자 답변에 따라 아래 코드 실행 여부 결정
fi
```

**Claude의 처리 (원격 저장소 연결 시):**

```bash
# GitHub CLI 사용 가능한 경우
if command -v gh &> /dev/null; then
  # Claude가 사용자에게 물어봄:
  # "1. 새 저장소 생성"
  # "2. 기존 저장소 연결"
  
  # 옵션 1: 새 저장소 생성
  if [ "$OPTION" = "1" ]; then
    PROJECT_NAME=$(basename "$(pwd)")
    
    # Claude가 사용자에게 물어봄:
    # - 저장소 이름 (기본: $PROJECT_NAME)
    # - 공개/비공개
    
    REPO_NAME="${USER_INPUT_NAME:-$PROJECT_NAME}"
    IS_PUBLIC="${USER_INPUT_PUBLIC:-true}"
    
    if [ "$IS_PUBLIC" = "true" ]; then
      if gh repo create "$REPO_NAME" --public --source=. --remote=origin --push; then
        echo "✅ GitHub 저장소 생성 및 푸시 완료"
        REMOTE_URL=$(git remote get-url origin)
        echo "🔗 ${REMOTE_URL}"
      else
        echo "❌ 저장소 생성 실패"
        echo "수동으로 생성: https://github.com/new"
        exit 1
      fi
    else
      if gh repo create "$REPO_NAME" --private --source=. --remote=origin --push; then
        echo "✅ GitHub 저장소 생성 및 푸시 완료"
      else
        echo "❌ 저장소 생성 실패"
        exit 1
      fi
    fi
  
  # 옵션 2: 기존 저장소 연결
  elif [ "$OPTION" = "2" ]; then
    # Claude가 사용자에게 물어봄:
    # "저장소 URL을 입력하세요"
    
    REPO_URL="$USER_INPUT_URL"
    
    if git remote add origin "$REPO_URL"; then
      echo "✅ 원격 저장소 연결: ${REPO_URL}"
      
      # main 브랜치로 푸시
      if git branch -M main && git push -u origin main; then
        echo "✅ main 브랜치 푸시 완료"
      else
        echo "❌ 푸시 실패"
        echo "수동 푸시: git push -u origin main"
        exit 1
      fi
    else
      echo "❌ 원격 저장소 연결 실패"
      exit 1
    fi
  fi
  
else
  # GitHub CLI 없는 경우
  # Claude가 사용자에게 물어봄:
  # "저장소 URL을 입력하세요"
  
  REPO_URL="$USER_INPUT_URL"
  
  if [ -n "$REPO_URL" ]; then
    if git remote add origin "$REPO_URL"; then
      echo "✅ 원격 저장소 연결: ${REPO_URL}"
      
      # main 브랜치로 푸시
      if git branch -M main && git push -u origin main; then
        echo "✅ main 브랜치 푸시 완료"
      else
        echo "❌ 푸시 실패"
        echo "수동 푸시: git push -u origin main"
      fi
    else
      echo "❌ 원격 저장소 연결 실패"
      exit 1
    fi
  fi
fi
```

### Step 10: 최종 출력

```bash
echo ""
echo "=========================================="
echo "✅ Git 저장소 초기화 완료!"
echo "=========================================="
echo ""
echo "📁 생성된 파일:"
echo "  - .git/"
echo "  - .gitignore (${PROJECT_TYPE})"
echo "  - .gitattributes"
echo "  - README.md"
[ -f "CLAUDE.md" ] && echo "  - CLAUDE.md"
[ -d "docs" ] && echo "  - docs/"
[ -d ".claude" ] && echo "  - .claude/"
echo ""

echo "🌿 브랜치:"
CURRENT_BRANCH=$(git branch --show-current)
echo "  - ${CURRENT_BRANCH} (현재)"
echo ""

# 원격 저장소 확인
REMOTE_URL=$(git remote get-url origin 2>/dev/null || echo "")
if [ -n "$REMOTE_URL" ]; then
  echo "🔗 원격 저장소:"
  echo "  ${REMOTE_URL}"
  echo ""
fi

echo "🚀 다음 단계:"
echo "1. /setup-cicd ${PROJECT_TYPE}"
echo "2. /setup-pre-commit"
echo "3. develop 브랜치 생성:"
echo "   git checkout -b develop"
if [ -n "$REMOTE_URL" ]; then
  echo "   git push -u origin develop"
fi
echo ""

# 커밋 확인
echo "📝 초기 커밋:"
git log --oneline -1
echo ""
```

## Error Handling

### Git 미설치

```bash
if ! command -v git &> /dev/null; then
  echo "❌ Git이 설치되어 있지 않습니다."
  exit 1
fi
```

### 이미 초기화됨

```bash
if [ -d ".git" ]; then
  echo "⚠️  이미 Git 저장소가 초기화되어 있습니다."
  git log --oneline -5 2>/dev/null
  # Claude가 사용자에게 확인 요청
  exit 1
fi
```

### 사용자 정보 미설정

```bash
if [ -z "$GIT_USER" ] || [ -z "$GIT_EMAIL" ]; then
  echo "❌ Git 사용자 정보가 설정되지 않았습니다."
  echo "설정 방법: git config --global user.name ..."
  exit 1
fi
```

### 커밋 실패 시 롤백

```bash
if ! git commit -m "..."; then
  echo "❌ 커밋 실패"
  echo "롤백 방법: rm -rf .git"
  exit 1
fi
```

### 원격 저장소 연결 실패

```bash
if ! git remote add origin "$REPO_URL"; then
  echo "❌ 원격 저장소 연결 실패"
  echo "수동 연결: git remote add origin <url>"
  exit 1
fi
```

## Notes

### 대화형 처리

- `read` 명령어는 사용하지 않음
- Claude가 사용자에게 직접 질문하고 답변을 받음
- 사용자 답변에 따라 해당 bash 코드만 실행

### 파일 정리

- 기존 `.DS_Store`, `__pycache__` 자동 제거
- `.gitignore`에 있는 파일은 자동으로 제외됨
- `node_modules`가 있으면 경고만 표시

### 초기 커밋 범위

- `.gitignore`, `.gitattributes`, `README.md` (필수)
- `CLAUDE.md` (있으면)
- `docs/` (있으면)
- `.claude/` (있으면, `local/` 제외)

### 에러 처리

- 모든 중요 단계에서 에러 체크
- 실패 시 롤백 방법 안내
- `exit 1`로 명확한 실패 표시

## Related Commands

- `/setup-cicd` - CI/CD 파이프라인 설정
- `/setup-pre-commit` - Pre-commit Hook 설정