"use client";
import { useTranslations } from "next-intl";
import type { Criterion } from "@/lib/api/types";

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
        <div key={index} className="border-s-2 border-teal-300 ps-4">
          <strong dir="auto">{criterion.name}</strong> · {criterion.max_points}{" "}
          {t("points")}
          <p className="text-sm muted" dir="auto">
            {criterion.description}
          </p>
        </div>
      ))}
    </section>
  );
}
