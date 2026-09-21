"use client";
import { useRef } from "react";
import {
  useInfiniteQuery,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { useLocale, useTranslations, useFormatter } from "next-intl";
import { Link } from "@/i18n/navigation";
import { request } from "@/lib/api/client";
import type { components } from "@/lib/api/schema";
import { Button } from "@/components/ui/button";
import { ErrorNotice, Loading, Stamp } from "@/components/common";
import { AcademicMarkdown } from "@/components/academic-markdown";
type S = components["schemas"];

export function TaskInsights({ taskId }: { taskId: number }) {
  const t = useTranslations(),
    locale = useLocale(),
    client = useQueryClient(),
    format = useFormatter();
  const pending = useRef<{
    rubric_id: number;
    language: string;
    request_id: string;
  } | null>(null);
  const query = useQuery({
    queryKey: ["analytics", taskId],
    queryFn: () => request<S["TaskAnalytics"]>(`/tasks/${taskId}/analytics`),
  });
  const task = useQuery({
    queryKey: ["task", taskId],
    queryFn: () => request<S["TaskDetailResponse"]>(`/tasks/${taskId}`),
  });
  const reports = useInfiniteQuery({
    queryKey: ["teaching-reports", taskId],
    initialPageParam: null as number | null,
    queryFn: ({ pageParam }) =>
      request<S["TeachingReportList"]>(
        `/tasks/${taskId}/analytics/reports${pageParam ? "?before=" + pageParam : ""}`,
      ),
    getNextPageParam: (page) => page.next_cursor,
  });
  const generate = useMutation({
    mutationFn: (rubric_id: number) => {
      if (
        !pending.current ||
        pending.current.rubric_id !== rubric_id ||
        pending.current.language !== locale
      )
        pending.current = {
          rubric_id,
          language: locale,
          request_id: crypto.randomUUID(),
        };
      return request<S["TeachingReportInfo"]>(
        `/tasks/${taskId}/analytics/reports`,
        { method: "POST", body: JSON.stringify(pending.current) },
      );
    },
    onSuccess: () => {
      pending.current = null;
    },
    onSettled: async () => {
      await Promise.all([
        client.invalidateQueries({ queryKey: ["teaching-reports", taskId] }),
        client.invalidateQueries({ queryKey: ["analytics", taskId] }),
      ]);
    },
  });
  const number = (n: number | null) =>
    n == null ? "—" : format.number(n, { maximumFractionDigits: 2 });
  return (
    <div className="stack">
      <Link className="text-teal-800 underline" href={`/staff/tasks/${taskId}`}>
        {t("openTask")}
      </Link>
      <h1>{t("insights.title")}</h1>
      {task.data && <p dir="auto">{task.data.title}</p>}
      <p className="muted">{t("insights.help")}</p>
      <Button
        variant="outline"
        disabled={query.isFetching || reports.isFetching}
        onClick={() => {
          void query.refetch();
          void reports.refetch();
        }}
      >
        {t("refresh")}
      </Button>
      {query.isPending && <Loading />}
      <ErrorNotice
        error={task.error || query.error}
        retry={() => {
          void task.refetch();
          void query.refetch();
        }}
      />
      {query.data && (
        <>
          <p>{t("insights.released", { count: query.data.released_count })}</p>
          {!!query.data.excluded_count && (
            <p>
              {t("insights.excluded", { count: query.data.excluded_count })}
            </p>
          )}
          {!query.data.groups.length && (
            <p className="panel">{t("insights.empty")}</p>
          )}
          {query.data.groups.map((group) => (
            <section className="panel stack" key={group.rubric_id}>
              <h2>
                {t("rubric")} · {t("version")} {group.rubric_version}
              </h2>
              <p>{t("insights.released", { count: group.student_count })}</p>
              <p className="text-sm text-amber-950">
                {t("insights.provenance", {
                  mock: group.mock_assessment_count,
                  unknown: group.unknown_provenance_count,
                })}
              </p>
              {!group.eligible ? (
                <p>
                  {t("insights.insufficient", {
                    count: query.data!.minimum_group_size,
                  })}
                </p>
              ) : (
                <>
                  <h3>{t("insights.statistics")}</h3>
                  <dl className="grid grid-cols-2 gap-4 sm:grid-cols-4">
                    <div>
                      <dt>{t("insights.average")}</dt>
                      <dd className="text-xl font-semibold">
                        {number(group.average_percentage)}%
                      </dd>
                    </div>
                    <div>
                      <dt>{t("insights.minimum")}</dt>
                      <dd>{number(group.minimum_percentage)}%</dd>
                    </div>
                    <div>
                      <dt>{t("insights.maximum")}</dt>
                      <dd>{number(group.maximum_percentage)}%</dd>
                    </div>
                    <div>
                      <dt>{t("insights.belowHalf")}</dt>
                      <dd>{number(group.below_half_count)}</dd>
                    </div>
                  </dl>
                  <p className="text-sm muted">{t("insights.criteriaHelp")}</p>
                  <div className="overflow-x-auto">
                    <table className="w-full text-start text-sm">
                      <caption className="text-start font-semibold mb-2">
                        {t("insights.criteria")}
                      </caption>
                      <thead>
                        <tr>
                          {["criterion", "samples", "meanScore", "low"].map(
                            (key) => (
                              <th key={key} className="p-2 text-start">
                                {t(`insights.${key}`)}
                              </th>
                            ),
                          )}
                        </tr>
                      </thead>
                      <tbody>
                        {group.criteria.map((c, index) => (
                          <tr key={c.criterion_id} className="border-t">
                            <td className="p-2">
                              <bdi>{c.name}</bdi>
                              <p className="muted">
                                {t("insights.criterionNumber", {
                                  number: index + 1,
                                })}
                              </p>
                            </td>
                            <td className="p-2">{number(c.sample_count)}</td>
                            <td className="p-2">
                              <bdi dir="ltr">
                                {number(c.average_score)} /{" "}
                                {number(c.max_points)}
                              </bdi>
                            </td>
                            <td className="p-2">{number(c.low_score_count)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  <p className="text-sm">
                    {t("insights.findings")}:{" "}
                    {Object.entries(group.severity_counts || {})
                      .map(
                        ([key, count]) =>
                          `${t(`insights.${key}`)}: ${number(count)}`,
                      )
                      .join(" · ") || t("empty")}
                  </p>
                  <Button
                    disabled={generate.isPending || reports.isFetching}
                    onClick={() => generate.mutate(group.rubric_id)}
                  >
                    {t(generate.isPending ? "working" : "insights.generate")}
                  </Button>
                </>
              )}
            </section>
          ))}
        </>
      )}
      <ErrorNotice error={generate.error} />
      <h2>{t("insights.reports")}</h2>
      <p className="muted">{t("insights.caution")}</p>
      {reports.isPending && <Loading />}
      <ErrorNotice error={reports.error} retry={() => reports.refetch()} />
      {reports.data?.pages[0].items.length === 0 && (
        <p>{t("insights.noReports")}</p>
      )}
      {reports.data?.pages
        .flatMap((p) => p.items)
        .map((report) => (
          <article className="panel stack" key={report.id}>
            <h3>
              {t("version")} {report.rubric_version} ·{" "}
              <bdi>{report.language === "ar" ? "العربية" : "English"}</bdi> ·{" "}
              <Stamp value={report.created_at} />
            </h3>
            {(report.stale ||
              (query.data &&
                report.input_fingerprint !== query.data.input_fingerprint)) && (
              <p className="text-amber-950" role="status">
                {t("insights.stale")}
              </p>
            )}
            {report.is_mock && (
              <p className="text-amber-950">{t("insights.mock")}</p>
            )}
            <p className="text-sm muted">
              {t("insights.snapshot", {
                count: report.input_snapshot.student_count,
                average: number(report.input_snapshot.average_percentage),
              })}
            </p>
            <AcademicMarkdown content={report.result.summary} />
            {report.result.common_issues?.map((issue, i) => (
              <section className="stack" key={i}>
                <h4 className="font-semibold" dir="auto">
                  {issue.title}
                </h4>
                <AcademicMarkdown content={issue.description} />
                <p dir="auto">{issue.evidence}</p>
              </section>
            ))}
            {report.result.misconceptions?.map((m, i) => (
              <section className="stack" key={i}>
                <h4 className="font-semibold" dir="auto">
                  {m.concept}
                </h4>
                <AcademicMarkdown content={m.description} />
                <AcademicMarkdown content={m.suggested_remediation} />
              </section>
            ))}
            {report.result.teaching_focus?.map((focus, i) => (
              <AcademicMarkdown key={i} content={focus} />
            ))}
            {report.result.warnings?.map((warning, i) => (
              <p className="text-sm text-amber-950" dir="auto" key={i}>
                {warning}
              </p>
            ))}
          </article>
        ))}
      {reports.hasNextPage && (
        <Button
          variant="outline"
          disabled={reports.isFetchingNextPage}
          onClick={() => reports.fetchNextPage()}
        >
          {t("insights.older")}
        </Button>
      )}
    </div>
  );
}
