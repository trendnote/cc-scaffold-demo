# Git Workflow Commands Reference

완전한 Git workflow를 위한 실용적인 명령어 모음입니다. 각 섹션은 실제 프로젝트에서 사용한 명령어를 기반으로 구성되었습니다.

---

## 목차
1. [초기 설정](#1-초기-설정)
2. [Repository 생성 및 클론](#2-repository-생성-및-클론)
3. [Branch 관리](#3-branch-관리)
4. [Worktree 관리](#4-worktree-관리)
5. [일상적인 작업 (Add, Commit, Push)](#5-일상적인-작업-add-commit-push)
6. [Pull Request Workflow](#6-pull-request-workflow)
7. [동기화 및 업데이트](#7-동기화-및-업데이트)
8. [정보 조회](#8-정보-조회)
9. [되돌리기 및 수정](#9-되돌리기-및-수정)
10. [고급 기능](#10-고급-기능)
11. [문제 해결](#11-문제-해결)

---

## 1. 초기 설정

### 1.1 Git 사용자 정보 설정
```bash
# 전역 사용자 정보 설정 (모든 프로젝트에 적용)
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# 현재 프로젝트에만 적용
git config user.name "Your Name"
git config user.email "your.email@example.com"

# 설정 확인
git config --list
git config user.name
git config user.email
```

### 1.2 기본 에디터 설정
```bash
# VS Code를 기본 에디터로 설정
git config --global core.editor "code --wait"

# Vim을 기본 에디터로 설정
git config --global core.editor "vim"

# Nano를 기본 에디터로 설정
git config --global core.editor "nano"
```

### 1.3 기본 브랜치 이름 설정
```bash
# 기본 브랜치를 main으로 설정
git config --global init.defaultBranch main

# 또는 master로 설정
git config --global init.defaultBranch master
```

### 1.4 유용한 전역 설정
```bash
# 색상 출력 활성화
git config --global color.ui auto

# 자동으로 CRLF를 LF로 변환 (macOS/Linux)
git config --global core.autocrlf input

# 자동으로 CRLF를 LF로 변환 (Windows)
git config --global core.autocrlf true

# Push 기본 동작 설정 (현재 브랜치만 push)
git config --global push.default current

# Pull 시 rebase 사용
git config --global pull.rebase true
```

---

## 2. Repository 생성 및 클론

### 2.1 로컬에서 새 Repository 생성
```bash
# 현재 디렉토리를 Git repository로 초기화
git init

# 새 디렉토리를 만들고 초기화
git init my-project
cd my-project
```

### 2.2 원격 Repository 클론
```bash
# HTTPS로 클론
git clone https://github.com/username/repo.git

# SSH로 클론
git clone git@github.com:username/repo.git

# 특정 브랜치만 클론
git clone -b branch-name https://github.com/username/repo.git

# 얕은 클론 (최신 커밋만, 히스토리 없이)
git clone --depth 1 https://github.com/username/repo.git

# 특정 디렉토리 이름으로 클론
git clone https://github.com/username/repo.git my-folder
```

### 2.3 원격 Repository 연결
```bash
# 원격 저장소 추가
git remote add origin https://github.com/username/repo.git

# 원격 저장소 확인
git remote -v

# 원격 저장소 URL 변경
git remote set-url origin https://github.com/username/new-repo.git

# 원격 저장소 제거
git remote remove origin
```

---

## 3. Branch 관리

### 3.1 Branch 생성 및 전환
```bash
# 현재 브랜치 확인
git branch

# 모든 브랜치 확인 (원격 포함)
git branch -a

# 새 브랜치 생성
git branch feature/new-feature

# 새 브랜치 생성 후 전환
git checkout -b feature/new-feature

# 또는 (Git 2.23+)
git switch -c feature/new-feature

# 원격 브랜치 기반으로 로컬 브랜치 생성
git checkout -b feature/new-feature origin/feature/new-feature

# 기존 브랜치로 전환
git checkout main
# 또는
git switch main
```

### 3.2 Branch 삭제
```bash
# 로컬 브랜치 삭제 (병합된 경우에만)
git branch -d feature/old-feature

# 로컬 브랜치 강제 삭제 (병합 여부 무관)
git branch -D feature/old-feature

# 원격 브랜치 삭제
git push origin --delete feature/old-feature

# 원격에서 삭제된 브랜치 로컬에서 정리
git fetch --prune
# 또는
git remote prune origin
```

### 3.3 Branch 이름 변경
```bash
# 현재 브랜치 이름 변경
git branch -m new-branch-name

# 다른 브랜치 이름 변경
git branch -m old-name new-name

# 원격의 브랜치 이름도 변경 (old 삭제 + new push)
git push origin :old-name new-name
git push origin -u new-name
```

---

## 4. Worktree 관리

### 4.1 Worktree 생성
```bash
# 새 브랜치로 worktree 생성
git worktree add ../my-feature feature/my-feature

# 기존 브랜치로 worktree 생성
git worktree add ../bugfix bugfix/issue-123

# 현재 브랜치 기반으로 새 브랜치 + worktree 생성
git worktree add -b feature/new-feature ../new-feature

# 특정 커밋에서 worktree 생성
git worktree add --detach ../temp abc1234
```

### 4.2 Worktree 조회
```bash
# 모든 worktree 목록 보기
git worktree list

# Worktree 상세 정보
git worktree list --porcelain
```

### 4.3 Worktree 제거
```bash
# Worktree 제거 (디렉토리는 수동 삭제 필요)
git worktree remove ../my-feature

# Worktree 강제 제거
git worktree remove --force ../my-feature

# Worktree 정리 (이미 삭제된 디렉토리의 메타데이터 제거)
git worktree prune

# Worktree와 디렉토리 모두 제거
git worktree remove ../my-feature && rm -rf ../my-feature
```

### 4.4 Worktree 이동
```bash
# Worktree 경로 이동
git worktree move ../old-path ../new-path
```

---

## 5. 일상적인 작업 (Add, Commit, Push)

### 5.1 변경 사항 확인
```bash
# 작업 디렉토리 상태 확인
git status

# 간단한 상태 확인
git status -s

# 변경된 파일 목록만 보기
git diff --name-only

# Staged 파일 확인
git diff --cached
git diff --staged
```

### 5.2 파일 추가 (Staging)
```bash
# 특정 파일 추가
git add file1.txt file2.txt

# 현재 디렉토리의 모든 변경사항 추가
git add .

# 모든 변경사항 추가 (삭제 포함)
git add -A

# 수정된 파일만 추가 (새 파일 제외)
git add -u

# 대화형 추가 (일부만 선택 가능)
git add -p
```

### 5.3 커밋
```bash
# 기본 커밋
git commit -m "feat: add new feature"

# 여러 줄 커밋 메시지 (에디터 열림)
git commit

# 여러 줄 커밋 메시지 (heredoc 사용)
git commit -m "$(cat <<'EOF'
feat: add user authentication

- Implement JWT-based authentication
- Add login and logout endpoints
- Create user session management

🤖 Generated with Claude Code

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
EOF
)"

# 수정과 커밋을 동시에 (tracked 파일만)
git commit -am "fix: resolve bug"

# 마지막 커밋 수정 (메시지 변경)
git commit --amend -m "new message"

# 마지막 커밋에 파일 추가 (메시지 유지)
git add forgotten-file.txt
git commit --amend --no-edit

# 빈 커밋 생성 (CI 재실행 등에 유용)
git commit --allow-empty -m "chore: trigger CI"
```

### 5.4 Push
```bash
# 현재 브랜치를 origin에 push
git push

# 처음 push할 때 upstream 설정
git push -u origin feature/my-feature

# 강제 push (주의: 히스토리 덮어쓰기)
git push --force

# 안전한 강제 push (원격이 예상과 다르면 실패)
git push --force-with-lease

# 모든 브랜치 push
git push --all

# 태그 push
git push --tags

# 특정 태그 push
git push origin v1.0.0
```

---

## 6. Pull Request Workflow

### 6.1 Feature 브랜치 생성 및 작업
```bash
# main에서 최신 상태 가져오기
git checkout main
git pull origin main

# Feature 브랜치 생성
git checkout -b feature/user-auth

# 작업 수행
# ... code changes ...

# 변경사항 커밋
git add .
git commit -m "feat: implement user authentication"

# 원격에 push
git push -u origin feature/user-auth
```

### 6.2 GitHub CLI로 Pull Request 생성
```bash
# PR 생성 (대화형)
gh pr create

# PR 생성 (제목과 본문 지정)
gh pr create --title "Add user authentication" --body "Implements JWT-based auth"

# PR 생성 (heredoc으로 본문 작성)
gh pr create --title "Add user authentication" --body "$(cat <<'EOF'
## Summary
- Implement JWT-based authentication
- Add login/logout endpoints

## Test Plan
- [ ] Unit tests pass
- [ ] Integration tests pass

🤖 Generated with Claude Code
EOF
)"

# Draft PR 생성
gh pr create --draft

# 특정 브랜치로 PR 생성
gh pr create --base main --head feature/user-auth

# Reviewer 지정
gh pr create --reviewer username1,username2

# Label 추가
gh pr create --label "enhancement,backend"
```

### 6.3 Pull Request 관리
```bash
# PR 목록 보기
gh pr list

# 특정 PR 보기
gh pr view 123

# PR을 브라우저에서 열기
gh pr view --web

# PR 체크아웃 (로컬에서 테스트)
gh pr checkout 123

# PR 병합
gh pr merge 123

# PR 병합 (squash)
gh pr merge 123 --squash

# PR 병합 (rebase)
gh pr merge 123 --rebase

# PR 닫기
gh pr close 123

# PR 다시 열기
gh pr reopen 123

# PR에 코멘트 추가
gh pr comment 123 --body "LGTM!"
```

### 6.4 코드 리뷰 반영
```bash
# 리뷰 코멘트 확인 후 수정
# ... code changes ...

# 추가 커밋
git add .
git commit -m "fix: address review comments"
git push

# 또는 기존 커밋에 병합 (커밋 히스토리 정리)
git add .
git commit --amend --no-edit
git push --force-with-lease
```

---

## 7. 동기화 및 업데이트

### 7.1 원격 변경사항 가져오기
```bash
# 원격 변경사항 확인 (가져오기만)
git fetch origin

# 모든 원격 브랜치 가져오기
git fetch --all

# 원격 변경사항 가져오고 병합
git pull

# 원격 변경사항 가져오고 rebase
git pull --rebase

# 특정 브랜치에서 가져오기
git pull origin main
```

### 7.2 Main 브랜치와 동기화
```bash
# Feature 브랜치에서 작업 중일 때 main의 최신 변경사항 반영

# 방법 1: Merge (병합 커밋 생성)
git checkout feature/my-feature
git fetch origin
git merge origin/main

# 방법 2: Rebase (커밋 히스토리 선형 유지)
git checkout feature/my-feature
git fetch origin
git rebase origin/main

# Rebase 중 충돌 해결 후
git add .
git rebase --continue

# Rebase 취소
git rebase --abort

# 방법 3: Pull with rebase
git checkout feature/my-feature
git pull --rebase origin main
```

### 7.3 로컬 저장소를 원격과 동기화
```bash
# 원격과 완전히 동기화 (로컬 변경사항 버림, 주의!)
git fetch origin
git reset --hard origin/main

# 원격에서 삭제된 브랜치 정리
git fetch --prune

# 모든 원격 브랜치 정보 업데이트
git remote update origin --prune
```

---

## 8. 정보 조회

### 8.1 커밋 히스토리
```bash
# 커밋 로그 보기
git log

# 한 줄로 요약
git log --oneline

# 최근 N개 커밋만
git log -n 5
git log -5

# 그래프로 보기
git log --graph --oneline --all

# 특정 파일의 히스토리
git log -- path/to/file.txt

# 특정 작성자의 커밋만
git log --author="John Doe"

# 특정 기간의 커밋
git log --since="2 weeks ago"
git log --since="2024-01-01" --until="2024-12-31"

# 커밋 메시지로 검색
git log --grep="fix"

# 상세 변경사항 포함
git log -p

# 통계 정보
git log --stat
```

### 8.2 Diff (차이점 확인)
```bash
# 작업 디렉토리 vs Staging area
git diff

# Staging area vs 마지막 커밋
git diff --cached
git diff --staged

# 작업 디렉토리 vs 마지막 커밋
git diff HEAD

# 두 커밋 비교
git diff abc1234 def5678

# 두 브랜치 비교
git diff main feature/my-feature

# 특정 파일만 비교
git diff -- path/to/file.txt

# 단어 단위로 비교
git diff --word-diff

# 변경된 파일 목록만
git diff --name-only
```

### 8.3 파일 상태 및 히스토리
```bash
# 파일의 각 줄이 언제 누가 수정했는지 확인
git blame path/to/file.txt

# 특정 범위만 확인
git blame -L 10,20 path/to/file.txt

# 파일이 언제 삭제되었는지 찾기
git log --all --full-history -- path/to/file.txt

# 특정 커밋의 파일 내용 보기
git show abc1234:path/to/file.txt
```

### 8.4 브랜치 관계
```bash
# 현재 브랜치의 upstream 확인
git branch -vv

# 브랜치 간 차이 확인 (커밋 수)
git rev-list --left-right --count main...feature/my-feature

# 병합되지 않은 브랜치 찾기
git branch --no-merged

# 이미 병합된 브랜치 찾기
git branch --merged
```

---

## 9. 되돌리기 및 수정

### 9.1 변경사항 되돌리기
```bash
# 작업 디렉토리의 변경사항 버리기 (특정 파일)
git restore path/to/file.txt
# 또는 (구버전)
git checkout -- path/to/file.txt

# 모든 변경사항 버리기
git restore .

# Staging area에서 제거 (unstage)
git restore --staged path/to/file.txt
# 또는
git reset HEAD path/to/file.txt

# 모든 파일 unstage
git restore --staged .
git reset HEAD .
```

### 9.2 커밋 되돌리기
```bash
# 마지막 커밋 취소 (변경사항은 유지)
git reset --soft HEAD~1

# 마지막 커밋 취소 (변경사항 staging area에 유지)
git reset --mixed HEAD~1
git reset HEAD~1  # --mixed가 기본값

# 마지막 커밋 취소 (변경사항 완전히 버림, 주의!)
git reset --hard HEAD~1

# N개의 커밋 되돌리기
git reset --hard HEAD~3

# 특정 커밋으로 되돌리기
git reset --hard abc1234

# 되돌리기 전 백업
git branch backup-branch
git reset --hard HEAD~1
```

### 9.3 커밋 되돌리기 (Revert)
```bash
# 특정 커밋을 되돌리는 새 커밋 생성 (안전)
git revert abc1234

# 여러 커밋 되돌리기
git revert abc1234 def5678

# 병합 커밋 되돌리기
git revert -m 1 abc1234

# 커밋하지 않고 변경사항만 적용
git revert --no-commit abc1234
```

### 9.4 파일 삭제 및 이동
```bash
# 파일 삭제 (Git에서 추적 제거 + 파일 삭제)
git rm file.txt

# Git에서만 제거 (파일은 유지)
git rm --cached file.txt

# 디렉토리 삭제
git rm -r directory/

# 파일 이동 또는 이름 변경
git mv old-name.txt new-name.txt
```

---

## 10. 고급 기능

### 10.1 Stash (임시 저장)
```bash
# 현재 변경사항 임시 저장
git stash

# 메시지와 함께 저장
git stash save "WIP: working on feature X"

# Untracked 파일도 포함
git stash -u

# Stash 목록 보기
git stash list

# Stash 내용 확인
git stash show
git stash show -p  # 상세 변경사항

# 특정 stash 확인
git stash show stash@{1}

# Stash 적용 (stash 유지)
git stash apply

# 특정 stash 적용
git stash apply stash@{1}

# Stash 적용 후 삭제
git stash pop

# Stash 삭제
git stash drop
git stash drop stash@{1}

# 모든 stash 삭제
git stash clear

# Stash를 브랜치로 만들기
git stash branch new-branch-name
```

### 10.2 Cherry-pick
```bash
# 다른 브랜치의 특정 커밋만 가져오기
git cherry-pick abc1234

# 여러 커밋 가져오기
git cherry-pick abc1234 def5678

# 커밋 범위 가져오기
git cherry-pick abc1234..def5678

# 커밋하지 않고 변경사항만 적용
git cherry-pick --no-commit abc1234
```

### 10.3 Rebase (고급)
```bash
# Interactive rebase (커밋 히스토리 정리)
git rebase -i HEAD~5

# 여러 커밋을 하나로 합치기 (squash)
git rebase -i HEAD~3
# 에디터에서 'pick'을 'squash' 또는 's'로 변경

# 커밋 순서 변경
git rebase -i HEAD~5
# 에디터에서 커밋 줄 순서 변경

# 특정 브랜치 기준으로 rebase
git rebase main

# Rebase 계속 진행 (충돌 해결 후)
git add .
git rebase --continue

# Rebase 건너뛰기
git rebase --skip

# Rebase 취소
git rebase --abort
```

### 10.4 Tag
```bash
# 태그 목록 보기
git tag

# 패턴으로 태그 검색
git tag -l "v1.*"

# Lightweight 태그 생성
git tag v1.0.0

# Annotated 태그 생성 (권장)
git tag -a v1.0.0 -m "Release version 1.0.0"

# 특정 커밋에 태그
git tag -a v1.0.0 abc1234 -m "Release 1.0.0"

# 태그 정보 확인
git show v1.0.0

# 태그 push
git push origin v1.0.0

# 모든 태그 push
git push origin --tags

# 태그 삭제 (로컬)
git tag -d v1.0.0

# 태그 삭제 (원격)
git push origin --delete v1.0.0

# 태그로 체크아웃
git checkout v1.0.0
```

### 10.5 Submodule
```bash
# Submodule 추가
git submodule add https://github.com/user/repo.git path/to/submodule

# Submodule 초기화 및 업데이트
git submodule init
git submodule update

# 또는 한 번에
git submodule update --init --recursive

# Submodule을 포함하여 클론
git clone --recursive https://github.com/user/repo.git

# Submodule 업데이트
git submodule update --remote

# Submodule 제거
git submodule deinit path/to/submodule
git rm path/to/submodule
rm -rf .git/modules/path/to/submodule
```

---

## 11. 문제 해결

### 11.1 충돌 해결
```bash
# 충돌 발생 시 충돌 파일 확인
git status

# 충돌 내용 확인
git diff

# 충돌 해결 후
git add path/to/resolved-file.txt
git commit  # merge의 경우
git rebase --continue  # rebase의 경우

# 병합 취소
git merge --abort

# Rebase 취소
git rebase --abort

# 특정 파일만 우리 것으로 (ours)
git checkout --ours path/to/file.txt

# 특정 파일만 그들 것으로 (theirs)
git checkout --theirs path/to/file.txt
```

### 11.2 실수 복구
```bash
# 삭제된 커밋 복구 (reflog 사용)
git reflog
git checkout abc1234  # reflog에서 찾은 커밋

# 삭제된 브랜치 복구
git reflog
git checkout -b recovered-branch abc1234

# 강제 push 전으로 되돌리기
git reflog
git reset --hard abc1234

# 변경사항 임시로 되돌리고 나중에 다시 적용
git stash
# ... 다른 작업 ...
git stash pop
```

### 11.3 원격 저장소 문제
```bash
# 원격 브랜치가 삭제되었는데 로컬에 남아있을 때
git fetch --prune

# 원격과 완전히 동기화 (로컬 변경사항 버림)
git fetch origin
git reset --hard origin/main

# Push rejected 문제 (원격이 앞서있을 때)
git pull --rebase
git push

# 또는 강제 push (주의!)
git push --force-with-lease
```

### 11.4 .gitignore 문제
```bash
# .gitignore에 추가했는데 계속 추적될 때
git rm --cached path/to/file.txt
git commit -m "chore: remove tracked file"

# 디렉토리 전체
git rm -r --cached path/to/directory/
git commit -m "chore: remove tracked directory"

# .gitignore 캐시 초기화
git rm -r --cached .
git add .
git commit -m "chore: refresh gitignore"
```

### 11.5 히스토리 정리
```bash
# 히스토리에서 파일 완전히 제거 (주의: 위험!)
git filter-branch --tree-filter 'rm -f passwords.txt' HEAD

# 또는 BFG Repo-Cleaner 사용 (더 빠름)
bfg --delete-files passwords.txt

# 모든 원격 브랜치 강제 업데이트
git push origin --force --all
```

### 11.6 성능 최적화
```bash
# Repository 최적화
git gc

# 더 강력한 최적화
git gc --aggressive

# 저장소 크기 확인
git count-objects -vH

# Dangling commits 제거
git reflog expire --expire=now --all
git gc --prune=now --aggressive
```

---

## 12. 유용한 Alias 설정

```bash
# 자주 사용하는 명령어를 짧게
git config --global alias.co checkout
git config --global alias.br branch
git config --global alias.ci commit
git config --global alias.st status

# 복잡한 명령어를 간단하게
git config --global alias.unstage 'reset HEAD --'
git config --global alias.last 'log -1 HEAD'
git config --global alias.visual 'log --graph --oneline --all'
git config --global alias.amend 'commit --amend --no-edit'

# 사용 예시
git co main  # git checkout main
git st       # git status
git visual   # git log --graph --oneline --all
git amend    # git commit --amend --no-edit
```

---

## 13. 일반적인 Workflow 예시

### 13.1 Feature 개발 전체 플로우
```bash
# 1. Main 브랜치에서 최신 코드 가져오기
git checkout main
git pull origin main

# 2. Feature 브랜치 생성
git checkout -b feature/user-profile

# 3. 작업 수행 및 커밋
git add .
git commit -m "feat: add user profile page"

# 4. Main에 새로운 변경사항이 있다면 rebase
git fetch origin
git rebase origin/main

# 5. 원격에 push
git push -u origin feature/user-profile

# 6. PR 생성
gh pr create --title "Add user profile page" --body "..."

# 7. 리뷰 받고 수정사항 반영
git add .
git commit -m "fix: address review comments"
git push

# 8. PR 병합 후 로컬 정리
git checkout main
git pull origin main
git branch -d feature/user-profile
```

### 13.2 Hotfix 긴급 수정 플로우
```bash
# 1. Main에서 hotfix 브랜치 생성
git checkout main
git pull origin main
git checkout -b hotfix/critical-bug

# 2. 버그 수정 및 커밋
git add .
git commit -m "fix: resolve critical security issue"

# 3. 즉시 push 및 PR
git push -u origin hotfix/critical-bug
gh pr create --title "HOTFIX: Critical security issue" --label "urgent"

# 4. 승인 즉시 병합
gh pr merge --squash

# 5. Main 업데이트 후 개발 브랜치에도 반영
git checkout main
git pull origin main
git checkout feature/my-feature
git rebase main
```

### 13.3 Worktree를 활용한 동시 작업
```bash
# 1. Main에서 작업 중
# ... working on feature ...

# 2. 긴급 버그 발견, worktree로 별도 작업
git worktree add ../hotfix hotfix/urgent-fix
cd ../hotfix

# 3. Hotfix 작업
git add .
git commit -m "fix: urgent bug"
git push -u origin hotfix/urgent-fix

# 4. 원래 작업으로 복귀
cd ../main-project

# 5. Hotfix 완료 후 worktree 정리
git worktree remove ../hotfix
```

---

## 14. Best Practices

### 14.1 커밋 메시지 가이드
```bash
# Conventional Commits 형식 사용
feat: 새로운 기능 추가
fix: 버그 수정
docs: 문서 변경
style: 코드 포맷팅 (기능 변경 없음)
refactor: 리팩토링
test: 테스트 추가/수정
chore: 빌드 프로세스, 툴 설정 등

# 예시
git commit -m "feat: add user authentication"
git commit -m "fix: resolve login redirect issue"
git commit -m "docs: update API documentation"
```

### 14.2 브랜치 네이밍 컨벤션
```bash
feature/feature-name    # 새 기능
bugfix/bug-description  # 버그 수정
hotfix/urgent-fix       # 긴급 수정
refactor/component-name # 리팩토링
docs/documentation-name # 문서
test/test-description   # 테스트
```

### 14.3 안전한 작업 습관
```bash
# 1. 자주 커밋하기 (작은 단위로)
# 2. Push 전에 항상 pull/rebase
# 3. 강제 push는 최대한 피하기 (--force-with-lease 사용)
# 4. Main 브랜치에 직접 커밋 금지
# 5. 중요한 작업 전 백업 브랜치 생성

# 백업 브랜치 예시
git branch backup-$(date +%Y%m%d)
```

---

## 15. 참고 리소스

### 공식 문서
- [Git 공식 문서](https://git-scm.com/doc)
- [GitHub CLI 문서](https://cli.github.com/manual/)
- [Conventional Commits](https://www.conventionalcommits.org/)

### 유용한 도구
- **GitKraken**: GUI Git 클라이언트
- **SourceTree**: 무료 Git GUI
- **VSCode Git Extension**: IDE 통합
- **git-flow**: Git workflow 자동화
- **BFG Repo-Cleaner**: 대용량 파일 정리

### 학습 자료
- [Learn Git Branching](https://learngitbranching.js.org/) - 인터랙티브 튜토리얼
- [Oh My Git!](https://ohmygit.org/) - Git 학습 게임
- [Git Flight Rules](https://github.com/k88hudson/git-flight-rules) - 문제 해결 가이드

---

## 마치며

이 문서는 실제 프로젝트에서 사용한 Git 명령어를 기반으로 작성되었습니다. 각 명령어는 copy-paste하여 바로 사용할 수 있도록 구성했습니다.

**추천 학습 순서**:
1. 초기 설정 (섹션 1)
2. Branch 관리 (섹션 3)
3. 일상적인 작업 (섹션 5)
4. Pull Request Workflow (섹션 6)
5. 고급 기능 (섹션 10)

**문제 발생 시**:
1. `git status`로 현재 상태 확인
2. 섹션 11 (문제 해결) 참고
3. 백업 브랜치 생성 후 실험
4. `git reflog`로 복구 가능

---

**Last Updated**: 2026-01-01
**Version**: 1.0.0
