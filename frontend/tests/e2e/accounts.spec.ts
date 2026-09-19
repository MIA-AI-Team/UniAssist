import { test, expect, type Page } from "@playwright/test";
import { execFileSync } from "node:child_process";
import path from "node:path";
const api = process.env.TEST_API_URL || "http://localhost:18001";
const password = "Verify-account-browser-123";

test("profile recovery, admin correction, suspension and Arabic operational privacy", async ({
  browser,
  request,
}, testInfo) => {
  // Operator bootstrap is test-only and cannot target the normal app database.
  expect(api).toBe("http://localhost:18001");
  const tag = "accounts" + Date.now(),
    root = path.resolve(process.cwd(), "..");
  const adminEmail = `${tag}-admin@example.com`,
    studentEmail = `${tag}-student@example.com`;
  execFileSync(
    path.join(
      root,
      ".venv",
      process.platform === "win32" ? "Scripts/python.exe" : "bin/python",
    ),
    [
      "-c",
      "import asyncio,sys; from backend.bootstrap_admin import bootstrap; asyncio.run(bootstrap('Browser Operator',sys.argv[1],sys.argv[2]))",
      adminEmail,
      password,
    ],
    {
      cwd: root,
      env: {
        ...process.env,
        PYTHONPATH: [
          path.join(root, "backend"),
          path.join(root, "AI-Service"),
        ].join(path.delimiter),
        DATABASE_URL:
          "postgresql+asyncpg://verify:verify-local-only@localhost:15432/verify",
        SECRET_KEY: "verification-bootstrap-only",
        MOCK_MODE: "true",
      },
    },
  );
  const registered = await request.post(api + "/auth/register", {
    data: {
      name: "Browser Student",
      email: studentEmail,
      password,
      role: "student",
      student_number: tag,
      cohort_year: 2027,
      major: "CS",
    },
  });
  expect(registered.status()).toBe(201);
  const studentId = (await registered.json()).id;
  async function login(page: Page, email: string) {
    await page.goto("/en/login");
    await page.getByLabel("Email address").fill(email);
    await page.getByLabel("Password", { exact: true }).fill(password);
    await page.getByRole("button", { name: "Sign in", exact: true }).click();
    await expect(page).toHaveURL(
      email === adminEmail ? /\/en\/admin$/ : /\/en\/student$/,
    );
  }
  const studentContext = await browser.newContext(),
    adminContext = await browser.newContext();
  const student = await studentContext.newPage(),
    admin = await adminContext.newPage();
  await login(student, studentEmail);
  await student.getByRole("link", { name: "My profile", exact: true }).click();
  await expect(student.getByLabel("Full name")).toHaveValue("Browser Student");
  await expect(student.getByLabel("Cohort year")).toHaveCount(0);
  await student.getByLabel("Full name").fill("Preserved Student");
  await student.getByLabel("GitHub username").fill("student-proof");
  await student.route("**/api/backend/auth/me", async (route) => {
    if (route.request().method() === "PATCH")
      await route.fulfill({
        status: 503,
        contentType: "application/json",
        body: JSON.stringify({ code: "backend_unavailable" }),
      });
    else await route.continue();
  });
  await student
    .getByRole("button", { name: "Save changes", exact: true })
    .click();
  await expect(
    student.getByRole("alert").filter({ hasText: "backend" }),
  ).toBeVisible();
  await expect(student.getByLabel("Full name")).toHaveValue(
    "Preserved Student",
  );
  await student.unroute("**/api/backend/auth/me");
  await student
    .getByRole("button", { name: "Save changes", exact: true })
    .click();
  await expect(
    student.getByRole("alert").filter({ hasText: "backend" }),
  ).toHaveCount(0);
  await student.reload();
  await expect(student.getByLabel("GitHub username")).toHaveValue(
    "student-proof",
  );
  await login(admin, adminEmail);
  await admin.getByLabel("Name, email or student number").fill(tag);
  await admin.getByRole("button", { name: "Search", exact: true }).click();
  await admin
    .getByRole("link", { name: "Preserved Student", exact: true })
    .click();
  await expect(admin).toHaveURL(new RegExp(`/admin/users/${studentId}$`));
  await admin.getByLabel("Cohort year").fill("2028");
  await admin.getByLabel("Account status").selectOption("suspended");
  await admin
    .getByRole("button", { name: "Save changes", exact: true })
    .click();
  await admin
    .getByRole("alertdialog")
    .getByRole("button", { name: "Confirm", exact: true })
    .click();
  await expect(
    admin.getByText("Changes saved.", { exact: true }),
  ).toBeVisible();
  await student.reload();
  await expect(student).toHaveURL(/\/login\?expired=1/);
  await admin.getByLabel("Account status").selectOption("active");
  await admin
    .getByRole("button", { name: "Save changes", exact: true })
    .click();
  await admin
    .getByRole("alertdialog")
    .getByRole("button", { name: "Confirm", exact: true })
    .click();
  await expect(admin.getByLabel("Account status")).toHaveValue("active");
  await login(student, studentEmail);
  await admin.getByRole("link", { name: "Audit history", exact: true }).click();
  await expect(
    admin.getByText("account.corrected", { exact: true }).first(),
  ).toBeVisible();
  await expect(admin.getByText("student-proof", { exact: true })).toHaveCount(
    0,
  );
  await admin.getByRole("link", { name: "AI operations", exact: true }).click();
  await admin.getByRole("link", { name: "العربية", exact: true }).click();
  await expect(admin).toHaveURL(/\/ar\/admin\/metrics$/);
  await expect(admin.locator("html")).toHaveAttribute("dir", "rtl");
  await admin.setViewportSize({ width: 390, height: 844 });
  await expect(
    admin.getByRole("heading", {
      name: "عمليات الذكاء الاصطناعي",
      exact: true,
    }),
  ).toBeVisible();
  expect(
    await admin.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await admin.screenshot({
    path: testInfo.outputPath("admin-ar-mobile.png"),
    fullPage: true,
  });
  await admin.goto("/en/student");
  await expect(
    admin.getByRole("heading", {
      name: "This workspace is not available for administrators.",
    }),
  ).toBeVisible();
  await adminContext.close();
  await studentContext.close();
});
