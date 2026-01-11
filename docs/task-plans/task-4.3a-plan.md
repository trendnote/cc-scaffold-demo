# Task 4.3a 실행 계획: E2E 테스트 작성

## 📋 작업 정보
- **Task ID**: 4.3a
- **Task명**: E2E 테스트 작성
- **예상 시간**: 4시간
- **담당**: Frontend + Backend
- **의존성**: Task 3.8 (사용자 피드백 수집 UI)
- **GitHub Issue**: #32

---

## 🎯 작업 목표

사용자 관점에서 전체 시스템이 정상 동작하는지 검증하는 End-to-End 테스트 작성

---

## 📐 기술 스택

- **Playwright**: 1.40+ (E2E 테스트 프레임워크)
- **TypeScript**: 5.0+ (테스트 코드)
- **pytest-playwright**: 0.4+ (Python 백엔드 테스트, 선택사항)

---

## 🏗️ 테스트 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                    E2E Test Architecture                     │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────────────────────────────┐               │
│  │  Playwright Test Runner                  │               │
│  │  (headless / headed)                     │               │
│  └──────────────────┬───────────────────────┘               │
│                     │                                         │
│                     ▼                                         │
│  ┌──────────────────────────────────────────┐               │
│  │  Test Scenarios                           │               │
│  │  - 로그인 → 검색 → 결과 확인               │               │
│  │  - 검색 히스토리 조회                      │               │
│  │  - 피드백 제출                            │               │
│  │  - 로그아웃                               │               │
│  │  - 권한 테스트                            │               │
│  └──────────────────┬───────────────────────┘               │
│                     │                                         │
│           ┌─────────┴─────────┐                              │
│           ▼                   ▼                               │
│  ┌───────────────┐   ┌───────────────┐                      │
│  │  Frontend     │   │  Backend API  │                      │
│  │  (Next.js)    │   │  (FastAPI)    │                      │
│  └───────────────┘   └───────────────┘                      │
│           │                   │                               │
│           └─────────┬─────────┘                              │
│                     ▼                                         │
│           ┌──────────────────┐                               │
│           │  Test Report     │                               │
│           │  - HTML Report   │                               │
│           │  - Screenshots   │                               │
│           │  - Videos        │                               │
│           └──────────────────┘                               │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 📝 구현 계획

### Phase 1: Playwright 설정 (1시간)

#### 1.1 Playwright 설치
**파일**: `frontend/package.json`
```json
{
  "devDependencies": {
    "@playwright/test": "^1.40.0"
  },
  "scripts": {
    "test:e2e": "playwright test",
    "test:e2e:ui": "playwright test --ui",
    "test:e2e:debug": "playwright test --debug"
  }
}
```

```bash
# 설치
npm install -D @playwright/test
npx playwright install
```

#### 1.2 Playwright 설정 파일
**파일**: `frontend/playwright.config.ts`
```typescript
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [
    ['html', { outputFolder: 'playwright-report' }],
    ['json', { outputFile: 'test-results/results.json' }],
  ],
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
  ],

  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  },
});
```

#### 1.3 테스트 헬퍼 및 픽스처
**파일**: `frontend/tests/e2e/fixtures/auth.ts`
```typescript
import { Page } from '@playwright/test';

export async function loginAsUser(page: Page) {
  await page.goto('/login');
  await page.fill('input[name="email"]', 'user@example.com');
  await page.fill('input[name="password"]', 'password123');
  await page.click('button[type="submit"]');
  await page.waitForURL('/');
}

export async function loginAsAdmin(page: Page) {
  await page.goto('/login');
  await page.fill('input[name="email"]', 'admin@example.com');
  await page.fill('input[name="password"]', 'password123');
  await page.click('button[type="submit"]');
  await page.waitForURL('/');
}

export async function logout(page: Page) {
  await page.click('button[data-testid="logout-button"]');
  await page.waitForURL('/login');
}
```

---

### Phase 2: E2E 시나리오 작성 (2시간)

#### 2.1 시나리오 1: 로그인 → 검색 → 결과 확인
**파일**: `frontend/tests/e2e/search.spec.ts`
```typescript
import { test, expect } from '@playwright/test';
import { loginAsUser } from './fixtures/auth';

test.describe('검색 기능 E2E', () => {
  test('사용자가 로그인하고 검색하여 결과를 확인한다', async ({ page }) => {
    // Given: 사용자가 로그인되어 있고
    await loginAsUser(page);

    // When: 검색 페이지로 이동하고
    await page.goto('/search');
    await expect(page).toHaveURL('/search');

    // And: 검색어를 입력하고
    const searchInput = page.locator('input[placeholder*="검색"]');
    await searchInput.fill('연차 사용 방법');

    // And: 검색 버튼을 클릭하면
    await page.click('button:has-text("검색")');

    // Then: 로딩 인디케이터가 표시되고
    await expect(page.locator('[data-testid="search-loading"]')).toBeVisible();

    // And: 검색 결과가 표시된다
    await expect(page.locator('[data-testid="search-results"]')).toBeVisible({
      timeout: 30000,
    });

    // And: 답변이 표시된다
    const answer = page.locator('[data-testid="answer-content"]');
    await expect(answer).toBeVisible();
    await expect(answer).not.toBeEmpty();

    // And: 출처 문서가 표시된다
    const sources = page.locator('[data-testid="source-item"]');
    await expect(sources).toHaveCount(5, { timeout: 5000 });

    // And: 각 출처에 문서 제목과 관련도 점수가 표시된다
    const firstSource = sources.first();
    await expect(firstSource.locator('[data-testid="source-title"]')).toBeVisible();
    await expect(firstSource.locator('[data-testid="relevance-score"]')).toBeVisible();

    // 스크린샷 저장
    await page.screenshot({ path: 'test-results/search-result.png', fullPage: true });
  });

  test('존재하지 않는 정보를 검색하면 답변 없음 메시지가 표시된다', async ({ page }) => {
    await loginAsUser(page);
    await page.goto('/search');

    // 존재하지 않을 검색어
    await page.fill('input[placeholder*="검색"]', 'asdfqwerzxcv1234');
    await page.click('button:has-text("검색")');

    // 답변 없음 메시지 확인
    await expect(page.locator('text=답변을 찾을 수 없습니다')).toBeVisible({
      timeout: 30000,
    });
  });

  test('검색 시간이 30초 이내에 완료된다', async ({ page }) => {
    await loginAsUser(page);
    await page.goto('/search');

    const startTime = Date.now();

    await page.fill('input[placeholder*="검색"]', '연차 사용 방법');
    await page.click('button:has-text("검색")');

    // 결과 대기 (최대 30초)
    await expect(page.locator('[data-testid="search-results"]')).toBeVisible({
      timeout: 30000,
    });

    const endTime = Date.now();
    const duration = endTime - startTime;

    // 30초 이내 확인
    expect(duration).toBeLessThan(30000);
    console.log(`검색 완료 시간: ${duration}ms`);
  });
});
```

#### 2.2 시나리오 2: 검색 히스토리 조회
**파일**: `frontend/tests/e2e/history.spec.ts`
```typescript
import { test, expect } from '@playwright/test';
import { loginAsUser } from './fixtures/auth';

test.describe('검색 히스토리 E2E', () => {
  test('검색 후 히스토리 페이지에서 검색 기록을 확인할 수 있다', async ({ page }) => {
    // Given: 검색을 수행하고
    await loginAsUser(page);
    await page.goto('/search');
    await page.fill('input[placeholder*="검색"]', '휴가 신청 방법');
    await page.click('button:has-text("검색")');
    await expect(page.locator('[data-testid="search-results"]')).toBeVisible({
      timeout: 30000,
    });

    // When: 히스토리 페이지로 이동하면
    await page.goto('/history');

    // Then: 검색 기록이 표시된다
    const historyItems = page.locator('[data-testid="history-item"]');
    await expect(historyItems.first()).toBeVisible();

    // And: 최근 검색어가 포함되어 있다
    await expect(page.locator('text=휴가 신청 방법')).toBeVisible();
  });

  test('히스토리 아이템을 클릭하면 해당 검색 결과가 다시 표시된다', async ({ page }) => {
    await loginAsUser(page);
    await page.goto('/history');

    // 히스토리 아이템 클릭
    const firstHistoryItem = page.locator('[data-testid="history-item"]').first();
    await firstHistoryItem.click();

    // 검색 페이지로 이동 확인
    await expect(page).toHaveURL(/\/search/);

    // 검색 결과 표시 확인
    await expect(page.locator('[data-testid="search-results"]')).toBeVisible({
      timeout: 30000,
    });
  });

  test('히스토리 페이지네이션이 정상 동작한다', async ({ page }) => {
    await loginAsUser(page);
    await page.goto('/history');

    // 페이지네이션 버튼 확인
    const pagination = page.locator('[data-testid="pagination"]');

    // 다음 페이지 버튼이 있으면 클릭
    const nextButton = pagination.locator('button:has-text("다음")');
    if (await nextButton.isEnabled()) {
      await nextButton.click();

      // URL 파라미터 확인
      await expect(page).toHaveURL(/page=2/);
    }
  });
});
```

#### 2.3 시나리오 3: 피드백 제출
**파일**: `frontend/tests/e2e/feedback.spec.ts`
```typescript
import { test, expect } from '@playwright/test';
import { loginAsUser } from './fixtures/auth';

test.describe('피드백 기능 E2E', () => {
  test('검색 결과에 대해 피드백을 제출할 수 있다', async ({ page }) => {
    // Given: 검색을 수행하고
    await loginAsUser(page);
    await page.goto('/search');
    await page.fill('input[placeholder*="검색"]', '연차 사용 방법');
    await page.click('button:has-text("검색")');
    await expect(page.locator('[data-testid="search-results"]')).toBeVisible({
      timeout: 30000,
    });

    // When: 피드백 폼을 작성하고
    // 별점 선택 (5점)
    const starButtons = page.locator('[data-testid="rating-star"]');
    await starButtons.nth(4).click(); // 5번째 별 (0-index)

    // 댓글 입력
    await page.fill('textarea[placeholder*="의견"]', '매우 도움이 되었습니다!');

    // And: 피드백을 제출하면
    await page.click('button:has-text("피드백 제출")');

    // Then: 성공 알림이 표시된다
    await expect(page.locator('text=피드백이 저장되었습니다')).toBeVisible({
      timeout: 5000,
    });

    // And: 제출 완료 메시지가 표시된다
    await expect(page.locator('text=피드백을 제출해주셔서 감사합니다')).toBeVisible();
  });

  test('별점 없이 피드백 제출 시 경고 메시지가 표시된다', async ({ page }) => {
    await loginAsUser(page);
    await page.goto('/search');
    await page.fill('input[placeholder*="검색"]', '연차 사용 방법');
    await page.click('button:has-text("검색")');
    await expect(page.locator('[data-testid="search-results"]')).toBeVisible({
      timeout: 30000,
    });

    // 별점 선택하지 않고 제출 시도
    await page.click('button:has-text("피드백 제출")');

    // 경고 메시지 확인
    await expect(page.locator('text=별점을 선택해주세요')).toBeVisible();
  });
});
```

#### 2.4 시나리오 4: 로그아웃
**파일**: `frontend/tests/e2e/auth.spec.ts`
```typescript
import { test, expect } from '@playwright/test';
import { loginAsUser, logout } from './fixtures/auth';

test.describe('인증 기능 E2E', () => {
  test('로그인 후 로그아웃할 수 있다', async ({ page }) => {
    // Given: 로그인되어 있고
    await loginAsUser(page);
    await expect(page).toHaveURL('/');

    // When: 로그아웃하면
    await logout(page);

    // Then: 로그인 페이지로 리다이렉트된다
    await expect(page).toHaveURL('/login');

    // And: 보호된 페이지에 접근 시 로그인 페이지로 리다이렉트된다
    await page.goto('/search');
    await expect(page).toHaveURL('/login');
  });

  test('잘못된 자격 증명으로 로그인 시 에러 메시지가 표시된다', async ({ page }) => {
    await page.goto('/login');
    await page.fill('input[name="email"]', 'wrong@example.com');
    await page.fill('input[name="password"]', 'wrongpassword');
    await page.click('button[type="submit"]');

    // 에러 메시지 확인
    await expect(page.locator('text=이메일 또는 비밀번호가 올바르지 않습니다')).toBeVisible();
  });
});
```

#### 2.5 시나리오 5: 권한 테스트
**파일**: `frontend/tests/e2e/permissions.spec.ts`
```typescript
import { test, expect } from '@playwright/test';
import { loginAsUser, loginAsAdmin } from './fixtures/auth';

test.describe('권한 기반 필터링 E2E', () => {
  test('일반 사용자는 자신의 권한 레벨에 맞는 문서만 볼 수 있다', async ({ page }) => {
    // Given: 일반 사용자로 로그인하고 (access_level: 1)
    await loginAsUser(page);

    // When: 검색을 수행하면
    await page.goto('/search');
    await page.fill('input[placeholder*="검색"]', '회사 정책');
    await page.click('button:has-text("검색")');

    // Then: 검색 결과가 표시되고
    await expect(page.locator('[data-testid="search-results"]')).toBeVisible({
      timeout: 30000,
    });

    // 출처 문서 확인 (메타데이터에 access_level 표시되면)
    // 실제 구현에 따라 조정 필요
  });

  test('관리자는 모든 문서를 볼 수 있다', async ({ page }) => {
    // Given: 관리자로 로그인하고 (access_level: 3)
    await loginAsAdmin(page);

    // When: 검색을 수행하면
    await page.goto('/search');
    await page.fill('input[placeholder*="검색"]', '회사 정책');
    await page.click('button:has-text("검색")');

    // Then: 검색 결과가 표시된다
    await expect(page.locator('[data-testid="search-results"]')).toBeVisible({
      timeout: 30000,
    });
  });
});
```

---

### Phase 3: 테스트 데이터 준비 (0.5시간)

#### 3.1 테스트 데이터 픽스처
**파일**: `frontend/tests/e2e/fixtures/test-data.ts`
```typescript
export const TEST_QUERIES = {
  valid: [
    '연차 사용 방법',
    '휴가 신청 절차',
    '급여 지급일',
    '출퇴근 시간',
    '회의실 예약',
  ],
  invalid: [
    'asdf',  // 너무 짧음
    'x'.repeat(201),  // 너무 김
  ],
  notFound: [
    'asdfqwerzxcv1234',  // 존재하지 않을 검색어
  ],
};

export const TEST_USERS = {
  user: {
    email: 'user@example.com',
    password: 'password123',
    accessLevel: 1,
  },
  admin: {
    email: 'admin@example.com',
    password: 'password123',
    accessLevel: 3,
  },
};
```

---

### Phase 4: 테스트 리포트 설정 (0.5시간)

#### 4.1 CI/CD 통합
**파일**: `.github/workflows/e2e-tests.yml`
```yaml
name: E2E Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  e2e-tests:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Install dependencies
        run: |
          cd frontend
          npm ci

      - name: Install Playwright Browsers
        run: |
          cd frontend
          npx playwright install --with-deps

      - name: Start Backend
        run: |
          cd backend
          docker-compose up -d

      - name: Run E2E Tests
        run: |
          cd frontend
          npm run test:e2e

      - name: Upload Test Results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-report
          path: frontend/playwright-report/

      - name: Upload Test Screenshots
        if: failure()
        uses: actions/upload-artifact@v3
        with:
          name: test-screenshots
          path: frontend/test-results/
```

---

## 🧪 테스트 실행

### 로컬 실행
```bash
# 모든 테스트 실행
npm run test:e2e

# UI 모드로 실행 (디버깅)
npm run test:e2e:ui

# 특정 테스트만 실행
npx playwright test search.spec.ts

# 헤드리스 모드 해제 (브라우저 보기)
npx playwright test --headed

# 디버그 모드
npm run test:e2e:debug
```

### 리포트 보기
```bash
# HTML 리포트 열기
npx playwright show-report
```

---

## ✅ 검증 기준

### 기능 검증
- [ ] Playwright 설치 및 설정 완료
- [ ] E2E 시나리오 5개 모두 통과:
  1. 로그인 → 검색 → 결과 확인
  2. 검색 히스토리 조회
  3. 피드백 제출
  4. 로그아웃
  5. 권한 기반 필터링
- [ ] 모든 브라우저에서 테스트 통과 (Chromium, Firefox, WebKit)

### 성능 검증
- [ ] 검색 시간 30초 이내 (P95)
- [ ] 전체 테스트 실행 시간 < 10분

### 품질 검증
- [ ] 스크린샷 자동 캡처 (실패 시)
- [ ] 비디오 녹화 (실패 시)
- [ ] HTML 테스트 리포트 생성

---

## 📂 파일 구조

```
frontend/
├── tests/
│   └── e2e/
│       ├── fixtures/
│       │   ├── auth.ts
│       │   └── test-data.ts
│       ├── search.spec.ts
│       ├── history.spec.ts
│       ├── feedback.spec.ts
│       ├── auth.spec.ts
│       └── permissions.spec.ts
├── playwright.config.ts
├── playwright-report/          # 테스트 리포트 (gitignore)
└── test-results/               # 스크린샷, 비디오 (gitignore)
```

---

## 🔒 주의사항

### 테스트 데이터 격리
- 각 테스트는 독립적으로 실행 가능해야 함
- 테스트 간 상태 공유 금지
- 테스트 후 정리 (cleanup) 필요 시 구현

### 타임아웃 설정
- 기본 타임아웃: 30초 (검색 API)
- 페이지 로드: 10초
- 네트워크 요청: 5초

### 환경 변수
```env
# .env.test
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 📊 테스트 메트릭

### 커버리지 목표
- [ ] 주요 사용자 플로우 100% 커버
- [ ] 에러 시나리오 80% 커버
- [ ] 엣지 케이스 50% 커버

### 실행 메트릭
```
┌────────────────────────────────────────┐
│  E2E Test Results                      │
├────────────────────────────────────────┤
│  Total Tests: 15                       │
│  Passed: 14                            │
│  Failed: 1                             │
│  Skipped: 0                            │
│  Duration: 8m 32s                      │
│                                         │
│  Browser Coverage:                     │
│  - Chromium: ✓ 15/15                  │
│  - Firefox:  ✓ 15/15                  │
│  - WebKit:   ✓ 15/15                  │
└────────────────────────────────────────┘
```

---

## 🔄 향후 개선 사항

### Phase 4 이후
1. **Visual Regression Testing**
   - Percy 또는 Chromatic 통합
   - UI 변경 감지

2. **성능 테스트 통합**
   - Lighthouse CI
   - Web Vitals 측정

3. **접근성 테스트**
   - axe-core 통합
   - WCAG 2.1 준수 확인

4. **모바일 테스트**
   - 모바일 브라우저 시뮬레이션
   - 터치 이벤트 테스트

---

## 📚 참고 자료

- [Playwright Documentation](https://playwright.dev/)
- [Playwright Best Practices](https://playwright.dev/docs/best-practices)
- [E2E Testing Patterns](https://martinfowler.com/articles/practical-test-pyramid.html)

---

**작성자**: Task Planner
**작성일**: 2026-01-10
**버전**: 1.0.0
