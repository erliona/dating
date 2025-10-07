import { test, expect } from "@playwright/test";

test.describe("Smoke Tests", () => {
  test("health endpoint returns healthy status", async ({ request }) => {
    const response = await request.get("/api/health");
    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data.status).toBe("healthy");
    expect(data.service).toBe("webapp");
    expect(data.timestamp).toBeTruthy();
  });

  test("homepage loads successfully", async ({ page }) => {
    await page.goto("/");

    // Should redirect to /ru or /en
    await expect(page).toHaveURL(/\/(ru|en)/);

    // Should have a title
    await expect(page).toHaveTitle(/Dating/);
  });

  test("language switcher works", async ({ page }) => {
    await page.goto("/en");

    // Check English content is present
    await expect(page.getByText("Welcome to Dating")).toBeVisible();

    // Click language switcher
    await page.getByRole("button", { name: /switch language/i }).click();

    // Should redirect to Russian
    await expect(page).toHaveURL("/ru");

    // Check Russian content is present
    await expect(page.getByText("Добро пожаловать в Dating")).toBeVisible();
  });

  test("API proxy is accessible", async ({ request }) => {
    // Test that the proxy route exists (even if backend is not available)
    const response = await request.get("/api/proxy/health", {
      failOnStatusCode: false,
    });

    // Should return 502 if backend is down, or 200+ if backend is up
    expect([200, 502]).toContain(response.status());
  });
});
