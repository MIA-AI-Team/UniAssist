import { describe, it, expect, vi, afterEach } from "vitest";
import { render, screen, cleanup } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Profile } from "../src/features/accounts";
import { FileMetadata } from "../src/components/file-metadata";
import type { Identity } from "../src/lib/api/types";
import en from "../messages/en.json";
import ar from "../messages/ar.json";
vi.mock("@/i18n/navigation", () => ({
  Link: () => null,
  usePathname: () => "/profile",
}));
vi.mock("next/navigation", () => ({
  useSearchParams: () => new URLSearchParams(),
}));
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});
describe("account and artifact boundaries", () => {
  it.each(["en", "ar"])(
    "only self-service fields are editable in %s",
    (locale) => {
      const user: Identity = {
        id: 1,
        role: "student",
        name: "Student Name",
        email: "student@example.com",
        student_number: "SAFE-ID",
        cohort_year: 2027,
        major: "CS",
        department: null,
        github_username: "student-code",
        profile_version: 1,
      };
      vi.stubGlobal(
        "fetch",
        vi.fn().mockResolvedValue({ ok: true, json: async () => user }),
      );
      const messages = locale === "ar" ? ar : en;
      const { container } = render(
        <NextIntlClientProvider locale={locale} messages={messages}>
          <QueryClientProvider
            client={
              new QueryClient({ defaultOptions: { queries: { retry: false } } })
            }
          >
            <Profile user={user} />
          </QueryClientProvider>
        </NextIntlClientProvider>,
      );
      expect(screen.getByLabelText(messages.name)).toHaveValue("Student Name");
      expect(screen.getByLabelText(messages.accounts.github)).toHaveValue(
        "student-code",
      );
      expect(
        screen.queryByLabelText(messages.cohort_year),
      ).not.toBeInTheDocument();
      expect(screen.queryByLabelText(messages.role)).not.toBeInTheDocument();
      expect(screen.getByText(/SAFE-ID/)).toBeInTheDocument();
      expect(container.querySelector(".summary-list")).not.toBeNull();
      expect(container.querySelector(".action-well")).not.toBeNull();
    },
  );
  it.each(["en", "ar"])(
    "shows authorized metadata without using storage paths in %s",
    async (locale) => {
      const messages = locale === "ar" ? ar : en;
      vi.stubGlobal(
        "fetch",
        vi.fn().mockResolvedValue({
          ok: true,
          json: async () => ({
            file_id: 3,
            file_name: "answer.txt",
            file_type: "txt",
            purpose: "submission",
            size_bytes: 12,
            uploaded_at: "2026-09-19T00:00:00Z",
            storage_path: "PRIVATE_PATH_SENTINEL",
          }),
        }),
      );
      render(
        <NextIntlClientProvider locale={locale} messages={messages}>
          <QueryClientProvider
            client={
              new QueryClient({ defaultOptions: { queries: { retry: false } } })
            }
          >
            <FileMetadata id={3} />
          </QueryClientProvider>
        </NextIntlClientProvider>,
      );
      expect(await screen.findByRole("link")).toHaveAttribute(
        "href",
        "/api/backend/files/3/download",
      );
      expect(
        screen.queryByText("PRIVATE_PATH_SENTINEL"),
      ).not.toBeInTheDocument();
      expect(screen.getByText(/answer.txt/)).toBeInTheDocument();
    },
  );
});
