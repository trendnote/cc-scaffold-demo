---
name: task-developer
description: >
  Task를 4-8시간 단위로 구현합니다.
  사용: "Task 1.1 구현해주세요" 또는 "Task 2.3을 개발해주세요"
  CLAUDE.md 규칙, 보안 체크, 코딩 컨벤션을 자동으로 적용합니다.
allowed-tools: Read, Edit, Write, Bash, Grep, Glob, LSP
---

# Task Developer Skill

이 Skill은 **KakaoPay CLAUDE.md 규칙**을 완벽하게 준수하며 Task를 구현합니다.

## 보장 사항

1. **규칙 준수**: CLAUDE.md의 모든 [HARD RULE] 확인
2. **안전성**: Pre-Flight Reasoning (CLAUDE.md Section 6)
3. **보안**: 데이터 보호, 인증 무결성 (Section 3)
4. **정확성**: Correctness First (Section 2.1)
5. **테스트**: Test as Specification (Section 2.5)
6. **유지보수성**: Maintainability over Cleverness (Section 2.6)

---

## 구현 프로세스

### Phase 1: Pre-Flight Reasoning (필수, 10분)

CLAUDE.md Section 6에 따라 코딩 전 다음을 분석합니다:

- [ ] **Task 정보 확인**
  - Task Plan 문서 읽기 (`docs/task-plans/task-{ID}-plan.md`)
  - Acceptance Criteria 이해
  - 구현 범위 파악

- [ ] **Scope & Blast Radius**
  - 영향받는 파일/모듈 식별
  - 변경의 파급 효과 분석
  - 다른 Task와의 의존성 확인

- [ ] **Production Impact**
  - 프로덕션 영향 여부 판단
  - 실험 코드 vs 프로덕션 코드 분류
  - 롤백 전략 검토

- [ ] **Security & Privacy Implications**
  - 민감 데이터 처리 여부 확인
  - 인증/인가 로직 변경 여부
  - 보안 체크리스트 적용 (`SECURITY-CHECKLIST.md` 참조)

- [ ] **Technology Stack Rules**
  - 기술 스택별 규칙 확인 (`TECH-STACK-GUIDE.md` 참조)
  - 코딩 컨벤션 검토
  - 프로젝트 패턴 준수

**⚠️ 불확실한 사항이 있으면 여기서 멈추고 사용자에게 질문합니다.**

---

### Phase 2: Implementation (주 시간, 2-6시간)

Task Plan의 각 Step을 30분-1시간 단위로 구현합니다:

#### Step-by-Step 구현

- [ ] **Step 구현**
  - 한 번에 하나의 Step만 집중
  - Small, Reversible Changes (Section 2.4)
  - Explicit over Implicit (Section 2.3)

- [ ] **코드 작성 원칙**
  - Correctness First: 이해하지 못한 동작은 구현하지 않음
  - Safety over Speed: 빠르지만 잘못된 코드는 기술 부채
  - No assumptions: 엣지 케이스, 실패 시나리오 명시적 처리

- [ ] **각 Step 완료 후**
  - 해당 Step의 테스트 작성
  - Lint 통과 확인
  - 로컬에서 동작 검증
  - 다음 Step 진행

---

### Phase 3: Verification (필수, 15분)

모든 구현이 완료된 후:

- [ ] **테스트 검증**
  - 모든 테스트 통과 확인
  - Edge case 테스트 포함
  - Error path 테스트 포함

- [ ] **코드 품질**
  - Lint/Format 통과
  - Type check 통과 (TypeScript/Python 등)
  - 컨벤션 준수 확인

- [ ] **보안 재검증**
  - SECURITY-CHECKLIST.md 최종 확인
  - 민감 데이터 노출 여부
  - 하드코딩된 시크릿 없음

- [ ] **CLAUDE.md 규칙 재확인**
  - [HARD RULE] 위반 없음
  - Pre-Flight Reasoning 항목 모두 만족
  - 문서화 필요 여부 판단

---

### Phase 4: Finalization (5-10분)

- [ ] **Git Commit**
  - Conventional Commit 포맷 사용
  - 의미있는 커밋 메시지 작성
  - Co-authored-by: Claude 포함

- [ ] **Documentation (필요시)**
  - API 변경 시: OpenAPI/스펙 업데이트
  - 아키텍처 변경 시: ADR 작성
  - 사용법 변경 시: README 업데이트

- [ ] **Task 완료 보고**
  - Acceptance Criteria 충족 확인
  - 완료된 내용 요약
  - 다음 Task 준비 (워크트리 전환 등)

---

## 금지 사항 (CLAUDE.md 기반)

### [HARD RULE] 위반 시 즉시 중단

- ❌ **가정 기반 구현**: 불확실하면 "I don't know" 명시
- ❌ **민감 데이터**: 실제 고객/결제/계정/인증 데이터 생성/가정
- ❌ **보안 우회**: Auth/Authz 로직 무단 수정/제거/약화
- ❌ **프로덕션 무단 수정**: 명시적 지시 없이 프로덕션 설정 변경
- ❌ **빠른 것이 우선**: 속도가 안전성을 희생하는 경우

### 과도한 엔지니어링 방지

CLAUDE.md에 명시되지 않았지만 중요:

- ❌ 요청되지 않은 기능 추가
- ❌ 불필요한 리팩토링
- ❌ 가상의 미래 요구사항 대비
- ❌ 한 번만 쓰는 코드를 helper/utility로 추상화
- ❌ 발생할 수 없는 시나리오에 대한 에러 핸들링

**원칙**: 현재 Task에 필요한 최소한의 복잡도만 유지

---

## 기술 스택별 규칙

상세 내용은 `TECH-STACK-GUIDE.md`를 참조하되, 기본 원칙:

- **Java/Spring**: `@claude-rules/backend-core.md` 적용
- **Node.js/TypeScript**: `@claude-rules/backend-bff.md` 적용
- **Python/FastAPI**: `@claude-rules/backend-ai.md` 적용
- **Next.js**: `@claude-rules/frontend-ui.md` 적용

Task가 여러 도메인에 걸치면 **모든 관련 규칙 적용**

---

## 보안 체크리스트

상세 내용은 `SECURITY-CHECKLIST.md`를 참조하되, 필수 항목:

- [ ] 민감 데이터 로그에 노출 안 됨
- [ ] 하드코딩된 시크릿 없음
- [ ] 사용자 입력 검증 (외부 경계)
- [ ] SQL Injection, XSS, Command Injection 방지
- [ ] 인증/인가 로직 무결성 유지

---

## 사용 예시

### 기본 사용법

```
사용자: Task 1.1을 구현해주세요
```

Claude가 자동으로 이 Skill을 선택하고:
1. Pre-Flight Reasoning 수행
2. Task Plan 읽기
3. Step별 구현
4. 테스트 작성
5. 검증 후 커밋

### 명시적 호출

```
사용자: Use task-developer skill for Task 2.3
```

### 연속 구현

```
사용자: Task 1.1, 1.2, 1.3을 순차적으로 구현해주세요
```

각 Task마다 Pre-Flight Reasoning부터 시작하여 완료 후 다음 Task 진행

---

## 실패 처리

### 구현 중 막힌 경우

1. 현재 상태 저장 (부분 커밋)
2. 막힌 이유 명확히 설명
3. 사용자에게 도움 요청
4. 다음 Task로 넘어갈지 여부 확인

### 테스트 실패

1. 실패 원인 분석
2. 수정 후 재테스트
3. 3회 이상 실패 시 사용자에게 보고

### 보안 우려 발견

1. 즉시 구현 중단
2. 보안 이슈 설명
3. 사용자 승인 후 진행

---

## Quality Gates

모든 Task는 다음을 만족해야 완료로 간주됩니다:

- ✅ Pre-Flight Reasoning 완료
- ✅ 모든 Acceptance Criteria 충족
- ✅ 테스트 작성 및 통과
- ✅ Lint/Format/Type check 통과
- ✅ SECURITY-CHECKLIST.md 확인
- ✅ CLAUDE.md [HARD RULE] 위반 없음
- ✅ Git commit 완료

---

## 참고 문서

- `CLAUDE.md`: 회사 전체 규칙 (최상위 우선순위)
- `CLAUDE-RULES.md`: CLAUDE.md 요약 (이 디렉토리)
- `SECURITY-CHECKLIST.md`: 보안 체크리스트
- `TECH-STACK-GUIDE.md`: 기술 스택별 가이드
- `docs/task-plans/`: 각 Task의 구현 계획

---

## 성공 기준

이 Skill은 다음을 목표로 합니다:

1. **신뢰성**: 항상 CLAUDE.md 규칙 준수
2. **안전성**: 보안/프로덕션 영향 사전 차단
3. **효율성**: 토큰 최소화, 반복 작업 자동화
4. **일관성**: 모든 Task가 동일한 품질 기준
5. **투명성**: 모든 결정이 명확하고 추적 가능

---

> **Remember**:
> KakaoPay에서 Claude Code는 지능을 증명하기 위한 것이 아니라,
> **피할 수 있는 실수를 방지**하기 위해 사용됩니다.
>
> 신뢰, 안정성, 책임성이 최우선입니다.
