---
name: task-breaker
description: PRD, Architecture, Tech Stack을 기반으로 작업을 작은 단위(4-8시간)로 분해. 작업 분해, task breakdown, 구현 계획 관련 질문 시 사용.
---

# Task Breaker Skill

## Overview

PRD와 Architecture 문서를 분석하여
실행 가능한 작은 작업 단위로 분해합니다.

## 핵심 원칙

1. **INVEST 원칙** - Independent, Negotiable, Valuable, Estimable, Small, Testable
2. **크기: 4-8시간** - 1일 이내 완료
3. **Vertical Slice** - 기능별 수직 분할
4. **명확한 완료 기준** - Acceptance Criteria 필수

## 분해 프로세스

### Step 1: 문서 읽기

```bash
# PRD 읽기
cat docs/prd/[prd-file].md

# Architecture 읽기 (선택)
cat docs/architecture/architecture.md

# Tech Stack 읽기 (선택)
cat docs/tech-stack/tech-stack.md
```

PRD에서 추출:
- Phase 정의 (Section 9)
- Functional Requirements (Section 5)
- Data Models (Section 7.2)
- Testing Strategy (Section 8)

### Step 2: Phase 확인

"PRD를 분석했습니다.

**Phase 정보:**
- Phase 1: [이름] ([Scope])
- Phase 2: [이름] ([Scope])
- ...

어느 Phase를 분해할까요?"

### Step 3: Epic 정의

선택된 Phase를:

"Phase 1을 Epic으로 나누겠습니다.

**제안 Epic:**

Epic 1: [이름]
- Scope: [범위]
- Goal: [목표]
- Estimate: [예상 시간]

Epic 2: [이름]
...

이 구조로 진행할까요?"

### Step 4: Task 분해

각 Epic을 4-8시간 Task로 분해:

"Epic 1을 Task로 분해하겠습니다.

**Task 1.1**: [이름]
- Description: [설명]
- Estimate: 4-6h
- Acceptance Criteria:
  - [ ] [기준 1]
  - [ ] [기준 2]
- Technical: [구현 힌트]
  - 파일: vector_store.py
  - 함수: connect(), store(), search()
  - 라이브러리: pinecone-client
- Tests:
  - Unit: test_connect()
  - Integration: test_e2e_store_search()
- Dependencies: None
- Priority: P0

**Task 1.2**: [이름]
- Estimate: 2-3h
- Dependencies: Task 1.1
...

각 Task가 4-8시간인가요? 조정이 필요한가요?"

### Step 5: 의존성 분석

```
Task 간 의존성:

Task 1.1 (Pinecone 연결)
  ↓
Task 1.2 (임베딩 생성)
  ↓
Task 1.3 (벡터 저장)

실행 순서: 1.1 → 1.2 → 1.3
병렬 가능: 없음
```

### Step 6: 우선순위 설정

```
P0 (Must-Have): Task 1.1, 1.2, 1.3, 2.1
P1 (Should-Have): Task 1.4, 2.2
P2 (Nice-to-Have): Task 3.1

P0부터 순서대로 진행
```

### Step 7: 문서 생성

```bash
mkdir -p docs/tasks

cat > docs/tasks/phase-1-tasks.md << 'EOFTASK'
# Task Breakdown: Phase 1 - [Phase Name]

[템플릿 기반으로 모든 정보 채우기]

## Meta
- PRD: [파일명]
- Phase: Phase 1
- Total Estimate: [N]h
- Target: [N]주

## Epic 1: [Epic Name]

### Task 1.1: [Task Name]
- Description: [상세]
- Acceptance Criteria:
  - [ ] [기준]
- Estimate: 4h
- Priority: P0
- Dependencies: None

[... 모든 Task ...]

EOFTASK
```

### Step 8: 요약

"✅ Task 분해 완료!

📁 docs/tasks/phase-1-tasks.md

📊 요약:
- Total Epics: [N]
- Total Tasks: [N]
- P0 Tasks: [N] ([예상 시간]h)
- P1 Tasks: [N] ([예상 시간]h)
- Estimated Duration: [N]주

📋 Task 크기 분포:
- 4-6h: [N]개
- 6-8h: [N]개
- Average: [N]h

🔗 의존성:
- Critical Path: Task [X] → [Y] → [Z]
- 병렬 가능: [N]개 Task

✅ INVEST 원칙 준수:
- Independent: ✓
- Negotiable: ✓
- Valuable: ✓
- Estimable: ✓
- Small: ✓ (모두 8h 이하)
- Testable: ✓

다음 단계:
1. Task 분해 검토
2. Task 1.1부터 시작
3. 매일 1-2 Task 완료

첫 Task를 시작할까요?"
```

## Best Practices

### Task 크기 조정

```
너무 큰 Task (12h):
→ 2개로 분해 (6h + 6h)

적절한 Task (6h):
→ 유지

너무 작은 Task (1h):
→ 다른 Task와 병합
```

### Acceptance Criteria 작성

```
✅ 좋은 Criteria:
- [ ] 샘플 PDF 3개 파싱 성공
- [ ] 손상된 PDF에서 에러 메시지 반환
- [ ] 단위 테스트 5개 작성 및 통과

❌ 나쁜 Criteria:
- [ ] PDF 파서 동작
- [ ] 테스트 작성
```

### Technical Details 제공

```
✅ 좋은 Details:
- 파일: services/pdf_parser.py
- 함수: parse_pdf(file_path) -> str
- 라이브러리: PyPDF2
- 예외: InvalidPDFError, CorruptedPDFError

❌ 나쁜 Details:
- PDF 파싱 구현
```

## Error Handling

### PRD 파일 없음

"Task를 분해하려면 PRD가 필요합니다.

PRD 파일 경로를 알려주세요.
또는 /prd-new로 먼저 PRD를 작성하세요."

### Phase 정보 불명확

"PRD에서 Phase 정보를 찾을 수 없습니다.

PRD Section 9 (Implementation Plan)를 확인해주세요.
또는 수동으로 Phase를 정의해주세요."

### Task 너무 큼

"Task [N]이 12시간으로 예상됩니다.

이것은 INVEST 원칙의 'Small'을 위반합니다.
2개로 분해하시겠어요?

Option A: [분해 방안 1]
Option B: [분해 방안 2]"

## 특수 케이스

### 병렬 작업 식별

```
병렬 가능한 Task 그룹:

Group A (Frontend):
- Task 3.1: 검색 UI
- Task 3.2: 결과 표시 UI

Group B (Backend):
- Task 2.1: 검색 API
- Task 2.2: 답변 생성 API

→ Group A와 B는 병렬 진행 가능
```

### 리스크 높은 Task

```
⚠️ High-Risk Task:

Task 2.3: LLM API 연동
- Risk: API 불안정성, 응답 지연
- Mitigation:
  - 타임아웃 설정 (30초)
  - Fallback 메커니즘 추가
  - 재시도 로직 구현
- Spike Task 고려: 2시간 조사 먼저
```

## 마무리

Task 분해의 목표:
- ✅ 매일 완료 가능한 크기
- ✅ 명확한 완료 기준
- ✅ 빠른 피드백
- ✅ 리스크 최소화

이 스킬로 체계적인 작업 분해를! 🚀
