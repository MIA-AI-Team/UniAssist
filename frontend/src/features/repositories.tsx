"use client";
import { useRef, useState } from "react";
import {
  useInfiniteQuery,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { Link } from "@/i18n/navigation";
import { request } from "@/lib/api/client";
import type { components } from "@/lib/api/schema";
import type { Identity } from "@/lib/api/types";
import { Button } from "@/components/ui/button";
import { Confirm } from "@/components/ui/confirm";
import { ErrorNotice, Field, Loading, Stamp } from "@/components/common";
type S = components["schemas"];

function useRequestId() {
  const pending = useRef({ signature: "", id: "" });
  return (body: unknown) => {
    const signature = JSON.stringify(body);
    if (pending.current.signature !== signature)
      pending.current = { signature, id: crypto.randomUUID() };
    return pending.current.id;
  };
}

export function RepositoryList({
  teamId,
  user,
}: {
  teamId: number;
  user: Identity;
}) {
  const t = useTranslations(),
    client = useQueryClient(),
    requestId = useRequestId();
  const [url, setUrl] = useState("");
  const area = user.role === "student" ? "student" : "staff";
  const team = useQuery({
    queryKey: ["team", teamId],
    queryFn: () => request<S["TeamInfo"]>(`/teams/${teamId}`),
  });
  const list = useInfiniteQuery({
    queryKey: ["repositories", teamId],
    initialPageParam: null as number | null,
    queryFn: ({ pageParam }) =>
      request<S["RepositoryList"]>(
        `/teams/${teamId}/repositories${pageParam ? "?before=" + pageParam : ""}`,
      ),
    getNextPageParam: (p) => p.next_cursor,
  });
  const proposal = useMutation({
    mutationFn: () =>
      request<S["RepositoryInfo"]>(`/teams/${teamId}/repositories`, {
        method: "POST",
        body: JSON.stringify({ repo_url: url, request_id: requestId(url) }),
      }),
    onSuccess: () => setUrl(""),
    onSettled: () =>
      client.invalidateQueries({ queryKey: ["repositories", teamId] }),
  });
  const repositories = list.data?.pages.flatMap((page) => page.items) ?? [];
  return (
    <div className="stack">
      <Link className="underline text-action" href={`/${area}/teams/${teamId}`}>
        {t("teams.title")}
      </Link>
      <h1>{t("repos.title")}</h1>
      <p>{t("repos.help")}</p>
      <p className="notice">{t("repos.noScoring")}</p>
      {team.data?.status !== "approved" && (
        <p>{t("errors.team_not_approved")}</p>
      )}
      {area === "student" && team.data?.status === "approved" && (
        <form
          className="action-well stack"
          onSubmit={(e) => {
            e.preventDefault();
            proposal.mutate();
          }}
        >
          <Field label={t("repos.url")}>
            <input
              dir="ltr"
              value={url}
              maxLength={250}
              disabled={proposal.isPending}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://github.com/owner/repository"
            />
          </Field>
          <p>{t("repos.publicWarning")}</p>
          <ErrorNotice error={proposal.error} />
          <Button disabled={proposal.isPending || !url.trim()}>
            {t("repos.propose")}
          </Button>
        </form>
      )}
      <Button
        variant="outline"
        disabled={list.isFetching}
        onClick={() => list.refetch()}
      >
        {t("refresh")}
      </Button>
      {(list.isPending || team.isPending) && <Loading />}
      <ErrorNotice
        error={list.error || team.error}
        retry={() => {
          void list.refetch();
          void team.refetch();
        }}
      />
      {!list.isPending && repositories.length === 0 && (
        <p className="notice">{t("repos.empty")}</p>
      )}
      {!!repositories.length && (
        <div className="record-list">
          {repositories.map((repository) => (
            <Link
              className="record-row record-row-link"
              key={repository.id}
              href={`/${area}/repositories/${repository.id}`}
            >
              <div className="record-copy">
                <bdi className="record-title break-all">
                  {repository.full_name || t("repos.legacy")}
                </bdi>
                {repository.is_fixture && (
                  <p className="record-description">{t("repos.fixture")}</p>
                )}
              </div>
              <span className="record-trailing">
                {t(`repos.${repository.status}`)}
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
          {t("teams.more")}
        </Button>
      )}
    </div>
  );
}

export function SnapshotSummary({ snapshot }: { snapshot: S["SnapshotInfo"] }) {
  const t = useTranslations(),
    p = snapshot.provenance;
  return (
    <section className="document-section stack">
      <h2>{t("repos.snapshot")}</h2>
      {p.is_fixture && (
        <p className="notice notice-warning">{t("repos.fixture")}</p>
      )}
      <dl className="summary-list">
        <div className="summary-row">
          <dt className="summary-key">{t("repos.url")}</dt>
          <dd className="summary-value break-all" dir="ltr">
            {p.repo_url}
          </dd>
        </div>
        <div className="summary-row">
          <dt className="summary-key">{t("repos.sha")}</dt>
          <dd className="summary-value">
            <bdi className="break-all font-mono">{p.commit_sha}</bdi>
          </dd>
        </div>
        <div className="summary-row">
          <dt className="summary-key">{t("repos.captured")}</dt>
          <dd className="summary-value">
            <Stamp value={p.captured_at} />
          </dd>
        </div>
        <div className="summary-row">
          <dt className="summary-key">{t("repos.manifest")}</dt>
          <dd className="summary-value">
            {t("repos.omitted", { count: p.omitted_files })}
          </dd>
        </div>
      </dl>
      <p className="muted">{t("repos.snapshotHelp")}</p>
      <a
        className="underline text-action"
        href={`/api/backend/repository-snapshots/${snapshot.id}/download`}
      >
        {t("repos.download")}
      </a>
      <details className="disclosure-section">
        <summary>{t("repos.manifest")}</summary>
        <div className="disclosure-content stack">
          <p className="break-all font-mono" dir="ltr">
            SHA-256: {p.archive_sha256}
          </p>
          <ul className="record-list">
            {p.files.map((file) => (
              <li className="record-row" key={file.path}>
                <div className="record-copy">
                  <bdi className="record-title break-all">{file.path}</bdi>
                  <p className="record-description">
                    {file.size} {t("repos.bytes")}
                  </p>
                </div>
                <span className="record-trailing">
                  {t(file.included ? "repos.included" : "repos.excluded")}
                </span>
              </li>
            ))}
          </ul>
        </div>
      </details>
    </section>
  );
}

export function RepositoryPage({
  repoId,
  user,
}: {
  repoId: number;
  user: Identity;
}) {
  const t = useTranslations(),
    client = useQueryClient(),
    requestId = useRequestId(),
    captureId = useRequestId();
  const area = user.role === "student" ? "student" : "staff";
  const [sha, setSha] = useState(""),
    [attributions, setAttributions] = useState<Record<number, string>>({});
  const query = useQuery({
    queryKey: ["repository", repoId],
    queryFn: () => request<S["RepositoryInfo"]>(`/repositories/${repoId}`),
  });
  const team = useQuery({
    queryKey: ["team", query.data?.team_id],
    enabled: !!query.data,
    queryFn: () => request<S["TeamInfo"]>(`/teams/${query.data!.team_id}`),
  });
  const commits = useInfiniteQuery({
    queryKey: ["commits", repoId],
    initialPageParam: null as number | null,
    queryFn: ({ pageParam }) =>
      request<S["CommitList"]>(
        `/repositories/${repoId}/commits${pageParam ? "?before=" + pageParam : ""}`,
      ),
    getNextPageParam: (p) => p.next_cursor,
  });
  const history = useInfiniteQuery({
    queryKey: ["repository-history", repoId],
    initialPageParam: null as number | null,
    queryFn: ({ pageParam }) =>
      request<S["RepositoryEventList"]>(
        `/repositories/${repoId}/history${pageParam ? "?before=" + pageParam : ""}`,
      ),
    getNextPageParam: (p) => p.next_cursor,
  });
  const action = useMutation({
    mutationFn: (fields: {
      action: string;
      commit_id?: number;
      student_id?: number | null;
    }) => {
      const body = { ...fields, expected_version: query.data!.version };
      return request(`/repositories/${repoId}/actions`, {
        method: "POST",
        body: JSON.stringify({ ...body, request_id: requestId(body) }),
      });
    },
    onSettled: () => client.invalidateQueries(),
  });
  const capture = useMutation({
    mutationFn: () =>
      request<S["SnapshotInfo"]>(`/repositories/${repoId}/snapshots`, {
        method: "POST",
        body: JSON.stringify({
          commit_sha: sha,
          request_id: captureId({ sha, version: query.data?.version }),
        }),
      }),
  });
  if (query.isPending) return <Loading />;
  if (query.error)
    return <ErrorNotice error={query.error} retry={() => query.refetch()} />;
  const repo = query.data!,
    busy = action.isPending || capture.isPending || query.isFetching;
  return (
    <div className="stack">
      <Link
        className="underline text-action"
        href={`/${area}/teams/${repo.team_id}/repositories`}
      >
        {t("repos.title")}
      </Link>
      <h1 className="break-all" dir="auto">
        {repo.full_name || t("repos.legacy")}
      </h1>
      <dl className="summary-list">
        <div className="summary-row">
          <dt className="summary-key">{t("status")}</dt>
          <dd className="summary-value">{t(`repos.${repo.status}`)}</dd>
        </div>
        <div className="summary-row">
          <dt className="summary-key">{t("version")}</dt>
          <dd className="summary-value">{repo.version}</dd>
        </div>
        <div className="summary-row">
          <dt className="summary-key">{t("repos.lastSync")}</dt>
          <dd className="summary-value">
            {repo.last_synced_at ? <Stamp value={repo.last_synced_at} /> : "—"}
          </dd>
        </div>
        <div className="summary-row">
          <dt className="summary-key">{t("repos.commits")}</dt>
          <dd className="summary-value">
            {t(repo.partial_history ? "repos.partial" : "repos.bounded")}
          </dd>
        </div>
      </dl>
      {repo.is_fixture && (
        <p className="notice notice-warning">{t("repos.fixture")}</p>
      )}
      <p>{t("repos.noScoring")}</p>
      {repo.unavailable_reason && (
        <p className="notice">{t(`errors.${repo.unavailable_reason}`)}</p>
      )}
      {repo.sync_error && <p role="status">{t(`errors.${repo.sync_error}`)}</p>}
      <Button
        variant="outline"
        disabled={busy}
        onClick={() => client.invalidateQueries()}
      >
        {t("refresh")}
      </Button>
      <ErrorNotice error={action.error} />
      {action.isSuccess && <p role="status">{t("repos.saved")}</p>}
      {repo.actions.some((actionName) =>
        ["approve", "reject", "sync"].includes(actionName),
      ) && (
        <div className="action-well flex flex-wrap gap-3">
          {["approve", "reject"]
            .filter((a) => repo.actions.includes(a))
            .map((a) => (
              <Confirm
                key={a}
                title={t(`repos.${a}`)}
                description={t("repos.approvalWarning")}
                disabled={busy}
                onConfirm={() => action.mutate({ action: a })}
              />
            ))}
          {repo.actions.includes("sync") && (
            <Button
              disabled={busy}
              onClick={() => action.mutate({ action: "sync" })}
            >
              {t(action.isPending ? "working" : "repos.sync")}
            </Button>
          )}
        </div>
      )}
      <section className="document-section stack">
        <h2>{t("repos.commits")}</h2>
        {commits.isPending && <Loading />}
        <ErrorNotice error={commits.error} retry={() => commits.refetch()} />
        {commits.data?.pages[0].items.length === 0 && (
          <p>{t("repos.noCommits")}</p>
        )}
        {commits.data?.pages
          .flatMap((p) => p.items)
          .map((commit) => (
            <article className="record-row record-row-wide" key={commit.id}>
              <div className="record-copy stack">
                <p className="break-all font-mono" dir="ltr">
                  {commit.commit_hash}
                </p>
                <p dir="auto" className="whitespace-pre-wrap break-words">
                  {commit.message}
                </p>
                <p>
                  <bdi>{commit.author_name}</bdi> ·{" "}
                  <bdi>{commit.author_github_username || "—"}</bdi> ·{" "}
                  <Stamp value={commit.committed_at} />
                </p>
                <p>
                  {commit.attributed_at
                    ? t("repos.attributed", {
                        student:
                          team.data?.members.find(
                            (m) => m.student_id === commit.student_id,
                          )?.name || String(commit.student_id ?? "—"),
                      })
                    : t("repos.unverified")}
                </p>
                {(repo.actions.includes("attribute") ||
                  repo.actions.includes("snapshot")) && (
                  <div className="task-actions">
                    {repo.actions.includes("attribute") && (
                      <div className="stack min-w-[min(100%,20rem)]">
                        <Field label={t("repos.attribution")}>
                          <select
                            disabled={busy}
                            value={
                              attributions[commit.id] ??
                              String(commit.student_id ?? "")
                            }
                            onChange={(e) =>
                              setAttributions({
                                ...attributions,
                                [commit.id]: e.target.value,
                              })
                            }
                          >
                            <option value="">{t("repos.unassigned")}</option>
                            {team.data?.members.map((m) => (
                              <option key={m.student_id} value={m.student_id}>
                                {m.name} — {m.student_number}
                              </option>
                            ))}
                          </select>
                        </Field>
                        <Confirm
                          title={t("repos.attribute")}
                          description={t("repos.attributionWarning")}
                          disabled={busy || !team.data}
                          onConfirm={() =>
                            action.mutate({
                              action: "attribute",
                              commit_id: commit.id,
                              student_id:
                                Number(
                                  attributions[commit.id] ?? commit.student_id,
                                ) || null,
                            })
                          }
                        />
                      </div>
                    )}
                    {repo.actions.includes("snapshot") && (
                      <Button
                        variant="outline"
                        disabled={busy}
                        onClick={() => setSha(commit.commit_hash)}
                      >
                        {t("repos.selectCommit")}
                      </Button>
                    )}
                  </div>
                )}
              </div>
            </article>
          ))}
        {commits.hasNextPage && (
          <Button
            disabled={commits.isFetchingNextPage}
            onClick={() => commits.fetchNextPage()}
          >
            {t("teams.more")}
          </Button>
        )}
      </section>
      {repo.actions.includes("snapshot") && (
        <form
          className="action-well stack"
          onSubmit={(e) => {
            e.preventDefault();
            capture.mutate();
          }}
        >
          <h2>{t("repos.capture")}</h2>
          <p>{t("repos.captureHelp")}</p>
          <Field label={t("repos.sha")}>
            <input
              dir="ltr"
              className="font-mono"
              value={sha}
              maxLength={40}
              disabled={busy}
              onChange={(e) => setSha(e.target.value)}
            />
          </Field>
          <ErrorNotice error={capture.error} />
          <Button disabled={busy || !/^[0-9a-f]{40}$/.test(sha)}>
            {t(capture.isPending ? "working" : "repos.capture")}
          </Button>
        </form>
      )}
      {capture.data && (
        <>
          <SnapshotSummary snapshot={capture.data} />
          <Link
            className="underline text-action"
            href={`/student/tasks/${repo.task_id}/submit?snapshot=${capture.data.id}`}
          >
            {t("repos.useSnapshot")}
          </Link>
        </>
      )}
      <details className="disclosure-section">
        <summary>{t("repos.history")}</summary>
        <div className="disclosure-content stack">
          <ErrorNotice error={history.error} retry={() => history.refetch()} />
          {history.isPending && <Loading />}
          <ol className="history-list">
            {history.data?.pages
              .flatMap((p) => p.items)
              .map((event) => (
                <li className="history-row" key={event.id}>
                  <p>
                    {t(`repos.${event.action}`)} · {t("version")}{" "}
                    {event.version} · <Stamp value={event.created_at} />
                  </p>
                  {event.action === "attribute" && (
                    <p className="record-description">
                      {t("repos.attributionChange", {
                        from: String(event.details.previous_student_id ?? "—"),
                        to: String(event.details.student_id ?? "—"),
                      })}
                    </p>
                  )}
                </li>
              ))}
          </ol>
          {history.hasNextPage && (
            <Button
              disabled={history.isFetchingNextPage}
              onClick={() => history.fetchNextPage()}
            >
              {t("teams.more")}
            </Button>
          )}
        </div>
      </details>
    </div>
  );
}
