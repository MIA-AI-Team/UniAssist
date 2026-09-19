import { test, expect, type Page } from "@playwright/test";
const api = process.env.TEST_API_URL || "http://localhost:18001";
const password = "Verify-repository-browser-123";

test("approved public repository becomes private pinned evidence and released feedback", async ({
  browser,
  request,
}) => {
  const tag = "repository" + Date.now();
  const accounts: {
    email: string;
    headers: { Authorization: string };
    id: number;
  }[] = [];
  for (const role of ["professor", "student"]) {
    const email = `${role}-${tag}@example.com`;
    const registered = await request.post(api + "/auth/register", {
      data: {
        name: role + " " + tag,
        email,
        password,
        role,
        staff_role: role,
        department: "CS",
        student_number: tag,
        cohort_year: 2027,
        major: "CS",
      },
    });
    expect(registered.status()).toBe(201);
    const login = await request.post(api + "/auth/login", {
      data: { email, password },
    });
    accounts.push({
      email,
      id: (await registered.json()).id,
      headers: { Authorization: "Bearer " + (await login.json()).access_token },
    });
  }
  const staff = accounts[0].headers,
    student = accounts[1].headers;
  const created = await request.post(api + "/tasks/", {
    headers: staff,
    data: {
      type: "project",
      require_team: true,
      title: tag,
      description: "Explain the code in your chosen commit.",
      due_date: new Date(Date.now() + 86400000).toISOString(),
      target_cohort_year: 2027,
      target_major: "CS",
    },
  });
  expect(created.status()).toBe(201);
  const task = (await created.json()).id;
  const rubric = await request.post(`${api}/tasks/${task}/rubrics/create`, {
    headers: staff,
    data: {
      criteria: [
        { name: "Clarity", description: "Clear explanation", max_points: 20 },
      ],
    },
  });
  expect(
    (
      await request.patch(
        `${api}/tasks/${task}/rubrics/status?rubric_id=${(await rubric.json()).rubric_id}`,
        { headers: staff, data: { status: "accepted" } },
      )
    ).ok(),
  ).toBeTruthy();
  const team = (
    await (
      await request.post(`${api}/tasks/${task}/teams`, {
        headers: student,
        data: { request_id: crypto.randomUUID(), name: "Repository team" },
      })
    ).json()
  ).id;
  expect(
    (
      await request.post(`${api}/teams/${team}/actions`, {
        headers: student,
        data: {
          request_id: crypto.randomUUID(),
          expected_version: 1,
          action: "request_approval",
        },
      })
    ).ok(),
  ).toBeTruthy();
  expect(
    (
      await request.post(`${api}/teams/${team}/actions`, {
        headers: staff,
        data: {
          request_id: crypto.randomUUID(),
          expected_version: 2,
          action: "approve",
        },
      })
    ).ok(),
  ).toBeTruthy();
  const studentContext = await browser.newContext(),
    staffContext = await browser.newContext();
  const learner = await studentContext.newPage(),
    professor = await staffContext.newPage();
  async function login(page: Page, index: number) {
    await page.goto("/en/login");
    await page
      .getByLabel("Email address", { exact: true })
      .fill(accounts[index].email);
    await page.getByLabel("Password", { exact: true }).fill(password);
    await page.getByRole("button", { name: "Sign in", exact: true }).click();
    await expect(page).toHaveURL(index === 0 ? "/en/staff" : "/en/student");
  }
  async function confirm(page: Page, name: string) {
    await page.getByRole("button", { name, exact: true }).click();
    await page
      .getByRole("alertdialog")
      .getByRole("button", { name: "Confirm", exact: true })
      .click();
  }
  await login(learner, 1);
  await login(professor, 0);
  await learner.goto(`/en/student/teams/${team}`);
  await learner
    .getByRole("link", { name: "Public GitHub repositories", exact: true })
    .click();
  await learner
    .getByLabel("Public GitHub URL or owner/repository", { exact: true })
    .fill("https://github.com/uniassist-fixtures/demo");
  await learner
    .getByRole("button", { name: "Propose repository", exact: true })
    .click();
  await learner.getByRole("link", { name: /uniassist-fixtures\/demo/ }).click();
  await expect(learner).toHaveURL(/\/student\/repositories\/\d+$/);
  const repo = learner.url().split("/").pop();
  await professor.goto(`/en/staff/repositories/${repo}`);
  await confirm(professor, "Approve repository");
  await professor
    .getByRole("button", { name: "Sync recent commits", exact: true })
    .click();
  await expect(
    professor.getByText("Student attribution is unverified.", { exact: true }),
  ).toBeVisible();
  await professor
    .getByLabel("Attribute this commit to", { exact: true })
    .selectOption(String(accounts[1].id));
  await confirm(professor, "Confirm attribution");
  await expect(
    professor.getByText(/Staff-reviewed attribution: student/),
  ).toBeVisible();
  await learner.reload();
  await learner
    .getByRole("button", { name: "Select this commit", exact: true })
    .click();
  let failed = false;
  await learner.route(/\/repositories\/\d+\/snapshots$/, async (route) => {
    if (!failed) {
      failed = true;
      await route.fulfill({
        status: 503,
        contentType: "application/json",
        body: JSON.stringify({ code: "github_unavailable" }),
      });
    } else await route.continue();
  });
  await learner
    .getByRole("button", { name: "Save commit snapshot", exact: true })
    .click();
  await expect(
    learner
      .getByRole("alert")
      .filter({ hasText: "Public GitHub repository or commit unavailable" }),
  ).toBeVisible();
  await expect(
    learner.getByLabel("Full commit SHA", { exact: true }),
  ).toHaveValue("a".repeat(40));
  await learner
    .getByRole("button", { name: "Save commit snapshot", exact: true })
    .click();
  await learner
    .getByRole("link", { name: "Use snapshot in my submission", exact: true })
    .click();
  await expect(learner).toHaveURL(
    new RegExp(`/student/tasks/${task}/submit\\?snapshot=\\d+$`),
  );
  await learner
    .getByLabel("Your work or explanation", { exact: true })
    .fill("My explanation of this exact commit.");
  await learner
    .getByRole("button", { name: "Submit work", exact: true })
    .click();
  await expect(learner).toHaveURL(/\/student\/submissions\/\d+$/);
  const submission = learner.url().split("/").pop();
  await expect(
    learner.getByRole("heading", {
      name: "Saved repository evidence",
      exact: true,
    }),
  ).toBeVisible();
  const download = learner.waitForEvent("download");
  await learner
    .getByRole("link", { name: "Download saved archive", exact: true })
    .click();
  expect((await download).suggestedFilename()).toContain("a".repeat(40));
  await professor.goto(`/en/staff/submissions/${submission}`);
  await professor
    .getByRole("button", { name: "Run AI evaluation", exact: true })
    .click();
  await expect(
    professor.getByText("Demo assessment · Mock AI", { exact: true }),
  ).toBeVisible();
  await professor.getByLabel("Final grade", { exact: true }).fill("18");
  await confirm(professor, "Confirm and release grade");
  await learner.reload();
  await expect(
    learner.getByText("Grade released", { exact: true }),
  ).toBeVisible();
  await learner.getByRole("link", { name: "العربية", exact: true }).click();
  await expect(learner.locator("html")).toHaveAttribute("dir", "rtl");
  await expect(
    learner.getByRole("heading", {
      name: "دليل المستودع المحفوظ",
      exact: true,
    }),
  ).toBeVisible();
  await learner.setViewportSize({ width: 390, height: 844 });
  expect(
    await learner.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBeTruthy();
  await learner.screenshot({
    path: test.info().outputPath("repository-ar-mobile.png"),
    fullPage: true,
  });
  await studentContext.close();
  await staffContext.close();
});
