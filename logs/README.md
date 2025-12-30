# Task Execution Logs

이 디렉토리는 **task-executor Agent**와 **task-developer Skill**이 Task를 수행한 기록을 자동으로 저장합니다.

## 📋 목적

- Task 구현 과정 추적
- 실행 이력 분석
- 문제 해결 및 디버깅
- 성과 측정 및 개선

## 📁 파일 명명 규칙

```
task-{TASK_ID}-{TIMESTAMP}.md
```

### 예시

- `task-1.1-20251230-220530.md`
- `task-2.3-20251231-143022.md`
- `task-3.1-alpha-20250101-091500.md`

### 구성 요소

- **TASK_ID**: Task 식별자 (예: `1.1`, `2.3`, `3.1-alpha`)
- **TIMESTAMP**: 실행 시작 시간 (`YYYYMMDD-HHMMSS` 형식)

## 📝 로그 파일 구조

각 로그 파일은 다음 섹션을 포함합니다:

### 1. Task Information
- Task ID
- Task Title
- Task Description
- Task Plan 경로

### 2. Execution Timeline
- 시작 시간
- 종료 시간
- 총 소요 시간

### 3. Pre-Flight Reasoning
- Scope & Blast Radius 분석
- Production Impact 평가
- Security & Privacy 체크
- Technology Stack 확인

### 4. Implementation Steps
- 각 Step별 실행 내역
- Step 시작/종료 시간
- Step 완료 여부

### 5. Test Results
- 테스트 실행 결과
- 통과/실패 개수
- 실패 사유 (있는 경우)

### 6. Quality Gates
- Lint 결과
- Type Check 결과
- Security Checklist 확인
- CLAUDE.md 규칙 준수 여부

### 7. Git Commit
- Commit Hash
- Commit Message
- Changed Files

### 8. Summary
- 성공/실패 여부
- 주요 이슈
- 개선 사항

## 🔒 보안

**중요**: 로그 파일에는 **민감 데이터를 절대 기록하지 않습니다**.

### 기록 금지 항목
- ❌ API 키, 비밀번호, 토큰
- ❌ 개인정보 (이름, 이메일, 전화번호 등)
- ❌ 실제 고객 데이터
- ❌ 프로덕션 설정 정보

### 기록 가능 항목
- ✅ Task ID 및 제목
- ✅ 파일 경로 및 변경 내역
- ✅ 테스트 결과 (민감 데이터 제외)
- ✅ 실행 시간 및 성능 메트릭
- ✅ 에러 메시지 (민감 데이터 마스킹)

## 📊 로그 분석

로그 파일을 활용하여 다음을 분석할 수 있습니다:

### 성과 측정
```bash
# 평균 Task 완료 시간
grep "총 소요 시간" logs/*.md

# 성공률
grep "Status:" logs/*.md | grep -c "Success"
```

### 문제 패턴 식별
```bash
# 실패한 Task 찾기
grep "Status: Failed" logs/*.md

# 자주 발생하는 에러
grep "Error:" logs/*.md | sort | uniq -c | sort -rn
```

### 보안 체크 이력
```bash
# 보안 체크 통과 여부
grep "Security Checklist" logs/*.md -A 5
```

## 🗂️ 관리

### 로그 보관 정책

- **단기**: 최근 30일 로그는 보관
- **장기**: 30일 이상된 로그는 압축 또는 삭제 고려
- **중요**: 실패한 Task 로그는 90일 보관 권장

### 로그 정리 스크립트 (예시)

```bash
#!/bin/bash
# 30일 이상된 로그 삭제
find logs/ -name "task-*.md" -mtime +30 -delete

# 또는 압축
find logs/ -name "task-*.md" -mtime +30 -exec gzip {} \;
```

## 📌 참고

- 로그 디렉토리는 `.gitignore`에 등록되어 Git 추적 대상이 아닙니다
- 로그는 로컬 환경에만 저장됩니다
- CI/CD 파이프라인에서는 별도 로그 시스템 사용 권장

## 🔗 관련 문서

- `.claude/skills/task-developer/SKILL.md` - Task 구현 프로세스
- `.claude/agents/task-executor/AGENT.md` - Task 실행 Agent
- `docs/task-plans/` - Task Plan 문서

---

> **Note**: 이 디렉토리는 자동으로 관리되며, 수동으로 파일을 생성할 필요가 없습니다.
