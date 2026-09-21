"use client";
import { AcademicMarkdown } from "@/components/academic-markdown";
import { MarkdownPreview } from "@/components/markdown-preview";
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { useSearchParams } from "next/navigation";
import { Link, useRouter, usePathname } from "@/i18n/navigation";
import { request, ApiError } from "@/lib/api/client";
import type { Rubric, QueueItem, Criterion } from "@/lib/api/types";
import { Button } from "@/components/ui/button";
import { Confirm } from "@/components/ui/confirm";
import {
  Field,
  ErrorNotice,
  Loading,
  Status,
  Stamp,
} from "@/components/common";
export function Rubrics({
  taskId,
  professor,
}: {
  taskId: number;
  professor: boolean;
}) {
  const t = useTranslations(),
    client = useQueryClient();
  const [criteria, setCriteria] = useState<Criterion[]>([
    { name: "", description: "", max_points: 10, sort_order: 1 },
  ]);
  const [feedback, setFeedback] = useState<Record<number, string>>({});
  const [success, setSuccess] = useState(false),
    [showManual, setShowManual] = useState(false),
    [refreshBlocked, setRefreshBlocked] = useState(false);
  const query = useQuery({
    queryKey: ["rubrics", taskId],
    queryFn: () => request<Rubric[]>(`/tasks/${taskId}/rubrics`),
  });
  const mutation = useMutation({
    mutationFn: ({
      path,
      body,
      method = "POST",
    }: {
      path: string;
      body?: unknown;
      method?: string;
    }) =>
      request(`/tasks/${taskId}/rubrics/${path}`, {
        method,
        body: body ? JSON.stringify(body) : undefined,
      }),
    onSuccess: async () => {
      setSuccess(true);
      await client.invalidateQueries();
    },
    onMutate: () => setSuccess(false),
    onError: async (error) => {
      if (error instanceof ApiError && error.ambiguous) {
        const refreshed = await query.refetch();
        setRefreshBlocked(!!refreshed.error);
      }
    },
  });
  function update(index: number, patch: Partial<Criterion>) {
    setCriteria((values) =>
      values.map((c, i) => (i === index ? { ...c, ...patch } : c)),
    );
  }
  return (
    <section className="panel stack">
      <div className="flex flex-wrap justify-between gap-3">
        <h2>{t("rubricVersions")}</h2>
        <div className="flex flex-wrap gap-2">
          <Button variant="outline" onClick={() => setShowManual(!showManual)}>
            {t("manual")}
          </Button>
          <Button
            disabled={mutation.isPending || refreshBlocked}
            onClick={() => mutation.mutate({ path: "suggest" })}
          >
            {t("suggest")}
          </Button>
        </div>
      </div>
      {showManual && (
        <form
          className="stack rounded-xl bg-slate-50 p-4"
          onSubmit={(e) => {
            e.preventDefault();
            if (refreshBlocked) return;
            mutation.mutate({
              path: "create",
              body: {
                criteria: criteria.map((c, i) => ({ ...c, sort_order: i + 1 })),
              },
            });
          }}
        >
          {criteria.map((c, i) => (
            <fieldset
              key={i}
              className="grid gap-3 rounded-xl border border-slate-200 p-4 sm:grid-cols-[1fr_7rem_auto]"
            >
              <legend className="px-2 text-sm">
                {t("criterion")} {i + 1}
              </legend>
              <Field label={t("criterionName")}>
                <input
                  required
                  value={c.name}
                  onChange={(e) => update(i, { name: e.target.value })}
                />
              </Field>
              <Field label={t("maxPoints")}>
                <input
                  required
                  type="number"
                  min="0.01"
                  step="0.01"
                  value={c.max_points}
                  onChange={(e) =>
                    update(i, { max_points: Number(e.target.value) })
                  }
                />
              </Field>
              <Button
                type="button"
                variant="ghost"
                disabled={criteria.length === 1}
                onClick={() => setCriteria((v) => v.filter((_, n) => n !== i))}
              >
                {t("remove")}
              </Button>
              <div className="sm:col-span-3">
                <MarkdownPreview
                  content={c.name}
                  label={t("criterionName")}
                  inline
                  className="mb-3"
                />
                <Field label={t("criterionDescription")}>
                  <textarea
                    value={c.description || ""}
                    onChange={(e) => update(i, { description: e.target.value })}
                  />
                </Field>
                <MarkdownPreview
                  content={c.description || ""}
                  label={t("criterionDescription")}
                  className="mt-3"
                />
              </div>
            </fieldset>
          ))}
          <div className="flex flex-wrap gap-3 items-center">
            <Button
              type="button"
              variant="outline"
              onClick={() =>
                setCriteria((v) => [
                  ...v,
                  {
                    name: "",
                    description: "",
                    max_points: 10,
                    sort_order: v.length + 1,
                  },
                ])
              }
            >
              {t("addCriterion")}
            </Button>
            <span>
              {t("total")}: {criteria.reduce((sum, c) => sum + c.max_points, 0)}
            </span>
            <Button disabled={mutation.isPending || refreshBlocked}>
              {t("save")}
            </Button>
          </div>
        </form>
      )}
      <ErrorNotice error={mutation.error} />
      {mutation.isPending && <p role="status">{t("evaluating")}</p>}
      {success && !mutation.isPending && (
        <p role="status" className="text-teal-800">
          {t("success")}
        </p>
      )}
      {query.isPending ? (
        <Loading />
      ) : query.error ? (
        <ErrorNotice
          error={query.error}
          retry={async () => {
            const result = await query.refetch();
            setRefreshBlocked(!!result.error);
          }}
        />
      ) : !query.data?.length ? (
        <p className="muted">{t("noRubrics")}</p>
      ) : (
        query.data.map((r) => (
          <article
            key={r.id}
            className="rounded-xl border border-slate-200 p-4 stack"
          >
            <div className="flex flex-wrap justify-between gap-2">
              <h3>
                {t("version")} {r.version} · {t("rubric_" + r.status)}
              </h3>
              <span className="text-sm muted">
                {t("source_" + r.source)} · {t("total")}:{" "}
                {r.criteria.reduce((s, c) => s + c.max_points, 0)}
              </span>
            </div>
            <ul className="space-y-3">
              {r.criteria.map((c, i) => (
                <li key={i}>
                  <div className="flex justify-between gap-4">
                    <strong dir="auto">
                      <AcademicMarkdown content={c.name} inline />
                    </strong>
                    <span>
                      {c.max_points} {t("points")}
                    </span>
                  </div>
                  <AcademicMarkdown
                    className="text-sm muted"
                    content={c.description || ""}
                  />
                </li>
              ))}
            </ul>
            <form
              className="grid gap-3 sm:grid-cols-[1fr_auto]"
              onSubmit={(e) => {
                e.preventDefault();
                mutation.mutate({
                  path: "refine?rubric_id=" + r.id,
                  body: { staff_feedback: feedback[r.id] },
                });
              }}
            >
              <Field label={t("refineFeedback")}>
                <input
                  required
                  value={feedback[r.id] || ""}
                  onChange={(e) =>
                    setFeedback({ ...feedback, [r.id]: e.target.value })
                  }
                />
              </Field>
              <Button
                className="self-end"
                variant="outline"
                disabled={mutation.isPending || refreshBlocked}
              >
                {t("refine")}
              </Button>
              <MarkdownPreview
                content={feedback[r.id] || ""}
                label={t("refineFeedback")}
                className="sm:col-span-2"
              />
            </form>
            {professor && r.status === "pending" && (
              <div className="flex flex-wrap gap-3">
                <Confirm
                  title={t("approve")}
                  description={t("approveWarning")}
                  disabled={mutation.isPending || refreshBlocked}
                  onConfirm={() =>
                    mutation.mutate({
                      path: "status?rubric_id=" + r.id,
                      method: "PATCH",
                      body: { status: "accepted" },
                    })
                  }
                />
                <Button
                  variant="outline"
                  disabled={mutation.isPending || refreshBlocked}
                  onClick={() =>
                    mutation.mutate({
                      path: "status?rubric_id=" + r.id,
                      method: "PATCH",
                      body: { status: "rejected" },
                    })
                  }
                >
                  {t("reject")}
                </Button>
              </div>
            )}
          </article>
        ))
      )}
    </section>
  );
}
export function Queue({ taskId }: { taskId: number }) {
  const t = useTranslations(),
    search = useSearchParams(),
    router = useRouter(),
    pathname = usePathname();
  const latest = search.get("latest_only") !== "false",
    status = search.get("status") || "";
  function filter(key: string, value: string) {
    const p = new URLSearchParams(search);
    p.set(key, value);
    router.replace(pathname + "?" + p.toString());
  }
  const query = useQuery({
    queryKey: ["queue", taskId, latest, status],
    queryFn: () =>
      request<QueueItem[]>(
        `/tasks/${taskId}/submissions?latest_only=${latest}${status ? "&status=" + status : ""}`,
      ),
  });
  return (
    <section className="panel stack">
      <h2>{t("queue")}</h2>
      <div className="flex flex-wrap items-end gap-6">
        <label className="!flex items-center gap-3">
          <input
            type="checkbox"
            checked={latest}
            onChange={(e) => filter("latest_only", String(e.target.checked))}
          />
          {t("latestOnly")}
        </label>
        <Field label={t("status")}>
          <select
            value={status}
            onChange={(e) => filter("status", e.target.value)}
          >
            <option value="">{t("all")}</option>
            {["pending", "ai_graded", "staff_confirmed"].map((s) => (
              <option key={s} value={s}>
                {t("staff_" + s)}
              </option>
            ))}
          </select>
        </Field>
      </div>
      {query.isPending ? (
        <Loading />
      ) : query.error ? (
        <ErrorNotice error={query.error} retry={() => query.refetch()} />
      ) : !query.data?.length ? (
        <p className="muted">{t("noSubmissions")}</p>
      ) : (
        <div className="overflow-x-auto">
          <table>
            <thead>
              <tr>
                <th>{t("studentName")}</th>
                <th>{t("attempt")}</th>
                <th>{t("status")}</th>
                <th>{t("submittedAt")}</th>
              </tr>
            </thead>
            <tbody>
              {query.data.map((s) => (
                <tr key={s.id}>
                  <td>
                    <Link
                      className="font-semibold text-teal-800 underline"
                      href={"/staff/submissions/" + s.id}
                    >
                      <bdi>{s.student_name}</bdi>
                    </Link>
                    <p className="text-xs muted">
                      <bdi>{s.student_number}</bdi>
                    </p>
                  </td>
                  <td>
                    {s.attempt_number}
                    {s.is_latest ? " · " + t("latest") : ""}
                  </td>
                  <td>
                    <Status value={s.status} staff />
                  </td>
                  <td className="text-sm">
                    <Stamp value={s.submitted_at} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
