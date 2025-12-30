---
name: prd-creator
description: 간결하고 실용적인 PRD 작성 지원. PRD, 요구사항, 제품 명세서 작성 시 사용. Use when user wants to create, review, or enhance Product Requirements Document.
---

# PRD Creator Skill

## Overview

이 스킬은 실용적이고 간결한 PRD 작성을 돕습니다.
프로젝트의 PRD 작성 철학을 기반으로 명확하고 구체적인 요구사항 정의를 지원합니다.

## 핵심 원칙

1. **명확성 우선** - 애매한 표현 금지
2. **문제 정의 > 해결책** - How보다 What과 Why
3. **범위 명시** - Out of Scope가 매우 중요
4. **측정 가능한 성공 기준** - 정량 지표 포함

## When to Use This Skill

사용자가 다음을 언급할 때:
- "PRD 작성"
- "요구사항 정의"
- "제품 명세서"
- "기능 정의"

## PRD 작성이 필요한 경우

다음 중 하나라도 해당되면 PRD 작성:
- 새로운 기능 또는 서비스 개발
- 기존 기능의 의미 있는 변경
- 사용자 경험(UX) 변화
- 정책/규칙/조건 변경
- 여러 팀이 함께 작업하는 경우

## 인터뷰 프로세스

### Phase 1: 핵심 이해 (5개 질문)

**질문 1: Problem Statement**
```
문제를 명확히 정의하겠습니다.

사용자가 현재 겪고 있는 구체적인 문제는 무엇인가요?

원칙: "해결책보다 문제 정의"
- 기술적 구현이 아닌, 사용자 관점의 문제
- 왜 지금 이 문제가 중요한지

❌ 나쁜 예: "결제 API를 개선해야 한다"
✅ 좋은 예: "사용자가 결제 완료까지 평균 45초가 걸려 이탈률이 30%"
```

**질문 2: Goals (목표)**
```
이 PRD로 달성하려는 목표를 말씀해주세요.

원칙: "측정 가능하게"
- 정량적 지표 포함
- 최소 성공 조건 정의

❌ 나쁜 예: "결제를 빠르게 한다"
✅ 좋은 예: "결제 완료 시간을 평균 20초 이내로 단축, 이탈률 10% 이하"
```

**질문 3: Non-Goals (의도적 제외)**
```
이번 범위에서 의도적으로 제외하는 것은 무엇인가요?

원칙: "Out of Scope는 매우 중요하다"
- 범위 크립(Scope Creep) 방지

예시:
- "해외 결제는 이번 범위에서 제외"
- "정기 결제 기능은 2단계로 미룸"
```

**질문 4: Target Users**
```
주요 사용자는 누구인가요?

구체적으로:
- 사용자 유형/역할
- 각 유형의 특징
- 예상 사용 빈도

예시:
✅ "일일 거래 10건 이상 처리하는 소상공인 (월 1,000명 추정)"
```

**질문 5: Success Metrics**
```
성공을 어떻게 측정하나요?

원칙: "잘 되었는지 판단 가능해야 함"

다음 중 측정 가능한 지표를 선택:
1. 사용성 지표 (예: 완료율, 소요 시간, 에러율)
2. 비즈니스 지표 (예: 전환율, 재방문율, 매출)
3. 기술 지표 (예: 응답 시간, 가용성, 처리량)

최소 2개 이상 정의해주세요.
```

### Phase 2: 상세 요구사항 (7개 영역)

사용자의 답변을 바탕으로 다음을 순차적으로 질문:

**영역 1: User Stories**
```
주요 사용 시나리오를 Given/When/Then 형식으로 말씀해주세요.

예시:
- Given: 로그인한 상태에서
- When: 결제 버튼을 클릭하면
- Then: 2초 이내에 결제 화면이 표시된다

최소 2-3개 시나리오를 부탁드립니다.
```

**영역 2: Functional Requirements (P0)**
```
Must-Have 요구사항을 알려주세요.

원칙: "각 항목은 테스트 가능해야 함"

예시 형식:
FR-1: 사용자 인증
- Description: 이메일/비밀번호로 로그인
- Acceptance Criteria:
  - [ ] 유효한 이메일 형식 검증
  - [ ] 비밀번호 8자 이상 검증
  - [ ] 5회 실패 시 계정 잠금

각 요구사항마다 구체적인 인수 조건을 포함해주세요.
```

**영역 3: Non-Functional Requirements**
```
성능, 보안, 가용성 요구사항이 있나요?

- Performance: 목표 응답 시간?
- Security: 보안 요구사항?
- Availability: 목표 가동률?
- Accessibility: 접근성 요구사항?

예시:
- "API 응답 시간 95%ile < 500ms"
- "개인정보는 암호화 저장"
- "99.9% 가용성 목표"
```

**영역 4: Data Models**
```
주요 데이터 구조를 TypeScript 인터페이스로 정의해주시겠어요?

원칙: "가능하면 TypeScript 인터페이스로 작성"

예시:
```typescript
interface Payment {
  id: string;
  amount: number;        // 100-10,000,000 원
  status: 'pending' | 'completed' | 'failed';
  createdAt: Date;
}
```

주요 엔티티 2-3개만 부탁드립니다.
```

**영역 5: Testing Strategy**
```
테스트 전략을 말씀해주세요.

- Unit Tests: 어떤 단위를 테스트?
- Integration Tests: 어떤 통합 시나리오?
- E2E Tests: 어떤 전체 플로우?

예시:
- Unit: "결제 금액 검증 로직"
- Integration: "결제 API와 DB 연동"
- E2E: "로그인 → 결제 → 완료 전체 플로우"
```

**영역 6: Implementation Plan**
```
구현을 몇 단계로 나누고 싶으신가요?

각 Phase마다:
- Scope: 범위
- Deliverables: 산출물
- Acceptance Criteria: 완료 조건

예시:
Phase 1: 기본 결제 플로우
- Scope: 카드 결제만 지원
- Deliverables: API 3개, UI 2개 화면
- Acceptance Criteria: 전체 E2E 테스트 통과
```

**영역 7: Risks & Mitigation**
```
예상되는 리스크와 완화 방안이 있나요?

예시:
- Risk: 외부 결제 게이트웨이 장애
- Mitigation: 타임아웃 설정 + 재시도 로직

최소 2-3개 정도만 부탁드립니다.
```

## PRD 생성 프로세스

### Step 1: 템플릿 로딩

```bash
# 프로젝트의 PRD 템플릿 확인
if [ -f "docs/prd/TEMPLATE.md" ]; then
  cat docs/prd/TEMPLATE.md
else
  echo "템플릿을 찾을 수 없습니다. 기본 구조를 사용하겠습니다."
fi
```

### Step 2: 인터뷰 기반 PRD 작성

인터뷰에서 수집한 정보로 PRD 생성:

1. Meta 정보 채우기
2. Executive Summary 작성 (1문단 요약)
3. Problem Statement 상세화
4. Goals & Non-Goals 명시
5. User Stories 작성 (Given/When/Then)
6. Functional Requirements 나열 (각 FR마다 인수 조건)
7. Technical Considerations 포함
8. Testing Strategy 정의
9. Implementation Plan 단계화
10. Claude Code Instructions 추가

### Step 3: PRD 파일 생성

```bash
# kebab-case 파일명 생성
FEATURE_SLUG=$(echo "$FEATURE_NAME" | tr '[:upper:]' '[:lower:]' | tr ' ' '-')

# PRD 파일 저장
cat > "docs/prd/${FEATURE_SLUG}-prd.md" << 'EOF'
[생성된 PRD 내용]
EOF

echo "✅ PRD 생성 완료: docs/prd/${FEATURE_SLUG}-prd.md"
```

### Step 4: 검토 및 요약

```
✅ PRD 생성 완료!

📄 파일: docs/prd/[feature-name]-prd.md

📋 포함 내용:
- Problem Statement: [1문장 요약]
- Goals: [주요 목표 1-2개]
- P0 Requirements: [개수]
- User Stories: [개수]
- Testing Strategy: 포함됨
- Implementation Phases: [개수]

⚠️ [TODO] 표시된 섹션:
- [섹션명]: [이유]

다음 단계:
1. PRD 검토 필요 시: "PRD 검토해줘"
2. 특정 섹션 보강: "[섹션명] 더 자세히 작성해줘"
3. 구현 시작: "이 PRD로 구현 시작"
```

## PRD 작성 베스트 프랙티스

### 명확성 확보

**❌ 피해야 할 표현:**
- "적당히", "유연하게", "가능하면"
- "좋은 성능", "빠르게", "안정적으로"
- "사용자 친화적", "편리하게"

**✅ 권장 표현:**
- "3초 이내", "에러율 5% 이하"
- "월 10만 건 처리", "동시 접속 1000명"
- "3단계 이내 완료", "클릭 2번으로 완료"

### Out of Scope 작성 요령

```
✅ 좋은 Non-Goals:
- "모바일 앱은 이번 범위에서 제외 (웹만 우선)"
- "다국어 지원은 2단계에서 진행"
- "AI 추천 기능은 별도 PRD로 작성 예정"

이유 명시:
- 리소스 제약
- 우선순위
- 기술적 제약
- 비즈니스 판단
```

### 측정 가능한 성공 기준

```
✅ 좋은 Success Metrics:
- "결제 완료율 85% 이상"
- "평균 응답 시간 2초 이내"
- "월간 활성 사용자 10,000명"
- "고객 만족도 4.0/5.0 이상"

각 지표마다:
- 측정 방법 명시
- 목표 수치 명시
- 측정 주기 명시
```

## Claude Code 통합

### PRD 읽기 지침

PRD가 완성되면 Claude Code에게 다음 지침 포함:

```markdown
### Claude Code Instructions

#### Before Starting
1. Read this entire PRD
2. Confirm understanding of:
   - Problem Statement (Section 2)
   - All P0 Requirements (Section 5)
   - Data Models (Section 7.2)
3. If anything is unclear or ambiguous, ASK before proceeding

#### During Implementation
1. Implement requirements in order: FR-1 → FR-2 → ...
2. Use data models EXACTLY as defined
3. Include all acceptance criteria as test cases
4. Follow testing strategy in Section 8
5. Do NOT add features not in P0 requirements

#### Validation Checklist
- [ ] All P0 requirements implemented
- [ ] All acceptance criteria met
- [ ] All tests passing (unit + integration + E2E)
- [ ] No Out-of-Scope features added
- [ ] Performance requirements met

#### When in Doubt
❌ DON'T: Make assumptions and implement
✅ DO: Ask "The requirement says X, but doesn't specify Y. Should I...?"
```

## 에러 처리

### 불충분한 정보

```
사용자가 답변을 "잘 모르겠어" 또는 "나중에 결정"이라고 하면:

"이해했습니다. 이 부분은 [TODO: 결정 필요]로 표시하겠습니다.

다만, P0 요구사항은 구현 전에 반드시 명확해야 합니다.
나중에 이 섹션을 보완하시겠어요, 아니면 지금 더 논의하시겠어요?"
```

### 모호한 답변

```
답변이 모호한 경우:

"말씀하신 '[사용자 답변]'을 구체화하고 싶습니다.

예를 들어:
- Option A: [구체적 해석 1]
- Option B: [구체적 해석 2]

어느 쪽에 더 가까운가요? 또는 다른 의미인가요?"
```

### 범위 초과

```
사용자가 너무 많은 기능을 요구하면:

"말씀하신 내용이 상당히 많습니다.

현재 Goals:
- [Goal 1]
- [Goal 2]

다음은 별도 PRD로 분리하는 것이 좋을 것 같습니다:
- [기능 A]: 이유 - [별도 PRD 권장 이유]
- [기능 B]: 이유 - [별도 PRD 권장 이유]

현재 PRD는 [핵심 기능]에 집중하시겠어요?"
```

## 품질 체크리스트

PRD 생성 후 자동 확인:

```
✅ 필수 섹션 완성도:
- [ ] Problem Statement: 구체적인가?
- [ ] Goals: 측정 가능한가?
- [ ] Non-Goals: 명시되었는가?
- [ ] User Stories: Given/When/Then 형식인가?
- [ ] FR (P0): 각각 인수 조건이 있는가?
- [ ] Data Models: TypeScript 인터페이스인가?
- [ ] Testing Strategy: 구체적인가?
- [ ] Success Metrics: 측정 방법이 명시되었는가?

⚠️ 품질 확인:
- [ ] 애매한 표현 없음 ("적당히", "유연하게" 등)
- [ ] 모든 P0에 테스트 가능한 인수 조건
- [ ] 숫자/수치로 명시된 성공 기준
- [ ] Claude Code Instructions 포함
```

## 마무리

PRD 생성 완료 후:

```
🎉 PRD 작성 완료!

📁 파일: docs/prd/[feature-name]-prd.md

📊 통계:
- P0 Requirements: [N]개
- User Stories: [N]개
- Test Scenarios: [N]개
- Implementation Phases: [N]개

다음 단계:
1. ✅ PRD 검토: "이 PRD 검토해줘"
2. ✅ 특정 섹션 보강: "[섹션] 더 자세히"
3. ✅ 이해관계자 공유 후 승인
4. ✅ 승인 후 구현 시작: "Phase 1 구현 시작"

원칙 준수:
✅ 명확성: 애매한 표현 없음
✅ 문제 정의: 기술보다 비즈니스 중심
✅ 범위 명시: Out of Scope 명확
✅ 측정 가능: 정량 지표 포함
```

## 예시: 빠른 시작

```
사용자: "사용자 로그인 기능 PRD 작성해줘"

Skill 활성화 →

Claude: "사용자 로그인 기능의 PRD를 작성하겠습니다.

먼저 문제를 명확히 하겠습니다.

질문 1/5: Problem Statement

현재 사용자가 로그인과 관련해서 겪고 있는 구체적인 문제는 무엇인가요?

원칙: '해결책보다 문제 정의'

❌ 나쁜 예: '로그인 기능이 없다'
✅ 좋은 예: '사용자가 매번 정보를 입력해야 해서 이탈률이 40%'

답변 부탁드립니다."
```

## 중요 원칙 (항상 기억)

1. **한 번에 하나씩 질문** - 사용자 압도 방지
2. **답변 확인 후 진행** - 오해 방지
3. **구체적 예시 제공** - 명확성 확보
4. **Todo 명시** - 불완전한 부분 표시
5. **Claude Code 지침 포함** - 구현 가능성 보장

이 스킬의 목표는 **"잘못된 개발을 예방하기 위한 도구"**로서 PRD를 만드는 것입니다.
