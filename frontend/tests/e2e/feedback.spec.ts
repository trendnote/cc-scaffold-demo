/**
 * Feedback Submission E2E Tests
 *
 * Task 4.3a: E2E Testing
 *
 * 검증 시나리오:
 * 1. 긍정 피드백 제출
 * 2. 부정 피드백 제출 (코멘트 포함)
 */
import { test, expect } from '@playwright/test';
import { loginAsUser } from './fixtures/auth';
import { testQueries, testFeedback } from './fixtures/test-data';

test.describe('Feedback Submission', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsUser(page);

    // 검색 실행 (피드백 대상 생성)
    await page.goto('/search');
    await page.fill('input[name="query"]', testQueries[0]);
    await page.click('button[type="submit"]');
    await expect(page.locator('[data-testid="search-results"]')).toBeVisible({ timeout: 30000 });
  });

  test('should submit positive feedback successfully', async ({ page }) => {
    // 1. 피드백 섹션 확인
    await expect(page.locator('[data-testid="feedback-section"]')).toBeVisible();

    // 2. 별점 5점 선택
    await page.locator('[data-testid="rating-5"]').click();

    // 3. 코멘트 입력
    await page.fill('textarea[name="comment"]', testFeedback.positive.comment);

    // 4. 제출
    await page.click('button[data-testid="submit-feedback"]');

    // 5. 성공 메시지 확인
    await expect(page.locator('text=피드백이 제출되었습니다')).toBeVisible({ timeout: 5000 });

    // 6. 피드백 섹션 초기화 확인
    await expect(page.locator('textarea[name="comment"]')).toHaveValue('');
  });

  test('should submit negative feedback with comment', async ({ page }) => {
    // 1. 피드백 섹션 확인
    await expect(page.locator('[data-testid="feedback-section"]')).toBeVisible();

    // 2. 별점 1점 선택
    await page.locator('[data-testid="rating-1"]').click();

    // 3. 부정 피드백 코멘트 입력
    await page.fill('textarea[name="comment"]', testFeedback.negative.comment);

    // 4. 제출
    await page.click('button[data-testid="submit-feedback"]');

    // 5. 성공 메시지 확인
    await expect(page.locator('text=피드백이 제출되었습니다')).toBeVisible({ timeout: 5000 });

    // 6. 피드백이 저장되었는지 확인 (히스토리에서)
    await page.goto('/history');
    const historyItem = page.locator('[data-testid="history-item"]').first();
    await expect(historyItem.locator('[data-testid="feedback-indicator"]')).toBeVisible();
  });
});
