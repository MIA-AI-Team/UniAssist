import { afterEach, beforeEach, expect, it, vi } from "vitest";
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { NextIntlClientProvider } from "next-intl";
import type { ReactNode } from "react";
import en from "../messages/en.json";
import ar from "../messages/ar.json";
import { AcademicMarkdown } from "../src/components/academic-markdown";
import { RubricSummary } from "../src/components/rubric-summary";
import { CreateTask } from "../src/features/create-task";
import { GradingGuidance, UsedGuidance } from "../src/features/guidance";
import { Review } from "../src/features/review";
import { Rubrics } from "../src/features/teaching";
import { ApiError, request } from "../src/lib/api/client";
import type { Identity } from "../src/lib/api/types";

vi.mock("@/i18n/navigation", () => ({
  Link: () => null,
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
  usePathname: () => "/staff",
}));
vi.mock("next/navigation", () => ({
  useSearchParams: () => new URLSearchParams(),
}));
vi.mock("@/lib/api/client", async (original) => ({
  ...(await original<typeof import("../src/lib/api/client")>()),
  request: vi.fn(),
}));

afterEach(cleanup);
beforeEach(() => vi.mocked(request).mockReset());

function setup(
  children: ReactNode,
  locale = "en",
  data: [unknown[], unknown][] = [],
) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false, staleTime: Infinity } },
  });
  for (const [key, value] of data) client.setQueryData(key, value);
  const rendered = render(
    <QueryClientProvider client={client}>
      <NextIntlClientProvider
        locale={locale}
        messages={locale === "ar" ? ar : en}
      >
        {children}
      </NextIntlClientProvider>
    </QueryClientProvider>,
  );
  return { ...rendered, client };
}

it.each(["en", "ar"])("renders accepted rubric math in %s", (locale) => {
  const { container } = setup(
    <RubricSummary
      version={1}
      total={10}
      criteria={[
        {
          name: String.raw`Explain \(x^2\)`,
          description: String.raw`Use \[\frac{1}{2}\]`,
          max_points: 10,
        },
      ]}
    />,
    locale,
  );
  expect(container.querySelectorAll(".katex")).toHaveLength(2);
  expect(container.querySelector("strong .katex-display")).toBeNull();
});

it.each(["en", "ar"])(
  "previews instructions and preserves original input after a failed save in %s",
  async (locale) => {
    const messages = locale === "ar" ? ar : en;
    const content = String.raw`Explain **why** \(x^2\), then \[\frac{1}{2}\].`;
    setup(<CreateTask />, locale);
    const input = screen.getByLabelText(messages.description, { exact: true });
    expect(screen.getByText(messages.markdown.empty)).toBeVisible();
    fireEvent.change(input, { target: { value: content } });
    const preview = screen.getByRole("region", {
      name: messages.markdown.preview.replace("{field}", messages.description),
    });
    expect(preview.querySelectorAll(".katex")).toHaveLength(2);
    expect(preview.closest("label")).toBeNull();
    expect(request).not.toHaveBeenCalled();
    fireEvent.change(screen.getByLabelText(messages.title, { exact: true }), {
      target: { value: "Math task" },
    });
    fireEvent.change(screen.getByLabelText(messages.due, { exact: true }), {
      target: { value: "2027-01-01T12:00" },
    });
    fireEvent.change(
      screen.getByLabelText(messages.cohort_year, { exact: true }),
      { target: { value: "2027" } },
    );
    vi.mocked(request).mockRejectedValueOnce(
      new ApiError("request_failed", 503),
    );
    fireEvent.submit(input.closest("form")!);
    await waitFor(() => expect(request).toHaveBeenCalledTimes(1));
    expect(
      JSON.parse(vi.mocked(request).mock.calls[0][1]!.body as string)
        .description,
    ).toBe(content);
    await screen.findByRole("alert");
    expect(input).toHaveValue(content);
    expect(preview.querySelectorAll(".katex")).toHaveLength(2);
  },
);

it("updates manual rubric and refinement previews without requests", () => {
  setup(<Rubrics taskId={1} professor />, "en", [
    [
      ["rubrics", 1],
      [
        {
          id: 1,
          version: 1,
          status: "pending",
          source: "manual",
          criteria: [
            { name: "Reasoning", description: "Explain", max_points: 10 },
          ],
        },
      ],
    ],
  ]);
  fireEvent.click(screen.getByRole("button", { name: en.manual }));
  fireEvent.change(screen.getByLabelText(en.criterionName), {
    target: { value: String.raw`\(x^2\)` },
  });
  fireEvent.change(screen.getByLabelText(en.criterionDescription), {
    target: { value: String.raw`\[y^2\]` },
  });
  fireEvent.change(screen.getByLabelText(en.refineFeedback), {
    target: { value: String.raw`Explain \(z^2\)` },
  });
  for (const label of [
    en.criterionName,
    en.criterionDescription,
    en.refineFeedback,
  ]) {
    const preview = screen.getByRole("region", {
      name: en.markdown.preview.replace("{field}", label),
    });
    expect(preview.querySelector(".katex")).not.toBeNull();
  }
  expect(request).not.toHaveBeenCalled();
});

it("renders private guidance history and used guidance, with a local editable preview", () => {
  const guidance = {
    id: 5,
    version: 2,
    content: String.raw`Private \(a^2\)`,
    created_at: "2026-09-21T00:00:00Z",
  };
  const { container } = setup(
    <>
      <GradingGuidance taskId={1} />
      <UsedGuidance taskId={1} guidanceId={5} pending={false} />
    </>,
    "en",
    [
      [
        ["guidance", 1],
        {
          pages: [{ items: [guidance], next_cursor: null }],
          pageParams: [null],
        },
      ],
      [["guidance-version", 1, 5], guidance],
    ],
  );
  fireEvent.change(screen.getByLabelText(en.guidance.content), {
    target: { value: String.raw`New \[b^2\]` },
  });
  expect(container.querySelectorAll(".katex")).toHaveLength(3);
  expect(request).not.toHaveBeenCalled();
});

it.each(
  [false, true].flatMap((released) =>
    ["en", "ar"].map((locale) => ({ released, locale })),
  ),
)(
  "preserves release gating and feedback order in $locale (released=$released)",
  ({ released, locale }) => {
    const messages = locale === "ar" ? ar : en;
    const user = { id: 3, name: "Student", role: "student" } as Identity;
    const { container } = setup(<Review id={1} user={user} />, locale, [
      [
        ["submission", 1],
        {
          id: 1,
          task_id: 1,
          attempt_number: 1,
          status: released ? "staff_confirmed" : "ai_graded",
          is_latest: true,
          submitted_at: "2026-09-21T00:00:00Z",
          rubric_version: 1,
          total_possible_grade: 10,
          rubric_criteria: [],
          artifacts: [],
          submission_text: String.raw`Exact artifact \(a^2\)`,
          feedback: String.raw`Feedback \(b^2\)`,
          criterion_evaluations: [
            {
              criterion_name: String.raw`\(c\)`,
              reasoning: String.raw`Reason \[d^2\]`,
              score_given: 5,
              max_points: 10,
            },
          ],
          code_reviews: [
            {
              file_path: "main.py",
              finding: String.raw`Finding \(e\)`,
              severity: "low",
            },
          ],
          ai_warnings: [String.raw`Warning \(f\)`],
          final_grade: released ? 5 : null,
        },
      ],
    ]);
    expect(container.querySelector("pre")).toHaveTextContent(
      String.raw`Exact artifact \(a^2\)`,
    );
    expect(container.querySelector("pre .katex")).toBeNull();
    expect(container.querySelectorAll(".katex")).toHaveLength(released ? 5 : 0);
    expect(screen.queryByText(messages.guidance.used)).toBeNull();
    if (!released) expect(screen.getByText(messages.awaiting)).toBeVisible();
    else {
      const feedback = container.querySelector(".academic-markdown")!;
      const grade = screen.getByText(messages.finalGrade);
      const artifact = screen.getByRole("heading", { name: messages.artifact });
      expect(
        feedback.compareDocumentPosition(grade) &
          Node.DOCUMENT_POSITION_FOLLOWING,
      ).toBeTruthy();
      expect(
        grade.compareDocumentPosition(artifact) &
          Node.DOCUMENT_POSITION_FOLLOWING,
      ).toBeTruthy();
      expect(
        screen.queryByRole("heading", { name: messages.desk.decision }),
      ).toBeNull();
    }
  },
);

it("uses the same saved-content renderer as the preview", () => {
  const content = String.raw`Same \[x^2\]`;
  setup(
    <>
      <CreateTask />
      <section aria-label="Saved">
        <AcademicMarkdown content={content} />
      </section>
    </>,
  );
  fireEvent.change(screen.getByLabelText(en.description), {
    target: { value: content },
  });
  const preview = screen.getByRole("region", {
    name: en.markdown.preview.replace("{field}", en.description),
  });
  expect(preview.querySelector(".academic-markdown")!.innerHTML).toBe(
    within(screen.getByRole("region", { name: "Saved" })).getByText("Same")
      .parentElement!.innerHTML,
  );
});
