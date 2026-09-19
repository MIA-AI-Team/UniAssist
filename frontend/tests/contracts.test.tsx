import { describe, it, expect, vi, afterEach } from "vitest";
vi.mock("@/i18n/navigation", () => ({
  Link: () => null,
  usePathname: () => "/student",
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
}));
vi.mock("next/navigation", () => ({
  useSearchParams: () => new URLSearchParams(),
}));
import { render, screen, cleanup } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import en from "../messages/en.json";
import ar from "../messages/ar.json";
import { Button } from "../src/components/ui/button";
import { Status, Field } from "../src/components/common";
import { RubricSummary } from "../src/components/rubric-summary";
import { TutorMarkdown } from "../src/components/tutor-markdown";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { UsedGuidance } from "../src/features/guidance";
import { TeamPage } from "../src/features/teams";
import { SnapshotSummary } from "../src/features/repositories";
import type { Identity } from "../src/lib/api/types";
afterEach(cleanup);
function keys(value: object, prefix = ""): string[] {
  return Object.entries(value)
    .flatMap(([k, v]) =>
      typeof v === "object" ? keys(v, prefix + k + ".") : [prefix + k],
    )
    .sort();
}
describe("localized contracts", () => {
  it.each(["en", "ar"])(
    "renders pinned evidence and honest fixture provenance in %s",
    (locale) => {
      const messages = locale === "ar" ? ar : en;
      render(
        <NextIntlClientProvider locale={locale} messages={messages}>
          <SnapshotSummary
            snapshot={{
              id: 8,
              repository_id: 2,
              commit_sha: "a".repeat(40),
              created_at: "2026-09-19T00:00:00Z",
              provenance: {
                task_id: 1,
                team_id: 1,
                repository_id: 2,
                repo_url: "https://github.com/a/b",
                github_id: 1,
                commit_sha: "a".repeat(40),
                archive_sha256: "b".repeat(64),
                compressed_bytes: 100,
                captured_at: "2026-09-19T00:00:00Z",
                team_version: 3,
                repository_version: 2,
                is_fixture: true,
                omitted_files: 0,
                attribution: [],
                files: [
                  {
                    path: "main.py",
                    size: 10,
                    sha256: "c".repeat(64),
                    included: true,
                  },
                ],
              },
            }}
          />
        </NextIntlClientProvider>,
      );
      expect(screen.getByText(messages.repos.fixture)).toBeVisible();
      expect(screen.getByText("a".repeat(40))).toBeVisible();
      expect(
        screen.getByRole("link", { name: messages.repos.download }),
      ).toHaveAttribute("href", "/api/backend/repository-snapshots/8/download");
      expect(screen.queryByText(messages.aiGrade)).toBeNull();
    },
  );
  it.each(["en", "ar"])(
    "shows locked team privacy and no roster controls in %s",
    (locale) => {
      const messages = locale === "ar" ? ar : en;
      const queryClient = new QueryClient({
        defaultOptions: { queries: { retry: false, staleTime: Infinity } },
      });
      queryClient.setQueryData(["team", 1], {
        id: 1,
        task_id: 1,
        name: "Approved team",
        created_by: 4,
        status: "approved",
        version: 5,
        locked_at: "2026-09-18T12:00:00Z",
        unavailable_reason: "team_locked",
        actions: [],
        invitations: [],
        members: [
          {
            student_id: 4,
            name: "Student",
            student_number: "CS123",
            accepted_at: "2026-09-18T11:00:00Z",
          },
        ],
      });
      queryClient.setQueryData(["team-history", 1], {
        pages: [{ items: [], next_cursor: null }],
        pageParams: [null],
      });
      const user = {
        id: 4,
        role: "student",
        name: "Student",
        student_number: "CS123",
      } as Identity;
      render(
        <QueryClientProvider client={queryClient}>
          <NextIntlClientProvider locale={locale} messages={messages}>
            <TeamPage teamId={1} user={user} />
          </NextIntlClientProvider>
        </QueryClientProvider>,
      );
      expect(screen.getByText(messages.errors.team_locked)).toBeVisible();
      expect(screen.getByText(messages.teams.individual)).toBeVisible();
      expect(
        screen.queryByRole("button", { name: messages.teams.archive }),
      ).toBeNull();
      expect(
        screen.queryByRole("button", { name: messages.teams.sendInvitation }),
      ).toBeNull();
    },
  );
  it.each(["en", "ar"])(
    "shows the private-guidance release warning without inventing historical provenance in %s",
    (locale) => {
      const messages = locale === "ar" ? ar : en;
      const queryClient = new QueryClient({
        defaultOptions: { queries: { retry: false } },
      });
      render(
        <QueryClientProvider client={queryClient}>
          <NextIntlClientProvider locale={locale} messages={messages}>
            <UsedGuidance taskId={1} guidanceId={null} pending={false} />
          </NextIntlClientProvider>
        </QueryClientProvider>,
      );
      expect(screen.getByText(messages.guidance.warning)).toBeVisible();
      expect(screen.getByText(messages.guidance.unknown)).toBeVisible();
      expect(screen.queryByText(messages.guidance.next)).toBeNull();
    },
  );
  it("renders tutor math/code without executable HTML or tracking images", () => {
    const { container } = render(
      <TutorMarkdown
        content={
          "**Hint** $x^2$\n\n```js\nconst x = 2;\n```\n\n<script>alert(1)</script>\n\n![track](https://example.com/pixel)\n\n[bad](javascript:alert%281%29)"
        }
      />,
    );
    expect(screen.getByText("Hint")).toBeVisible();
    expect(container.querySelector(".katex")).not.toBeNull();
    expect(container.querySelector("pre")).toHaveAttribute("dir", "ltr");
    expect(
      container.querySelector("script, img, a[href^='javascript:']"),
    ).toBeNull();
  });
  it.each(["en", "ar"])(
    "shows approved expectations independently of assessment in %s",
    (locale) => {
      render(
        <NextIntlClientProvider
          locale={locale}
          messages={locale === "ar" ? ar : en}
        >
          <RubricSummary
            version={2}
            total={25}
            criteria={[
              {
                name: "Reasoning",
                description: "Explain your approach",
                max_points: 25,
              },
            ]}
          />
        </NextIntlClientProvider>,
      );
      expect(
        screen.getByRole("heading", {
          name: locale === "ar" ? ar.approvedRubric : en.approvedRubric,
        }),
      ).toBeVisible();
      expect(screen.getByText("Explain your approach")).toBeVisible();
      expect(screen.queryByText(en.aiGrade)).toBeNull();
    },
  );
  it("associates select labels without including option text", () => {
    render(
      <Field label="Role">
        <select>
          <option>Student</option>
          <option>Professor</option>
        </select>
      </Field>,
    );
    expect(screen.getByRole("combobox", { name: "Role" })).toBeVisible();
  });
  it("has complete translation key parity", () =>
    expect(keys(ar)).toEqual(keys(en)));
  it("keeps provisional state distinct from grade release", () => {
    render(
      <NextIntlClientProvider locale="en" messages={en}>
        <Status value="ai_graded" />
      </NextIntlClientProvider>,
    );
    expect(screen.getByText("Instructor review in progress")).toBeVisible();
    expect(screen.queryByText("Grade released")).toBeNull();
  });
  it("renders Arabic released status", () => {
    render(
      <NextIntlClientProvider locale="ar" messages={ar}>
        <Status value="staff_confirmed" />
      </NextIntlClientProvider>,
    );
    expect(screen.getByText("تم إصدار الدرجة")).toBeVisible();
  });
  it("preserves native disabled and button semantics", () => {
    render(<Button disabled>Save</Button>);
    expect(screen.getByRole("button", { name: "Save" })).toBeDisabled();
  });
});
