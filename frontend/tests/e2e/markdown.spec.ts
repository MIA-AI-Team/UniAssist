import { test, expect } from "@playwright/test";
import en from "../../messages/en.json";
import ar from "../../messages/ar.json";

const api = process.env.TEST_API_URL || "http://localhost:18001";
const password = "Verify-math-browser-123";

for (const locale of ["en", "ar"] as const) {
  test(`math authoring, saved content and mobile layout in ${locale}`, async ({
    page,
    request,
    browser,
  }, testInfo) => {
    expect(api).toBe("http://localhost:18001");
    const m = locale === "ar" ? ar : en;
    const tag = `math-${locale}-${Date.now()}`;
    const professorEmail = `${tag}-prof@example.com`;
    const studentEmail = `${tag}-student@example.com`;
    for (const role of ["professor", "student"] as const) {
      const registered = await request.post(api + "/auth/register", {
        data: {
          name: `${role} ${tag}`,
          email: role === "professor" ? professorEmail : studentEmail,
          password,
          role,
          ...(role === "professor"
            ? { staff_role: "professor", department: "CS" }
            : { student_number: tag, cohort_year: 2027, major: "CS" }),
        },
      });
      expect(registered.status()).toBe(201);
    }
    await page.goto(`/${locale}/login`);
    await page.getByLabel(m.email, { exact: true }).fill(professorEmail);
    await page.getByLabel(m.password, { exact: true }).fill(password);
    await page.getByRole("button", { name: m.login, exact: true }).click();
    await expect(page).toHaveURL(new RegExp(`/${locale}/staff$`));
    await page.goto(`/${locale}/staff/tasks/new`);
    const wide = Array.from({ length: 40 }, (_, i) => `a_{${i + 1}}`).join(
      " + ",
    );
    const instructions =
      (locale === "ar" ? "اشرح المعادلة" : "Explain the equation") +
      String.raw` \(\frac{1}{2}\)` +
      "\n\n\\[\n" +
      wide +
      "\n\\]";
    await page.getByLabel(m.title, { exact: true }).fill(tag);
    await page.getByLabel(m.description, { exact: true }).fill(instructions);
    const preview = page.getByRole("region", {
      name: m.markdown.preview.replace("{field}", m.description),
    });
    await expect(preview.locator(".katex")).toHaveCount(2);
    const previewMath = await preview.locator("annotation").allTextContents();
    await page
      .getByLabel(m.due, { exact: true })
      .fill(new Date(Date.now() + 172800000).toISOString().slice(0, 16));
    await page.getByLabel(m.cohort_year, { exact: true }).fill("2027");
    const taskResponse = page.waitForResponse(
      (r) =>
        /\/api\/backend\/tasks\/?$/.test(r.url()) &&
        r.request().method() === "POST" &&
        r.status() !== 308,
    );
    await page.getByRole("button", { name: m.createTask, exact: true }).click();
    const response = await taskResponse;
    expect(response.status()).toBe(201);
    expect(response.request().postDataJSON().description).toBe(instructions);
    await expect(page).toHaveURL(/\/staff\/tasks\/\d+$/);
    const taskId = page.url().split("/").at(-1)!;
    await expect(
      page.locator(".academic-markdown").first().locator("annotation"),
    ).toHaveText(previewMath);

    await page.getByRole("button", { name: m.manual, exact: true }).click();
    const criterionName = String.raw`Reasoning \(x^2\)`;
    const criterionDescription = String.raw`Explain \[\sqrt{x}\]`;
    await page.getByLabel(m.criterionName, { exact: true }).fill(criterionName);
    await page
      .getByLabel(m.criterionDescription, { exact: true })
      .fill(criterionDescription);
    await expect(
      page
        .getByRole("region", {
          name: m.markdown.preview.replace("{field}", m.criterionDescription),
        })
        .locator(".katex"),
    ).toHaveCount(1);
    await page.getByRole("button", { name: m.save, exact: true }).click();
    const rubric = page.locator("article").filter({
      has: page.getByRole("heading", { name: new RegExp(`${m.version} 1`) }),
    });
    await expect(rubric.locator(".katex")).toHaveCount(2);
    await rubric.getByRole("button", { name: m.approve, exact: true }).click();
    await page
      .getByRole("alertdialog")
      .getByRole("button", { name: m.confirm, exact: true })
      .click();
    await expect(
      rubric.getByRole("heading", { name: new RegExp(`${m.version} 1`) }),
    ).toContainText(m.rubric_accepted);

    const guidance = String.raw`Private expectation \(q_{private}\)`;
    await page.getByLabel(m.guidance.content, { exact: true }).fill(guidance);
    await expect(
      page
        .getByRole("region", {
          name: m.markdown.preview.replace("{field}", m.guidance.content),
        })
        .locator(".katex"),
    ).toHaveCount(1);
    await page
      .getByRole("button", { name: m.guidance.save, exact: true })
      .click();
    await page
      .getByRole("alertdialog")
      .getByRole("button", { name: m.confirm, exact: true })
      .click();
    await expect(
      page.getByText(m.guidance.saved, { exact: true }),
    ).toBeVisible();
    await page.reload();
    const guidanceHistory = page
      .locator("details")
      .filter({ has: page.locator("annotation", { hasText: "q_{private}" }) });
    await guidanceHistory.locator("summary").click();
    await expect(guidanceHistory.locator(".katex")).toBeVisible();

    const studentContext = await browser.newContext({
      viewport: { width: 390, height: 844 },
    });
    try {
      const student = await studentContext.newPage();
      await student.goto(`/${locale}/login`);
      await student.getByLabel(m.email, { exact: true }).fill(studentEmail);
      await student.getByLabel(m.password, { exact: true }).fill(password);
      await student.getByRole("button", { name: m.login, exact: true }).click();
      await expect(student).toHaveURL(new RegExp(`/${locale}/student$`));
      await student.goto(`/${locale}/student/tasks/${taskId}`);
      await expect(
        student.getByRole("heading", { name: tag, exact: true }),
      ).toBeVisible();
      await expect(student.locator("html")).toHaveAttribute(
        "dir",
        locale === "ar" ? "rtl" : "ltr",
      );
      await expect(student.locator(".katex")).toHaveCount(4);
      await expect(
        student.getByText(m.guidance.title, { exact: true }),
      ).toHaveCount(0);
      await expect(
        student.locator("annotation", { hasText: "q_{private}" }),
      ).toHaveCount(0);
      const equation = student.locator(".katex-display").first();
      await expect(equation).toHaveCSS("direction", "ltr");
      await expect(equation).toHaveCSS("overflow-x", "auto");
      expect(
        await equation.evaluate((el) => el.scrollWidth > el.clientWidth),
      ).toBe(true);
      expect(
        await student.evaluate(
          () => document.documentElement.scrollWidth <= window.innerWidth + 1,
        ),
      ).toBe(true);
      await student.screenshot({
        path: testInfo.outputPath(`math-${locale}-mobile.png`),
        fullPage: true,
      });
    } finally {
      await studentContext.close();
    }
  });
}
