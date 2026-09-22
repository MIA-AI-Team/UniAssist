"use client";
import { useRef, useState } from "react";
import {
  useInfiniteQuery,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { z } from "zod";
import { Link } from "@/i18n/navigation";
import { request } from "@/lib/api/client";
import type { components } from "@/lib/api/schema";
import { Button } from "@/components/ui/button";
import { Confirm } from "@/components/ui/confirm";
import { ErrorNotice, Field, Loading, Stamp } from "@/components/common";
import { AcademicMarkdown } from "@/components/academic-markdown";
type S = components["schemas"];

export function TutorSharing({
  sessionId,
  turns,
}: {
  sessionId: number;
  turns: S["ChatTurnInfo"][];
}) {
  const t = useTranslations(),
    client = useQueryClient();
  const [email, setEmail] = useState(""),
    [through, setThrough] = useState("");
  const identity = useRef<{
    email: string;
    through: string;
    request_id: string;
  } | null>(null);
  const preview = useQuery({
    queryKey: ["chat-preview", sessionId, through],
    enabled: !!through,
    queryFn: () =>
      request<S["SharedTurn"][]>(
        `/chat-sessions/${sessionId}/share-preview?through_turn_id=${through}`,
      ),
  });
  const shares = useInfiniteQuery({
    queryKey: ["chat-shares", sessionId],
    initialPageParam: null as number | null,
    queryFn: ({ pageParam }) =>
      request<S["ShareList"]>(
        `/chat-sessions/${sessionId}/shares${pageParam ? "?before=" + pageParam : ""}`,
      ),
    getNextPageParam: (page) => page.next_cursor,
  });
  const share = useMutation({
    mutationFn: () => {
      if (
        !identity.current ||
        identity.current.email !== email ||
        identity.current.through !== through
      )
        identity.current = { email, through, request_id: crypto.randomUUID() };
      return request<S["ShareInfo"]>(`/chat-sessions/${sessionId}/shares`, {
        method: "POST",
        body: JSON.stringify({
          recipient_email: email,
          through_turn_id: Number(through),
          preview_turn_ids: preview.data?.map((turn) => turn.id),
          request_id: identity.current.request_id,
        }),
      });
    },
    onSuccess: async () => {
      identity.current = null;
      await client.invalidateQueries({ queryKey: ["chat-shares", sessionId] });
    },
  });
  const revoke = useMutation({
    mutationFn: (id: number) =>
      request(`/chat-shares/${id}`, { method: "DELETE" }),
    onSuccess: () =>
      client.invalidateQueries({ queryKey: ["chat-shares", sessionId] }),
  });
  return (
    <details className="disclosure-section">
      <summary>{t("tutor.sharing")}</summary>
      <div className="disclosure-content stack">
        <p className="text-sm muted">{t("tutor.shareHelp")}</p>
        <Field label={t("tutor.recipient")}>
          <input
            type="email"
            dir="ltr"
            value={email}
            disabled={share.isPending}
            onChange={(e) => setEmail(e.target.value)}
          />
        </Field>
        <Field label={t("tutor.through")}>
          <select
            value={through}
            disabled={share.isPending}
            onChange={(e) => {
              setThrough(e.target.value);
              share.reset();
            }}
          >
            <option value="">{t("tutor.selectTurn")}</option>
            {turns
              .filter((m) => m.status === "completed")
              .map((m) => (
                <option value={m.id} key={m.id}>
                  {m.content.slice(0, 80)}
                </option>
              ))}
          </select>
        </Field>
        {through && preview.isPending && <Loading />}
        <ErrorNotice error={preview.error} retry={() => preview.refetch()} />
        {preview.data && (
          <section className="stack max-h-96 overflow-auto">
            <h3>{t("tutor.preview")}</h3>
            <div className="transcript">
              {preview.data.map((m) => (
                <article key={m.id} className="transcript-turn">
                  <div className="transcript-entry">
                    <h4 className="transcript-speaker">{t("tutor.you")}</h4>
                    <div className="transcript-body">
                      <AcademicMarkdown content={m.content} />
                    </div>
                  </div>
                  <div className="transcript-entry">
                    <h4 className="transcript-speaker">{t("tutor.title")}</h4>
                    <div className="transcript-body">
                      <AcademicMarkdown content={m.reply} />
                    </div>
                  </div>
                </article>
              ))}
            </div>
          </section>
        )}
        <ErrorNotice error={share.error || revoke.error} />
        {share.isSuccess && <p role="status">{t("tutor.sharedSuccess")}</p>}
        <Confirm
          title={t("tutor.share")}
          description={`${t("tutor.shareWarning")} ${email}`}
          disabled={
            !z.email().safeParse(email).success ||
            !preview.data?.length ||
            share.isPending ||
            preview.isFetching
          }
          onConfirm={() => share.mutate()}
        />
        {shares.isPending && <Loading />}
        <ErrorNotice error={shares.error} retry={() => shares.refetch()} />
        {!!shares.data?.pages.flatMap((p) => p.items).length && (
          <div className="record-list">
            {shares.data.pages
              .flatMap((p) => p.items)
              .map((s) => (
                <div key={s.id} className="record-row">
                  <div className="record-body">
                    <p className="record-title">
                      <bdi>{s.recipient_name}</bdi>
                    </p>
                    <p className="record-description">
                      <Stamp value={s.created_at} />
                    </p>
                  </div>
                  <div className="record-trailing">
                    {s.revoked_at ? (
                      <span>{t("tutor.revoked")}</span>
                    ) : (
                      <Confirm
                        title={t("tutor.revoke")}
                        description={t("tutor.revokeWarning")}
                        disabled={revoke.isPending}
                        onConfirm={() => revoke.mutate(s.id)}
                      />
                    )}
                  </div>
                </div>
              ))}
          </div>
        )}
        {shares.hasNextPage && (
          <Button
            variant="outline"
            onClick={() => shares.fetchNextPage()}
            disabled={shares.isFetchingNextPage}
          >
            {t("tutor.more")}
          </Button>
        )}
      </div>
    </details>
  );
}

export function SharedTutoring({ shareId }: { shareId?: number }) {
  const t = useTranslations();
  const list = useInfiniteQuery({
    queryKey: ["received-chats"],
    enabled: !shareId,
    initialPageParam: null as number | null,
    queryFn: ({ pageParam }) =>
      request<S["ShareList"]>(
        `/chat-shares${pageParam ? "?before=" + pageParam : ""}`,
      ),
    getNextPageParam: (page) => page.next_cursor,
  });
  const detail = useQuery({
    queryKey: ["received-chat", shareId],
    enabled: !!shareId,
    refetchInterval: 15000,
    queryFn: () => request<S["ShareDetail"]>(`/chat-shares/${shareId}`),
  });
  if (shareId)
    return (
      <div className="stack">
        <Link href="/staff/shared-tutoring" className="underline text-action">
          {t("back")}
        </Link>
        {detail.isPending ? (
          <Loading />
        ) : detail.error ? (
          <ErrorNotice error={detail.error} retry={() => detail.refetch()} />
        ) : (
          <>
            <h1>{t("tutor.sharedInbox")}</h1>
            <p>
              <bdi>{detail.data!.student_name}</bdi> · {detail.data!.title}
            </p>
            <p className="muted">{t("tutor.snapshotNotice")}</p>
            <div className="transcript">
              {detail.data!.snapshot.map((m) => (
                <article className="transcript-turn" key={m.id}>
                  <div className="transcript-entry">
                    <div className="transcript-speaker">
                      <h2>{t("tutor.youShared")}</h2>
                      <Stamp value={m.created_at} />
                    </div>
                    <div className="transcript-body">
                      <AcademicMarkdown content={m.content} />
                    </div>
                  </div>
                  <div className="transcript-entry">
                    <h2 className="transcript-speaker">{t("tutor.title")}</h2>
                    <div className="transcript-body stack">
                      {m.is_mock && (
                        <p className="text-warning">{t("tutor.mock")}</p>
                      )}
                      <AcademicMarkdown content={m.reply} />
                    </div>
                  </div>
                </article>
              ))}
            </div>
          </>
        )}
      </div>
    );
  return (
    <div className="stack">
      <h1>{t("tutor.sharedInbox")}</h1>
      <p className="muted">{t("tutor.snapshotNotice")}</p>
      {list.isPending && <Loading />}
      <ErrorNotice error={list.error} retry={() => list.refetch()} />
      {list.data?.pages[0].items.length === 0 && <p>{t("empty")}</p>}
      {!!list.data?.pages.flatMap((p) => p.items).length && (
        <div className="record-list">
          {list.data.pages
            .flatMap((p) => p.items)
            .map((s) => (
              <Link
                className="record-row"
                key={s.id}
                href={`/staff/shared-tutoring/${s.id}`}
              >
                <span className="record-body">
                  <span className="record-title" dir="auto">
                    {s.title}
                  </span>
                  <span className="record-description">
                    <bdi>{s.student_name}</bdi>
                  </span>
                </span>
                <span className="record-trailing">
                  <Stamp value={s.created_at} />
                </span>
              </Link>
            ))}
        </div>
      )}
      {list.hasNextPage && (
        <Button
          disabled={list.isFetchingNextPage}
          onClick={() => list.fetchNextPage()}
        >
          {t("tutor.more")}
        </Button>
      )}
    </div>
  );
}

export function LabTutorSettings({ taskId }: { taskId: number }) {
  const t = useTranslations(),
    client = useQueryClient();
  const query = useQuery({
    queryKey: ["tutor-settings", taskId],
    queryFn: () =>
      request<S["TutorSettings"]>(`/tasks/${taskId}/tutor-settings`),
  });
  const save = useMutation({
    mutationFn: (lab_mode: string) =>
      request(`/tasks/${taskId}/tutor-settings`, {
        method: "PATCH",
        body: JSON.stringify({ lab_mode }),
      }),
    onSuccess: () =>
      client.invalidateQueries({ queryKey: ["tutor-settings", taskId] }),
  });
  return (
    <section className="document-section stack">
      <h2>{t("tutor.labSettings")}</h2>
      {query.isPending ? (
        <Loading />
      ) : query.error ? (
        <ErrorNotice error={query.error} retry={() => query.refetch()} />
      ) : (
        <>
          <Field label={t("tutor.labMode")}>
            <select
              value={query.data!.lab_mode}
              disabled={save.isPending}
              onChange={(e) => save.mutate(e.target.value)}
            >
              <option value="experiment">{t("tutor.experiment")}</option>
              <option value="coding">{t("tutor.coding")}</option>
            </select>
          </Field>
          <p className="text-sm muted">{t("tutor.settingsHelp")}</p>
          <ErrorNotice error={save.error} />
          {save.isSuccess && <p role="status">{t("tutor.saved")}</p>}
        </>
      )}
    </section>
  );
}
