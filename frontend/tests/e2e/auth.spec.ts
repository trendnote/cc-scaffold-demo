/**
 * Authentication Flow E2E Tests
 *
 * Task 4.3a: E2E Testing
 *
 * 검증 시나리오:
 * 1. 로그인 성공 플로우
 * 2. 로그아웃 플로우
 */
import { test, expect } from '@playwright/test';
import { testUsers } from './fixtures/test-data';

test.describe('Authentication Flow', () => {
  test('should login successfully with valid credentials', async ({ page }) => {
    // 1. 로그인 페이지로 이동
    await page.goto('/login');

    // 2. 로그인 폼 확인
    await expect(page.locator('h1:has-text("로그인")')).toBeVisible();

    // 3. 이메일 입력
    await page.fill('input[name="email"]', testUsers.user.email);

    // 4. 비밀번호 입력
    await page.fill('input[name="password"]', testUsers.user.password);

    // 5. 로그인 버튼 클릭
    await page.click('button[type="submit"]');

    // 6. 홈 페이지로 리다이렉트 확인
    await expect(page).toHaveURL('/', { timeout: 5000 });

    // 7. 사용자 정보 표시 확인
    await expect(page.locator('[data-testid="user-name"]')).toContainText(testUsers.user.name);

    // 8. 로그아웃 버튼 존재 확인
    await expect(page.locator('button:has-text("로그아웃")')).toBeVisible();
  });

  test('should logout successfully', async ({ page }) => {
    // 1. 먼저 로그인
    await page.goto('/login');
    await page.fill('input[name="email"]', testUsers.user.email);
    await page.fill('input[name="password"]', testUsers.user.password);
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL('/');

    // 2. 로그아웃 버튼 클릭
    await page.click('button:has-text("로그아웃")');

    // 3. 로그인 페이지로 리다이렉트 확인
    await expect(page).toHaveURL('/login', { timeout: 5000 });

    // 4. 로그인 폼 표시 확인
    await expect(page.locator('input[name="email"]')).toBeVisible();

    // 5. 보호된 페이지 접근 시도
    await page.goto('/search');

    // 6. 로그인 페이지로 리다이렉트 확인 (인증 필요)
    await expect(page).toHaveURL('/login');
  });
});
