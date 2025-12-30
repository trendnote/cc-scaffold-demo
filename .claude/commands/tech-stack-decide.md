# Decide Tech Stack

PRD를 기반으로 프로젝트 기술 스택을 결정합니다.

## Usage

```
/tech-stack-decide [prd-file]
```

Examples:
```
/tech-stack-decide rag-platform-prd
/tech-stack-decide docs/prd/user-auth-prd.md
```

## What This Command Does

1. **PRD 분석** - 요구사항 추출
2. **카테고리별 옵션 제시** - Backend, Frontend, Database, Infrastructure
3. **비교 기반 선택** - 최소 2-3개 옵션 비교
4. **Tech Stack 문서 생성** - `docs/tech-stack/tech-stack.md`
5. **검증 및 요약**

## Instructions for Claude

### Step 1: PRD 읽기

```bash
# 파일명 정규화
PRD_FILE="$ARGUMENTS"

# .md 추가 (없으면)
if [[ ! "$PRD_FILE" == *.md ]]; then
  PRD_FILE="${PRD_FILE}.md"
fi

# 경로 추가 (없으면)
if [[ ! "$PRD_FILE" == docs/prd/* ]]; then
  PRD_FILE="docs/prd/${PRD_FILE}"
fi

# PRD 존재 확인
if [ -f "$PRD_FILE" ]; then
  echo "📖 PRD 읽는 중: $PRD_FILE"
  cat "$PRD_FILE"
else
  echo "❌ PRD 파일을 찾을 수 없습니다: $PRD_FILE"
  echo ""
  echo "사용 가능한 PRD:"
  ls -1 docs/prd/*.md 2>/dev/null | grep -v "TEMPLATE.md" | grep -v "README.md"
  exit 1
fi
```

### Step 2: tech-stack-decider Skill 활성화

```
"$PRD_FILE의 기술 스택을 결정하겠습니다.

tech-stack-decider 스킬을 활성화합니다.

[PRD 분석 시작]"
```

이후 tech-stack-decider 스킬의 프로세스 따름:
1. PRD 요구사항 추출
2. 카테고리별 옵션 제시
3. 사용자 선택 받기
4. 비교 기반 문서화
5. tech-stack.md 생성

### Step 3: 문서 생성

```bash
# 템플릿 확인
if [ -f "docs/tech-stack/TEMPLATE.md" ]; then
  echo "✓ 템플릿 발견"
  TEMPLATE_CONTENT=$(cat docs/tech-stack/TEMPLATE.md)
else
  echo "ℹ️  템플릿 없음 - 기본 구조 사용"
fi

# Tech Stack 디렉토리 생성
mkdir -p docs/tech-stack

# 문서 생성
cat > docs/tech-stack/tech-stack.md << 'EOFTECH'
# Tech Stack: [Project Name from PRD]

[... 사용자 선택 기반으로 템플릿 채우기 ...]

EOFTECH

echo "✅ Tech Stack 문서 생성!"
```

### Step 4: 품질 체크

생성된 문서 검증:

```
✅ 필수 항목 체크:
- [ ] PRD Reference 명시
- [ ] 모든 카테고리 결정 (Backend, Frontend, Database, Infrastructure)
- [ ] 각 선택마다 Rationale 존재
- [ ] 최소 1개 비교 표 포함
- [ ] Risks & Mitigation 작성
- [ ] Team Readiness 평가

⚠️ 누락 항목 경고
```

### Step 5: 최종 요약

```
"🎉 Tech Stack 결정 완료!

📁 파일: docs/tech-stack/tech-stack.md

## 선택된 기술 스택

**Backend**
- Language: [선택]
- Framework: [선택]

**Frontend**
- Framework: [선택]
- Language: [선택]

**Database**
- Primary: [선택]
- Cache: [선택]
- Special: [선택]

**Infrastructure**
- Cloud: [선택]
- Container: [선택]

**External Services**
- [주요 서비스들]

## PRD 충족도

총점: [N]/25 → [비율]%
- Backend: [점수]/5
- Frontend: [점수]/5
- Database: [점수]/5
- Infrastructure: [점수]/5
- External: [점수]/5

✅ PRD 요구사항 충족 가능

## 주요 결정 근거

1. [Backend 선택]: [이유]
2. [Frontend 선택]: [이유]
3. [Database 선택]: [이유]

## 예상 비용

- Infrastructure: $[금액]/월
- External Services: $[금액]/월
- 총 예상: $[금액]/월

## Team Readiness

- 학습 필요 기술: [목록]
- 예상 학습 기간: [기간]
- 교육 계획: [필요/불필요]

## 다음 단계

1. ✅ Tech Stack 문서 검토
2. ⏭️ 이해관계자 승인
3. ⏭️ Architecture 설계: /architecture-design
4. ⏭️ 개발 환경 설정

질문이 있으신가요?"
```

## Best Practices

### DO:
- ✅ PRD 철저히 분석
- ✅ 최소 2-3개 옵션 비교
- ✅ 각 선택에 명확한 근거
- ✅ 팀 역량 고려
- ✅ 비용 추정 포함

### DON'T:
- ❌ 유행만 따르기
- ❌ 비교 없이 결정
- ❌ PRD 무시하고 선택
- ❌ 과도한 복잡도

## Example Usage

```
사용자: /tech-stack-decide rag-platform-prd

Claude: 📖 PRD 읽는 중: docs/prd/rag-platform-prd.md

[PRD 분석]

"RAG 기반 사내 정보 검색 플랫폼의 기술 스택을 결정하겠습니다.

**PRD 핵심 요구사항:**

기능적:
- FR-1: 자연어 검색
- FR-2: RAG 기반 답변 생성
- FR-3: 문서 인덱싱
- FR-4: 사용자 인증

비기능적:
- Performance: 응답 시간 30초 이내
- Scalability: 100명 동시 사용자
- Security: SSO 연동, 문서 권한 관리

특수 요구사항:
- LLM API 필요 (OpenAI/Claude)
- Vector Database 필요
- 문서 파싱 (PDF, DOCX, etc)

이 이해가 맞나요? 추가 제약사항이 있나요?"

사용자: "맞습니다. 예산은 월 $500 이내입니다."

Claude: "예산 제약 확인했습니다. 비용을 고려하여 옵션을 제시하겠습니다.

### Backend 언어 및 프레임워크

**Option 1: Python 3.11 + FastAPI** ⭐ 권장
- 장점:
  - LangChain, PyPDF2 등 문서 처리 라이브러리 풍부
  - AI/ML 생태계 최고
  - 빠른 개발 속도
- 단점:
  - 실행 속도 상대적으로 느림
- PRD 충족: ⭐⭐⭐⭐⭐
- 비용: $0 (오픈소스)

**Option 2: TypeScript + NestJS**
- 장점:
  - Frontend와 언어 통일
  - 엔터프라이즈급 구조
- 단점:
  - LLM/문서 처리 라이브러리 부족
- PRD 충족: ⭐⭐⭐
- 비용: $0

**Option 3: Go**
- 장점:
  - 뛰어난 성능
- 단점:
  - AI/ML 생태계 약함
  - RAG 구현 어려움
- PRD 충족: ⭐⭐
- 비용: $0

**권장: Python + FastAPI**
- RAG 기능에 필수적인 생태계
- 30초 성능 목표는 LLM API 지연이 주요 요인이므로 언어 속도 덜 중요
- 팀 학습 용이

선택해주세요."

[... 모든 카테고리 진행 ...]

Claude: "🎉 Tech Stack 결정 완료!

📁 docs/tech-stack/tech-stack.md

**선택 요약:**
- Backend: Python 3.11 + FastAPI
- Frontend: Next.js 14 + TypeScript
- Database: PostgreSQL + Pinecone
- Cloud: AWS (월 $300 예상)
- LLM: OpenAI GPT-4 (월 $150 예상)

**총 예상 비용**: $450/월 (예산 내)

다음: /architecture-design"
```
