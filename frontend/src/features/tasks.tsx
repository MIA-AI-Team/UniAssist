"use client";
import { AcademicMarkdown } from "@/components/academic-markdown";
import { FileMetadata } from "@/components/file-metadata";
import { RubricSummary } from "@/components/rubric-summary";
import { LabTutorSettings } from "./tutor-sharing";
import { GradingGuidance } from "./guidance";
import { SnapshotSummary } from "./repositories";
import type { components } from "@/lib/api/schema";
import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { useSearchParams } from "next/navigation";
import { Link, useRouter, usePathname } from "@/i18n/navigation";
import { request, upload, ApiError } from "@/lib/api/client";
import type { Task, TaskDetail, Identity, Attempt } from "@/lib/api/types";
import { Button } from "@/components/ui/button";
import { Confirm } from "@/components/ui/confirm";
import {
  ErrorNotice,
  Loading,
  Stamp,
  Status,
  Field,
} from "@/components/common";
import { Rubrics, Queue } from "./teaching";
export function TaskList({ staff = false }: { staff?: boolean }) {
  const t = useTranslations(),
    search = useSearchParams(),
    router = useRouter(),
    pathname = usePathname();
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    const timer = setInterval(() => setNow(Date.now()), 60000);
    return () => clearInterval(timer);
  }, []);
  const type = search.get("task_type") || "",
    term = search.get("q") || "";
  const query = useQuery({
    queryKey: ["tasks", type],
    queryFn: () =>
      request<Task[]>("/tasks/" + (type ? "?task_type=" + type : "")),
  });
  function filter(key: string, value: string) {
    const params = new URLSearchParams(search);
    if (value) params.set(key, value);
    else params.delete(key);
    router.replace(pathname + "?" + params.toString());
  }
  const rank = (task: Task) =>
    task.latest_submission?.status === "staff_confirmed"
      ? 3
      : task.latest_submission
        ? 2
        : new Date(task.due_date).getTime() > now
          ? 0
          : 4;
  const tasks = [...(query.data || [])]
    .filter((task) => task.title.toLowerCase().includes(term.toLowerCase()))
    .sort((a, b) => (staff ? 0 : rank(a) - rank(b)));
  return (
    <div className="stack">
      <div className="page-heading">
        <div>
          <h1>{t(staff ? "staffTasks" : "tasks")}</h1>
          <p className="muted mt-2">
            {t(staff ? "staffIntro" : "studentIntro")}
          </p>
        </div>
        {staff && (
          <Button asChild>
            <Link href="/staff/tasks/new">{t("createTask")}</Link>
          </Button>
        )}
      </div>
      <div className="filter-toolbar">
        <Field label={t("search")}>
          <input value={term} onChange={(e) => filter("q", e.target.value)} />
        </Field>
        <Field label={t("type")}>
          <select
            value={type}
            onChange={(e) => filter("task_type", e.target.value)}
          >
            <option value="">{t("all")}</option>
            {["lab", "assignment", "project"].map((v) => (
              <option key={v} value={v}>
                {t(v)}
              </option>
            ))}
          </select>
        </Field>
      </div>
      {query.isPending ? (
        <Loading />
      ) : query.error ? (
        <ErrorNotice error={query.error} retry={() => query.refetch()} />
      ) : tasks.length === 0 ? (
        <p className="notice">{t("noTasks")}</p>
      ) : (
        <div className="task-list">
          {tasks.map((task) => {
            const hours = (new Date(task.due_date).getTime() - now) / 3600000;
            return (
              <article key={task.id} className="task-row">
                <div className="min-w-0">
                  <p className="task-kind">{t(task.type)}</p>
                  <h2 dir="auto">
                    <Link
                      href={`/${staff ? "staff" : "student"}/tasks/${task.id}`}
                    >
                      {task.title}
                    </Link>
                  </h2>
                </div>
                <div className="task-deadline">
                  <p className="muted text-xs">{t("due")}</p>
                  <p>
                    <Stamp value={task.due_date} />
                  </p>
                  {hours >= 0 && hours <= 48 && (
                    <p className="font-semibold text-warning">{t("dueSoon")}</p>
                  )}
                  {hours < 0 && <p className="text-muted">{t("pastDue")}</p>}
                </div>
                {staff ? (
                  <dl className="task-counts">
                    {Object.entries(task.review_counts || {}).map(([s, n]) => (
                      <div key={s}>
                        <dt>{t("staff_" + s)}</dt>
                        <dd>{n}</dd>
                      </div>
                    ))}
                  </dl>
                ) : (
                  <div className="task-state">
                    {task.latest_submission ? (
                      <Status value={task.latest_submission.status} />
                    ) : (
                      <span className="muted text-sm">
                        {t("desk.noAttempt")}
                      </span>
                    )}
                  </div>
                )}
                <Button asChild variant="outline">
                  <Link
                    href={`/${staff ? "staff" : "student"}/tasks/${task.id}`}
                  >
                    {t("openTask")}
                  </Link>
                </Button>
              </article>
            );
          })}
        </div>
      )}
    </div>
  );
}
export function TaskPage({
  id,
  user,
  submitting = false,
}: {
  id: number;
  user: Identity;
  submitting?: boolean;
}) {
  const t = useTranslations(),
    router = useRouter(),
    client = useQueryClient(),
    staff = user.role !== "student";
  const task = useQuery({
    queryKey: ["task", id],
    queryFn: () => request<TaskDetail>("/tasks/" + id),
  });
  const attempts = useQuery({
    queryKey: ["attempts", id],
    queryFn: () => request<Attempt[]>("/submissions/my/" + id),
    enabled: !staff,
  });
  const deletion = useMutation({
    mutationFn: () => request("/tasks/" + id, { method: "DELETE" }),
    onSuccess: () => {
      client.invalidateQueries({ queryKey: ["tasks"] });
      router.replace("/staff");
    },
  });
  if (task.isPending) return <Loading />;
  if (task.error)
    return <ErrorNotice error={task.error} retry={() => task.refetch()} />;
  const data = task.data!,
    access = data.submission_eligibility;
  return (
    <div className="stack">
      <Link
        className="text-sm text-action underline"
        href={staff ? "/staff" : "/student"}
      >
        {t("back")}
      </Link>
      <header className="panel">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-sm font-semibold text-action mb-2">
              {t(data.type)}
            </p>
            <h1 dir="auto">{data.title}</h1>
          </div>
          <div className="text-sm">
            <p className="muted">{t("due")}</p>
            <p className="font-semibold">
              <Stamp value={data.due_date} />
            </p>
          </div>
        </div>
        {!staff && (
          <div className="task-actions">
            {!access.allowed ? (
              <p role="status" className="notice notice-warning">
                {t.has("errors." + access.reason_code)
                  ? t("errors." + access.reason_code)
                  : t("unavailable")}
              </p>
            ) : (
              !submitting && (
                <Button asChild>
                  <Link href={`/student/tasks/${id}/submit`}>
                    {t(attempts.data?.length ? "newAttempt" : "submit")}
                  </Link>
                </Button>
              )
            )}
            <Link
              className="button button-ghost underline"
              href={`/student/tasks/${id}/tutor`}
            >
              {t("tutor.title")}
            </Link>
          </div>
        )}
        {staff && (
          <nav
            aria-label={t("insights.taskTools")}
            className="section-nav mt-4"
          >
            <a href="#task-review">{t("queue")}</a>
            <a href="#task-rubrics">{t("rubricVersions")}</a>
            <a href="#task-guidance">{t("guidance.title")}</a>
            <Link href={`/staff/tasks/${id}/insights`}>
              {t("insights.title")}
            </Link>
          </nav>
        )}
        <div className="task-context mt-6">
          <section className="min-w-0">
            <h2 className="mb-3">{t("description")}</h2>
            <AcademicMarkdown content={data.description} />
          </section>
          <aside aria-label={t("desk.context")}>
            {data.project_details?.require_team && (
              <Link
                className="mt-4 inline-block underline text-action"
                href={`/${staff ? "staff" : "student"}/tasks/${id}/teams`}
              >
                {t("teams.title")}
              </Link>
            )}
            <div className="mt-5 flex flex-wrap items-center gap-4 text-sm">
              {data.reference_file_id && (
                <FileMetadata id={data.reference_file_id} />
              )}
              <span className="muted">
                {data.target_cohort_year} ·{" "}
                <bdi>{data.target_major || t("allMajors")}</bdi>
              </span>
            </div>
            {data.lab_details?.scheduled_date && (
              <p className="text-sm muted mt-3">
                {t("scheduled")}:{" "}
                <Stamp value={data.lab_details.scheduled_date} />
              </p>
            )}
            {data.assignment_details && (
              <p className="text-sm muted mt-3">
                {t("allowedTypes")}:{" "}
                <bdi>
                  {data.assignment_details.allowed_file_types?.join(", ")}
                </bdi>
                {data.assignment_details.allow_late && " · " + t("allowLate")}
              </p>
            )}
            <p className="text-sm font-semibold mt-4">
              {t(access.rubric_ready ? "rubricReady" : "rubricWaiting")}
              {access.rubric_total != null &&
                ` · ${access.rubric_total} ${t("points")}`}
            </p>
          </aside>
        </div>
      </header>
      {!staff && (
        <>
          {data.accepted_rubric && <RubricSummary {...data.accepted_rubric} />}
          {access.allowed && submitting && <SubmitForm task={data} />}
          <section className="panel stack">
            <h2>{t("history")}</h2>
            {attempts.isPending ? (
              <Loading />
            ) : attempts.error ? (
              <ErrorNotice
                error={attempts.error}
                retry={() => attempts.refetch()}
              />
            ) : !attempts.data?.length ? (
              <p className="muted">{t("empty")}</p>
            ) : (
              <ul className="divide-y divide-divider">
                {[...attempts.data].reverse().map((a) => (
                  <li
                    key={a.id}
                    className="flex flex-wrap items-center justify-between gap-3 py-4"
                  >
                    <div>
                      <Link
                        className="font-semibold text-action underline"
                        href={`/student/submissions/${a.id}`}
                      >
                        {t("attempt")} {a.attempt_number}{" "}
                        {a.is_latest ? "· " + t("latest") : ""}
                      </Link>
                      <p className="text-xs muted mt-1">
                        <Stamp value={a.submitted_at} />
                      </p>
                    </div>
                    <Status value={a.status} />
                  </li>
                ))}
              </ul>
            )}
          </section>
        </>
      )}
      {staff && (
        <>
          <div id="task-review">
            <Queue taskId={id} />
          </div>
          <div id="task-rubrics">
            <Rubrics taskId={id} professor={user.role === "professor"} />
          </div>
          <div id="task-guidance">
            <GradingGuidance key={id} taskId={id} />
          </div>
          {data.type === "lab" && <LabTutorSettings taskId={id} />}
          {user.role === "professor" && (
            <section className="panel">
              <ErrorNotice error={deletion.error} />
              <Confirm
                title={t("deleteTask")}
                description={t("deleteWarning")}
                disabled={deletion.isPending}
                destructive
                onConfirm={() => deletion.mutate()}
              />
            </section>
          )}
        </>
      )}
    </div>
  );
}
function SubmitForm({ task }: { task: TaskDetail }) {
  const search = useSearchParams();
  const [snapshotId, setSnapshotId] = useState<number | undefined>(() => {
    const value = search.get("snapshot") || "";
    return /^[1-9]\d*$/.test(value) ? Number(value) : undefined;
  });
  const snapshot = useQuery({
    queryKey: ["repository-snapshot", snapshotId],
    enabled: !!snapshotId,
    queryFn: () =>
      request<components["schemas"]["SnapshotInfo"]>(
        `/repository-snapshots/${snapshotId}`,
      ),
  });
  const snapshotReady =
    !snapshotId ||
    (!!snapshot.data && snapshot.data.provenance.task_id === task.id);
  const t = useTranslations(),
    router = useRouter(),
    client = useQueryClient();
  const [text, setText] = useState(""),
    [file, setFile] = useState<File>(),
    [fileId, setFileId] = useState<number>(),
    [stage, setStage] = useState(""),
    [error, setError] = useState<unknown>(),
    [busy, setBusy] = useState(false),
    [uncertain, setUncertain] = useState(false);
  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(undefined);
    setBusy(true);
    try {
      if (!text.trim() && !fileId && !file && !snapshotId)
        throw new ApiError("empty_submission", 422);
      if (!snapshotReady) throw new ApiError("repository_changed", 409);
      if (file && file.size > 25 * 1024 * 1024)
        throw new ApiError("file_too_large", 413);
      let artifact = fileId;
      if (file && !artifact) {
        setStage("uploading");
        artifact = (await upload(file, "submission", task.id)).file_id;
        setFileId(artifact);
        setStage("uploaded");
      }
      setStage("submitting");
      const result = await request<{ submission_id: number }>("/submissions/", {
        method: "POST",
        body: JSON.stringify({
          task_id: task.id,
          submission_text: text,
          file_id: artifact ?? null,
          team_id: task.submission_eligibility.team_id ?? null,
          repository_snapshot_id: snapshotId ?? null,
        }),
      });
      await client.invalidateQueries();
      router.push("/student/submissions/" + result.submission_id);
    } catch (e) {
      setError(e);
      setUncertain(e instanceof ApiError && e.ambiguous);
      setStage(fileId ? "uploaded" : "");
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="panel stack">
      <h2>{t("submit")}</h2>
      <p className="muted">{t("resubmitHelp")}</p>
      {task.project_details?.require_team && (
        <p className="rounded-lg bg-selection p-3">
          {t("teams.submissionHelp", {
            id: task.submission_eligibility.team_id ?? "—",
          })}
        </p>
      )}
      <form onSubmit={submit} className="stack">
        {snapshotId && (
          <div className="stack">
            {snapshot.isPending && <Loading />}
            <ErrorNotice
              error={snapshot.error}
              retry={() => snapshot.refetch()}
            />
            {snapshot.data && <SnapshotSummary snapshot={snapshot.data} />}
            {snapshot.data && !snapshotReady && (
              <p role="alert">{t("errors.team_forbidden")}</p>
            )}
            <Button
              type="button"
              variant="outline"
              disabled={busy}
              onClick={() => {
                setSnapshotId(undefined);
                router.replace(`/student/tasks/${task.id}/submit`);
              }}
            >
              {t("repos.detach")}
            </Button>
          </div>
        )}
        {!snapshotId && task.submission_eligibility.team_id && (
          <Link
            className="underline text-action"
            href={`/student/teams/${task.submission_eligibility.team_id}/repositories`}
          >
            {t("repos.choose")}
          </Link>
        )}
        <Field label={t("submissionText")}>
          <textarea
            rows={8}
            dir="auto"
            value={text}
            onChange={(e) => setText(e.target.value)}
            disabled={busy}
          />
        </Field>
        <Field label={t("file")}>
          <input
            type="file"
            disabled={busy || !!snapshotId}
            accept={task.assignment_details?.allowed_file_types
              ?.map((x) => "." + x)
              .join(",")}
            onChange={(e) => {
              setFile(e.target.files?.[0]);
              setFileId(undefined);
            }}
          />
        </Field>
        <p className="text-sm muted">{t("fileHelp")}</p>
        {(stage || fileId) && <p role="status">{t(stage || "uploaded")}</p>}
        <ErrorNotice error={error} />
        {uncertain && (
          <Button
            type="button"
            variant="outline"
            onClick={async () => {
              try {
                await client.refetchQueries({}, { throwOnError: true });
                setUncertain(false);
              } catch (error) {
                setError(error);
              }
            }}
          >
            {t("refresh")}
          </Button>
        )}
        <Button disabled={busy || uncertain || !snapshotReady}>
          {t(busy ? "working" : fileId ? "newAttempt" : "submit")}
        </Button>
      </form>
    </section>
  );
}
