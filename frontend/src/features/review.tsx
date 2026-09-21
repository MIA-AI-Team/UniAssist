"use client";
import { AcademicMarkdown } from "@/components/academic-markdown";
import { FileMetadata } from "@/components/file-metadata";
import { RubricSummary } from "@/components/rubric-summary";
import { UsedGuidance } from "./guidance";
import { SnapshotSummary } from "./repositories";
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { Link } from "@/i18n/navigation";
import { request, ApiError } from "@/lib/api/client";
import type { Submission, Identity } from "@/lib/api/types";
import { Button } from "@/components/ui/button";
import { Confirm } from "@/components/ui/confirm";
import {
  Field,
  ErrorNotice,
  Loading,
  Status,
  Stamp,
} from "@/components/common";
export function Review({ id, user }: { id: number; user: Identity }) {
  const t = useTranslations(),
    client = useQueryClient(),
    staff = user.role !== "student";
  const [grade, setGrade] = useState("");
  const query = useQuery({
    queryKey: ["submission", id],
    queryFn: () => request<Submission>("/submissions/" + id),
  });
  const mutate = useMutation({
    mutationFn: (action: "grade" | "confirm") =>
      request(`/submissions/${id}/${action}`, {
        method: action === "grade" ? "POST" : "PATCH",
        body:
          action === "confirm"
            ? JSON.stringify({ final_grade: Number(grade) })
            : undefined,
      }),
    onSuccess: () => client.invalidateQueries(),
    onError: async (error) => {
      if (error instanceof ApiError && error.ambiguous) await query.refetch();
    },
  });
  if (query.isPending) return <Loading />;
  if (query.error)
    return <ErrorNotice error={query.error} retry={() => query.refetch()} />;
  const data = query.data!,
    released = data.status === "staff_confirmed",
    visible = staff || released;
  const valid =
    grade.trim() !== "" &&
    Number.isFinite(Number(grade)) &&
    Number(grade) >= 0 &&
    Number(grade) <= data.total_possible_grade;
  return (
    <div className="stack min-w-0 [overflow-wrap:anywhere]">
      <Link
        className="text-teal-800 underline"
        href={`/${staff ? "staff" : "student"}/tasks/${data.task_id}`}
      >
        {t("openTask")}
      </Link>
      <header className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1>
            {t("attempt")} {data.attempt_number}
          </h1>
          <p className="muted mt-2">
            {t("submittedAt")}: <Stamp value={data.submitted_at} />
          </p>
        </div>
        <Status value={data.status} staff={staff} />
      </header>
      {!data.is_latest && <p className="panel">{t("previousAttempt")}</p>}
      {data.repository_snapshot && (
        <SnapshotSummary snapshot={data.repository_snapshot} />
      )}
      {data.team_snapshot && (
        <section className="panel stack">
          <h2>{t("teams.snapshot")}</h2>
          <p>
            <bdi>{data.team_snapshot.name}</bdi> · {t("version")}{" "}
            {data.team_snapshot.version}
          </p>
          <p className="muted">{t("teams.individual")}</p>
          <ul>
            {data.team_snapshot.members.map((m) => (
              <li key={m.student_id}>
                <bdi>{m.name}</bdi> · <bdi>{m.student_number}</bdi>
              </li>
            ))}
          </ul>
        </section>
      )}
      {!staff && (
        <Link
          className="text-teal-800 underline"
          href={`/student/tasks/${data.task_id}/tutor?submission=${id}`}
        >
          {t("tutor.title")}
        </Link>
      )}
      <RubricSummary
        associated
        version={data.rubric_version}
        total={data.total_possible_grade}
        criteria={data.rubric_criteria}
      />
      {staff && (
        <UsedGuidance
          taskId={data.task_id}
          guidanceId={data.grading_guidance_id}
          pending={data.status === "pending"}
        />
      )}
      <div className="grid gap-6 lg:grid-cols-2">
        <section className="panel stack self-start">
          <h2>{t("artifact")}</h2>
          <pre
            dir="auto"
            className="prose-content max-h-[36rem] overflow-auto rounded-lg bg-slate-50 p-4 text-sm"
          >
            {data.submission_text ||
              t(data.artifacts.length ? "fileOnly" : "noArtifact")}
          </pre>
          {data.artifacts.map((a) => (
            <FileMetadata key={a.file_id} id={a.file_id} />
          ))}
        </section>
        <section className="panel stack">
          <h2>{t("result")}</h2>
          {!visible ? (
            <p className="muted">{t("awaiting")}</p>
          ) : (
            <>
              {data.is_mock && (
                <div className="rounded-xl border border-amber-300 bg-amber-50 p-4">
                  <h3>{t("mock")}</h3>
                  <p className="text-sm">{t("mockNotice")}</p>
                </div>
              )}
              <div className="flex flex-wrap gap-8">
                {released && (
                  <div>
                    <p className="muted">{t("finalGrade")}</p>
                    <p className="text-3xl font-bold text-teal-800">
                      <bdi dir="ltr">
                        {data.final_grade}{" "}
                        <span className="text-base muted">
                          / {data.total_possible_grade}
                        </span>
                      </bdi>
                    </p>
                  </div>
                )}
                {data.ai_suggested_grade != null && (
                  <div>
                    <p className="muted">{t("aiGrade")}</p>
                    <p className="text-xl font-semibold">
                      <bdi dir="ltr">
                        {data.ai_suggested_grade} / {data.total_possible_grade}
                      </bdi>
                    </p>
                  </div>
                )}
              </div>
              {data.feedback && <AcademicMarkdown content={data.feedback} />}
              {!!data.criterion_evaluations?.length && (
                <div className="stack">
                  <h3>
                    {t("aiGrade")} · {t("reasoning")}
                  </h3>
                  {data.criterion_evaluations.map((c, i) => (
                    <div key={i} className="rounded-lg bg-slate-50 p-4">
                      <strong dir="auto">
                        <AcademicMarkdown content={c.criterion_name} inline />
                      </strong>{" "}
                      ·{" "}
                      <bdi dir="ltr">
                        {c.score_given} / {c.max_points}
                      </bdi>
                      <AcademicMarkdown
                        className="mt-2 text-sm"
                        content={c.reasoning}
                      />
                    </div>
                  ))}
                </div>
              )}
              {!!data.code_reviews?.length && (
                <div className="stack">
                  <h3>{t("findings")}</h3>
                  {data.code_reviews.map((c, i) => (
                    <div key={i} className="border-s-2 border-amber-400 ps-4">
                      <code className="text-sm">
                        {c.file_path}
                        {c.line_number ? ":" + c.line_number : ""}
                      </code>
                      <span className="ms-3 text-sm font-semibold">
                        {t.has("severity_" + c.severity)
                          ? t("severity_" + c.severity)
                          : c.severity}
                      </span>
                      <AcademicMarkdown content={c.finding} />
                    </div>
                  ))}
                </div>
              )}
              {!!data.ai_warnings?.length && (
                <div>
                  <h3>{t("warnings")}</h3>
                  <ul className="list-disc ps-5">
                    {data.ai_warnings.map((w, i) => (
                      <li key={i} dir="auto">
                        <AcademicMarkdown content={w} />
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {data.confirmed_at && (
                <p className="text-sm muted">
                  {t("released")} · <Stamp value={data.confirmed_at} />
                </p>
              )}
            </>
          )}
        </section>
      </div>
      {staff && data.is_latest && !released && (
        <section className="panel stack">
          <ErrorNotice error={mutate.error} />
          {mutate.isPending && <p role="status">{t("evaluating")}</p>}
          {data.status === "pending" && (
            <Button
              className="justify-self-start"
              disabled={mutate.isPending}
              onClick={() => mutate.mutate("grade")}
            >
              {t("evaluate")}
            </Button>
          )}
          {user.role === "professor" && data.status === "ai_graded" && (
            <>
              <p className="muted">{t("overrideNotice")}</p>
              <div className="max-w-xs">
                <Field
                  label={t("finalGrade")}
                  error={grade && !valid ? t("fieldInvalid") : undefined}
                >
                  <input
                    type="number"
                    min={0}
                    max={data.total_possible_grade}
                    step="0.01"
                    value={grade}
                    onChange={(e) => setGrade(e.target.value)}
                    placeholder={String(data.ai_suggested_grade ?? "")}
                  />
                </Field>
              </div>
              <div>
                <Confirm
                  title={t("confirmGrade")}
                  description={t("releaseWarning")}
                  disabled={mutate.isPending || !valid}
                  onConfirm={() => mutate.mutate("confirm")}
                />
              </div>
            </>
          )}
        </section>
      )}
    </div>
  );
}
