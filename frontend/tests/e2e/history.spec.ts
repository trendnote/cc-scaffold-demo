/**
 * Search History E2E Tests
 *
 * Task 4.3a: E2E Testing
 *
 * 검증 시나리오:
 * 1. 히스토리 페이지 접근
 * 2. 히스토리 목록 표시
 * 3. 히스토리 항목 클릭 → 상세 보기
 */
import { test, expect } from '@playwright/test';
import { loginAsUser } from './fixtures/auth';
import { testQueries } from './fixtures/test-data';

test.describe('Search History', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsUser(page);
  });

  test('should navigate to history page', async ({ page }) => {
    // 1. 홈 페이지에서 시작
    await expect(page).toHaveURL('/');

    // 2. 히스토리 링크 클릭
    await page.click('a[href="/history"]');

    // 3. 히스토리 페이지로 이동 확인
    await expect(page).toHaveURL('/history');

    // 4. 페이지 제목 확인
    await expect(page.locator('h1:has-text("검색 히스토리")')).toBeVisible();
  });

  test('should display search history list', async ({ page }) => {
    // 1. 먼저 검색 실행 (히스토리 생성)
    await page.goto('/search');
    await page.fill('input[name="query"]', testQueries[0]);
    await page.click('button[type="submit"]');
    await expect(page.locator('[data-testid="search-results"]')).toBeVisible({ timeout: 30000 });

    // 2. 히스토리 페이지로 이동
    await page.goto('/history');

    // 3. 히스토리 항목 확인
    const historyItems = page.locator('[data-testid="history-item"]');
    await expect(historyItems.first()).toBeVisible({ timeout: 5000 });

    // 4. 히스토리 항목에 쿼리 텍스트 포함 확인
    await expect(historyItems.first()).toContainText(testQueries[0]);

    // 5. 타임스탬프 확인
    await expect(historyItems.first().locator('[data-testid="history-timestamp"]')).toBeVisible();
  });

  test('should navigate to search detail from history', async ({ page }) => {
    // 1. 검색 실행
    await page.goto('/search');
    await page.fill('input[name="query"]', testQueries[2]);
    await page.click('button[type="submit"]');
    await expect(page.locator('[data-testid="search-results"]')).toBeVisible({ timeout: 30000 });

    // 2. 히스토리 페이지로 이동
    await page.goto('/history');

    // 3. 첫 번째 히스토리 항목 클릭
    await page.locator('[data-testid="history-item"]').first().click();

    // 4. 검색 상세 페이지로 이동 확인
    await expect(page).toHaveURL(/\/search\?query=/);

    // 5. 이전 검색 결과 표시 확인
    await expect(page.locator('[data-testid="search-results"]')).toBeVisible();
    await expect(page.locator('[data-testid="search-answer"]')).toBeVisible();
  });
});
