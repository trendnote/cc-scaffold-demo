/**
 * Authentication Test Fixtures
 *
 * Task 4.3a: E2E Testing
 */
import { Page } from '@playwright/test';

/**
 * L1 일반 사용자로 로그인
 */
export async function loginAsUser(page: Page) {
  await page.goto('/login');
  await page.fill('input[name="email"]', 'user@example.com');
  await page.fill('input[name="password"]', 'password123');
  await page.click('button[type="submit"]');
  await page.waitForURL('/');
}

/**
 * L2 팀장으로 로그인
 */
export async function loginAsTeamLead(page: Page) {
  await page.goto('/login');
  await page.fill('input[name="email"]', 'teamlead@example.com');
  await page.fill('input[name="password"]', 'password123');
  await page.click('button[type="submit"]');
  await page.waitForURL('/');
}

/**
 * L3 관리자로 로그인
 */
export async function loginAsAdmin(page: Page) {
  await page.goto('/login');
  await page.fill('input[name="email"]', 'admin@example.com');
  await page.fill('input[name="password"]', 'password123');
  await page.click('button[type="submit"]');
  await page.waitForURL('/');
}

/**
 * 로그아웃
 */
export async function logout(page: Page) {
  await page.click('button:has-text("로그아웃")');
  await page.waitForURL('/login');
}
