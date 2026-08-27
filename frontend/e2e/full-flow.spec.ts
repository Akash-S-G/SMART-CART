import { test, expect } from '@playwright/test';

const randomUser = () => {
  const id = Math.random().toString(36).slice(2, 8);
  return { username: `e2e${id}`, email: `e2e${id}@example.com`, password: 'Test12345!' };
};

test.describe('SmartCart — full commerce flow (local DB)', () => {
  test('register → browse → product → cart → checkout → payment → orders', async ({ page }) => {
    const user = randomUser();
    await page.goto('/');
    await expect(page.getByText(/SmartCart/i).first()).toBeVisible();

    // Open auth modal via Sign In
    await page.getByRole('button', { name: /Sign In/i }).click();
    await expect(page.getByRole('dialog')).toBeVisible();
    // Switch to Sign Up
    await page.getByRole('tab', { name: /Sign Up/i }).click();
    await page.getByLabel(/Username/i).fill(user.username);
    await page.getByLabel(/Email Address/i).fill(user.email);
    await page.getByLabel(/^Password/i).fill(user.password);
    await page.getByRole('button', { name: /Create Account/i }).click();
    // Should close modal and show toast / logged in
    await expect(page.getByRole('dialog')).toBeHidden({ timeout: 10000 });

    // Browse collections
    await page.goto('/collections');
    await expect(page.getByText(/Browse Grocery|Catalog Directory/i).first()).toBeVisible({ timeout: 10000 });
    // Wait for products or empty state, but with seeded DB there should be products
    await page.waitForTimeout(1500);
    const firstCard = page.locator('a[href^="/product/"]').first();
    await expect(firstCard).toBeVisible({ timeout: 10000 });
    await firstCard.click();
    await expect(page.getByText(/Add to Cart/i).first()).toBeVisible({ timeout: 10000 });

    // Add to cart
    const addBtn = page.getByRole('button', { name: /Add to Cart/i }).first();
    await expect(addBtn).toBeVisible({ timeout: 10000 });
    await addBtn.click();
    // wait for cart mutation + toast
    await page.waitForTimeout(1500);
    // verify cart badge updated (optional) — cart button shows price after add, so just wait for network
    await page.waitForLoadState('networkidle');

    // Go to checkout
    await page.goto('/checkout');
    await page.waitForLoadState('networkidle');
    await expect(page.getByText(/Checkout/i).first()).toBeVisible({ timeout: 10000 });
    // Should not show Sign In guard now that we're logged in
    await expect(page.getByText(/Sign In to Checkout/i)).toBeHidden();

    // Fill shipping if needed (if step 0 visible)
    const contBtn = page.getByRole('button', { name: /Continue to Payment/i });
    if (await contBtn.isVisible()) {
      await page.getByPlaceholder('Alex', { exact: true }).fill('E2E');
      await page.getByPlaceholder('Mercer', { exact: true }).fill('Tester');
      await page.getByPlaceholder('123 Innovation Drive, Apt 4B', { exact: true }).fill('123 Test St');
      await page.getByPlaceholder('Bengaluru', { exact: true }).first().fill('Bengaluru');
      await page.getByPlaceholder('Karnataka', { exact: true }).fill('Karnataka');
      await page.getByPlaceholder('560001', { exact: true }).fill('560001');
      await page.getByPlaceholder('India', { exact: true }).fill('India');
      await page.getByPlaceholder('alex@gmail.com', { exact: true }).fill(user.email);
      await page.getByPlaceholder('+91 99999 88888', { exact: true }).fill('9999988888');
      await expect(contBtn).toBeEnabled({ timeout: 5000 });
      await contBtn.click();
    }

    // Payment step — select card and review
    await expect(page.getByText(/Secure Payment|Review Information/i).first()).toBeVisible({ timeout: 10000 });
    // Try to go to review if not already
    const reviewBtn = page.getByRole('button', { name: /Review Details/i });
    if (await reviewBtn.isVisible()) await reviewBtn.click();
    await expect(page.getByText(/Review Information|Payment Method/i).first()).toBeVisible({ timeout: 10000 });
    const placeBtn = page.getByRole('button', { name: /Confirm & Place Order/i });
    await expect(placeBtn).toBeVisible();
    await placeBtn.click();
    // Should show order confirmation
    await expect(page.getByText(/Thank you for your order|Order number/i).first()).toBeVisible({ timeout: 15000 });
  });

  test('wishlist and reviews', async ({ page }) => {
    const user = randomUser();
    // register quickly via API instead of UI to speed up
    await page.request.post('http://localhost:8000/auth/register', {
      data: { username: user.username, email: user.email, password: user.password },
    });
    // login via UI to get session
    await page.goto('/');
    await page.getByRole('button', { name: /Sign In/i }).click();
    await page.getByRole('tab', { name: /Sign In/i }).click();
    await page.getByLabel(/Email Address/i).fill(user.email);
    await page.getByLabel(/^Password/i).fill(user.password);
    await page.getByRole('button', { name: 'Sign In', exact: true }).click();
    await expect(page.getByRole('dialog')).toBeHidden({ timeout: 10000 });

    await page.goto('/collections');
    const firstCard = page.locator('a[href^="/product/"]').first();
    await expect(firstCard).toBeVisible({ timeout: 10000 });
    await firstCard.click();
    await expect(page.getByText(/Add to Cart/i).first()).toBeVisible();
    // Wishlist heart
    const wishBtn = page.getByRole('button', { name: /Wishlist/i }).first();
    if (await wishBtn.isVisible()) {
      await wishBtn.click();
      await page.waitForTimeout(500);
    }
    // Reviews tab
    await page.getByRole('tab', { name: /Reviews/i }).click();
    await expect(page.getByText(/Customer Reviews|Write a Review/i).first()).toBeVisible({ timeout: 10000 });
  });
});
