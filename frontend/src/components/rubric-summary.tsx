"use client";
import { useTranslations } from "next-intl";
import type { Criterion } from "@/lib/api/types";
import { AcademicMarkdown } from "./academic-markdown";

export function RubricSummary({
  version,
  total,
  criteria,
  associated = false,
}: {
  version: number;
  total: number;
  criteria: Criterion[];
  associated?: boolean;
}) {
  const t = useTranslations();
  return (
    <section className="panel stack">
      <h2>{t(associated ? "acceptedRubric" : "approvedRubric")}</h2>
      <p className="text-sm muted">
        {t("version")} {version} · {t("rubricTotal")}: {total} {t("points")}
      </p>
      {criteria.map((criterion, index) => (
        <div key={index} className="evidence-row">
          <div className="evidence-heading">
            <strong dir="auto">
              <AcademicMarkdown content={criterion.name} inline />
            </strong>
            <span className="evidence-points">
              {criterion.max_points} {t("points")}
            </span>
          </div>
          <AcademicMarkdown
            className="mt-2 text-sm muted"
            content={criterion.description || ""}
          />
        </div>
      ))}
    </section>
  );
}
