"use client";
import { useLocale, useTranslations } from "next-intl";
import { useQueryClient } from "@tanstack/react-query";
import { useState, useId, isValidElement, cloneElement } from "react";
import { usePathname, Link } from "@/i18n/navigation";
import { useSearchParams } from "next/navigation";
import { ApiError } from "@/lib/api/client";
import { Button } from "./ui/button";
export function LanguageSwitch() {
  const locale = useLocale(),
    pathname = usePathname(),
    search = useSearchParams(),
    t = useTranslations();
  return (
    <Link
      className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
      href={pathname + (search.size ? "?" + search.toString() : "")}
      locale={locale === "en" ? "ar" : "en"}
      lang={locale === "en" ? "ar" : "en"}
    >
      {t("language")}
    </Link>
  );
}
export function ErrorNotice({
  error,
  retry,
}: {
  error: unknown;
  retry?: () => void;
}) {
  const t = useTranslations(),
    client = useQueryClient();
  const [refreshed, setRefreshed] = useState(false);
  if (!error) return null;
  const api = error instanceof ApiError ? error : undefined;
  const key = "errors." + (api?.code || "request_failed");
  return (
    <div
      role="alert"
      className="rounded-xl border border-red-200 bg-red-50 p-4 text-red-900"
    >
      <p>{t.has(key) ? t(key) : t("error")}</p>
      {api?.ambiguous && (
        <>
          <p>{t("ambiguous")}</p>
          <Button
            type="button"
            variant="outline"
            onClick={async () => {
              await client.refetchQueries();
              setRefreshed(true);
            }}
          >
            {t("refresh")}
          </Button>
          {refreshed && <p>{t("refreshDone")}</p>}
        </>
      )}
      {retry && (
        <Button type="button" variant="outline" onClick={retry}>
          {t("retry")}
        </Button>
      )}
    </div>
  );
}
export function Loading() {
  const t = useTranslations();
  return (
    <p role="status" className="panel">
      {t("loading")}
    </p>
  );
}
export function Stamp({ value }: { value: string }) {
  const locale = useLocale();
  return (
    <time dateTime={value} suppressHydrationWarning>
      {new Intl.DateTimeFormat(locale, {
        dateStyle: "medium",
        timeStyle: "short",
      }).format(new Date(value))}
    </time>
  );
}
export function Status({
  value,
  staff = false,
}: {
  value: string;
  staff?: boolean;
}) {
  const t = useTranslations();
  const key = (staff ? "staff_" : "") + value;
  return (
    <span
      className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold ${value === "staff_confirmed" ? "bg-teal-100 text-teal-900" : value === "ai_graded" ? "bg-amber-100 text-amber-900" : "bg-slate-100 text-slate-700"}`}
    >
      {t.has(key) ? t(key) : value}
    </span>
  );
}
export function Field({
  label,
  error,
  children,
}: {
  label: string;
  error?: string;
  children: React.ReactNode;
}) {
  const id = useId();
  const control = isValidElement<{
    id?: string;
    "aria-describedby"?: string;
    "aria-invalid"?: boolean;
  }>(children)
    ? cloneElement(children, {
        id,
        "aria-describedby": error ? id + "-error" : undefined,
        "aria-invalid": !!error,
      })
    : children;
  return (
    <div className="grid gap-1.5">
      <label htmlFor={id}>{label}</label>
      {control}
      {error && (
        <span id={id + "-error"} className="text-red-700 text-xs" role="alert">
          {error}
        </span>
      )}
    </div>
  );
}
