# 코딩 규칙 및 스타일 가이드 (Coding Standards)

## 목차

1. [General Principles](#general-principles)
2. [Python (Backend)](#python-backend)
3. [TypeScript (Frontend)](#typescript-frontend)
4. [Git Commit Messages](#git-commit-messages)
5. [Documentation](#documentation)
6. [Code Review](#code-review)

---

## General Principles

### 1. 코드 작성 원칙

**SOLID 원칙**:

- **S**ingle Responsibility: 하나의 클래스는 하나의 책임만
- **O**pen/Closed: 확장에 열려있고 수정에 닫혀있어야 함
- **L**iskov Substitution: 하위 타입은 상위 타입을 대체 가능해야 함
- **I**nterface Segregation: 클라이언트는 사용하지 않는 인터페이스에 의존하지 않아야 함
- **D**ependency Inversion: 추상화에 의존하고 구체화에 의존하지 않아야 함

**DRY (Don't Repeat Yourself)**:

- 중복 코드 최소화
- 재사용 가능한 함수/컴포넌트 작성
- 상수/설정은 한 곳에서 관리

**KISS (Keep It Simple, Stupid)**:

- 단순한 해결책 선호
- 과도한 추상화 지양
- 명확한 코드 > 영리한 코드

**YAGNI (You Aren't Gonna Need It)**:

- 필요하지 않은 기능 미리 구현하지 않기
- 요구사항에 집중
- 과도한 미래 대비 지양

### 2. 명명 규칙

| 대상 | 규칙 | 예시 |
|------|------|------|
| **변수/함수** | snake_case (Python), camelCase (TS) | `user_id`, `getUserName()` |
| **클래스** | PascalCase | `UserService`, `SearchAPI` |
| **상수** | UPPER_SNAKE_CASE | `MAX_RETRY_COUNT`, `API_TIMEOUT` |
| **파일** | snake_case (Python), kebab-case (TS) | `user_service.py`, `user-profile.tsx` |
| **환경변수** | UPPER_SNAKE_CASE | `DATABASE_URL`, `JWT_SECRET` |

**의미 있는 이름**:

```python
# ❌ 나쁜 예
def f(x, y):
    return x + y

# ✅ 좋은 예
def calculate_total_price(base_price: float, tax_rate: float) -> float:
    return base_price * (1 + tax_rate)
```

### 3. 코드 포맷팅

**일관성**:

- 프로젝트 전체에서 동일한 스타일 유지
- 자동 포맷터 사용 (Black, Prettier)
- Pre-commit Hook으로 강제

**들여쓰기**:

- Python: 4 spaces
- TypeScript: 2 spaces

**줄 길이**:

- Python: 88 characters (Black 기본값)
- TypeScript: 100 characters

---

## Python (Backend)

### 1. PEP 8 준수

```python
# ✅ 좋은 예
def get_user_by_email(email: str) -> Optional[User]:
    """이메일로 사용자 조회

    Args:
        email: 사용자 이메일

    Returns:
        User 객체 또는 None
    """
    return db.query(User).filter(User.email == email).first()
```

### 2. 타입 힌팅

```python
from typing import List, Dict, Optional, Union

# ✅ 타입 힌트 사용
def search_documents(
    query: str,
    limit: int = 10,
    filters: Optional[Dict[str, str]] = None
) -> List[Document]:
    """문서 검색"""
    # ...
    return documents

# ❌ 타입 힌트 없음
def search_documents(query, limit=10, filters=None):
    # ...
    return documents
```

### 3. Docstrings (Google Style)

```python
def calculate_relevance_score(
    query_embedding: List[float],
    document_embedding: List[float],
    boost_factor: float = 1.0
) -> float:
    """쿼리와 문서의 관련성 점수 계산

    두 벡터 간의 코사인 유사도를 계산하고 부스트 팩터를 적용합니다.

    Args:
        query_embedding: 쿼리 임베딩 벡터
        document_embedding: 문서 임베딩 벡터
        boost_factor: 점수 증폭 계수 (기본값: 1.0)

    Returns:
        0.0 ~ 1.0 사이의 관련성 점수

    Raises:
        ValueError: 벡터 차원이 일치하지 않을 때

    Example:
        >>> query_emb = [0.1, 0.2, 0.3]
        >>> doc_emb = [0.2, 0.3, 0.4]
        >>> score = calculate_relevance_score(query_emb, doc_emb)
        >>> print(f"{score:.2f}")
        0.99
    """
    if len(query_embedding) != len(document_embedding):
        raise ValueError("Vector dimensions must match")

    # 코사인 유사도 계산
    cosine_sim = np.dot(query_embedding, document_embedding) / (
        np.linalg.norm(query_embedding) * np.linalg.norm(document_embedding)
    )

    return min(cosine_sim * boost_factor, 1.0)
```

### 4. Error Handling

```python
# ✅ 좋은 예 - 구체적인 예외
def get_user(user_id: int) -> User:
    """사용자 조회"""
    try:
        user = db.query(User).filter(User.id == user_id).one()
        return user
    except NoResultFound:
        raise HTTPException(
            status_code=404,
            detail=f"User {user_id} not found"
        )
    except MultipleResultsFound:
        logger.error(f"Multiple users found for ID: {user_id}")
        raise HTTPException(
            status_code=500,
            detail="Database integrity error"
        )

# ❌ 나쁜 예 - 모든 예외를 잡음
def get_user(user_id: int) -> User:
    try:
        user = db.query(User).filter(User.id == user_id).one()
        return user
    except Exception as e:  # 너무 광범위함
        return None  # 에러 무시
```

### 5. Logging

```python
import structlog

logger = structlog.get_logger(__name__)

def process_search_query(query: str, user_id: str) -> SearchResult:
    """검색 쿼리 처리"""
    logger.info(
        "search_query_start",
        query=query,
        user_id=user_id,
        query_length=len(query)
    )

    try:
        result = search_service.search(query)

        logger.info(
            "search_query_complete",
            query=query,
            user_id=user_id,
            result_count=len(result.sources),
            duration_ms=result.duration
        )

        return result

    except Exception as e:
        logger.error(
            "search_query_failed",
            query=query,
            user_id=user_id,
            error=str(e),
            exc_info=True
        )
        raise
```

### 6. 파일 구조

```python
# ✅ 좋은 파일 구조

"""
문서 검색 서비스

이 모듈은 RAG 기반 문서 검색 기능을 제공합니다.
"""

# Standard library
import os
import sys
from typing import List, Optional

# Third-party
from fastapi import HTTPException
import structlog

# Local imports
from app.core.config import settings
from app.db.models import Document
from app.services.embedding import EmbeddingService
from app.services.llm import LLMService

# Constants
MAX_RESULTS = 10
DEFAULT_TIMEOUT = 30

# Module-level logger
logger = structlog.get_logger(__name__)


class SearchService:
    """문서 검색 서비스"""

    def __init__(
        self,
        embedding_service: EmbeddingService,
        llm_service: LLMService
    ):
        self.embedding = embedding_service
        self.llm = llm_service

    def search(self, query: str) -> SearchResult:
        """검색 실행"""
        # ...
```

### 7. 클래스 설계

```python
# ✅ 좋은 예 - 단일 책임, 의존성 주입

class UserService:
    """사용자 관리 서비스"""

    def __init__(self, db: Session, email_service: EmailService):
        self.db = db
        self.email_service = email_service

    def create_user(self, user_data: UserCreate) -> User:
        """사용자 생성"""
        # 검증
        if self._email_exists(user_data.email):
            raise ValueError("Email already exists")

        # 생성
        user = User(**user_data.dict())
        self.db.add(user)
        self.db.commit()

        # 이메일 전송
        self.email_service.send_welcome_email(user.email)

        return user

    def _email_exists(self, email: str) -> bool:
        """이메일 존재 확인 (private)"""
        return self.db.query(User).filter(User.email == email).first() is not None
```

---

## TypeScript (Frontend)

### 1. TypeScript 타입

```typescript
// ✅ 좋은 예 - 명시적 타입

interface SearchResult {
  answer: string;
  sources: Source[];
  searchId: string;
  duration: number;
}

interface Source {
  id: string;
  title: string;
  content: string;
  score: number;
}

// ✅ 타입 가드
function isSearchResult(obj: unknown): obj is SearchResult {
  return (
    typeof obj === 'object' &&
    obj !== null &&
    'answer' in obj &&
    'sources' in obj &&
    'searchId' in obj
  );
}

// ✅ Generic 사용
async function fetchData<T>(url: string): Promise<T> {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
  return response.json() as T;
}

// 사용
const result = await fetchData<SearchResult>('/api/search');
```

### 2. React 컴포넌트

```typescript
// ✅ 좋은 예 - 함수형 컴포넌트, Props 타입

interface SearchBoxProps {
  onSearch: (query: string) => void;
  isLoading?: boolean;
  placeholder?: string;
}

export function SearchBox({
  onSearch,
  isLoading = false,
  placeholder = 'Search...',
}: SearchBoxProps) {
  const [query, setQuery] = useState('');
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();

    if (!query.trim()) {
      setError('Please enter a search query');
      return;
    }

    setError(null);
    onSearch(query);
  };

  return (
    <form onSubmit={handleSubmit} className="search-box">
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder={placeholder}
        disabled={isLoading}
        aria-label="Search input"
      />
      <button type="submit" disabled={isLoading || !query.trim()}>
        {isLoading ? 'Searching...' : 'Search'}
      </button>
      {error && <p className="error" role="alert">{error}</p>}
    </form>
  );
}
```

### 3. Custom Hooks

```typescript
// ✅ 좋은 예 - 재사용 가능한 Hook

interface UseSearchOptions {
  autoSearch?: boolean;
  debounceMs?: number;
}

export function useSearch(options: UseSearchOptions = {}) {
  const { autoSearch = false, debounceMs = 500 } = options;
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const search = useCallback(async (searchQuery: string) => {
    if (!searchQuery.trim()) return;

    setIsLoading(true);
    setError(null);

    try {
      const data = await searchQuery(searchQuery);
      setResults(data);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Search failed'));
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Auto-search with debounce
  useEffect(() => {
    if (!autoSearch || !query) return;

    const timer = setTimeout(() => {
      search(query);
    }, debounceMs);

    return () => clearTimeout(timer);
  }, [query, autoSearch, debounceMs, search]);

  return {
    query,
    setQuery,
    results,
    isLoading,
    error,
    search,
  };
}

// 사용
function SearchPage() {
  const { query, setQuery, results, isLoading, error, search } = useSearch({
    autoSearch: true,
    debounceMs: 500,
  });

  return (
    <div>
      <input value={query} onChange={(e) => setQuery(e.target.value)} />
      {isLoading && <Loading />}
      {error && <Error message={error.message} />}
      {results && <Results data={results} />}
    </div>
  );
}
```

### 4. API 클라이언트

```typescript
// ✅ 좋은 예 - 타입 안전, 에러 처리

class APIClient {
  private baseURL: string;
  private token: string | null = null;

  constructor(baseURL: string) {
    this.baseURL = baseURL;
  }

  setToken(token: string) {
    this.token = token;
  }

  private async request<T>(
    path: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseURL}${path}`;
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new APIError(
        error.detail || 'Request failed',
        response.status
      );
    }

    return response.json();
  }

  async searchQuery(query: string): Promise<SearchResult> {
    return this.request<SearchResult>('/api/v1/search/query', {
      method: 'POST',
      body: JSON.stringify({ query }),
    });
  }
}

class APIError extends Error {
  constructor(message: string, public status: number) {
    super(message);
    this.name = 'APIError';
  }
}
```

---

## Git Commit Messages

### 1. Conventional Commits

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Type**:

- `feat`: 새로운 기능
- `fix`: 버그 수정
- `docs`: 문서 변경
- `style`: 코드 스타일 변경 (포매팅 등)
- `refactor`: 코드 리팩토링
- `test`: 테스트 추가/수정
- `chore`: 빌드/설정 변경

**예시**:

```
feat(search): Add filter by date range

- Add DateRangePicker component
- Add date filter to search API
- Update search results UI

Closes #123
```

```
fix(auth): Fix JWT token expiration handling

The token was not being refreshed correctly when expired.
This commit adds automatic token refresh using refresh token.

Fixes #456
```

### 2. 커밋 규칙

- 제목은 50자 이내
- 본문은 72자마다 줄바꿈
- 제목은 명령형 (Add, Fix, Update)
- 제목 끝에 마침표 없음
- 본문에는 무엇을, 왜 했는지 설명
- 관련 이슈 번호 포함 (Closes #123, Fixes #456)

---

## Documentation

### 1. README.md

```markdown
# Project Name

Brief description (1-2 sentences)

## Quick Start

```bash
# 3-5 commands to get started
```

## Features

- Feature 1
- Feature 2

## Documentation

- [API Reference](docs/api/)
- [Development Guide](docs/development/)

## License

MIT
```

### 2. API 문서

```python
# FastAPI는 자동으로 OpenAPI 문서 생성

@router.post(
    "/search/query",
    response_model=SearchResponse,
    summary="검색 쿼리 실행",
    description="""
    사용자 쿼리를 받아 RAG 기반 검색을 수행합니다.

    **처리 과정**:
    1. 쿼리 임베딩 생성
    2. Milvus에서 유사 문서 검색
    3. LLM으로 답변 생성

    **성능**: P95 < 30초
    """,
    responses={
        200: {"description": "검색 성공"},
        401: {"description": "인증 실패"},
        422: {"description": "잘못된 요청"},
    }
)
async def search_query(
    request: SearchRequest,
    current_user: User = Depends(get_current_user)
) -> SearchResponse:
    """검색 쿼리 API"""
    # ...
```

---

## Code Review

### 1. 리뷰어 체크리스트

**기능**:

- [ ] 요구사항을 충족하는가?
- [ ] 엣지 케이스를 고려했는가?
- [ ] 에러 처리가 적절한가?

**코드 품질**:

- [ ] 코딩 표준을 따르는가?
- [ ] 변수/함수명이 명확한가?
- [ ] 중복 코드가 없는가?

**테스트**:

- [ ] 테스트가 충분한가?
- [ ] 테스트가 통과하는가?
- [ ] 커버리지가 충분한가?

**보안**:

- [ ] SQL Injection 위험이 없는가?
- [ ] XSS 위험이 없는가?
- [ ] 시크릿이 노출되지 않는가?

**성능**:

- [ ] 불필요한 쿼리가 없는가?
- [ ] N+1 문제가 없는가?
- [ ] 메모리 누수 가능성이 없는가?

### 2. 리뷰 코멘트 예시

```
✅ 좋은 코멘트:
"이 함수는 N+1 쿼리 문제가 있습니다. prefetch_related를 사용하는 것이 좋겠습니다."

❌ 나쁜 코멘트:
"이거 왜 이렇게 했어요?"
```

```
✅ 좋은 코멘트:
"에러 처리가 누락되었습니다. network_error 케이스에 대한 처리를 추가해주세요."

❌ 나쁜 코멘트:
"에러 처리 안 했네요."
```

---

## 관련 문서

- [Development Setup](./setup.md) - 개발 환경 설정
- [Testing Guide](./testing-guide.md) - 테스트 작성 및 실행

---

**좋은 코드는 읽기 쉬운 코드입니다!** 📖
