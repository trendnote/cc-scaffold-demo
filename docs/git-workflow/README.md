# Git Workflow Package

Git/GitHub 기반 개발 프로세스를 자동화하는 Commands와 Skills 모음입니다.

## 📦 구성

```
git-workflow-package/
├── .claude/
│   ├── skills/      (3개) - 개발 가이드
│   └── commands/    (11개) - 자동화 명령어
└── docs/
    └── git-workflow/
        └── README.md - 상세 가이드
```

## 🚀 빠른 시작

### 1. 설치

```bash
# 프로젝트에 복사
cp -r git-workflow-package/.claude your-project/
cp -r git-workflow-package/docs your-project/
```

### 2. 초기 설정 (1회)

```bash
cd your-project/

# Git 초기화
/git-init

# CI/CD 설정
/setup-cicd python-fastapi

# Pre-commit Hook 설정
/setup-pre-commit

# develop 브랜치 생성
git checkout -b develop
git push -u origin develop
```

### 3. 개발 사이클 (반복)

```bash
# 1. Issue 생성
/issue-create 1.1

# 2. 브랜치 생성
/branch-create 1

# 3. 개발 (TDD)
# ...

# 4. 커밋
/commit feat "Add feature"

# 5. PR 생성
/pr-create

# 6. 정리 (Merge 후)
/pr-cleanup
```

## 📋 Commands

### 필수 (Phase 1)

| Command | 설명 | 사용 빈도 |
|---------|------|----------|
| `/issue-create` | GitHub Issue 자동 생성 | 매 Task |
| `/branch-create` | Feature 브랜치 생성 | 매 Task |
| `/worktree-create` | Worktree 생성 (고급) | 병렬 작업 시 |
| `/commit` | Conventional Commits 적용 | 하루 5-10회 |
| `/pr-create` | PR 자동 생성 | 매 Task |

### 선택 (Phase 3)

| Command | 설명 |
|---------|------|
| `/pr-cleanup` | 브랜치 정리 |
| `/worktree-cleanup` | Worktree 정리 |
| `/git-init` | Git 저장소 초기화 |
| `/setup-cicd` | CI/CD 파이프라인 설정 |
| `/setup-pre-commit` | Pre-commit Hook 설정 |
| `/release-create` | Release 생성 |

## 🎓 Skills

| Skill | 설명 |
|-------|------|
| `git-flow-guide` | GitFlow 브랜치 전략 가이드 |
| `tdd-developer` | TDD 개발 방법론 가이드 |
| `code-reviewer` | 코드 리뷰 체크리스트 |

## 💡 주요 기능

### 1. Issue 자동 생성

Task Breakdown을 읽어서 GitHub Issue를 자동으로 생성합니다.

```bash
/issue-create 1.1
# → Issue #1 생성
```

### 2. 브랜치 자동 생성

Issue 정보를 기반으로 브랜치명을 자동 생성합니다.

```bash
/branch-create 1
# → feature/issue-1-docker-setup
```

### 3. Conventional Commits

커밋 메시지를 자동으로 규칙에 맞게 작성합니다.

```bash
/commit feat "Add PostgreSQL service"
# → feat(infra): Add PostgreSQL service
#
#   Ref: #1
```

### 4. PR 자동 생성

커밋 내역을 분석하여 PR을 자동 생성합니다.

```bash
/pr-create
# → PR #2 생성, CI 자동 실행
```

## 🎯 워크플로우 비교

### Feature Branch (일반)

```bash
/issue-create → /branch-create → 개발 → /commit → /pr-create → /pr-cleanup
```

**사용 시기:** 1개 Task 집중, 순차적 개발

### Worktree (고급)

```bash
/issue-create → /worktree-create → 개발 → /commit → /pr-create → /worktree-cleanup
```

**사용 시기:** 병렬 작업, 긴급 수정 빈번

## 📊 효과

| 항목 | Before | After | 절감 |
|------|--------|-------|------|
| Issue 생성 | 10분 | 1분 | 9분 |
| 브랜치 생성 | 2분 | 30초 | 1.5분 |
| 커밋 (5회) | 25분 | 5분 | 20분 |
| PR 생성 | 10분 | 1분 | 9분 |
| 정리 | 3분 | 30초 | 2.5분 |
| **총합** | **50분** | **8분** | **42분 (84%)** |

**29 Tasks × 42분 = 20시간 절약!**

## 📖 상세 가이드

더 자세한 내용은 [docs/git-workflow/README.md](docs/git-workflow/README.md)를 참고하세요.

- GitFlow 브랜치 전략
- Commit 메시지 규칙
- PR 프로세스
- Worktree 사용법
- 트러블슈팅
- FAQ

## 🔧 커스터마이징

### Commands 수정

`.claude/commands/` 아래 파일을 수정하여 프로젝트에 맞게 조정하세요.

### Skills 추가

`.claude/skills/` 아래에 프로젝트별 가이드를 추가하세요.

## 📝 요구사항

### 필수

- Git 2.x+
- GitHub CLI (`gh`)
- GitHub 계정

### 선택

- Python 3.11+ (pre-commit용)
- Docker (CI/CD 테스트용)

## 🤝 기여

개선 사항이나 버그 리포트는 Issue로 제출해주세요.

## 📄 라이선스

MIT License

---

**Git Workflow Package로 생산성 극대화!** 🚀
