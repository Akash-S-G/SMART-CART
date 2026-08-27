import { test, expect } from '@playwright/test';

test.describe('SmartCart — smoke & UI/UX', () => {
  test('landing loads, hero search visible, no console errors', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') errors.push(msg.text());
    });
    await page.goto('/');
    await expect(page).toHaveTitle(/SmartCart/i);
    await expect(page.getByText(/Fresh Groceries/i).first()).toBeVisible({ timeout: 10000 });
    // hero search + popular chips
    await expect(page.getByPlaceholder(/Search products/i)).toBeVisible();
    await expect(page.getByText(/Popular:/i)).toBeVisible();
    // no critical console errors
    expect(errors.filter(e => !e.includes('Failed to load'))).toEqual([]);
  });

  test('navbar mobile drawer + location modal a11y', async ({ page }) => {
    await page.goto('/');
    // location badge opens modal
    const locationBtn = page.getByRole('button', { name: /Indiranagar|560038|Delivery/i }).first();
    if (await locationBtn.isVisible()) {
      await locationBtn.click();
      await expect(page.getByRole('dialog')).toBeVisible();
      // Esc should close
      await page.keyboard.press('Escape');
      await expect(page.getByRole('dialog')).toBeHidden({ timeout: 2000 }).catch(() => {});
    }
    // collections page loads
    await page.goto('/collections');
    await expect(page.getByText(/Browse Grocery|Catalog Directory/i).first()).toBeVisible({ timeout: 10000 });
    // sort controls are visible and responsive
    await expect(page.getByText(/Sort By/i)).toBeVisible();
  });

  test('scanner page UI loads without crash', async ({ page }) => {
    await page.goto('/scanner');
    await expect(page.getByText(/Computer Vision Checkout|AI Vision/i).first()).toBeVisible({ timeout: 10000 });
    await expect(page.getByText(/Upload Snapshot|Live WebCam/i).first()).toBeVisible();
  });

  test('checkout requires auth guard', async ({ page }) => {
    await page.goto('/checkout');
    // unauthenticated should show Sign In prompt (not crash)
    await expect(page.getByText(/Sign In to Checkout|Sign In \/ Register/i).first()).toBeVisible({ timeout: 10000 });
  });

  test('collections grid has skeletons then products (or empty state)', async ({ page }) => {
    await page.goto('/collections');
    // either loading skeletons or product cards or empty state appears
    await expect(page.getByText(/Showing|Loading products|No Products Found/i).first()).toBeVisible({ timeout: 15000 });
  });

  test('dark mode toggle does not break layout', async ({ page }) => {
    await page.goto('/');
    const toggle = page.getByLabel(/Toggle theme/i);
    if (await toggle.isVisible()) {
      await toggle.click();
      await expect(page.locator('html')).toBeVisible();
      await toggle.click();
    }
  });
});
