import { test, expect } from "@playwright/test";

test.describe("Authentication", () => {
  test("login page loads successfully", async ({ page }) => {
    await page.goto("/en/login");

    // Verify page loads
    await expect(page).toHaveURL(/\/en\/login/);

    // Verify login UI elements are present
    await expect(page.getByRole("heading", { name: /login/i })).toBeVisible();

    // Verify Telegram widget container exists
    await expect(page.locator("#telegram-login-widget")).toBeVisible();
  });

  test("login page shows unauthorized message from query param", async ({ page }) => {
    await page.goto("/en/login?reason=unauthorized");

    // Verify unauthorized message is shown
    await expect(page.getByText(/need to login/i)).toBeVisible();
  });

  test("protected routes redirect to login when not authenticated", async ({
    page,
  }) => {
    // Try to access a protected route (profile)
    await page.goto("/en/profile");

    // Should redirect to login with reason
    await expect(page).toHaveURL(/\/en\/login\?reason=unauthorized/);
  });

  test("logout API endpoint is accessible", async ({ request }) => {
    const response = await request.post("/api/auth/logout");

    // Should succeed (even without cookies)
    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data.success).toBe(true);
  });

  test("refresh API endpoint requires authentication", async ({ request }) => {
    const response = await request.post("/api/auth/refresh", {
      failOnStatusCode: false,
    });

    // Should return 401 without refresh token
    expect(response.status()).toBe(401);
  });

  test("auth tg endpoint validates request body", async ({ request }) => {
    const response = await request.post("/api/auth/tg", {
      data: {},
      failOnStatusCode: false,
    });

    // Should return 400 for missing initData
    expect(response.status()).toBe(400);

    const data = await response.json();
    expect(data.error).toContain("Missing initData");
  });
});
