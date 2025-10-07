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

    // Verify page renders with main content region
    await expect(page.locator("main")).toBeVisible();

    // Verify a heading is present (structure check, not content)
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
  });

  test("language switcher works", async ({ page }) => {
    await page.goto("/en");

    // Verify English locale via URL and html[lang] attribute
    await expect(page).toHaveURL("/en");
    await expect(page.locator("html")).toHaveAttribute("lang", "en");

    // Verify main content region is visible (structure check)
    await expect(page.locator("main")).toBeVisible();

    // Click language switcher
    await page.getByRole("button", { name: /switch language/i }).click();

    // Should redirect to Russian
    await expect(page).toHaveURL("/ru");

    // Verify Russian locale via html[lang] attribute
    await expect(page.locator("html")).toHaveAttribute("lang", "ru");

    // Verify main content region remains visible after language switch
    await expect(page.locator("main")).toBeVisible();
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
