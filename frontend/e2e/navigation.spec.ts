import { test, expect, type Page } from '@playwright/test';

async function login(page: Page) {
  await page.goto('/login');
  await page.fill('input[id*="username"]', 'admin');
  await page.fill('input[type="password"]', 'admin');
  await page.click('button[type="submit"]');
  await expect(page).not.toHaveURL(/\/login/, { timeout: 5000 });
}

test.describe('Navigation', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test('should show dashboard after login', async ({ page }) => {
    await expect(page.locator('.ant-statistic')).toHaveCount(4, { timeout: 10000 });
  });

  test('should navigate to map page', async ({ page }) => {
    await page.click('text=Карта');
    await expect(page).toHaveURL(/\/map/);
    await expect(page.locator('.leaflet-container')).toBeVisible({ timeout: 10000 });
  });

  test('should navigate to metrics page', async ({ page }) => {
    await page.click('text=Метрики');
    await expect(page).toHaveURL(/\/metrics/);
    await expect(page.locator('.ant-select')).toBeVisible();
  });

  test('should navigate to alerts page', async ({ page }) => {
    await page.click('text=Алерты');
    await expect(page).toHaveURL(/\/alerts/);
    await expect(page.locator('.ant-table')).toBeVisible();
  });

  test('should navigate to incidents page', async ({ page }) => {
    await page.click('text=Инциденты');
    await expect(page).toHaveURL(/\/incidents/);
    await expect(page.locator('.ant-table')).toBeVisible();
  });

  test('should navigate to settings page', async ({ page }) => {
    await page.click('text=Настройки');
    await expect(page).toHaveURL(/\/settings/);
    await expect(page.locator('.ant-tabs')).toBeVisible();
  });

  test('should navigate to admin page', async ({ page }) => {
    await page.click('text=Администрирование');
    await expect(page).toHaveURL(/\/admin/);
    await expect(page.locator('.ant-tabs')).toBeVisible();
  });

  test('should collapse and expand sidebar', async ({ page }) => {
    const sider = page.locator('.ant-layout-sider');
    await expect(sider).not.toHaveClass(/ant-layout-sider-collapsed/);

    await page.click('[class*="anticon-menu-fold"]');
    await expect(sider).toHaveClass(/ant-layout-sider-collapsed/);

    await page.click('[class*="anticon-menu-unfold"]');
    await expect(sider).not.toHaveClass(/ant-layout-sider-collapsed/);
  });
});
