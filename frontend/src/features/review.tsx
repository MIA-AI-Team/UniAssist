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
  const artifact = (
    <section className="panel stack self-start">
      <h2>{t("artifact")}</h2>
      <pre
        dir="auto"
        className="prose-content max-h-[36rem] overflow-auto rounded-lg bg-surface-subtle p-4 text-sm"
      >
        {data.submission_text ||
          t(data.artifacts.length ? "fileOnly" : "noArtifact")}
      </pre>
      {data.artifacts.map((a) => (
        <FileMetadata key={a.file_id} id={a.file_id} />
      ))}
    </section>
  );
  return (
    <div className="stack min-w-0 [overflow-wrap:anywhere]">
      <Link
        className="text-action underline"
        href={`/${staff ? "staff" : "student"}/tasks/${data.task_id}`}
      >
        {t("openTask")}
      </Link>
      <header className="receipt" aria-label={t("desk.receipt")}>
        <div className="flex flex-wrap items-center justify-between gap-4">
          <h1>
            {t("attempt")} {data.attempt_number}
          </h1>
          <Status value={data.status} staff={staff} />
        </div>
        <dl>
          <div>
            <dt>{t("submittedAt")}</dt>
            <dd>
              <Stamp value={data.submitted_at} />
            </dd>
          </div>
          <div>
            <dt>{t("rubric")}</dt>
            <dd>
              {t("version")} {data.rubric_version}
            </dd>
          </div>
          <div>
            <dt>{t("rubricTotal")}</dt>
            <dd>
              {data.total_possible_grade} {t("points")}
            </dd>
          </div>
          {data.repository_snapshot && (
            <div className="min-w-0">
              <dt>{t("repos.sha")}</dt>
              <dd>
                <code className="break-all">
                  {data.repository_snapshot.commit_sha}
                </code>
              </dd>
            </div>
          )}
          {released && data.confirmed_at && (
            <div>
              <dt>{t("released")}</dt>
              <dd>
                <Stamp value={data.confirmed_at} />
              </dd>
            </div>
          )}
        </dl>
        {staff && (
          <a
            className="button button-ghost underline mt-4 me-3"
            href="#attempt-rubric"
          >
            {t("desk.expectationsTitle")}
          </a>
        )}
        {staff && data.is_latest && !released && (
          <a className="button button-outline mt-4" href="#review-decision">
            {t("desk.decision")}
          </a>
        )}
      </header>
      {!data.is_latest && <p className="panel">{t("previousAttempt")}</p>}
      {!staff && (
        <Link
          className="text-action underline"
          href={`/student/tasks/${data.task_id}/tutor?submission=${id}`}
        >
          {t("tutor.title")}
        </Link>
      )}
      <div className={staff ? "review-columns" : "stack"}>
        {staff && artifact}
        <section className="panel stack">
          <h2>{t("result")}</h2>
          {!visible ? (
            <p className="muted">{t("awaiting")}</p>
          ) : (
            <>
              {data.status === "pending" && (
                <p className="notice">{t("staff_pending")}</p>
              )}
              {data.is_mock && (
                <div className="notice notice-warning">
                  <h3>{t("mock")}</h3>
                  <p className="text-sm">{t("mockNotice")}</p>
                </div>
              )}
              {data.feedback && <AcademicMarkdown content={data.feedback} />}
              {(released || data.ai_suggested_grade != null) && (
                <div className="grade-summary">
                  {released && (
                    <div>
                      <p className="muted">{t("finalGrade")}</p>
                      <p className="grade-value text-action">
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
                      <p className="grade-value">
                        <bdi dir="ltr">
                          {data.ai_suggested_grade} /{" "}
                          {data.total_possible_grade}
                        </bdi>
                      </p>
                    </div>
                  )}
                </div>
              )}
              {!!data.criterion_evaluations?.length && (
                <div className="stack">
                  <h3>
                    {t("aiGrade")} · {t("reasoning")}
                  </h3>
                  {data.criterion_evaluations.map((c, i) => (
                    <div key={i} className="evidence-row">
                      <div className="evidence-heading">
                        <strong dir="auto">
                          <AcademicMarkdown content={c.criterion_name} inline />
                        </strong>
                        <bdi className="evidence-points" dir="ltr">
                          {c.score_given} / {c.max_points}
                        </bdi>
                      </div>
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
                    <div key={i} className="border-s-2 border-warning ps-4">
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
      <div id="attempt-rubric">
        <RubricSummary
          associated
          version={data.rubric_version}
          total={data.total_possible_grade}
          criteria={data.rubric_criteria}
        />
      </div>
      {staff && (
        <UsedGuidance
          taskId={data.task_id}
          guidanceId={data.grading_guidance_id}
          pending={data.status === "pending"}
        />
      )}
      {!staff && artifact}
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
      {staff && data.is_latest && !released && (
        <section id="review-decision" className="decision-panel stack">
          <h2>{t("desk.decision")}</h2>
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
