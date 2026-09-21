import { test, expect, type Page } from "@playwright/test";
import en from "../../messages/en.json";
import ar from "../../messages/ar.json";

async function noPageOverflow(page: Page) {
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth + 1,
    ),
  ).toBe(true);
}

for (const locale of ["en", "ar"] as const) {
  const m = locale === "ar" ? ar : en;
  test(`review desk sign-in, focus and reduced motion in ${locale}`, async ({
    page,
  }, info) => {
    await page.emulateMedia({ reducedMotion: "reduce" });
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto(`/${locale}/login`);
    await expect(page.locator("body")).toHaveCSS(
      "font-family",
      locale === "ar" ? /^"Noto Sans Arabic"/ : /^"Source Sans 3"/,
    );
    await expect(page.locator("html")).toHaveAttribute(
      "dir",
      locale === "ar" ? "rtl" : "ltr",
    );
    const submit = page.getByRole("button", { name: m.login, exact: true });
    await expect(submit).toBeInViewport();
    const email = page.getByLabel(m.email, { exact: true });
    await email.focus();
    await page.keyboard.press("Tab");
    const password = page.getByLabel(m.password, { exact: true });
    await expect(password).toBeFocused();
    await expect(password).toHaveCSS("outline-style", "solid");
    await expect(submit).toHaveCSS("transition-duration", "0s");
    await noPageOverflow(page);
    await page.screenshot({
      path: info.outputPath(`login-${locale}-mobile.png`),
      fullPage: true,
    });
    for (const width of [768, 1440]) {
      await page.setViewportSize({ width, height: 1000 });
      await noPageOverflow(page);
    }
    await page.screenshot({
      path: info.outputPath(`login-${locale}-desktop.png`),
      fullPage: true,
    });
  });

  test(`task rows and staff review access survive reflow in ${locale}`, async ({
    page,
    request,
  }, info) => {
    const api = process.env.TEST_API_URL || "http://localhost:18001";
    expect(api).toBe("http://localhost:18001");
    const tag = `design-${locale}-${Date.now()}`;
    const email = `${tag}@example.com`,
      password = "Verify-design-123";
    const register = await request.post(api + "/auth/register", {
      data: {
        name: "Review desk verifier",
        email,
        password,
        role: "professor",
        staff_role: "professor",
        department: "CS",
      },
    });
    expect(register.status()).toBe(201);
    const login = await request.post(api + "/auth/login", {
      data: { email, password },
    });
    expect(login.ok()).toBe(true);
    const headers = {
      Authorization: `Bearer ${(await login.json()).access_token}`,
    };
    const title = `${tag} — ${locale === "ar" ? "تحليل خوارزمية البحث وتفسير الأدلة" : "Binary search: explain the invariant and support each step with evidence"}`;
    const created = await request.post(api + "/tasks/", {
      headers,
      data: {
        type: "assignment",
        title,
        description: "Explain the invariant.\n\n\\[x^2 + y^2\\]",
        due_date: new Date(Date.now() + 86400000).toISOString(),
        target_cohort_year: 2029,
        allowed_file_types: ["txt"],
      },
    });
    expect(created.ok()).toBe(true);
    const task = await created.json();
    await page.goto(`/${locale}/login`);
    await page.getByLabel(m.email, { exact: true }).fill(email);
    await page.getByLabel(m.password, { exact: true }).fill(password);
    await page.getByRole("button", { name: m.login, exact: true }).click();
    await expect(page).toHaveURL(new RegExp(`/${locale}/staff$`));
    await page.getByLabel(m.search, { exact: true }).fill(tag);
    await expect(page.locator("article")).toHaveCount(1);
    await expect(page.locator("article")).toContainText(title);
    for (const width of [390, 768, 1440]) {
      await page.setViewportSize({ width, height: width === 390 ? 844 : 1000 });
      await noPageOverflow(page);
      await expect(
        page.getByRole("link", { name: m.openTask, exact: true }),
      ).toBeVisible();
      await page.screenshot({
        path: info.outputPath(`tasks-${locale}-${width}.png`),
        fullPage: true,
      });
    }
    // CSS zoom exercises a 200% layout magnification in the real browser.
    await page.evaluate(() => {
      document.documentElement.style.zoom = "2";
    });
    await noPageOverflow(page);
    await page.evaluate(() => {
      document.documentElement.style.zoom = "";
    });
    await page.getByRole("link", { name: m.language, exact: true }).click();
    await expect(page).toHaveURL(
      new RegExp(`/${locale === "en" ? "ar" : "en"}/staff\\?q=${tag}`),
    );
    await expect(page.locator("article")).toHaveCount(1);
    await page.goto(`/${locale}/staff/tasks/${task.id}`);
    const queueLink = page.getByRole("link", { name: m.queue, exact: true });
    await expect(queueLink).toBeInViewport();
    await queueLink.click();
    await expect(page).toHaveURL(/#task-review$/);
    await expect(
      page.getByRole("heading", { name: m.queue, exact: true }),
    ).toBeInViewport();
    const order = await page.evaluate(
      () =>
        document
          .querySelector("#task-review")!
          .compareDocumentPosition(document.querySelector("#task-guidance")!) &
        Node.DOCUMENT_POSITION_FOLLOWING,
    );
    expect(order).toBeTruthy();
    await page.getByRole("button", { name: m.deleteTask, exact: true }).click();
    const dialog = page.getByRole("alertdialog");
    await expect(dialog).toBeVisible();
    await expect(
      dialog.getByRole("button", { name: m.cancel, exact: true }),
    ).toBeFocused();
    await page.keyboard.press("Escape");
    await expect(dialog).toHaveCount(0);
    await expect(
      page.getByRole("button", { name: m.deleteTask, exact: true }),
    ).toBeFocused();
    await page.setViewportSize({ width: 390, height: 844 });
    await page.evaluate(() => scrollTo(0, 0));
    await noPageOverflow(page);
    await page.screenshot({
      path: info.outputPath(`staff-task-${locale}-mobile.png`),
      fullPage: true,
    });
  });
}
