import { test, expect, type Page } from '@playwright/test';

async function login(page: Page) {
  await page.goto('/login');
  await page.fill('input[id*="username"]', 'admin');
  await page.fill('input[type="password"]', 'admin');
  await page.click('button[type="submit"]');
  await expect(page).not.toHaveURL(/\/login/, { timeout: 5000 });
}

test.describe('Incidents', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
    await page.click('text=Инциденты');
    await expect(page).toHaveURL(/\/incidents/);
  });

  test('should display incidents table', async ({ page }) => {
    await expect(page.locator('.ant-table')).toBeVisible();
    await expect(page.locator('.ant-table-thead')).toBeVisible();
  });

  test('should open create incident modal', async ({ page }) => {
    await page.click('button:has-text("Создать")');
    await expect(page.locator('.ant-modal')).toBeVisible();
    await expect(page.locator('.ant-modal-title')).toContainText('инцидент');
  });

  test('should close create modal on cancel', async ({ page }) => {
    await page.click('button:has-text("Создать")');
    await expect(page.locator('.ant-modal')).toBeVisible();
    await page.click('.ant-modal .ant-btn:not(.ant-btn-primary)');
    await expect(page.locator('.ant-modal')).not.toBeVisible();
  });

  test('should filter by status', async ({ page }) => {
    const statusSelect = page.locator('.ant-select').first();
    await statusSelect.click();
    await page.click('.ant-select-item-option >> text=Новый');
    // Table should refresh (just verify it doesn't crash)
    await expect(page.locator('.ant-table')).toBeVisible();
  });

  test('should filter by priority', async ({ page }) => {
    const prioritySelect = page.locator('.ant-select').nth(1);
    await prioritySelect.click();
    await page.click('.ant-select-item-option >> text=Критический');
    await expect(page.locator('.ant-table')).toBeVisible();
  });
});
