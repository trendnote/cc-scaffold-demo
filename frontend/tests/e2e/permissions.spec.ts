/**
 * Permission-based Access E2E Tests
 *
 * Task 4.3a: E2E Testing
 *
 * 검증 시나리오:
 * 1. L1 사용자는 L2 문서 접근 불가
 * 2. L3 관리자는 모든 문서 접근 가능
 */
import { test, expect } from '@playwright/test';
import { loginAsUser, loginAsAdmin } from './fixtures/auth';

test.describe('Permission-based Access', () => {
  test('L1 user should only see filtered search results', async ({ page }) => {
    // 1. L1 사용자로 로그인
    await loginAsUser(page);

    // 2. 검색 실행
    await page.goto('/search');
    await page.fill('input[name="query"]', '급여 정보');
    await page.click('button[type="submit"]');

    // 3. 검색 결과 대기
    await expect(page.locator('[data-testid="search-results"]')).toBeVisible({ timeout: 30000 });

    // 4. L1 권한으로 필터링된 결과 확인
    const sources = page.locator('[data-testid="source-item"]');
    const count = await sources.count();

    // 5. 각 출처의 접근 레벨 확인 (L1만 표시되어야 함)
    for (let i = 0; i < count; i++) {
      const source = sources.nth(i);
      const accessLevel = await source.locator('[data-testid="access-level"]').textContent();
      expect(accessLevel).toBe('L1');
    }

    // 6. L2, L3 문서 접근 시도 (URL 직접 접근)
    await page.goto('/documents/l2-document-id');

    // 7. 접근 거부 메시지 확인
    await expect(page.locator('text=접근 권한이 없습니다')).toBeVisible({ timeout: 5000 });
  });

  test('L3 admin should see all search results', async ({ page }) => {
    // 1. L3 관리자로 로그인
    await loginAsAdmin(page);

    // 2. 검색 실행
    await page.goto('/search');
    await page.fill('input[name="query"]', '전사 정책');
    await page.click('button[type="submit"]');

    // 3. 검색 결과 대기
    await expect(page.locator('[data-testid="search-results"]')).toBeVisible({ timeout: 30000 });

    // 4. 다양한 접근 레벨의 문서 확인
    const sources = page.locator('[data-testid="source-item"]');
    const count = await sources.count();

    expect(count).toBeGreaterThan(0);

    // 5. 관리자 배지 표시 확인
    await expect(page.locator('[data-testid="admin-badge"]')).toBeVisible();

    // 6. 모든 레벨 문서 접근 가능 확인
    const accessLevels = await sources.locator('[data-testid="access-level"]').allTextContents();
    const hasMultipleLevels = new Set(accessLevels).size > 1;

    expect(hasMultipleLevels).toBe(true); // L1, L2, L3 문서 모두 포함
  });
});
