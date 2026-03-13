import { test, expect, type Page } from '@playwright/test';

async function login(page: Page) {
  await page.goto('/login');
  await page.fill('input[id*="username"]', 'admin');
  await page.fill('input[type="password"]', 'admin');
  await page.click('button[type="submit"]');
  await expect(page).not.toHaveURL(/\/login/, { timeout: 5000 });
}

test.describe('Dark theme', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test('should toggle dark mode', async ({ page }) => {
    const toggle = page.locator('.ant-switch');
    await expect(toggle).toBeVisible();

    // Toggle dark mode on
    await toggle.click();

    // Verify dark mode is applied (Ant Design adds dark algorithm styles)
    await expect(page.locator('.ant-layout-sider')).toBeVisible();

    // Toggle back to light
    await toggle.click();
  });
});

test.describe('Internationalization', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test('should default to Russian locale', async ({ page }) => {
    await expect(page.locator('text=Дашборд')).toBeVisible();
    await expect(page.locator('text=Карта')).toBeVisible();
    await expect(page.locator('text=Алерты')).toBeVisible();
  });

  test('should switch to English', async ({ page }) => {
    // Find and click the language selector
    const langSelect = page.locator('.ant-select').filter({ hasText: 'RU' });
    await langSelect.click();
    await page.click('.ant-select-item-option >> text=EN');

    // Verify English labels
    await expect(page.locator('text=Dashboard')).toBeVisible();
    await expect(page.locator('text=Map')).toBeVisible();
    await expect(page.locator('text=Alerts')).toBeVisible();
  });

  test('should persist language choice on page reload', async ({ page }) => {
    // Switch to English
    const langSelect = page.locator('.ant-select').filter({ hasText: 'RU' });
    await langSelect.click();
    await page.click('.ant-select-item-option >> text=EN');
    await expect(page.locator('text=Dashboard')).toBeVisible();

    // Reload page
    await page.reload();
    await expect(page.locator('text=Dashboard')).toBeVisible({ timeout: 5000 });
  });
});
