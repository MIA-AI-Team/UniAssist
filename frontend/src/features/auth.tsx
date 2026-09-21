"use client";
import { useState } from "react";
import { useForm, useWatch } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { useTranslations } from "next-intl";
import { useQueryClient } from "@tanstack/react-query";
import { useSearchParams } from "next/navigation";
import { Link, useRouter } from "@/i18n/navigation";
import { request, ApiError } from "@/lib/api/client";
import type { Identity } from "@/lib/api/types";
import { Button } from "@/components/ui/button";
import { Field, ErrorNotice, LanguageSwitch } from "@/components/common";
export function Auth({ registering = false }: { registering?: boolean }) {
  const t = useTranslations(),
    router = useRouter(),
    client = useQueryClient(),
    search = useSearchParams();
  const [error, setError] = useState<unknown>();
  const [done, setDone] = useState(false);
  const schema = z
    .object({
      email: z.email(t("fieldInvalid")),
      password: z.string().min(registering ? 8 : 1, t("fieldInvalid")),
      name: z.string(),
      role: z.enum(["student", "teaching_assistant", "professor"]),
      student_number: z.string(),
      cohort_year: z.string(),
      major: z.string(),
      department: z.string(),
    })
    .superRefine((data, ctx) => {
      if (!registering) return;
      const fields =
        data.role === "student"
          ? (["name", "student_number", "cohort_year", "major"] as const)
          : (["name", "department"] as const);
      for (const field of fields)
        if (
          !data[field].trim() ||
          (field === "name" && data[field].trim().length < 2) ||
          (field === "cohort_year" &&
            (!Number.isInteger(Number(data[field])) || Number(data[field]) < 1))
        )
          ctx.addIssue({
            code: "custom",
            path: [field],
            message: t("fieldInvalid"),
          });
    });
  const form = useForm<z.infer<typeof schema>>({
    resolver: zodResolver(schema),
    defaultValues: {
      email: "",
      password: "",
      name: "",
      role: "student",
      student_number: "",
      cohort_year: "",
      major: "",
      department: "",
    },
  });
  const role = useWatch({ control: form.control, name: "role" });
  const submit = form.handleSubmit(async (values) => {
    setError(undefined);
    try {
      if (registering) {
        await request("/auth/register", {
          method: "POST",
          body: JSON.stringify({
            ...values,
            cohort_year: values.cohort_year ? Number(values.cohort_year) : null,
            staff_role: values.role,
          }),
        });
        setDone(true);
      } else {
        const user = await request<Identity>(
          "",
          {
            method: "POST",
            body: JSON.stringify({
              email: values.email,
              password: values.password,
            }),
          },
          true,
        );
        client.clear();
        router.replace(
          user.role === "student"
            ? "/student"
            : user.role === "admin"
              ? "/admin"
              : "/staff",
        );
      }
    } catch (e) {
      setError(e);
      if (e instanceof ApiError && Array.isArray(e.detail))
        for (const issue of e.detail) {
          const key = issue.loc?.at(-1) as keyof z.infer<typeof schema>;
          if (key in values) form.setError(key, { message: t("fieldInvalid") });
        }
    }
  });
  const field = (key: keyof z.infer<typeof schema>, type = "text") => (
    <Field label={t(key)} error={form.formState.errors[key]?.message}>
      <input
        type={type}
        dir={
          ["email", "password", "student_number"].includes(key)
            ? "ltr"
            : undefined
        }
        autoComplete={
          key === "password"
            ? registering
              ? "new-password"
              : "current-password"
            : key === "email"
              ? "email"
              : key === "name"
                ? "name"
                : "off"
        }
        aria-invalid={!!form.formState.errors[key]}
        {...form.register(key)}
      />
    </Field>
  );
  return (
    <main className="workspace-width min-h-screen py-4">
      <header className="flex items-center justify-between">
        <Link href="/" className="brand" dir="ltr">
          UniAssist<span className="text-action">.</span>
        </Link>
        <LanguageSwitch />
      </header>
      <div className="auth-layout">
        <section className="auth-intro">
          <h2>{t("tagline")}</h2>
          <ol className="auth-process">
            {["expectations", "attempt", "review", "release"].map(
              (step, index) => (
                <li key={step}>
                  <span aria-hidden="true">0{index + 1}</span>
                  {t(`desk.${step}`)}
                </li>
              ),
            )}
          </ol>
        </section>
        <section className="panel auth-form">
          <h1>{t(registering ? "register" : "welcome")}</h1>
          <p className="muted mb-6">
            {t(registering ? "registerHint" : "loginHint")}
          </p>
          {search.has("expired") && (
            <p role="status" className="mb-4 text-warning">
              {t("sessionExpired")}
            </p>
          )}
          {done ? (
            <div role="status" className="stack">
              <p>{t("accountCreated")}</p>
              <Button asChild>
                <Link href="/login">{t("login")}</Link>
              </Button>
            </div>
          ) : (
            <form onSubmit={submit} className="stack" noValidate>
              {registering && field("name")}
              {field("email", "email")}
              {field("password", "password")}
              {registering && (
                <>
                  <Field label={t("role")}>
                    <select {...form.register("role")}>
                      {["student", "teaching_assistant", "professor"].map(
                        (r) => (
                          <option key={r} value={r}>
                            {t(r)}
                          </option>
                        ),
                      )}
                    </select>
                  </Field>
                  {role === "student" ? (
                    <>
                      {field("student_number")}
                      {field("cohort_year", "number")}
                      {field("major")}
                    </>
                  ) : (
                    field("department")
                  )}
                </>
              )}
              <ErrorNotice error={error} />
              <Button disabled={form.formState.isSubmitting}>
                {t(
                  form.formState.isSubmitting
                    ? "working"
                    : registering
                      ? "register"
                      : "login",
                )}
              </Button>
              <p className="text-sm muted">
                {t(registering ? "hasAccount" : "noAccount")}{" "}
                <Link
                  className="font-semibold text-action underline"
                  href={registering ? "/login" : "/register"}
                >
                  {t(registering ? "login" : "register")}
                </Link>
              </p>
            </form>
          )}
        </section>
      </div>
    </main>
  );
}
