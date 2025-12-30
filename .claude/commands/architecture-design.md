# Design Architecture

PRD와 Tech Stack을 기반으로 시스템 아키텍처를 설계합니다.

## Usage

```
/architecture-design [prd-file] [tech-stack-file]
```

Examples:
```
/architecture-design rag-platform-prd tech-stack
/architecture-design docs/prd/user-auth-prd.md docs/tech-stack/tech-stack.md
```

## What This Command Does

1. **PRD + Tech Stack 읽기**
2. **System Context 파악**
3. **High-Level Architecture 설계**
4. **Component 상세 설계**
5. **API/Database 설계**
6. **Deployment Architecture**
7. **Architecture 문서 생성** - `docs/architecture/architecture.md`

## Instructions for Claude

### Step 1: 입력 문서 읽기

```bash
# PRD와 Tech Stack 파일 읽기
PRD_FILE="$1"
TECH_FILE="${2:-docs/tech-stack/tech-stack.md}"

if [ -f "$PRD_FILE" ] && [ -f "$TECH_FILE" ]; then
  echo "📖 문서 읽는 중..."
  cat "$PRD_FILE"
  cat "$TECH_FILE"
else
  echo "❌ 파일을 찾을 수 없습니다"
  exit 1
fi
```

### Step 2: architecture-designer Skill 활성화

architecture-designer 스킬의 프로세스 따름:
1. 시스템 컨텍스트 파악
2. High-Level Architecture
3. Component 설계
4. API/DB 설계
5. Deployment 설계

### Step 3: 문서 생성

```bash
mkdir -p docs/architecture

cat > docs/architecture/architecture.md << 'EOFARCH'
# Architecture: [Project Name]

[PRD + Tech Stack 기반으로 템플릿 채우기]

## 3. System Architecture

```mermaid
[생성된 다이어그램]
```

[... 모든 섹션 ...]

EOFARCH

echo "✅ Architecture 문서 생성!"
```

### Step 4: 최종 요약

"🎉 Architecture 설계 완료!

📁 docs/architecture/architecture.md

**주요 컴포넌트:**
- Frontend: [구조]
- Backend: [레이어 구조]
- Database: [스키마 개수]
- API Endpoints: [개수]

**배포 구조:**
- [설명]

**다음 단계:**
1. ✅ Architecture 검토
2. ⏭️ 승인
3. ⏭️ 프로젝트 구조 생성
4. ⏭️ 구현 시작

질문이 있으신가요?"
```

## Related Commands

- `/tech-stack-decide [prd-file]` - 기술 스택 결정 (이전 단계)
- `/prd-review [prd-file]` - PRD 검토
