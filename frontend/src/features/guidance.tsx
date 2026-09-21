"use client";
import { AcademicMarkdown } from "@/components/academic-markdown";
import { MarkdownPreview } from "@/components/markdown-preview";
import { useRef, useState } from "react";
import {
  useInfiniteQuery,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { request } from "@/lib/api/client";
import type { components } from "@/lib/api/schema";
import { Button } from "@/components/ui/button";
import { Confirm } from "@/components/ui/confirm";
import { ErrorNotice, Field, Loading, Stamp } from "@/components/common";
type S = components["schemas"];

export function GradingGuidance({ taskId }: { taskId: number }) {
  const t = useTranslations(),
    client = useQueryClient();
  const [content, setContent] = useState("");
  const pending = useRef<{ request_id: string; content: string } | null>(null);
  const history = useInfiniteQuery({
    queryKey: ["guidance", taskId],
    initialPageParam: null as number | null,
    queryFn: ({ pageParam }) =>
      request<S["GuidanceList"]>(
        `/tasks/${taskId}/grading-guidance${pageParam ? "?before=" + pageParam : ""}`,
      ),
    getNextPageParam: (page) => page.next_cursor,
  });
  const save = useMutation({
    mutationFn: () => {
      if (!pending.current || pending.current.content !== content)
        pending.current = { request_id: crypto.randomUUID(), content };
      return request<S["GuidanceInfo"]>(`/tasks/${taskId}/grading-guidance`, {
        method: "POST",
        body: JSON.stringify(pending.current),
      });
    },
    onSuccess: () => {
      setContent("");
      pending.current = null;
    },
    onSettled: () =>
      client.invalidateQueries({ queryKey: ["guidance", taskId] }),
  });
  return (
    <section className="panel stack">
      <h2>{t("guidance.title")}</h2>
      <p className="muted">{t("guidance.help")}</p>
      <p className="rounded-lg bg-amber-50 p-3 text-amber-950">
        {t("guidance.warning")}
      </p>
      <Field label={t("guidance.content")}>
        <textarea
          dir="auto"
          rows={6}
          maxLength={12000}
          value={content}
          disabled={save.isPending}
          onChange={(e) => {
            setContent(e.target.value);
            save.reset();
          }}
        />
      </Field>
      <MarkdownPreview content={content} label={t("guidance.content")} />
      <p className="text-sm muted">{t("guidance.clearHelp")}</p>
      <ErrorNotice error={save.error} />
      {save.isSuccess && <p role="status">{t("guidance.saved")}</p>}
      <Confirm
        title={t("guidance.save")}
        description={t(
          content.trim() ? "guidance.confirm" : "guidance.clearConfirm",
        )}
        disabled={save.isPending || history.isFetching}
        onConfirm={() => save.mutate()}
      />
      <h3>{t("guidance.history")}</h3>
      {history.isPending && <Loading />}
      <ErrorNotice error={history.error} retry={() => history.refetch()} />
      {history.data?.pages[0].items.length === 0 && <p>{t("guidance.none")}</p>}
      {history.data?.pages
        .flatMap((p) => p.items)
        .map((row) => (
          <details key={row.id} className="rounded-lg border p-3">
            <summary className="cursor-pointer">
              {t("version")} {row.version} · <Stamp value={row.created_at} />
            </summary>
            <AcademicMarkdown
              className="mt-3"
              content={
                row.content.trim() ? row.content : t("guidance.disabled")
              }
            />
          </details>
        ))}
      {history.hasNextPage && (
        <Button
          variant="outline"
          disabled={history.isFetchingNextPage}
          onClick={() => history.fetchNextPage()}
        >
          {t("guidance.older")}
        </Button>
      )}
    </section>
  );
}

export function UsedGuidance({
  taskId,
  guidanceId,
  pending,
}: {
  taskId: number;
  guidanceId?: number | null;
  pending: boolean;
}) {
  const t = useTranslations();
  const query = useQuery({
    queryKey: ["guidance-version", taskId, guidanceId],
    enabled: !!guidanceId,
    queryFn: () =>
      request<S["GuidanceInfo"]>(
        `/tasks/${taskId}/grading-guidance/${guidanceId}`,
      ),
  });
  return (
    <section className="panel stack">
      <h2>{t("guidance.used")}</h2>
      <p className="text-sm text-amber-950">{t("guidance.warning")}</p>
      {!guidanceId ? (
        <p>{t(pending ? "guidance.next" : "guidance.unknown")}</p>
      ) : query.isPending ? (
        <Loading />
      ) : query.error ? (
        <ErrorNotice error={query.error} retry={() => query.refetch()} />
      ) : (
        <details>
          <summary>
            {t("version")} {query.data!.version}
          </summary>
          <AcademicMarkdown
            className="mt-3"
            content={
              query.data!.content.trim()
                ? query.data!.content
                : t("guidance.disabled")
            }
          />
        </details>
      )}
    </section>
  );
}
