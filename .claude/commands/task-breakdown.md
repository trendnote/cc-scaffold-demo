# Task Breakdown

PRD의 특정 Phase를 작은 작업 단위로 분해합니다.

## Usage

```
/task-breakdown [prd-file] [phase]
```

Examples:
```
/task-breakdown rag-platform-prd phase-1
/task-breakdown docs/prd/user-auth-prd.md phase-2
```

## What This Command Does

1. **PRD 읽기** - Phase 정보 추출
2. **Epic 정의** - 큰 단위 분해
3. **Task 분해** - 4-8시간 단위
4. **의존성 분석** - Task 순서 결정
5. **우선순위 설정** - P0/P1/P2
6. **Task 문서 생성** - `docs/tasks/[phase]-tasks.md`

## Instructions for Claude

### Step 1: PRD 읽기

```bash
PRD_FILE="$1"
PHASE="${2:-phase-1}"

# 파일명 정규화
if [[ ! "$PRD_FILE" == *.md ]]; then
  PRD_FILE="${PRD_FILE}.md"
fi

if [[ ! "$PRD_FILE" == docs/prd/* ]]; then
  PRD_FILE="docs/prd/${PRD_FILE}"
fi

if [ -f "$PRD_FILE" ]; then
  echo "📖 PRD 읽는 중: $PRD_FILE"
  cat "$PRD_FILE"
else
  echo "❌ PRD를 찾을 수 없습니다"
  exit 1
fi
```

### Step 2: task-breaker Skill 활성화

task-breaker 스킬의 프로세스 따름:
1. Phase 확인 및 선택
2. Epic 정의
3. Task 분해 (4-8시간)
4. Acceptance Criteria 정의
5. 의존성 분석
6. 우선순위 설정

### Step 3: 문서 생성

```bash
mkdir -p docs/tasks

OUTPUT_FILE="docs/tasks/${PHASE}-tasks.md"

cat > "$OUTPUT_FILE" << 'EOFTASK'
# Task Breakdown: [Phase Name from PRD]

[사용자 입력과 PRD 기반으로 템플릿 채우기]

EOFTASK

echo "✅ Task 분해 완료: $OUTPUT_FILE"
```

### Step 4: 품질 체크

```
✅ 품질 검증:
- [ ] 모든 Task 4-8시간
- [ ] 각 Task에 Acceptance Criteria
- [ ] 의존성 명시
- [ ] 우선순위 설정 (P0/P1/P2)
- [ ] Technical Details 포함
- [ ] Test Strategy 정의

⚠️ 경고:
- Task [N]이 10시간 → 분해 권장
- Task [N]에 Criteria 없음 → 추가 필요
```

### Step 5: 최종 요약

"🎉 Task 분해 완료!

📁 docs/tasks/[phase]-tasks.md

## 분해 요약

**Epics**: [N]개
**Tasks**: [N]개
**Estimated Duration**: [N]주

## Task 분포

| Priority | Count | Hours |
|----------|-------|-------|
| P0 | [N] | [Nh] |
| P1 | [N] | [Nh] |
| P2 | [N] | [Nh] |
| **Total** | **[N]** | **[Nh]** |

## Task 크기

- 4-6h: [N]개
- 6-8h: [N]개
- Average: [N]h

✅ 모두 8시간 이하

## 의존성

Critical Path:
Task [X] → Task [Y] → Task [Z]

병렬 가능:
- Group A: Task [X], [Y]
- Group B: Task [Z], [W]

## INVEST 체크

- ✅ Independent
- ✅ Negotiable
- ✅ Valuable
- ✅ Estimable
- ✅ Small (모두 ≤8h)
- ✅ Testable

## 다음 단계

1. ✅ Task 검토 및 조정
2. ⏭️ Task 1.1부터 시작
3. ⏭️ 매일 1-2 Task 완료
4. ⏭️ Weekly Review

첫 Task를 시작할까요?
- Task 1.1: [이름] (4h)
- Acceptance: [기준]
- Technical: [힌트]"
```

## Best Practices

### DO:
- ✅ PRD Phase 충실히 반영
- ✅ 4-8시간 크기 엄수
- ✅ 명확한 Acceptance Criteria
- ✅ Technical Details 제공
- ✅ 의존성 명시

### DON'T:
- ❌ 너무 크게 분해 (10h+)
- ❌ 수평 분할 (레이어별)
- ❌ 애매한 완료 기준
- ❌ Technical Details 생략
- ❌ 의존성 무시

## Example Usage

```
사용자: /task-breakdown rag-platform-prd phase-1

Claude: 📖 PRD 읽는 중: docs/prd/rag-platform-prd.md

[PRD 분석]

"Phase 1: 기본 인프라 구축을 분해하겠습니다.

**PRD Phase 1 Scope:**
- 벡터 DB 구축 (Pinecone)
- LLM API 연동 (OpenAI)
- 문서 파싱 (PDF, TXT)
- 임베딩 파이프라인

**제안 Epic:**

Epic 1: 외부 서비스 연동 (2일)
- Pinecone, OpenAI API

Epic 2: 문서 처리 (3일)
- 파싱, 청킹, 벡터화

진행할까요?"

사용자: "네"

Claude: "Epic 1을 Task로 분해합니다.

**Task 1.1**: Pinecone 초기 설정
- Estimate: 4h
- Acceptance:
  - [ ] API 키 설정 및 환경 변수
  - [ ] 인덱스 생성 (dimension=1536)
  - [ ] 연결 테스트 성공
- Technical:
  - 파일: services/vector_store.py
  - 라이브러리: pinecone-client
  - 환경 변수: PINECONE_API_KEY, PINECONE_ENV
- Tests:
  - test_connection()
  - test_create_index()
- Dependencies: None
- Priority: P0

**Task 1.2**: OpenAI API 연동
- Estimate: 2h
- Acceptance:
  - [ ] API 키 설정
  - [ ] 임베딩 생성 테스트 (text-embedding-ada-002)
  - [ ] 에러 핸들링 (rate limit, timeout)
- Dependencies: None
- Priority: P0

[... 모든 Task ...]

✅ 총 15개 Task, 예상 4주

docs/tasks/phase-1-tasks.md 생성 완료!"
```

## Related Commands

- `/prd-new [feature]` - PRD 작성
- `/architecture-design [prd]` - 아키텍처 설계
- `/task-plan` - 일일 Task 계획 (다음)
