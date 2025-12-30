# Create New PRD

간결하고 실용적인 PRD를 작성합니다.

## Usage

```
/prd-new [feature-name]
```

Examples:
```
/prd-new 사용자 로그인
/prd-new user-authentication
```

## What This Command Does

1. **PRD 작성 필요성 확인**
2. **구조화된 인터뷰 진행** (12개 질문)
3. **PRD 파일 생성** (`docs/prd/[feature-name]-prd.md`)
4. **품질 검증 및 요약**

## Instructions for Claude

### Step 1: 템플릿 확인

```bash
# 프로젝트 템플릿 확인
if [ -f "docs/prd/TEMPLATE.md" ]; then
  echo "✓ 프로젝트 템플릿 발견"
  cat docs/prd/TEMPLATE.md
  TEMPLATE_FOUND=true
else
  echo "ℹ️  템플릿 없음 - 기본 구조 사용"
  TEMPLATE_FOUND=false
fi

# README 확인
if [ -f "docs/prd/README.md" ]; then
  echo "✓ PRD 가이드 발견"
  cat docs/prd/README.md
fi
```

### Step 2: Skill 활성화

```
prd-creator 스킬을 활성화합니다.

사용자에게:

"'$ARGUMENTS' 기능의 PRD를 작성하겠습니다.

간결하고 실용적인 PRD 작성 원칙:
1. 명확성 우선 - 애매한 표현 금지
2. 문제 정의 > 해결책
3. Out of Scope 명시 (매우 중요)
4. 측정 가능한 성공 기준

12개 질문으로 15-20분 소요됩니다.
시작할까요?"
```

### Step 3: 인터뷰 진행

prd-creator 스킬의 인터뷰 프로세스 따름:

**Phase 1: 핵심 이해 (5개 질문)**
1. Problem Statement
2. Goals
3. Non-Goals
4. Target Users
5. Success Metrics

**Phase 2: 상세 요구사항 (7개 질문)**
6. User Stories
7. Functional Requirements (P0)
8. Non-Functional Requirements
9. Data Models
10. Testing Strategy
11. Implementation Plan
12. Risks & Mitigation

**중요: 한 번에 하나씩 질문!**

### Step 4: PRD 생성

```bash
# 파일명 생성
FEATURE_NAME="$ARGUMENTS"
FEATURE_SLUG=$(echo "$FEATURE_NAME" | tr '[:upper:]' '[:lower:]' | tr ' ' '-' | tr -cd '[:alnum:]-')

# PRD 디렉토리 생성
mkdir -p docs/prd

# PRD 작성
cat > "docs/prd/${FEATURE_SLUG}-prd.md" << 'EOFPRD'
# PRD: ${FEATURE_NAME}

---

## Meta
- Status: Draft
- Owner: [작성자명]
- Stakeholders: [이해관계자]
- Last Updated: $(date +%Y-%m-%d)
- Target Release: [목표 릴리스]

---

## 1. Executive Summary

[인터뷰에서 수집한 정보로 1-2문단 요약:
- 어떤 문제를 해결하는가
- 어떻게 해결하는가
- 성공을 어떻게 측정하는가]

---

## 2. Problem Statement

[질문 1에서 수집한 내용:
- 사용자가 겪는 구체적 문제
- 왜 지금 중요한지
- 현재 상황과 영향]

---

## 3. Goals & Non-Goals

### 3.1 Goals

[질문 2에서 수집한 목표 - 측정 가능하게]
- Goal 1: [구체적 목표 + 지표]
- Goal 2: [구체적 목표 + 지표]

### 3.2 Non-Goals

[질문 3에서 수집 - 의도적 제외 항목]
- Non-Goal 1: [이유와 함께]
- Non-Goal 2: [이유와 함께]

---

## 4. Target Users & Use Cases

### 4.1 Target Users

[질문 4에서 수집]
- User Type 1: [설명]
- User Type 2: [설명]

### 4.2 User Stories

[질문 6에서 수집 - Given/When/Then]

**US-1**: [제목]
- Given: [초기 상태]
- When: [사용자 행동]
- Then: [예상 결과]

**US-2**: [제목]
- Given: [초기 상태]
- When: [사용자 행동]
- Then: [예상 결과]

---

## 5. Functional Requirements (P0)

[질문 7에서 수집 - Must-Have만]

**FR-1**: [요구사항 제목]
- Description: [상세 설명]
- Acceptance Criteria:
  - [ ] [테스트 가능한 조건 1]
  - [ ] [테스트 가능한 조건 2]
  - [ ] [테스트 가능한 조건 3]

**FR-2**: [요구사항 제목]
- Description: [상세 설명]
- Acceptance Criteria:
  - [ ] [테스트 가능한 조건 1]
  - [ ] [테스트 가능한 조건 2]

---

## 6. Non-Functional Requirements

[질문 8에서 수집]

- **Performance**: [응답 시간, 처리량 등]
- **Security**: [보안 요구사항]
- **Availability**: [목표 가동률]
- **Accessibility**: [접근성 요구사항]

---

## 7. Technical Considerations

### 7.1 Architecture Overview

[고수준 아키텍처 설명]

### 7.2 Data Models

[질문 9에서 수집 - TypeScript 인터페이스]

```typescript
[인터뷰에서 수집한 데이터 모델을 TypeScript로]
```

### 7.3 Dependencies

- Internal: [내부 의존성]
- External: [외부 의존성]

---

## 8. Testing Strategy

[질문 10에서 수집]

### 8.1 Unit Tests
- [테스트 대상 1]
- [테스트 대상 2]

### 8.2 Integration Tests
- [통합 시나리오 1]
- [통합 시나리오 2]

### 8.3 E2E Tests
- [전체 플로우 1]
- [전체 플로우 2]

---

## 9. Implementation Plan

[질문 11에서 수집]

### Phase 1: [단계명]
- **Scope**: [범위]
- **Deliverables**: [산출물]
- **Acceptance Criteria**:
  - [ ] [완료 조건 1]
  - [ ] [완료 조건 2]

### Phase 2: [단계명]
- **Scope**: [범위]
- **Deliverables**: [산출물]
- **Acceptance Criteria**:
  - [ ] [완료 조건 1]
  - [ ] [완료 조건 2]

---

### Claude Code Instructions

#### Before Starting
1. Read this entire PRD
2. Confirm understanding of:
   - Problem Statement (Section 2)
   - All P0 Requirements (Section 5)
   - Data Models (Section 7.2)
3. If anything is unclear, ASK before coding

#### During Implementation
1. Implement requirements in order: FR-1 → FR-2 → ...
2. Use data models EXACTLY as defined in Section 7.2
3. Include all acceptance criteria as test cases
4. Follow testing strategy in Section 8
5. Do NOT add features not in P0 requirements

#### Validation Checklist
- [ ] All P0 requirements implemented
- [ ] All acceptance criteria met
- [ ] All tests passing (unit + integration + E2E)
- [ ] No Out-of-Scope features added
- [ ] Performance requirements met (Section 6)

#### When in Doubt
❌ DON'T: Make assumptions
✅ DO: Ask "The requirement says X but doesn't specify Y. Should I...?"

---

## 10. Risks & Open Questions

[질문 12에서 수집]

### 10.1 Risks
- **Risk 1**: [위험]
  - Mitigation: [완화 방안]
- **Risk 2**: [위험]
  - Mitigation: [완화 방안]

### 10.2 Open Questions
- [OPEN QUESTION] [미결정 사항]

---

## 11. Metrics & Monitoring

[질문 5에서 수집한 Success Metrics 확장]

### Launch Criteria
- [ ] All P0 requirements implemented and tested
- [ ] Performance benchmarks met
- [ ] Security review completed
- [ ] Stakeholder approval received

### Success Metrics (30일 후 측정)

| 지표 | 목표 | 측정 방법 |
|------|------|-----------|
| [Metric 1] | [Target] | [Method] |
| [Metric 2] | [Target] | [Method] |
| [Metric 3] | [Target] | [Method] |

---

## 12. Change Log

| Date | Author | Description |
|------|--------|-------------|
| $(date +%Y-%m-%d) | [작성자] | Initial version |

EOFPRD

echo "✅ PRD 생성 완료: docs/prd/${FEATURE_SLUG}-prd.md"
```

### Step 5: 품질 체크 및 요약

```
생성된 PRD 파일을 읽고 품질 검증:

✅ 필수 섹션 완성도:
- [ ] Problem Statement: 구체적인가?
- [ ] Goals: 측정 가능한가?
- [ ] Non-Goals: 명시되었는가?
- [ ] P0 Requirements: 인수 조건 포함?
- [ ] Data Models: TypeScript 형식?
- [ ] Testing Strategy: 구체적인가?
- [ ] Claude Code Instructions: 포함?

⚠️ 품질 경고:
- "적당히", "유연하게" 같은 애매한 표현 발견 시 경고
- 측정 불가능한 목표 발견 시 경고
- P0 요구사항에 인수 조건 없으면 경고

최종 요약 제공:

🎉 PRD 작성 완료!

📁 파일: docs/prd/[feature]-prd.md

📊 통계:
- Problem: [1문장 요약]
- Goals: [N]개 (모두 측정 가능)
- Non-Goals: [N]개
- P0 Requirements: [N]개
- User Stories: [N]개
- Test Scenarios: [N]개
- Implementation Phases: [N]개

⚠️ [TODO] 항목: [N]개
[필요시 목록]

✅ 품질 체크:
- 명확성: 애매한 표현 없음
- 측정 가능성: 모든 목표 정량화
- 범위: Out of Scope 명시
- 테스트 가능성: 모든 FR에 인수 조건

다음 단계:
1. PRD 검토: /prd-review [feature-name]
2. 섹션 보강: "[섹션명] 더 자세히 작성해줘"
3. 구현 시작: /prd-implement [feature-name]
```

## Best Practices

### DO:
- ✅ 한 번에 하나씩 질문
- ✅ 사용자 답변 확인 후 다음 진행
- ✅ 구체적 예시 제공
- ✅ 애매한 답변은 명확히
- ✅ [TODO] 명시

### DON'T:
- ❌ 여러 질문 한번에
- ❌ 사용자 답변 가정
- ❌ 기술 구현 방식 제안
- ❌ Out of Scope 누락
- ❌ Claude Code Instructions 빠뜨림

## Example Usage

```
사용자: /prd-new 사용자 로그인

Claude: "사용자 로그인 기능의 PRD를 작성하겠습니다.

간결하고 실용적인 PRD 작성 원칙:
1. 명확성 우선
2. 문제 정의 > 해결책
3. Out of Scope 명시
4. 측정 가능한 성공 기준

12개 질문으로 15-20분 소요됩니다.
시작할까요?"

사용자: "네"

Claude: "좋습니다!

질문 1/12: Problem Statement

현재 사용자가 로그인과 관련해서 겪고 있는 구체적인 문제는 무엇인가요?

원칙: '해결책보다 문제 정의'

❌ 나쁜 예: '로그인 기능이 없다'
✅ 좋은 예: '사용자가 매번 정보를 입력해야 해서 이탈률이 40%'

답변 부탁드립니다."

[인터뷰 계속...]
```

## Related Commands

- `/prd-review [filename]` - PRD 품질 검토
