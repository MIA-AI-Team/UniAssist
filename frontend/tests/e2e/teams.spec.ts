import { test, expect, type Page } from "@playwright/test";
const api = process.env.TEST_API_URL || "http://localhost:18001";
const password = "Verify-team-browser-123";

test("consented team approval, individual submission and Arabic locked roster", async ({
  browser,
  request,
}) => {
  const tag = "team" + Date.now();
  const accounts: {
    email: string;
    number: string;
    headers: { Authorization: string };
  }[] = [];
  for (const [index, role] of [
    "professor",
    "student",
    "student",
    "teaching_assistant",
  ].entries()) {
    const email = `${tag}-${index}@example.com`;
    const response = await request.post(api + "/auth/register", {
      data: {
        name: `Team member ${index}`,
        email,
        password,
        role,
        staff_role: role,
        department: "CS",
        student_number: `${tag}-${index}`,
        cohort_year: 2027,
        major: "CS",
      },
    });
    expect(response.status()).toBe(201);
    const login = await request.post(api + "/auth/login", {
      data: { email, password },
    });
    accounts.push({
      email,
      number: `${tag}-${index}`,
      headers: { Authorization: "Bearer " + (await login.json()).access_token },
    });
  }
  const taskResponse = await request.post(api + "/tasks/", {
    headers: accounts[0].headers,
    data: {
      type: "project",
      require_team: true,
      title: tag,
      description: "Individual explanations with approved team context.",
      due_date: new Date(Date.now() + 86400000).toISOString(),
      target_cohort_year: 2027,
      target_major: "CS",
    },
  });
  expect(taskResponse.status()).toBe(201);
  const task = (await taskResponse.json()).id;
  const rubric = await request.post(`${api}/tasks/${task}/rubrics/create`, {
    headers: accounts[0].headers,
    data: {
      criteria: [
        { name: "Clarity", description: "Explain clearly", max_points: 20 },
      ],
    },
  });
  const rid = (await rubric.json()).rubric_id;
  expect(
    (
      await request.patch(
        `${api}/tasks/${task}/rubrics/status?rubric_id=${rid}`,
        {
          headers: accounts[0].headers,
          data: { status: "accepted" },
        },
      )
    ).ok(),
  ).toBeTruthy();
  const contexts = await Promise.all([
    browser.newContext(),
    browser.newContext(),
    browser.newContext(),
  ]);
  const [owner, member, staff] = await Promise.all(
    contexts.map((c) => c.newPage()),
  );
  async function login(page: Page, index: number) {
    await page.goto("/en/login");
    await page
      .getByLabel("Email address", { exact: true })
      .fill(accounts[index].email);
    await page.getByLabel("Password", { exact: true }).fill(password);
    await page.getByRole("button", { name: "Sign in", exact: true }).click();
    await expect(page).toHaveURL(index === 3 ? "/en/staff" : "/en/student");
  }
  async function confirm(page: Page, name: string) {
    await page.getByRole("button", { name, exact: true }).click();
    await page
      .getByRole("alertdialog")
      .getByRole("button", { name: "Confirm", exact: true })
      .click();
  }
  await login(owner, 1);
  await login(member, 2);
  await login(staff, 3);
  await owner.goto(`/en/student/tasks/${task}`);
  await owner.getByRole("link", { name: "Project teams", exact: true }).click();
  await owner
    .getByLabel("Team name", { exact: true })
    .fill("Consent browser team");
  await owner.getByRole("button", { name: "Create team", exact: true }).click();
  await expect(owner).toHaveURL(/\/student\/teams\/\d+$/);
  const team = owner.url().split("/").pop();
  let failed = false;
  await owner.route(/\/teams\/\d+\/actions$/, async (route) => {
    if (!failed) {
      failed = true;
      await route.fulfill({
        status: 503,
        contentType: "application/json",
        body: JSON.stringify({ code: "backend_unavailable" }),
      });
    } else await route.continue();
  });
  await owner
    .getByLabel("Exact student number", { exact: true })
    .fill(accounts[2].number);
  await owner
    .getByRole("button", { name: "Send invitation", exact: true })
    .click();
  await expect(
    owner.getByRole("alert").filter({ hasText: "backend is unavailable" }),
  ).toBeVisible();
  await expect(
    owner.getByLabel("Exact student number", { exact: true }),
  ).toHaveValue(accounts[2].number);
  await owner
    .getByRole("button", { name: "Send invitation", exact: true })
    .click();
  await expect(
    owner.getByLabel("Exact student number", { exact: true }),
  ).toHaveValue("");
  await member
    .getByRole("link", { name: "Team invitations", exact: true })
    .click();
  await member.getByRole("link", { name: /Consent browser team/ }).click();
  await confirm(member, "Accept invitation");
  await expect(
    member.getByRole("button", { name: "Leave team", exact: true }),
  ).toBeVisible();
  await owner.reload();
  await confirm(owner, "Request approval");
  await staff.goto(`/en/staff/tasks/${task}/teams`);
  await staff
    .getByLabel("Team status", { exact: true })
    .selectOption("awaiting_approval");
  await staff.getByRole("link", { name: /Consent browser team/ }).click();
  await confirm(staff, "Approve roster");
  await expect(
    staff.getByRole("button", { name: "Approve roster", exact: true }),
  ).toHaveCount(0);
  await owner.goto(`/en/student/tasks/${task}/submit`);
  await owner
    .getByLabel("Your work or explanation", { exact: true })
    .fill("My individual reasoning.");
  await owner.getByRole("button", { name: "Submit work", exact: true }).click();
  await expect(owner).toHaveURL(/\/submissions\/\d+$/);
  await expect(
    owner.getByRole("heading", {
      name: "Team roster at submission",
      exact: true,
    }),
  ).toBeVisible();
  await member.goto(`/ar/student/teams/${team}`);
  await expect(member.locator("html")).toHaveAttribute("dir", "rtl");
  await expect(
    member.getByText("أول تسليم للفريق ثبّت الأعضاء. لا يمكن تعديل العضوية.", {
      exact: true,
    }),
  ).toBeVisible();
  await member.setViewportSize({ width: 390, height: 844 });
  expect(
    await member.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBeTruthy();
  await member.screenshot({
    path: test.info().outputPath("team-ar-mobile.png"),
    fullPage: true,
  });
  await Promise.all(contexts.map((c) => c.close()));
});
