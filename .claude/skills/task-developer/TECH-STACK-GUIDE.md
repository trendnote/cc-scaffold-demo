# Technology Stack Guide

이 문서는 각 기술 스택별 코딩 컨벤션과 베스트 프랙티스를 정의합니다.
CLAUDE.md Section 5에서 참조하는 규칙들의 실용적 가이드입니다.

---

## 규칙 바인딩 (CLAUDE.md Section 5)

Task 범위에 따라 해당 규칙 적용:

- **Java/Spring**: `@claude-rules/backend-core.md` (현재 미정의, 이 가이드 참조)
- **Node.js/TypeScript**: `@claude-rules/backend-bff.md` (현재 미정의, 이 가이드 참조)
- **Python/FastAPI**: `@claude-rules/backend-ai.md` (현재 미정의, 이 가이드 참조)
- **Next.js**: `@claude-rules/frontend-ui.md` (현재 미정의, 이 가이드 참조)

**여러 도메인에 걸친 Task는 모든 관련 규칙 적용**

---

## 공통 원칙 (모든 스택)

### 코드 스타일

```
✅ 일관된 들여쓰기 (프로젝트 설정 따름)
✅ 의미있는 변수/함수명
✅ 함수는 한 가지 일만 수행
✅ 매직 넘버 사용 금지 (상수로 정의)
```

### 에러 처리

```
✅ 모든 에러 경로 명시적 처리
✅ 의미있는 에러 메시지
❌ 빈 catch 블록 금지
✅ 에러 복구 전략 명확히
```

### 테스트

```
✅ 단위 테스트: 함수/메서드 레벨
✅ 통합 테스트: API/서비스 레벨
✅ E2E 테스트: 주요 사용자 플로우
✅ 테스트 커버리지 80% 이상 목표
```

### 문서화

```
✅ 복잡한 로직은 주석 설명
✅ API는 스펙 문서 작성
✅ README 업데이트 (변경 시)
❌ 자명한 코드에 불필요한 주석 금지
```

---

## Java / Spring Boot

### 프로젝트 구조

```
src/main/java/com/young/
├── domain/           # 도메인 모델
├── controller/       # REST 컨트롤러
├── service/          # 비즈니스 로직
├── repository/       # 데이터 접근
├── dto/              # Data Transfer Objects
├── config/           # 설정
└── exception/        # 커스텀 예외
```

### 코딩 컨벤션

```java
// ✅ GOOD: 명확한 책임 분리
@RestController
@RequestMapping("/api/users")
public class UserController {
    private final UserService userService;

    @GetMapping("/{id}")
    public ResponseEntity<UserDto> getUser(@PathVariable Long id) {
        return ResponseEntity.ok(userService.getUserById(id));
    }
}

@Service
public class UserService {
    private final UserRepository userRepository;

    public UserDto getUserById(Long id) {
        return userRepository.findById(id)
            .map(UserDto::from)
            .orElseThrow(() -> new UserNotFoundException(id));
    }
}
```

### 베스트 프랙티스

- [ ] **Dependency Injection**: 생성자 주입 사용 (필드 주입 금지)
  ```java
  // ✅ GOOD
  private final UserService userService;

  public UserController(UserService userService) {
      this.userService = userService;
  }

  // ❌ BAD
  @Autowired
  private UserService userService;
  ```

- [ ] **Exception Handling**: `@ControllerAdvice`로 중앙화
  ```java
  @ControllerAdvice
  public class GlobalExceptionHandler {
      @ExceptionHandler(UserNotFoundException.class)
      public ResponseEntity<ErrorResponse> handleUserNotFound(
          UserNotFoundException e
      ) {
          return ResponseEntity.status(404)
              .body(new ErrorResponse(e.getMessage()));
      }
  }
  ```

- [ ] **Repository**: JPA/Hibernate 사용 (SQL Injection 방지)
  ```java
  // ✅ GOOD
  @Query("SELECT u FROM User u WHERE u.email = :email")
  Optional<User> findByEmail(@Param("email") String email);

  // ❌ BAD: Native query with string concatenation
  ```

- [ ] **DTO 사용**: 엔티티 직접 노출 금지
  ```java
  // ✅ GOOD
  public record UserDto(Long id, String name, String email) {
      public static UserDto from(User user) {
          return new UserDto(user.getId(), user.getName(), user.getEmail());
      }
  }
  ```

- [ ] **Validation**: Bean Validation 사용
  ```java
  public record CreateUserRequest(
      @NotBlank String name,
      @Email String email,
      @Size(min = 8) String password
  ) {}
  ```

### 테스트

```java
@SpringBootTest
class UserServiceTest {
    @Autowired
    private UserService userService;

    @MockBean
    private UserRepository userRepository;

    @Test
    void getUserById_WhenExists_ReturnsUser() {
        // given
        User user = new User(1L, "test", "test@example.com");
        when(userRepository.findById(1L)).thenReturn(Optional.of(user));

        // when
        UserDto result = userService.getUserById(1L);

        // then
        assertThat(result.name()).isEqualTo("test");
    }
}
```

---

## Node.js / TypeScript (BFF)

### 프로젝트 구조

```
src/
├── controllers/      # 요청 핸들러
├── services/         # 비즈니스 로직
├── repositories/     # 데이터 접근
├── models/           # 타입 정의
├── middlewares/      # Express 미들웨어
├── routes/           # 라우트 정의
├── config/           # 설정
└── utils/            # 유틸리티
```

### 코딩 컨벤션

```typescript
// ✅ GOOD: 타입 안전성
interface User {
  id: string;
  name: string;
  email: string;
}

interface CreateUserDto {
  name: string;
  email: string;
  password: string;
}

class UserService {
  async getUserById(id: string): Promise<User> {
    const user = await this.userRepository.findById(id);
    if (!user) {
      throw new UserNotFoundError(id);
    }
    return user;
  }
}
```

### 베스트 프랙티스

- [ ] **타입 안전성**: `any` 사용 최소화
  ```typescript
  // ✅ GOOD
  function processUser(user: User): void { /* ... */ }

  // ❌ BAD
  function processUser(user: any): void { /* ... */ }
  ```

- [ ] **Async/Await**: Promise 체이닝보다 선호
  ```typescript
  // ✅ GOOD
  async function getUser(id: string): Promise<User> {
    const user = await db.query('SELECT * FROM users WHERE id = ?', [id]);
    return user;
  }

  // ❌ BAD
  function getUser(id: string): Promise<User> {
    return db.query('SELECT * FROM users WHERE id = ?', [id])
      .then(user => user);
  }
  ```

- [ ] **에러 핸들링**: 중앙화된 에러 미들웨어
  ```typescript
  app.use((err: Error, req: Request, res: Response, next: NextFunction) => {
    if (err instanceof UserNotFoundError) {
      return res.status(404).json({ error: err.message });
    }
    // 스택 트레이스 클라이언트 노출 금지
    logger.error(err);
    res.status(500).json({ error: 'Internal server error' });
  });
  ```

- [ ] **환경 변수**: dotenv + 타입 정의
  ```typescript
  // config/env.ts
  import { z } from 'zod';

  const envSchema = z.object({
    PORT: z.string().default('3000'),
    DATABASE_URL: z.string(),
    API_KEY: z.string(),
  });

  export const env = envSchema.parse(process.env);
  ```

- [ ] **입력 검증**: Zod, Yup 등 사용
  ```typescript
  import { z } from 'zod';

  const createUserSchema = z.object({
    name: z.string().min(1),
    email: z.string().email(),
    password: z.string().min(8),
  });

  app.post('/users', (req, res) => {
    const data = createUserSchema.parse(req.body);
    // ...
  });
  ```

### 테스트

```typescript
import { describe, it, expect, vi } from 'vitest';

describe('UserService', () => {
  it('should get user by id', async () => {
    // given
    const mockRepo = {
      findById: vi.fn().mockResolvedValue({
        id: '1',
        name: 'test'
      }),
    };
    const service = new UserService(mockRepo);

    // when
    const result = await service.getUserById('1');

    // then
    expect(result.name).toBe('test');
    expect(mockRepo.findById).toHaveBeenCalledWith('1');
  });
});
```

---

## Python / FastAPI

### 프로젝트 구조

```
app/
├── api/              # API 라우터
│   └── v1/
│       ├── endpoints/
│       └── dependencies.py
├── core/             # 설정, 보안
├── models/           # Pydantic 모델
├── services/         # 비즈니스 로직
├── repositories/     # 데이터 접근
└── main.py           # 앱 엔트리포인트
```

### 코딩 컨벤션

```python
# ✅ GOOD: 타입 힌트 + Pydantic
from pydantic import BaseModel, EmailStr
from typing import Optional

class User(BaseModel):
    id: int
    name: str
    email: EmailStr

class CreateUserDto(BaseModel):
    name: str
    email: EmailStr
    password: str

    class Config:
        min_anystr_length = 1

async def get_user(user_id: int) -> Optional[User]:
    user = await db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
```

### 베스트 프랙티스

- [ ] **타입 힌트**: 모든 함수에 타입 명시
  ```python
  # ✅ GOOD
  def calculate_total(items: list[Item]) -> float:
      return sum(item.price for item in items)

  # ❌ BAD
  def calculate_total(items):
      return sum(item.price for item in items)
  ```

- [ ] **Pydantic 검증**: 입력 자동 검증
  ```python
  @app.post("/users/", response_model=User)
  async def create_user(user: CreateUserDto):
      # Pydantic이 자동으로 검증
      return await user_service.create(user)
  ```

- [ ] **Dependency Injection**: FastAPI DI 활용
  ```python
  async def get_db() -> AsyncGenerator:
      async with SessionLocal() as session:
          yield session

  @app.get("/users/{user_id}")
  async def get_user(
      user_id: int,
      db: AsyncSession = Depends(get_db)
  ):
      return await user_service.get_by_id(db, user_id)
  ```

- [ ] **에러 핸들링**: HTTPException 사용
  ```python
  from fastapi import HTTPException

  if not user:
      raise HTTPException(
          status_code=404,
          detail="User not found"
      )
  ```

- [ ] **비동기**: I/O 작업은 async/await
  ```python
  # ✅ GOOD
  async def fetch_user(user_id: int) -> User:
      async with httpx.AsyncClient() as client:
          response = await client.get(f"/users/{user_id}")
          return User(**response.json())

  # ❌ BAD: 동기 I/O는 이벤트 루프 블록
  ```

### 테스트

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_get_user(client: AsyncClient):
    # given
    user_id = 1

    # when
    response = await client.get(f"/users/{user_id}")

    # then
    assert response.status_code == 200
    assert response.json()["id"] == user_id
```

---

## Next.js / React (Frontend)

### 프로젝트 구조

```
src/
├── app/              # App Router (Next.js 13+)
│   ├── (routes)/
│   └── api/
├── components/       # 재사용 컴포넌트
│   ├── ui/           # 기본 UI 컴포넌트
│   └── features/     # 기능별 컴포넌트
├── lib/              # 유틸리티, 헬퍼
├── hooks/            # 커스텀 훅
├── types/            # TypeScript 타입
└── styles/           # 글로벌 스타일
```

### 코딩 컨벤션

```typescript
// ✅ GOOD: 타입 안전한 컴포넌트
interface UserCardProps {
  user: {
    id: string;
    name: string;
    email: string;
  };
  onDelete?: (id: string) => void;
}

export function UserCard({ user, onDelete }: UserCardProps) {
  return (
    <div>
      <h3>{user.name}</h3>
      <p>{user.email}</p>
      {onDelete && (
        <button onClick={() => onDelete(user.id)}>
          Delete
        </button>
      )}
    </div>
  );
}
```

### 베스트 프랙티스

- [ ] **Server Components 우선**: 클라이언트 컴포넌트 최소화
  ```typescript
  // ✅ GOOD: Server Component (기본)
  async function UserList() {
    const users = await fetchUsers(); // 서버에서 데이터 fetch
    return <div>{users.map(user => <UserCard key={user.id} user={user} />)}</div>;
  }

  // Client Component는 필요시만
  'use client';
  export function InteractiveButton() {
    const [count, setCount] = useState(0);
    return <button onClick={() => setCount(c => c + 1)}>{count}</button>;
  }
  ```

- [ ] **데이터 Fetching**: Server Components에서 직접
  ```typescript
  // ✅ GOOD
  async function UserPage({ params }: { params: { id: string } }) {
    const user = await db.user.findUnique({ where: { id: params.id } });
    return <UserProfile user={user} />;
  }

  // ❌ BAD: 클라이언트에서 useEffect로 fetch
  ```

- [ ] **XSS 방지**: React 자동 이스케이프 활용
  ```typescript
  // ✅ GOOD: 자동 이스케이프
  <div>{userInput}</div>

  // ❌ BAD: dangerouslySetInnerHTML은 정말 필요할 때만
  <div dangerouslySetInnerHTML={{ __html: userInput }} />
  ```

- [ ] **환경 변수**: Public vs Private 구분
  ```typescript
  // Public (클라이언트 노출 OK)
  const publicKey = process.env.NEXT_PUBLIC_STRIPE_KEY;

  // Private (서버만)
  const secretKey = process.env.STRIPE_SECRET_KEY;
  ```

- [ ] **Image 최적화**: next/image 사용
  ```typescript
  import Image from 'next/image';

  // ✅ GOOD
  <Image src="/photo.jpg" alt="Photo" width={500} height={300} />

  // ❌ BAD
  <img src="/photo.jpg" alt="Photo" />
  ```

- [ ] **Form 처리**: Server Actions 활용
  ```typescript
  async function createUser(formData: FormData) {
    'use server';
    const name = formData.get('name') as string;
    await db.user.create({ data: { name } });
    revalidatePath('/users');
  }

  export function CreateUserForm() {
    return (
      <form action={createUser}>
        <input name="name" required />
        <button type="submit">Create</button>
      </form>
    );
  }
  ```

### 테스트

```typescript
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

describe('UserCard', () => {
  it('renders user information', () => {
    const user = { id: '1', name: 'Test', email: 'test@example.com' };
    render(<UserCard user={user} />);

    expect(screen.getByText('Test')).toBeInTheDocument();
    expect(screen.getByText('test@example.com')).toBeInTheDocument();
  });

  it('calls onDelete when button clicked', async () => {
    const onDelete = vi.fn();
    const user = { id: '1', name: 'Test', email: 'test@example.com' };
    render(<UserCard user={user} onDelete={onDelete} />);

    await userEvent.click(screen.getByText('Delete'));
    expect(onDelete).toHaveBeenCalledWith('1');
  });
});
```

---

## 데이터베이스

### SQL 안전성

```sql
-- ✅ GOOD: Parameterized query
SELECT * FROM users WHERE id = ?

-- ❌ BAD: String concatenation
SELECT * FROM users WHERE id = '${userId}'
```

### 마이그레이션

```
✅ 모든 스키마 변경은 마이그레이션 파일로
✅ 롤백 스크립트 함께 작성
✅ 프로덕션 적용 전 스테이징 검증
❌ 직접 프로덕션 DB 수정 금지
```

### 인덱싱

```
✅ WHERE, JOIN 조건 컬럼에 인덱스
✅ 복합 인덱스 순서 고려
⚠️ 과도한 인덱스는 쓰기 성능 저하
```

---

## Git Commit Convention

### Conventional Commits

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: 새로운 기능
- `fix`: 버그 수정
- `docs`: 문서 변경
- `style`: 코드 포맷팅 (기능 변경 없음)
- `refactor`: 리팩토링
- `test`: 테스트 추가/수정
- `chore`: 빌드, 설정 등

### 예시

```
feat(user): add email verification feature

- Send verification email on signup
- Add /verify endpoint
- Update user model with verified flag

Closes #123
```

---

## CI/CD

### Pre-commit Checks

```
✅ Lint 통과
✅ 타입 체크 통과
✅ 테스트 통과
✅ 보안 스캔 통과
```

### Pull Request

```
✅ 의미있는 제목과 설명
✅ 리뷰어 지정
✅ CI 통과 확인
✅ Conflict 해결
```

---

## Performance

### Backend

```
✅ N+1 쿼리 방지 (eager loading)
✅ 적절한 캐싱 (Redis 등)
✅ 페이지네이션 구현
✅ Rate limiting
```

### Frontend

```
✅ Code splitting
✅ Lazy loading
✅ Image 최적화
✅ 불필요한 리렌더링 방지 (memo, useMemo)
```

---

## 참고

이 가이드는 일반적인 베스트 프랙티스입니다.
프로젝트별 상세 규칙은 다음을 참조하세요:

- `@claude-rules/backend-core.md` (추후 작성)
- `@claude-rules/backend-bff.md` (추후 작성)
- `@claude-rules/backend-ai.md` (추후 작성)
- `@claude-rules/frontend-ui.md` (추후 작성)

---

> **Remember**:
> 컨벤션은 팀의 생산성을 높이기 위한 것입니다.
> 일관성이 개인의 선호보다 중요합니다.
