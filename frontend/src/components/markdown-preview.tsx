"use client";
import { useId } from "react";
import { useTranslations } from "next-intl";
import { AcademicMarkdown } from "./academic-markdown";

export function MarkdownPreview({
  content,
  label,
  inline = false,
  className = "",
}: {
  content: string;
  label: string;
  inline?: boolean;
  className?: string;
}) {
  const t = useTranslations("markdown");
  const id = useId();
  return (
    <section
      aria-labelledby={id}
      className={`min-w-0 border-s-2 border-divider bg-surface-subtle p-3 ${className}`}
    >
      <h3 id={id} className="text-sm">
        {t("preview", { field: label })}
      </h3>
      <p className="text-xs muted my-2">
        {t("syntax")}{" "}
        <bdi dir="ltr">
          <code>{String.raw`$x^2$ · $$x^2$$ · \(x^2\) · \[x^2\]`}</code>
        </bdi>{" "}
        {t("literalDollar")}{" "}
        <bdi dir="ltr">
          <code>{String.raw`\$`}</code>
        </bdi>
      </p>
      {content.trim() ? (
        <AcademicMarkdown content={content} inline={inline} />
      ) : (
        <p className="text-sm muted">{t("empty")}</p>
      )}
    </section>
  );
}
