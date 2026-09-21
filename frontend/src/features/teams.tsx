"use client";
import { useRef, useState } from "react";
import {
  useInfiniteQuery,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { Link, useRouter } from "@/i18n/navigation";
import { request } from "@/lib/api/client";
import type { Identity } from "@/lib/api/types";
import type { components } from "@/lib/api/schema";
import { Button } from "@/components/ui/button";
import { Confirm } from "@/components/ui/confirm";
import { ErrorNotice, Field, Loading, Stamp } from "@/components/common";
type S = components["schemas"];

export function ProjectTeams({
  taskId,
  user,
}: {
  taskId: number;
  user: Identity;
}) {
  const t = useTranslations(),
    router = useRouter(),
    client = useQueryClient();
  const staff = user.role !== "student",
    area = staff ? "staff" : "student";
  const [name, setName] = useState(""),
    [status, setStatus] = useState("");
  const pending = useRef<{ name: string; request_id: string } | null>(null);
  const list = useInfiniteQuery({
    queryKey: ["teams", taskId, status],
    initialPageParam: null as number | null,
    queryFn: ({ pageParam }) =>
      request<S["TeamList"]>(
        `/tasks/${taskId}/teams?limit=20${status ? "&status=" + status : ""}${pageParam ? "&before=" + pageParam : ""}`,
      ),
    getNextPageParam: (page) => page.next_cursor,
  });
  const create = useMutation({
    mutationFn: () => {
      if (!pending.current || pending.current.name !== name)
        pending.current = { name, request_id: crypto.randomUUID() };
      return request<S["TeamInfo"]>(`/tasks/${taskId}/teams`, {
        method: "POST",
        body: JSON.stringify(pending.current),
      });
    },
    onSuccess: (team) => router.push(`/student/teams/${team.id}`),
    onSettled: () => client.invalidateQueries({ queryKey: ["teams", taskId] }),
  });
  return (
    <div className="stack">
      <Link className="underline text-action" href={`/${area}/tasks/${taskId}`}>
        {t("openTask")}
      </Link>
      <h1>{t("teams.title")}</h1>
      <p className="muted">{t("teams.individual")}</p>
      {!staff && (
        <form
          className="panel stack"
          onSubmit={(e) => {
            e.preventDefault();
            create.mutate();
          }}
        >
          <p>
            {t("teams.yourNumber")}: <bdi>{user.student_number}</bdi>
          </p>
          <Field label={t("teams.name")}>
            <input
              dir="auto"
              value={name}
              maxLength={150}
              disabled={create.isPending}
              onChange={(e) => setName(e.target.value)}
            />
          </Field>
          <p className="muted text-sm">{t("teams.createHelp")}</p>
          <ErrorNotice error={create.error} />
          <Button disabled={create.isPending || name.trim().length < 2}>
            {t("teams.create")}
          </Button>
        </form>
      )}
      {staff && (
        <Field label={t("teams.filter")}>
          <select value={status} onChange={(e) => setStatus(e.target.value)}>
            <option value="">{t("teams.all")}</option>
            {[
              "draft",
              "awaiting_approval",
              "approved",
              "rejected",
              "archived",
              "legacy",
            ].map((s) => (
              <option key={s} value={s}>
                {t(`teams.${s}`)}
              </option>
            ))}
          </select>
        </Field>
      )}
      <Button
        variant="outline"
        disabled={list.isFetching}
        onClick={() => list.refetch()}
      >
        {t("refresh")}
      </Button>
      {list.isPending && <Loading />}
      <ErrorNotice error={list.error} retry={() => list.refetch()} />
      {list.data?.pages[0].items.length === 0 && (
        <p className="panel">{t("teams.empty")}</p>
      )}
      {list.data?.pages
        .flatMap((p) => p.items)
        .map((team) => (
          <Link
            className="panel stack text-action"
            key={team.id}
            href={`/${area}/teams/${team.id}`}
          >
            <h2 className="underline" dir="auto">
              {team.name}
            </h2>
            <p>
              {t(`teams.${team.status}`)} · {team.members.length}{" "}
              {t("teams.members")}
            </p>
          </Link>
        ))}
      {list.hasNextPage && (
        <Button
          onClick={() => list.fetchNextPage()}
          disabled={list.isFetchingNextPage}
        >
          {t("teams.more")}
        </Button>
      )}
    </div>
  );
}

export function InvitationInbox() {
  const t = useTranslations();
  const inbox = useInfiniteQuery({
    queryKey: ["team-invitations"],
    initialPageParam: null as number | null,
    queryFn: ({ pageParam }) =>
      request<S["InvitationList"]>(
        `/team-invitations${pageParam ? "?before=" + pageParam : ""}`,
      ),
    getNextPageParam: (page) => page.next_cursor,
  });
  return (
    <div className="stack">
      <h1>{t("teams.inbox")}</h1>
      <p className="muted">{t("teams.previewHelp")}</p>
      <Button
        variant="outline"
        onClick={() => inbox.refetch()}
        disabled={inbox.isFetching}
      >
        {t("refresh")}
      </Button>
      {inbox.isPending && <Loading />}
      <ErrorNotice error={inbox.error} retry={() => inbox.refetch()} />
      {inbox.data?.pages[0].items.length === 0 && (
        <p className="panel">{t("teams.noInvitations")}</p>
      )}
      {inbox.data?.pages
        .flatMap((p) => p.items)
        .map((i) => (
          <Link
            className="panel underline text-action"
            href={`/student/teams/${i.team_id}`}
            key={i.id}
          >
            <bdi>{i.team_name}</bdi> · <Stamp value={i.created_at} />
          </Link>
        ))}
      {inbox.hasNextPage && (
        <Button
          onClick={() => inbox.fetchNextPage()}
          disabled={inbox.isFetchingNextPage}
        >
          {t("teams.more")}
        </Button>
      )}
    </div>
  );
}

export function TeamPage({ teamId, user }: { teamId: number; user: Identity }) {
  const t = useTranslations(),
    client = useQueryClient(),
    router = useRouter();
  const area = user.role === "student" ? "student" : "staff";
  const [number, setNumber] = useState("");
  const pending = useRef<{ signature: string; request_id: string } | null>(
    null,
  );
  const query = useQuery({
    queryKey: ["team", teamId],
    queryFn: () => request<S["TeamInfo"]>(`/teams/${teamId}`),
  });
  const mayReadHistory =
    !!query.data &&
    (area === "staff" ||
      query.data.created_by === user.id ||
      query.data.members.some((m) => m.student_id === user.id));
  const history = useInfiniteQuery({
    queryKey: ["team-history", teamId],
    enabled: mayReadHistory,
    initialPageParam: null as number | null,
    queryFn: ({ pageParam }) =>
      request<S["TeamEventList"]>(
        `/teams/${teamId}/history${pageParam ? "?before=" + pageParam : ""}`,
      ),
    getNextPageParam: (page) => page.next_cursor,
  });
  const mutation = useMutation({
    mutationFn: ({
      action,
      student_id,
      invitation_id,
    }: {
      action: string;
      student_id?: number;
      invitation_id?: number;
    }) => {
      const response = action === "accept" || action === "decline";
      const body = {
        expected_version: query.data!.version,
        ...(response ? { decision: action } : { action }),
        ...(action === "invite" ? { student_number: number } : {}),
        ...(student_id ? { student_id } : {}),
        ...(!response && invitation_id ? { invitation_id } : {}),
      };
      const path = response
        ? `/team-invitations/${invitation_id}/respond`
        : `/teams/${teamId}/actions`;
      const signature = JSON.stringify({ path, body });
      if (!pending.current || pending.current.signature !== signature)
        pending.current = { signature, request_id: crypto.randomUUID() };
      return request<S["TeamMutationResult"]>(path, {
        method: "POST",
        body: JSON.stringify({
          ...body,
          request_id: pending.current.request_id,
        }),
      });
    },
    onSuccess: (_, variables) => {
      pending.current = null;
      if (variables.action === "invite") setNumber("");
      if (variables.action === "leave" || variables.action === "decline")
        router.replace(`/student/tasks/${query.data!.task_id}/teams`);
    },
    onSettled: () => client.invalidateQueries(),
  });
  if (query.isPending) return <Loading />;
  if (query.error)
    return <ErrorNotice error={query.error} retry={() => query.refetch()} />;
  const team = query.data!,
    actions = team.actions;
  const mine = team.invitations.find((i) => i.student_id === user.id);
  const busy = mutation.isPending || query.isFetching;
  return (
    <div className="stack">
      <Link
        className="underline text-action"
        href={`/${area}/tasks/${team.task_id}/teams`}
      >
        {t("teams.title")}
      </Link>
      <h1 dir="auto">{team.name}</h1>
      {(area === "staff" ||
        team.members.some((m) => m.student_id === user.id)) && (
        <Link
          className="underline text-action"
          href={`/${area}/teams/${team.id}/repositories`}
        >
          {t("repos.title")}
        </Link>
      )}
      <p>
        {t(`teams.${team.status}`)} · {t("version")} {team.version}
      </p>
      <p className="muted">{t("teams.individual")}</p>
      <Button
        variant="outline"
        disabled={busy}
        onClick={() => {
          void query.refetch();
          if (mayReadHistory) void history.refetch();
        }}
      >
        {t("refresh")}
      </Button>
      {team.unavailable_reason && (
        <p className="panel">{t(`errors.${team.unavailable_reason}`)}</p>
      )}
      {team.locked_at && (
        <p>
          {t("teams.lockedAt")}: <Stamp value={team.locked_at} />
        </p>
      )}
      <ErrorNotice error={mutation.error} />
      {mutation.isSuccess && <p role="status">{t("teams.saved")}</p>}
      <section className="panel stack">
        <h2>{t("teams.roster")}</h2>
        <ul className="divide-y">
          {team.members.map((m) => (
            <li
              key={m.student_id}
              className="flex flex-wrap justify-between items-center gap-3 py-3"
            >
              <p>
                <bdi>{m.name}</bdi> · <bdi>{m.student_number}</bdi> ·{" "}
                {t(m.accepted_at ? "teams.accepted" : "teams.unconfirmed")}
              </p>
              {actions.includes("remove") &&
                m.student_id !== team.created_by && (
                  <Confirm
                    title={t("teams.remove")}
                    description={t("teams.rosterWarning")}
                    disabled={busy}
                    onConfirm={() =>
                      mutation.mutate({
                        action: "remove",
                        student_id: m.student_id,
                      })
                    }
                  />
                )}
            </li>
          ))}
        </ul>
        {team.invitations.map((i) => (
          <div
            key={i.id}
            className="flex flex-wrap justify-between items-center gap-3 border-t pt-3"
          >
            <p>
              <bdi>{i.name}</bdi> · {t("teams.pending")}
            </p>
            {actions.includes("cancel_invitation") && (
              <Confirm
                title={t("teams.cancel_invitation")}
                description={t("teams.rosterWarning")}
                disabled={busy}
                onConfirm={() =>
                  mutation.mutate({
                    action: "cancel_invitation",
                    invitation_id: i.id,
                  })
                }
              />
            )}
          </div>
        ))}
      </section>
      {mine && !team.unavailable_reason && (
        <section className="panel stack">
          <h2>{t("teams.respond")}</h2>
          <p>{t("teams.consent")}</p>
          <div className="flex flex-wrap gap-3">
            {["accept", "decline"].map((action) => (
              <Confirm
                key={action}
                title={t(`teams.${action}`)}
                description={t(
                  action === "accept"
                    ? "teams.consent"
                    : "teams.declineWarning",
                )}
                disabled={busy}
                onConfirm={() =>
                  mutation.mutate({ action, invitation_id: mine.id })
                }
              />
            ))}
          </div>
        </section>
      )}
      {actions.includes("invite") && (
        <form
          className="panel stack"
          onSubmit={(e) => {
            e.preventDefault();
            mutation.mutate({ action: "invite" });
          }}
        >
          <h2>{t("teams.invite")}</h2>
          <Field label={t("teams.studentNumber")}>
            <input
              dir="ltr"
              maxLength={50}
              value={number}
              disabled={busy}
              onChange={(e) => setNumber(e.target.value)}
            />
          </Field>
          <p className="muted text-sm">{t("teams.inviteHelp")}</p>
          <Button disabled={busy || !number.trim()}>
            {t("teams.sendInvitation")}
          </Button>
        </form>
      )}
      <div className="flex flex-wrap gap-3">
        {["request_approval", "approve", "reject", "leave", "archive"]
          .filter((a) => actions.includes(a))
          .map((action) => (
            <Confirm
              key={action}
              title={t(`teams.${action}`)}
              description={t(
                action === "approve"
                  ? "teams.approveWarning"
                  : action === "archive"
                    ? "teams.archiveWarning"
                    : "teams.rosterWarning",
              )}
              disabled={busy}
              onConfirm={() => mutation.mutate({ action })}
            />
          ))}
      </div>
      {area === "student" &&
        team.status === "approved" &&
        team.members.some((m) => m.student_id === user.id) && (
          <Link
            className="underline text-action"
            href={`/student/tasks/${team.task_id}/submit`}
          >
            {t("submit")}
          </Link>
        )}
      {mayReadHistory && (
        <details className="panel">
          <summary className="cursor-pointer font-semibold">
            {t("teams.history")}
          </summary>
          {history.isPending && <Loading />}
          <ErrorNotice error={history.error} retry={() => history.refetch()} />
          {history.data?.pages[0].items.length === 0 && (
            <p>{t("teams.noHistory")}</p>
          )}
          {history.data?.pages
            .flatMap((p) => p.items)
            .map((event) => (
              <div className="mt-3 border-t py-3" key={event.id}>
                <p>
                  {t(`teams.${event.action}`)} · {t("version")} {event.version}{" "}
                  · <Stamp value={event.created_at} />
                </p>
                <p dir="auto">
                  {event.roster.members.map((m) => m.name).join(" · ")}
                </p>
              </div>
            ))}
          {history.hasNextPage && (
            <Button
              variant="outline"
              disabled={history.isFetchingNextPage}
              onClick={() => history.fetchNextPage()}
            >
              {t("teams.more")}
            </Button>
          )}
        </details>
      )}
    </div>
  );
}
