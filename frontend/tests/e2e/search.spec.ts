/**
 * Search Flow E2E Tests
 *
 * Task 4.3a: E2E Testing
 *
 * 검증 시나리오:
 * 1. 로그인 → 검색 → 결과 확인
 * 2. 검색 결과에서 출처 확인
 * 3. 잘못된 검색어 처리
 */
import { test, expect } from '@playwright/test';
import { loginAsUser } from './fixtures/auth';
import { testQueries } from './fixtures/test-data';

test.describe('Search Flow', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsUser(page);
  });

  test('should complete full search flow: login → search → results', async ({ page }) => {
    // 1. 홈 페이지 확인
    await expect(page).toHaveURL('/');

    // 2. 검색 페이지로 이동
    await page.goto('/search');

    // 3. 검색어 입력
    const query = testQueries[0]; // "연차 사용 방법"
    await page.fill('input[name="query"]', query);

    // 4. 검색 실행
    await page.click('button[type="submit"]');

    // 5. 로딩 상태 확인
    await expect(page.locator('text=검색 중')).toBeVisible();

    // 6. 검색 결과 확인 (최대 30초 대기)
    await expect(page.locator('[data-testid="search-results"]')).toBeVisible({ timeout: 30000 });

    // 7. 답변 존재 확인
    await expect(page.locator('[data-testid="search-answer"]')).toBeVisible();

    // 8. 출처 확인
    await expect(page.locator('[data-testid="search-sources"]')).toBeVisible();
  });

  test('should display sources with document information', async ({ page }) => {
    // 1. 검색 실행
    await page.goto('/search');
    await page.fill('input[name="query"]', testQueries[1]);
    await page.click('button[type="submit"]');

    // 2. 결과 대기
    await expect(page.locator('[data-testid="search-results"]')).toBeVisible({ timeout: 30000 });

    // 3. 출처 섹션 확인
    const sources = page.locator('[data-testid="source-item"]');
    await expect(sources).toHaveCount(3, { timeout: 5000 }); // 최소 3개 출처

    // 4. 첫 번째 출처 상세 확인
    const firstSource = sources.first();
    await expect(firstSource.locator('[data-testid="source-title"]')).toBeVisible();
    await expect(firstSource.locator('[data-testid="source-score"]')).toBeVisible();
  });

  test('should handle empty query gracefully', async ({ page }) => {
    // 1. 검색 페이지로 이동
    await page.goto('/search');

    // 2. 빈 검색어로 제출 시도
    await page.click('button[type="submit"]');

    // 3. 에러 메시지 확인
    await expect(page.locator('text=검색어를 입력해주세요')).toBeVisible();

    // 4. 검색 실행 안됨 확인
    await expect(page.locator('[data-testid="search-results"]')).not.toBeVisible();
  });
});
