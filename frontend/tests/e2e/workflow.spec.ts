import { test, expect, type Page } from "@playwright/test";
const api = process.env.TEST_API_URL || "http://localhost:18001";
const password = "Verify-browser-123";

function referencePdf() {
  let pdf = "%PDF-1.4\n";
  const offsets = [0];
  const objects = [
    "<< /Type /Catalog /Pages 2 0 R >>",
    "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
    "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 100 100] /Resources << >> >>",
  ];
  objects.forEach((content, index) => {
    offsets.push(Buffer.byteLength(pdf));
    pdf += `${index + 1} 0 obj\n${content}\nendobj\n`;
  });
  const xref = Buffer.byteLength(pdf);
  pdf += "xref\n0 4\n0000000000 65535 f \n";
  pdf += offsets
    .slice(1)
    .map((offset) => String(offset).padStart(10, "0") + " 00000 n \n")
    .join("");
  pdf += `trailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n${xref}\n%%EOF\n`;
  return Buffer.from(pdf);
}

test("lab PDF flow and Arabic staff rubric controls", async ({ page }) => {
  await register(page, "professor", "lab" + Date.now());
  await page.goto("/en/staff/tasks/new");
  await page.getByLabel("Task type", { exact: true }).selectOption("lab");
  await page
    .getByLabel("Title", { exact: true })
    .fill("Lab reference workflow");
  await page
    .getByLabel("Instructions", { exact: true })
    .fill("Read the reference and explain the experiment.");
  await page
    .getByLabel("Due", { exact: true })
    .fill(new Date(Date.now() + 172800000).toISOString().slice(0, 16));
  await page
    .getByLabel("Scheduled date (informational)", { exact: true })
    .fill(new Date(Date.now() + 86400000).toISOString().slice(0, 16));
  await page.getByLabel("Cohort year", { exact: true }).fill("2027");
  await page.getByLabel("Reference PDF", { exact: true }).setInputFiles({
    name: "reference.pdf",
    mimeType: "application/pdf",
    buffer: referencePdf(),
  });
  await page.getByRole("button", { name: "Create task", exact: true }).click();
  await expect(page).toHaveURL(/\/staff\/tasks\/\d+$/);
  await page
    .getByLabel("Guidance mode", { exact: true })
    .selectOption("coding");
  await expect(
    page.getByText("Settings saved.", { exact: true }),
  ).toBeVisible();
  await page.reload();
  await expect(page.getByLabel("Guidance mode", { exact: true })).toHaveValue(
    "coding",
  );
  await expect(
    page.getByRole("link", { name: /reference\.pdf/ }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Suggest rubric with AI", exact: true })
    .click();
  await expect(page.getByRole("heading", { name: /Version 1/ })).toBeVisible();
  await page.locator("summary").filter({ hasText: "Refine with AI" }).click();
  await page
    .getByLabel("What should the next version improve?", { exact: true })
    .fill("Focus on clarity and explanation");
  await page
    .getByRole("button", { name: "Refine with AI", exact: true })
    .click();
  await expect(page.getByRole("heading", { name: /Version 2/ })).toBeVisible();
  await page.getByRole("link", { name: "العربية", exact: true }).click();
  await page
    .getByRole("button", { name: "اعتماد المعايير", exact: true })
    .first()
    .click();
  await expect(page.getByRole("alertdialog")).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(page.getByRole("alertdialog")).toHaveCount(0);
  await page
    .getByRole("button", { name: "اعتماد المعايير", exact: true })
    .first()
    .click();
  await page
    .getByRole("alertdialog")
    .getByRole("button", { name: "تأكيد", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: /معايير نشطة/ }),
  ).toBeVisible();
  await page.goto("/ar/staff/tasks/new");
  await page.getByLabel("نوع المهمة", { exact: true }).selectOption("project");
  await page.getByLabel("العنوان", { exact: true }).fill("مشروع فردي");
  await page
    .getByLabel("التعليمات", { exact: true })
    .fill("اشرح خوارزمية البحث.");
  await page
    .getByLabel("الموعد النهائي", { exact: true })
    .fill(new Date(Date.now() + 172800000).toISOString().slice(0, 16));
  await page.getByLabel("سنة الدفعة", { exact: true }).fill("2027");
  await page.getByRole("checkbox").uncheck();
  await page.getByRole("button", { name: "إنشاء مهمة", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "مشروع فردي", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByText("لا توجد تسليمات تطابق هذا العرض.", { exact: true }),
  ).toBeVisible();
});
async function register(
  page: Page,
  role: "student" | "professor" | "teaching_assistant",
  tag: string,
) {
  const email = role + "-" + tag + "@example.com";
  await page.goto("/en/register");
  await page.getByLabel("Full name", { exact: true }).fill(role + " " + tag);
  await page.getByLabel("Email address", { exact: true }).fill(email);
  await page.getByLabel("Password", { exact: true }).fill(password);
  await page.getByLabel("Role", { exact: true }).selectOption(role);
  if (role === "student") {
    await page.getByLabel("Student number", { exact: true }).fill(tag);
    await page.getByLabel("Cohort year", { exact: true }).fill("2027");
    await page.getByLabel("Major", { exact: true }).fill("CS");
  } else await page.getByLabel("Department", { exact: true }).fill("CS");
  await page
    .getByRole("button", { name: "Create account", exact: true })
    .click();
  await expect(
    page.getByText("Account created. Sign in to continue."),
  ).toBeVisible();
  await page.getByRole("link", { name: "Sign in", exact: true }).click();
  await page.getByLabel("Email address", { exact: true }).fill(email);
  await page.getByLabel("Password", { exact: true }).fill(password);
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(page).toHaveURL(
    new RegExp("/en/" + (role === "student" ? "student" : "staff") + "$"),
  );
  return email;
}
async function seedTask(
  request: import("@playwright/test").APIRequestContext,
  tag: string,
) {
  const email = "seed-" + tag + "@example.com";
  await request.post(api + "/auth/register", {
    data: {
      name: "Seed Professor",
      email,
      password,
      role: "professor",
      staff_role: "professor",
      department: "CS",
    },
  });
  const login = await request.post(api + "/auth/login", {
    data: { email, password },
  });
  const { access_token } = await login.json();
  const headers = { Authorization: "Bearer " + access_token };
  const task = await request.post(api + "/tasks/", {
    headers,
    data: {
      type: "assignment",
      title: "Upload recovery " + tag,
      description: "Submit a short explanation.",
      due_date: new Date(Date.now() + 86400000).toISOString(),
      target_cohort_year: 2027,
      allowed_file_types: ["txt"],
    },
  });
  expect(task.ok()).toBeTruthy();
  const { id } = await task.json();
  const rubric = await request.post(api + "/tasks/" + id + "/rubrics/create", {
    headers,
    data: {
      criteria: [
        { name: "Clarity", description: "Clear explanation", max_points: 20 },
      ],
    },
  });
  const { rubric_id } = await rubric.json();
  await request.patch(
    api + "/tasks/" + id + "/rubrics/status?rubric_id=" + rubric_id,
    { headers, data: { status: "accepted" } },
  );
  return id;
}
test("three roles complete a real assessment and switch to Arabic", async ({
  browser,
}) => {
  const tag = Date.now().toString();
  const contextOptions = {
    baseURL: process.env.E2E_URL || "http://localhost:13000",
  };
  const profContext = await browser.newContext(contextOptions),
    taContext = await browser.newContext(contextOptions),
    studentContext = await browser.newContext(contextOptions);
  const professor = await profContext.newPage(),
    ta = await taContext.newPage(),
    student = await studentContext.newPage();
  await register(professor, "professor", tag);
  await professor
    .getByRole("link", { name: "Create task", exact: true })
    .click();
  await professor
    .getByLabel("Title", { exact: true })
    .fill("Browser workflow " + tag);
  await professor
    .getByLabel("Instructions", { exact: true })
    .fill("Explain binary search. وضّح خطوات البحث الثنائي.");
  await professor
    .getByLabel("Due", { exact: true })
    .fill(new Date(Date.now() + 172800000).toISOString().slice(0, 16));
  await professor.getByLabel("Cohort year", { exact: true }).fill("2027");
  await professor
    .getByRole("button", { name: "Create task", exact: true })
    .click();
  await expect(professor).toHaveURL(/\/staff\/tasks\/\d+$/);
  const id = professor.url().split("/").at(-1)!;
  await professor.getByText("Create manual rubric", { exact: true }).click();
  await professor
    .getByLabel("Criterion name", { exact: true })
    .fill("Reasoning");
  await professor.getByLabel("Maximum points", { exact: true }).fill("25");
  await professor
    .getByLabel("Description", { exact: true })
    .fill("Explain the search interval and complexity.");
  await professor.getByRole("button", { name: "Save", exact: true }).click();
  await professor
    .getByRole("button", { name: "Accept rubric", exact: true })
    .click();
  await professor
    .getByRole("alertdialog")
    .getByRole("button", { name: "Confirm", exact: true })
    .click();
  await expect(
    professor.getByText("Active rubric", { exact: false }),
  ).toBeVisible();
  await register(student, "student", tag);
  await student.goto("/en/student/tasks/" + id);
  await expect(
    student.getByRole("heading", { name: "Approved grading criteria" }),
  ).toBeVisible();
  await expect(
    student.getByText("Explain the search interval and complexity.", {
      exact: true,
    }),
  ).toBeVisible();
  await student.goto("/en/student/tasks/" + id + "/submit");
  await expect(
    student.getByRole("heading", { name: "Approved grading criteria" }),
  ).toBeVisible();
  await student
    .getByLabel("Your work or explanation", { exact: true })
    .fill("Binary search halves the sorted search space: O(log n). شرح مختصر.");
  await student
    .getByRole("button", { name: "Submit work", exact: true })
    .click();
  await expect(student).toHaveURL(/\/student\/submissions\/\d+$/);
  const sid = student.url().split("/").at(-1)!;
  await student.reload();
  await expect(
    student.getByRole("heading", {
      name: "Rubric associated with this attempt",
    }),
  ).toBeVisible();
  await expect(
    student.getByText("Explain the search interval and complexity.", {
      exact: true,
    }),
  ).toBeVisible();
  await expect(
    student.getByText("Your work has been received.", { exact: false }),
  ).toBeVisible();
  await register(ta, "teaching_assistant", tag);
  await ta.goto("/en/staff/tasks/" + id);
  await ta.getByRole("link", { name: "student " + tag, exact: true }).click();
  await ta
    .getByRole("button", { name: "Run AI evaluation", exact: true })
    .click();
  await expect(
    ta.getByText("Demo assessment · Mock AI", { exact: true }),
  ).toBeVisible();
  await expect(
    ta.getByRole("button", { name: "Confirm and release grade" }),
  ).toHaveCount(0);
  await student.reload();
  await expect(
    student.getByText("Instructor review in progress", { exact: true }),
  ).toBeVisible();
  await expect(
    student.getByText("AI-suggested grade", { exact: true }),
  ).toHaveCount(0);
  await professor.goto("/en/staff/submissions/" + sid);
  await professor.getByLabel("Final grade", { exact: true }).fill("23");
  await professor
    .getByRole("button", { name: "Confirm and release grade", exact: true })
    .click();
  await professor
    .getByRole("alertdialog")
    .getByRole("button", { name: "Confirm", exact: true })
    .click();
  await expect(
    professor.getByText("Final grade confirmed", { exact: true }),
  ).toBeVisible();
  await student.reload();
  await expect(
    student.getByText("Grade released", { exact: true }),
  ).toBeVisible();
  await student.getByRole("link", { name: "العربية", exact: true }).click();
  await expect(student).toHaveURL("/ar/student/submissions/" + sid);
  await expect(student.locator("html")).toHaveAttribute("dir", "rtl");
  await expect(
    student.getByText("تم إصدار الدرجة", { exact: true }),
  ).toBeVisible();
  await student.setViewportSize({ width: 390, height: 844 });
  await student.screenshot({
    path: test.info().outputPath("released-ar-mobile.png"),
    fullPage: true,
  });
  expect(
    await student.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBeTruthy();
  await student.goto("/ar/staff");
  await expect(
    student.getByRole("heading", { name: "ليس لديك صلاحية لفتح هذه المساحة." }),
  ).toBeVisible();
  await student
    .getByRole("button", { name: "تسجيل الخروج", exact: true })
    .click();
  await expect(student).toHaveURL("/ar/login");
  await profContext.close();
  await taContext.close();
  await studentContext.close();
});
test("student tutoring persists, recovers a failed request, and speaks Arabic", async ({
  page,
  request,
}) => {
  const tag = "tutor" + Date.now();
  const id = await seedTask(request, tag);
  await register(page, "student", tag);
  await page.goto(`/en/student/tasks/${id}`);
  await page.getByRole("link", { name: "Ask AI tutor", exact: true }).click();
  await page
    .getByRole("button", { name: "New conversation", exact: true })
    .click();
  await expect(page).toHaveURL(/tutor\?chat=\d+$/);
  const savedUrl = page.url();
  let failedOnce = false;
  await page.route(/\/chat-sessions\/\d+\/messages$/, async (route) => {
    if (route.request().method() === "POST" && !failedOnce) {
      failedOnce = true;
      await route.fulfill({
        status: 503,
        contentType: "application/json",
        body: JSON.stringify({ code: "backend_unavailable" }),
      });
    } else await route.continue();
  });
  await page
    .getByLabel("Your question", { exact: true })
    .fill("Can you give me a conceptual hint?");
  await page
    .getByRole("button", { name: "Send question", exact: true })
    .click();
  await expect(
    page.getByRole("alert").filter({ hasText: "The backend is unavailable" }),
  ).toBeVisible();
  await expect(page.getByLabel("Your question", { exact: true })).toHaveValue(
    "Can you give me a conceptual hint?",
  );
  await page
    .getByRole("button", { name: "Send question", exact: true })
    .click();
  await expect(
    page.getByText("Demo tutor · Mock AI, not a real model response", {
      exact: true,
    }),
  ).toBeVisible();
  await page.reload();
  await expect(page.locator("article")).toHaveCount(1);
  await expect(
    page
      .locator("article")
      .getByText("Can you give me a conceptual hint?", { exact: true }),
  ).toBeVisible();
  await page.getByRole("link", { name: "العربية", exact: true }).click();
  await expect(page).toHaveURL(savedUrl.replace("/en/", "/ar/"));
  await page.getByRole("button", { name: "محادثة جديدة", exact: true }).click();
  await expect(page).not.toHaveURL(savedUrl.replace("/en/", "/ar/"));
  await page.getByLabel("سؤالك", { exact: true }).fill("كيف أفهم المهمة؟");
  await page.getByRole("button", { name: "إرسال السؤال", exact: true }).click();
  await expect(
    page.getByText("يمكنني مساعدتك بتلميحات دون تقديم الحل الكامل.", {
      exact: false,
    }),
  ).toBeVisible();
  await page.setViewportSize({ width: 390, height: 844 });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBeTruthy();
});

test("student previews, shares and revokes a private tutor snapshot", async ({
  browser,
  request,
}) => {
  const tag = "share" + Date.now();
  const task = await seedTask(request, tag);
  const staffContext = await browser.newContext();
  const studentContext = await browser.newContext();
  const staff = await staffContext.newPage(),
    student = await studentContext.newPage();
  const email = await register(staff, "professor", tag);
  await register(student, "student", tag);
  await student.goto(`/en/student/tasks/${task}/tutor`);
  await student
    .getByRole("button", { name: "New conversation", exact: true })
    .click();
  await expect(student).toHaveURL(/tutor\?chat=\d+$/);
  await student
    .getByLabel("Your question", { exact: true })
    .fill("A question I choose to share");
  await student
    .getByRole("button", { name: "Send question", exact: true })
    .click();
  await expect(student.locator("article")).toHaveCount(1);
  await expect(
    student.getByText("Demo tutor · Mock AI, not a real model response", {
      exact: true,
    }),
  ).toBeVisible();
  await student.getByText("Share with teaching staff", { exact: true }).click();
  await student.getByLabel("Staff email address", { exact: true }).fill(email);
  await student
    .getByLabel("Share through this question", { exact: true })
    .selectOption({ label: "A question I choose to share" });
  await expect(
    student.getByRole("heading", { name: "Snapshot preview", exact: true }),
  ).toBeVisible();
  await student
    .getByRole("button", { name: "Share snapshot", exact: true })
    .click();
  await expect(student.getByRole("alertdialog")).toContainText(email);
  await student
    .getByRole("alertdialog")
    .getByRole("button", { name: "Confirm", exact: true })
    .click();
  await expect(
    student.getByText("Snapshot shared with the selected recipient.", {
      exact: true,
    }),
  ).toBeVisible();
  await student
    .getByLabel("Your question", { exact: true })
    .fill("LATER_PRIVATE_MESSAGE");
  await student
    .getByRole("button", { name: "Send question", exact: true })
    .click();
  await expect(student.locator("article")).toHaveCount(2);
  await staff
    .getByRole("link", { name: "Shared tutoring conversations", exact: true })
    .click();
  await staff.locator('a[href*="/staff/shared-tutoring/"]').click();
  await expect(
    staff.getByText("A question I choose to share", { exact: true }),
  ).toBeVisible();
  await expect(
    staff.getByText("LATER_PRIVATE_MESSAGE", { exact: true }),
  ).toHaveCount(0);
  await expect(staff.getByLabel("Your question", { exact: true })).toHaveCount(
    0,
  );
  await student
    .getByRole("button", { name: "Revoke access", exact: true })
    .click();
  await student
    .getByRole("alertdialog")
    .getByRole("button", { name: "Confirm", exact: true })
    .click();
  await expect(
    student.getByText("Access revoked", { exact: true }),
  ).toBeVisible();
  await staff.reload();
  await expect(
    staff.getByRole("alert").filter({ hasText: "This item was not found." }),
  ).toBeVisible();
  await expect(
    staff.getByText("A question I choose to share", { exact: true }),
  ).toHaveCount(0);
  await staffContext.close();
  await studentContext.close();
});

test("private guidance and released teaching insights work in both languages", async ({
  page,
  request,
}) => {
  const tag = "insights" + Date.now();
  const task = await seedTask(request, tag);
  const email = await register(page, "professor", tag);
  const login = await request.post(api + "/auth/login", {
    data: { email, password },
  });
  const staff = {
    Authorization: "Bearer " + (await login.json()).access_token,
  };
  await page.goto(`/en/staff/tasks/${task}`);
  let guidanceFailed = false;
  await page.route(/\/grading-guidance$/, async (route) => {
    if (route.request().method() === "POST" && !guidanceFailed) {
      guidanceFailed = true;
      await route.fulfill({
        status: 503,
        contentType: "application/json",
        body: JSON.stringify({ code: "backend_unavailable" }),
      });
    } else await route.continue();
  });
  await page.getByText("Add a guidance version", { exact: true }).click();
  await page
    .getByLabel("Private marking notes", { exact: true })
    .fill("PRIVATE_UI_GUIDANCE");
  async function saveGuidance() {
    await page
      .getByRole("button", { name: "Save guidance version", exact: true })
      .click();
    await page
      .getByRole("alertdialog")
      .getByRole("button", { name: "Confirm", exact: true })
      .click();
  }
  await saveGuidance();
  await expect(
    page.getByRole("alert").filter({ hasText: "The backend is unavailable" }),
  ).toBeVisible();
  await expect(
    page.getByLabel("Private marking notes", { exact: true }),
  ).toHaveValue("PRIVATE_UI_GUIDANCE");
  await saveGuidance();
  await expect(
    page.getByText("Guidance version saved.", { exact: true }),
  ).toBeVisible();
  async function attempt(index: number) {
    const email = `${tag}-${index}@example.com`;
    const response = await request.post(api + "/auth/register", {
      data: {
        name: "Insight Student",
        email,
        password,
        role: "student",
        student_number: `${tag}-${index}`,
        cohort_year: 2027,
        major: "CS",
      },
    });
    expect(response.status()).toBe(201);
    const token = await request.post(api + "/auth/login", {
      data: { email, password },
    });
    const headers = {
      Authorization: "Bearer " + (await token.json()).access_token,
    };
    const submitted = await request.post(api + "/submissions/", {
      headers,
      data: {
        task_id: task,
        submission_text: "Explain a sorted search interval.",
      },
    });
    const { submission_id } = await submitted.json();
    expect(
      (
        await request.post(api + `/submissions/${submission_id}/grade`, {
          headers: staff,
        })
      ).ok(),
    ).toBeTruthy();
    return submission_id as number;
  }
  async function release(id: number) {
    expect(
      (
        await request.patch(api + `/submissions/${id}/confirm`, {
          headers: staff,
          data: { final_grade: 15 },
        })
      ).ok(),
    ).toBeTruthy();
  }
  for (let i = 0; i < 2; i++) await release(await attempt(i));
  const third = await attempt(2);
  await page
    .getByRole("link", { name: "Teaching insights", exact: true })
    .click();
  await expect(
    page.getByText(
      "At least 3 released results using this rubric are needed.",
      { exact: false },
    ),
  ).toBeVisible();
  await expect(
    page.getByRole("button", {
      name: "Generate teaching suggestions",
      exact: true,
    }),
  ).toHaveCount(0);
  await release(third);
  await page
    .getByRole("button", { name: "Refresh server state", exact: true })
    .click();
  await expect(
    page.getByRole("heading", {
      name: "Calculated released-grade statistics",
      exact: true,
    }),
  ).toBeVisible();
  let reportFailed = false;
  await page.route(/\/analytics\/reports$/, async (route) => {
    if (route.request().method() === "POST" && !reportFailed) {
      reportFailed = true;
      await route.fulfill({
        status: 503,
        contentType: "application/json",
        body: JSON.stringify({ code: "ai_unavailable" }),
      });
    } else await route.continue();
  });
  await page
    .getByRole("button", { name: "Generate teaching suggestions", exact: true })
    .click();
  await expect(
    page
      .getByRole("alert")
      .filter({ hasText: "AI evaluation is temporarily unavailable." }),
  ).toBeVisible();
  await expect(page.locator("article")).toHaveCount(0);
  await page
    .getByRole("button", { name: "Generate teaching suggestions", exact: true })
    .click();
  await expect(
    page.getByText(
      "Demo teaching report · Mock AI, not a real model analysis",
      { exact: true },
    ),
  ).toBeVisible();
  await page.reload();
  await expect(page.locator("article")).toHaveCount(1);
  await release(await attempt(3));
  await page
    .getByRole("button", { name: "Refresh server state", exact: true })
    .click();
  await expect(
    page.getByText("Outdated snapshot — released results have changed.", {
      exact: false,
    }),
  ).toBeVisible();
  await page.getByRole("link", { name: "العربية", exact: true }).click();
  await expect(page).toHaveURL(`/ar/staff/tasks/${task}/insights`);
  await page
    .getByRole("button", { name: "توليد اقتراحات تعليمية", exact: true })
    .click();
  await expect(
    page.getByText("تقرير تجريبي لنتائج 4 طلاب.", { exact: false }),
  ).toBeVisible();
  await page.setViewportSize({ width: 390, height: 844 });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBeTruthy();
  await page.goto(`/en/staff/submissions/${third}`);
  const used = page.locator("section").filter({
    has: page.getByRole("heading", {
      name: "Guidance used for this evaluation",
      exact: true,
    }),
  });
  await used.locator("summary").click();
  await expect(
    used.getByText("PRIVATE_UI_GUIDANCE", { exact: true }),
  ).toBeVisible();
});

test("a completed upload is retained when submission fails", async ({
  page,
  request,
}) => {
  const tag = "upload" + Date.now();
  const id = await seedTask(request, tag);
  await register(page, "student", tag);
  await page.goto("/en/student/tasks/" + id + "/submit");
  let uploads = 0,
    submissions = 0;
  page.on("request", (req) => {
    if (req.url().includes("/files/upload")) uploads++;
  });
  await page.route(/\/api\/backend\/submissions\/?$/, async (route) => {
    submissions++;
    if (submissions === 1)
      await route.fulfill({
        status: 422,
        contentType: "application/json",
        body: JSON.stringify({ code: "invalid_input" }),
      });
    else await route.continue();
  });
  await page
    .getByLabel("Your work or explanation", { exact: true })
    .fill("Retain this text.");
  await page.getByLabel("File", { exact: true }).setInputFiles({
    name: "answer.txt",
    mimeType: "text/plain",
    buffer: Buffer.from("An explanation with code: print(1)"),
  });
  await page.getByRole("button", { name: "Submit work", exact: true }).click();
  await expect(page.getByRole("alert")).toBeVisible();
  await expect(
    page.getByLabel("Your work or explanation", { exact: true }),
  ).toHaveValue("Retain this text.");
  await page
    .getByRole("button", { name: "Create new attempt", exact: true })
    .click();
  await expect(page).toHaveURL(/\/student\/submissions\/\d+$/);
  expect(uploads).toBe(1);
  await expect(
    page.getByRole("link", { name: "Download: answer.txt" }),
  ).toBeVisible();
  const download = page.waitForEvent("download");
  await page.getByRole("link", { name: "Download: answer.txt" }).click();
  expect((await download).suggestedFilename()).toBe("answer.txt");
});
test("Arabic registration, language filters, session expiry, and same-origin guard", async ({
  page,
  request,
}) => {
  await page.goto("/ar/register");
  await expect(page.locator("html")).toHaveAttribute("lang", "ar");
  await page.getByRole("button", { name: "إنشاء حساب", exact: true }).click();
  await expect(page.getByRole("alert").first()).toBeVisible();
  await page.getByRole("link", { name: "English", exact: true }).click();
  await expect(page).toHaveURL("/en/register");
  await register(page, "student", "expiry" + Date.now());
  await page.goto("/en/student?task_type=assignment&q=preserved");
  await page.getByRole("link", { name: "العربية", exact: true }).click();
  await expect(page).toHaveURL(
    /\/ar\/student\?task_type=assignment&q=preserved/,
  );
  await page.context().clearCookies();
  await page.reload();
  await expect(page).toHaveURL("/ar/login?expired=1");
  const rejected = await request.post("/api/session", {
    data: { email: "x@example.com", password },
  });
  expect(rejected.status()).toBe(403);
  await page.keyboard.press("Tab");
  expect(await page.evaluate(() => document.activeElement?.tagName)).not.toBe(
    "BODY",
  );
});
