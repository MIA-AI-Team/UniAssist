"use client";
import { useRef, useState, useTransition } from "react";
import {
  useInfiniteQuery,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { useLocale, useTranslations } from "next-intl";
import { useSearchParams } from "next/navigation";
import { Link, useRouter } from "@/i18n/navigation";
import { request, ApiError } from "@/lib/api/client";
import type { components } from "@/lib/api/schema";
import { Button } from "@/components/ui/button";
import { ErrorNotice, Field, Loading, Stamp } from "@/components/common";
import { TutorMarkdown } from "@/components/tutor-markdown";
import { TutorSharing } from "./tutor-sharing";
type S = components["schemas"];
type Turn = S["ChatTurnInfo"];

export function Tutor({ taskId }: { taskId: number }) {
  const params = useSearchParams();
  return <TutorWorkspace key={params.toString()} taskId={taskId} />;
}

function TutorWorkspace({ taskId }: { taskId: number }) {
  const t = useTranslations(),
    locale = useLocale(),
    router = useRouter(),
    params = useSearchParams();
  const client = useQueryClient();
  const chatId = Number(params.get("chat") || 0),
    submissionId = Number(params.get("submission") || 0);
  const [draft, setDraft] = useState("");
  const [isRouting, startTransition] = useTransition();
  const creation = useRef<string | null>(null);
  const pending = useRef<{ request_id: string; content: string } | null>(null);
  const task = useQuery({
    queryKey: ["task", taskId],
    queryFn: () => request<S["TaskDetailResponse"]>(`/tasks/${taskId}`),
  });
  const sessions = useInfiniteQuery({
    queryKey: ["chats", taskId],
    initialPageParam: null as number | null,
    queryFn: ({ pageParam }) =>
      request<S["ChatList"]>(
        `/tasks/${taskId}/chat-sessions${pageParam ? "?before=" + pageParam : ""}`,
      ),
    getNextPageParam: (page) => page.next_cursor,
  });
  const session = useQuery({
    queryKey: ["chat", chatId],
    enabled: chatId > 0,
    queryFn: () => request<S["ChatInfo"]>(`/chat-sessions/${chatId}`),
  });
  const turns = useInfiniteQuery({
    queryKey: ["chat-turns", chatId],
    enabled: !!session.data && session.data.task_id === taskId,
    initialPageParam: null as number | null,
    queryFn: ({ pageParam }) =>
      request<S["ChatTurnList"]>(
        `/chat-sessions/${chatId}/messages${pageParam ? "?before=" + pageParam : ""}`,
      ),
    getNextPageParam: (page) => page.next_cursor,
    refetchInterval: (query) =>
      query.state.data?.pages.some((p) =>
        p.items.some((m) => m.status === "pending"),
      )
        ? 3000
        : false,
  });
  const legacy = useInfiniteQuery({
    queryKey: ["chat-legacy", chatId],
    enabled: !!session.data && session.data.task_id === taskId,
    initialPageParam: null as number | null,
    queryFn: ({ pageParam }) =>
      request<S["LegacyMessages"]>(
        `/chat-sessions/${chatId}/legacy-messages${pageParam ? "?before=" + pageParam : ""}`,
      ),
    getNextPageParam: (page) => page.next_cursor,
  });
  const newChat = useMutation({
    mutationFn: () => {
      creation.current ||= crypto.randomUUID();
      return request<S["ChatInfo"]>(`/tasks/${taskId}/chat-sessions`, {
        method: "POST",
        body: JSON.stringify({
          request_id: creation.current,
          language: locale,
          submission_id: submissionId || null,
        }),
      });
    },
    onSuccess: async (data) => {
      creation.current = null;
      await client.invalidateQueries({ queryKey: ["chats", taskId] });
      startTransition(() =>
        router.replace(`/student/tasks/${taskId}/tutor?chat=${data.id}`),
      );
    },
  });
  const send = useMutation({
    mutationFn: async (retryTurn?: Turn) => {
      let body;
      if (retryTurn)
        body = {
          request_id: retryTurn.request_id,
          content: retryTurn.content,
          retry: true,
        };
      else {
        if (!pending.current || pending.current.content !== draft)
          pending.current = { request_id: crypto.randomUUID(), content: draft };
        body = pending.current;
      }
      const result = await request<Turn>(`/chat-sessions/${chatId}/messages`, {
        method: "POST",
        body: JSON.stringify(body),
      });
      if (result.status !== "completed")
        throw new ApiError(result.error_code || "chat_interrupted", 409);
      return result;
    },
    onSuccess: (result) => {
      if (pending.current?.request_id === result.request_id) {
        setDraft("");
        pending.current = null;
      }
    },
    onSettled: async () => {
      await client.invalidateQueries({ queryKey: ["chat-turns", chatId] });
    },
  });
  if (task.isPending) return <Loading />;
  if (task.error)
    return <ErrorNotice error={task.error} retry={() => task.refetch()} />;
  const messages =
    turns.data?.pages
      .slice()
      .reverse()
      .flatMap((p) => p.items) || [];
  const busy =
    newChat.isPending ||
    isRouting ||
    send.isPending ||
    messages.some((m) => m.status === "pending");
  return (
    <div className="stack">
      <Link
        href={`/student/tasks/${taskId}`}
        className="text-teal-800 underline"
      >
        {t("openTask")}
      </Link>
      <header className="stack">
        <h1>{t("tutor.title")}</h1>
        <p dir="auto">{task.data?.title}</p>
        <p className="muted">{t("tutor.guidance")}</p>
        <p className="text-sm muted">{t("tutor.privacy")}</p>
      </header>
      <div className="grid gap-6 lg:grid-cols-[16rem_minmax(0,1fr)]">
        <aside className="panel stack self-start">
          <h2>{t("tutor.conversations")}</h2>
          {submissionId > 0 && (
            <p>
              {t("tutor.linkedAttempt")} <bdi>{submissionId}</bdi>
            </p>
          )}
          <Button
            disabled={newChat.isPending || busy}
            onClick={() => newChat.mutate()}
          >
            {t("tutor.newChat")}
          </Button>
          <ErrorNotice error={newChat.error} />
          {sessions.isPending && <Loading />}
          <ErrorNotice
            error={sessions.error}
            retry={() => sessions.refetch()}
          />
          {sessions.data?.pages
            .flatMap((p) => p.items)
            .map((s) => (
              <Link
                key={s.id}
                href={`/student/tasks/${taskId}/tutor?chat=${s.id}`}
                aria-current={s.id === chatId ? "page" : undefined}
                className="rounded-lg border border-slate-200 p-3 text-sm aria-[current=page]:bg-teal-50"
              >
                {t("tutor.conversation")} {s.id} · <bdi>{s.language}</bdi>
                <br />
                <Stamp value={s.created_at} />
              </Link>
            ))}
          {sessions.hasNextPage && (
            <Button
              variant="outline"
              disabled={sessions.isFetchingNextPage}
              onClick={() => sessions.fetchNextPage()}
            >
              {t("tutor.more")}
            </Button>
          )}
        </aside>
        <section className="panel stack min-w-0">
          {!chatId ? (
            <p>{t("tutor.choose")}</p>
          ) : session.isPending ? (
            <Loading />
          ) : session.error ? (
            <ErrorNotice error={session.error} />
          ) : session.data?.task_id !== taskId ? (
            <p>{t("errors.permission_denied")}</p>
          ) : (
            <>
              <p className="text-sm muted">
                {t("tutor.replyLanguage")}:{" "}
                {session.data.language === "ar" ? "العربية" : "English"}
              </p>
              {session.data.submission_id && (
                <p>
                  {t("tutor.linkedAttempt")}{" "}
                  <bdi>{session.data.submission_id}</bdi>
                </p>
              )}
              {turns.isPending && <Loading />}
              <ErrorNotice error={turns.error} retry={() => turns.refetch()} />
              {turns.hasNextPage && (
                <Button
                  variant="outline"
                  disabled={turns.isFetchingNextPage}
                  onClick={() => turns.fetchNextPage()}
                >
                  {t("tutor.older")}
                </Button>
              )}
              <ErrorNotice
                error={legacy.error}
                retry={() => legacy.refetch()}
              />
              {!!legacy.data?.pages[0].items.length && (
                <details className="rounded-lg border p-3">
                  <summary>{t("tutor.legacy")}</summary>
                  <p className="text-sm muted">{t("tutor.legacyNotice")}</p>
                  {legacy.hasNextPage && (
                    <Button
                      onClick={() => legacy.fetchNextPage()}
                      disabled={legacy.isFetchingNextPage}
                    >
                      {t("tutor.older")}
                    </Button>
                  )}
                  {legacy.data.pages
                    .slice()
                    .reverse()
                    .flatMap((p) => p.items)
                    .map((m) => (
                      <div className="border-b py-3" key={m.id}>
                        <h3>
                          {t(
                            m.sender_type === "user"
                              ? "tutor.you"
                              : "tutor.title",
                          )}
                        </h3>
                        <TutorMarkdown content={m.content} />
                      </div>
                    ))}
                </details>
              )}
              <div
                className="stack"
                aria-live="polite"
                aria-relevant="additions text"
              >
                {messages.map((m) => (
                  <article
                    key={m.id}
                    className="stack border-b border-slate-100 pb-5"
                  >
                    <div className="rounded-lg bg-slate-50 p-4">
                      <h3>{t("tutor.you")}</h3>
                      <p className="prose-content" dir="auto">
                        {m.content}
                      </p>
                    </div>
                    {m.status === "pending" && (
                      <p role="status">{t("tutor.thinking")}</p>
                    )}
                    {m.reply && (
                      <div className="stack">
                        <h3>{t("tutor.title")}</h3>
                        {m.is_mock && (
                          <p className="text-sm text-amber-900">
                            {t("tutor.mock")}
                          </p>
                        )}
                        <TutorMarkdown content={m.reply} />
                        {m.context_info && (
                          <div className="text-sm muted">
                            <p>
                              {t("tutor.materials")}: {t("instructions")}
                              {m.context_info.rubric_version &&
                                ` · ${t("rubric")} ${m.context_info.rubric_version}`}
                              {m.context_info.submission_id &&
                                ` · ${t("attempt")} ${m.context_info.submission_id}`}
                            </p>
                            {m.context_info.reference_file_id && (
                              <a
                                className="underline"
                                href={`/api/backend/files/${m.context_info.reference_file_id}/download`}
                              >
                                {t("reference")}
                              </a>
                            )}
                            {m.context_info.truncated && (
                              <p>{t("tutor.truncated")}</p>
                            )}
                          </div>
                        )}
                      </div>
                    )}
                    {m.status === "failed" && (
                      <div role="status">
                        <p>{t("tutor.failed")}</p>
                        {m.retryable && (
                          <Button
                            variant="outline"
                            disabled={busy}
                            onClick={() => send.mutate(m)}
                          >
                            {t("retry")}
                          </Button>
                        )}
                      </div>
                    )}
                  </article>
                ))}
              </div>
              <TutorSharing sessionId={chatId} turns={messages} />
              <form
                className="stack"
                onSubmit={(e) => {
                  e.preventDefault();
                  send.mutate(undefined);
                }}
              >
                <Field label={t("tutor.question")}>
                  <textarea
                    dir="auto"
                    rows={4}
                    maxLength={4000}
                    value={draft}
                    disabled={busy}
                    onChange={(e) => setDraft(e.target.value)}
                  />
                </Field>
                <p className="text-sm muted">{t("tutor.pasteHelp")}</p>
                <ErrorNotice error={send.error} />
                <Button disabled={busy || !draft.trim() || !!turns.error}>
                  {t(busy ? "tutor.thinking" : "tutor.send")}
                </Button>
              </form>
            </>
          )}
        </section>
      </div>
    </div>
  );
}
