"use client";
import { useState, useRef } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { useForm } from "react-hook-form";
import { Link } from "@/i18n/navigation";
import { request } from "@/lib/api/client";
import type { Identity } from "@/lib/api/types";
import type { components } from "@/lib/api/schema";
import { Button } from "@/components/ui/button";
import { Confirm } from "@/components/ui/confirm";
import { Field, ErrorNotice, Loading, Stamp } from "@/components/common";
type S = components["schemas"];

export function Profile({
  user,
  onSaved,
}: {
  user: Identity;
  onSaved?: () => Promise<unknown>;
}) {
  const t = useTranslations(),
    client = useQueryClient();
  const [done, setDone] = useState(false);
  const query = useQuery({
    queryKey: ["profile"],
    queryFn: () => request<Identity>("/auth/me"),
    initialData: user,
    refetchOnWindowFocus: false,
  });
  return (
    <section className="document-section stack max-w-3xl">
      <h1>{t("accounts.profile")}</h1>
      <p>{t("accounts.profileHelp")}</p>
      <ErrorNotice error={query.error} retry={() => query.refetch()} />
      {done && <p role="status">{t("accounts.saved")}</p>}
      <ProfileForm
        key={query.data.profile_version}
        user={query.data}
        saved={async () => {
          setDone(true);
          await query.refetch();
          await client.invalidateQueries({ queryKey: ["session"] });
          await onSaved?.();
        }}
      />
    </section>
  );
}

function ProfileForm({
  user,
  saved,
}: {
  user: Identity;
  saved: () => Promise<void>;
}) {
  const t = useTranslations();
  const form = useForm({
    defaultValues: {
      name: user.name,
      github_username: user.github_username || "",
    },
  });
  const save = useMutation({
    mutationFn: (values: { name: string; github_username: string }) =>
      request<Identity>("/auth/me", {
        method: "PATCH",
        body: JSON.stringify({
          name: values.name,
          ...(user.role === "student"
            ? { github_username: values.github_username || null }
            : {}),
          expected_version: user.profile_version,
        }),
      }),
    onSuccess: saved,
  });
  return (
    <form
      className="stack"
      onSubmit={form.handleSubmit((values) => save.mutate(values))}
    >
      <dl className="summary-list">
        <div className="summary-row">
          <dt className="summary-key">{t("email")}</dt>
          <dd className="summary-value">
            <bdi>{user.email}</bdi>
          </dd>
        </div>
        <div className="summary-row">
          <dt className="summary-key">{t("role")}</dt>
          <dd className="summary-value">{t(user.role)}</dd>
        </div>
        {user.role === "student" && (
          <>
            <div className="summary-row">
              <dt className="summary-key">{t("student_number")}</dt>
              <dd className="summary-value">
                <bdi>{user.student_number}</bdi>
              </dd>
            </div>
            <div className="summary-row">
              <dt className="summary-key">{t("cohort_year")}</dt>
              <dd className="summary-value">
                <bdi>{user.cohort_year}</bdi>
              </dd>
            </div>
            <div className="summary-row">
              <dt className="summary-key">{t("major")}</dt>
              <dd className="summary-value">
                <bdi>{user.major}</bdi>
              </dd>
            </div>
          </>
        )}
      </dl>
      <div className="action-well stack">
        <Field label={t("name")}>
          <input
            required
            minLength={2}
            maxLength={150}
            {...form.register("name")}
          />
        </Field>
        {user.role === "student" && (
          <Field label={t("accounts.github")}>
            <input
              dir="ltr"
              maxLength={39}
              pattern="[A-Za-z0-9]([A-Za-z0-9-]*[A-Za-z0-9])?"
              {...form.register("github_username")}
            />
          </Field>
        )}
        <ErrorNotice error={save.error} />
        <Button disabled={save.isPending}>{t("accounts.save")}</Button>
      </div>
    </form>
  );
}

export function AdminWorkspace({
  route,
  user,
}: {
  route: string[];
  user: Identity;
}) {
  const t = useTranslations();
  const section = route[1];
  return (
    <div className="stack min-w-0 [overflow-wrap:anywhere]">
      <h1>{t("accounts.adminTitle")}</h1>
      <p>{t("accounts.boundary")}</p>
      <nav className="section-nav" aria-label={t("accounts.adminTitle")}>
        <Link
          aria-current={!section || section === "users" ? "page" : undefined}
          href="/admin"
        >
          {t("accounts.users")}
        </Link>
        <Link
          aria-current={section === "audit" ? "page" : undefined}
          href="/admin/audit"
        >
          {t("accounts.audit")}
        </Link>
        <Link
          aria-current={section === "metrics" ? "page" : undefined}
          href="/admin/metrics"
        >
          {t("accounts.metrics")}
        </Link>
      </nav>
      {route.length === 1 ? (
        <Accounts />
      ) : section === "users" &&
        /^\d+$/.test(route[2]) &&
        route.length === 3 ? (
        <AccountDetail
          key={route[2]}
          id={Number(route[2])}
          currentId={user.id}
        />
      ) : section === "audit" && route.length === 2 ? (
        <Audit />
      ) : section === "metrics" && route.length === 2 ? (
        <Metrics />
      ) : (
        <h2>{t("notFound")}</h2>
      )}
    </div>
  );
}

function Accounts() {
  const t = useTranslations();
  const [input, setInput] = useState(""),
    [search, setSearch] = useState(""),
    [cursor, setCursor] = useState<number>();
  const query = useQuery({
    queryKey: ["accounts", search, cursor],
    queryFn: () =>
      request<S["AccountList"]>(
        `/admin/users?q=${encodeURIComponent(search)}${cursor ? `&before=${cursor}` : ""}`,
      ),
  });
  return (
    <section className="document-section stack">
      <h2>{t("accounts.users")}</h2>
      <form
        className="action-well flex flex-wrap items-end gap-3"
        onSubmit={(e) => {
          e.preventDefault();
          setCursor(undefined);
          setSearch(input);
        }}
      >
        <Field label={t("accounts.search")}>
          <input
            maxLength={150}
            value={input}
            onChange={(e) => setInput(e.target.value)}
          />
        </Field>
        <Button>{t("accounts.searchButton")}</Button>
      </form>
      {query.isPending ? (
        <Loading />
      ) : query.error ? (
        <ErrorNotice error={query.error} retry={() => query.refetch()} />
      ) : (
        <>
          {!query.data!.items.length && <p>{t("accounts.empty")}</p>}
          <ul className="record-list">
            {query.data!.items.map((u) => (
              <li key={u.id}>
                <Link
                  className="record-row record-row-link"
                  href={`/admin/users/${u.id}`}
                >
                  <span className="record-body">
                    <span className="record-title">
                      <bdi>{u.name}</bdi>
                    </span>
                    <span className="record-description">
                      <bdi>{u.email}</bdi> · {t(u.role)}
                    </span>
                  </span>
                  <span className="record-trailing">
                    {t(u.is_active ? "accounts.active" : "accounts.suspended")}
                  </span>
                </Link>
              </li>
            ))}
          </ul>
          <Paging
            cursor={cursor}
            next={query.data!.next_cursor}
            change={setCursor}
          />
        </>
      )}
    </section>
  );
}

function Paging({
  cursor,
  next,
  change,
}: {
  cursor?: number;
  next: number | null;
  change: (n?: number) => void;
}) {
  const t = useTranslations();
  return (
    <div className="flex gap-3">
      {cursor && (
        <Button variant="outline" onClick={() => change(undefined)}>
          {t("accounts.firstPage")}
        </Button>
      )}
      {next && (
        <Button variant="outline" onClick={() => change(next)}>
          {t("accounts.nextPage")}
        </Button>
      )}
    </div>
  );
}

function AccountDetail({ id, currentId }: { id: number; currentId: number }) {
  const t = useTranslations();
  const [done, setDone] = useState(false);
  const query = useQuery({
    queryKey: ["account", id],
    queryFn: () => request<S["AccountInfo"]>(`/admin/users/${id}`),
  });
  if (query.isPending) return <Loading />;
  if (query.error)
    return <ErrorNotice error={query.error} retry={() => query.refetch()} />;
  return (
    <section className="document-section stack max-w-3xl">
      <h2>{t("accounts.correct")}</h2>
      <p>{t("accounts.correctionHelp")}</p>
      {id === currentId && (
        <p className="text-warning">{t("accounts.selfWarning")}</p>
      )}
      {done && <p role="status">{t("accounts.saved")}</p>}
      <Button variant="outline" onClick={() => query.refetch()}>
        {t("refresh")}
      </Button>
      <dl className="summary-list">
        <div className="summary-row">
          <dt className="summary-key">{t("name")}</dt>
          <dd className="summary-value" dir="auto">
            {query.data!.name}
          </dd>
        </div>
        <div className="summary-row">
          <dt className="summary-key">{t("email")}</dt>
          <dd className="summary-value">
            <bdi>{query.data!.email}</bdi>
          </dd>
        </div>
        <div className="summary-row">
          <dt className="summary-key">{t("role")}</dt>
          <dd className="summary-value">{t(query.data!.role)}</dd>
        </div>
        <div className="summary-row">
          <dt className="summary-key">{t("accounts.status")}</dt>
          <dd className="summary-value">
            {t(
              query.data!.is_active ? "accounts.active" : "accounts.suspended",
            )}
          </dd>
        </div>
        <div className="summary-row">
          <dt className="summary-key">{t("accounts.created")}</dt>
          <dd className="summary-value">
            <Stamp value={query.data!.created_at} />
          </dd>
        </div>
      </dl>
      <AccountForm
        key={`${id}:${query.data!.profile_version}`}
        account={query.data!}
        saved={async () => {
          setDone(true);
          await query.refetch();
        }}
      />
    </section>
  );
}

function AccountForm({
  account,
  saved,
}: {
  account: S["AccountInfo"];
  saved: () => Promise<unknown>;
}) {
  const t = useTranslations();
  const formRef = useRef<HTMLFormElement>(null);
  const [values, setValues] = useState({
    name: account.name,
    email: account.email,
    role: account.role,
    is_active: account.is_active,
    student_number: account.student_number || "",
    cohort_year: String(account.cohort_year || ""),
    major: account.major || "",
    department: account.department || "",
    github_username: account.github_username || "",
  });
  const [invalid, setInvalid] = useState(false);
  const save = useMutation({
    mutationFn: () => {
      const body: S["AccountUpdate"] = {
        expected_version: account.profile_version,
        name: values.name,
        email: values.email,
        is_active: values.is_active,
      };
      if (account.role === "student")
        Object.assign(body, {
          student_number: values.student_number,
          cohort_year: Number(values.cohort_year),
          major: values.major,
          github_username: values.github_username || null,
        });
      if (["professor", "teaching_assistant"].includes(account.role))
        Object.assign(body, {
          department: values.department || null,
          role: values.role,
        });
      return request<S["AccountInfo"]>(`/admin/users/${account.id}`, {
        method: "PATCH",
        body: JSON.stringify(body),
      });
    },
    onSuccess: saved,
  });
  const fields = [
    "name",
    "email",
    ...(account.role === "student"
      ? ["student_number", "cohort_year", "major", "github_username"]
      : account.role !== "admin"
        ? ["department"]
        : []),
  ] as const;
  return (
    <form
      ref={formRef}
      className="action-well stack"
      onSubmit={(e) => e.preventDefault()}
      onInvalid={() => setInvalid(true)}
    >
      {fields.map((field) => (
        <Field
          key={field}
          label={field === "github_username" ? t("accounts.github") : t(field)}
        >
          <input
            type={
              field === "email"
                ? "email"
                : field === "cohort_year"
                  ? "number"
                  : "text"
            }
            required={!["department", "github_username"].includes(field)}
            min={field === "cohort_year" ? 1 : undefined}
            max={field === "cohort_year" ? 9999 : undefined}
            value={values[field as keyof typeof values] as string}
            onChange={(e) => {
              setInvalid(false);
              setValues({ ...values, [field]: e.target.value });
            }}
          />
        </Field>
      ))}
      {["professor", "teaching_assistant"].includes(account.role) && (
        <Field label={t("role")}>
          <select
            value={values.role}
            onChange={(e) => setValues({ ...values, role: e.target.value })}
          >
            <option value="teaching_assistant">
              {t("teaching_assistant")}
            </option>
            <option value="professor">{t("professor")}</option>
          </select>
        </Field>
      )}
      <Field label={t("accounts.status")}>
        <select
          value={values.is_active ? "active" : "suspended"}
          onChange={(e) =>
            setValues({ ...values, is_active: e.target.value === "active" })
          }
        >
          <option value="active">{t("accounts.active")}</option>
          <option value="suspended">{t("accounts.suspended")}</option>
        </select>
      </Field>
      {invalid && <p role="alert">{t("fieldInvalid")}</p>}
      <ErrorNotice error={save.error} />
      <Confirm
        title={t("accounts.save")}
        description={t("accounts.confirm")}
        disabled={save.isPending}
        onConfirm={() => {
          if (formRef.current?.reportValidity()) save.mutate();
        }}
      />
    </form>
  );
}

function Audit() {
  const t = useTranslations(),
    [cursor, setCursor] = useState<number>();
  const query = useQuery({
    queryKey: ["audit", cursor],
    queryFn: () =>
      request<S["AuditList"]>(
        `/admin/audit${cursor ? `?before=${cursor}` : ""}`,
      ),
  });
  return (
    <section className="document-section stack">
      <h2>{t("accounts.audit")}</h2>
      <p>{t("accounts.auditHelp")}</p>
      {query.isPending ? (
        <Loading />
      ) : query.error ? (
        <ErrorNotice error={query.error} retry={() => query.refetch()} />
      ) : (
        <>
          {!query.data!.items.length && <p>{t("accounts.empty")}</p>}
          <ol className="history-list">
            {query.data!.items.map((event) => (
              <li key={event.id} className="history-row stack gap-2">
                <h3 className="record-title">
                  <bdi>{event.action}</bdi>
                </h3>
                <p className="record-description">
                  <Stamp value={event.created_at} />
                </p>
                <p className="text-sm">
                  {t("accounts.actor")}:{" "}
                  <bdi>{event.actor_id ?? t("accounts.operator")}</bdi> ·{" "}
                  {t("accounts.target")}:{" "}
                  <bdi>
                    {event.target_type} #{event.target_id}
                  </bdi>
                </p>
                {!!event.fields.length && (
                  <p className="text-sm">
                    {t("accounts.changedFields")}:{" "}
                    <bdi>{event.fields.join(", ")}</bdi>
                  </p>
                )}
              </li>
            ))}
          </ol>
          <Paging
            cursor={cursor}
            next={query.data!.next_cursor}
            change={setCursor}
          />
        </>
      )}
    </section>
  );
}

function Metrics() {
  const t = useTranslations(),
    [days, setDays] = useState(30);
  const query = useQuery({
    queryKey: ["metrics", days],
    queryFn: () =>
      request<S["MetricsResponse"]>(`/admin/ai-metrics?days=${days}`),
  });
  const labels = [
    "calls",
    "errors",
    "incomplete",
    "average_latency_ms",
    "mock_calls",
    "unknown_mock_calls",
    "truncated_calls",
    "unknown_truncation_calls",
  ] as const;
  return (
    <section className="document-section stack">
      <h2>{t("accounts.metrics")}</h2>
      <p>{t("accounts.metricsHelp")}</p>
      <div className="action-well flex flex-wrap items-end gap-3">
        <Field label={t("accounts.window")}>
          <select
            value={days}
            onChange={(e) => setDays(Number(e.target.value))}
          >
            {[1, 7, 30, 365].map((n) => (
              <option key={n} value={n}>
                {t("accounts.days", { count: n })}
              </option>
            ))}
          </select>
        </Field>
        <Button variant="outline" onClick={() => query.refetch()}>
          {t("refresh")}
        </Button>
      </div>
      {query.isPending ? (
        <Loading />
      ) : query.error ? (
        <ErrorNotice error={query.error} retry={() => query.refetch()} />
      ) : (
        <>
          {!query.data!.groups.length && <p>{t("accounts.empty")}</p>}
          {!!query.data!.groups.length && (
            <div className="record-list">
              {query.data!.groups.map((group) => (
                <article
                  key={`${group.operation}:${group.provider}`}
                  className="record-row record-row-wide"
                >
                  <h3 className="record-title">
                    <bdi>
                      {group.operation} · {group.provider}
                    </bdi>
                  </h3>
                  <dl className="summary-list">
                    {labels.map((key) => (
                      <div className="summary-row" key={key}>
                        <dt className="summary-key">{t(`accounts.${key}`)}</dt>
                        <dd className="summary-value metric-value">
                          {key === "average_latency_ms"
                            ? group[key].toFixed(1)
                            : group[key]}
                        </dd>
                      </div>
                    ))}
                  </dl>
                </article>
              ))}
            </div>
          )}
        </>
      )}
    </section>
  );
}
