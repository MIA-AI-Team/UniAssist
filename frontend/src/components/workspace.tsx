"use client";
import { useEffect, useState } from "react";
import { useQuery, useQueryClient, useMutation } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { Link, useRouter } from "@/i18n/navigation";
import { request, ApiError } from "@/lib/api/client";
import type { Identity } from "@/lib/api/types";
import { Button } from "./ui/button";
import { ErrorNotice, LanguageSwitch, Loading } from "./common";
import { Providers } from "./providers";
export function Workspace({
  area,
  children,
}: {
  area: string;
  children: (
    user: Identity,
    refreshIdentity: () => Promise<unknown>,
  ) => React.ReactNode;
}) {
  const t = useTranslations(),
    router = useRouter(),
    client = useQueryClient();
  const [signingOut, setSigningOut] = useState(false);
  const auth = useQuery({
    queryKey: ["session"],
    queryFn: () => request<Identity>("", {}, true),
    staleTime: 0,
    refetchInterval: 60000,
    enabled: !signingOut,
  });
  useEffect(() => {
    if (
      !signingOut &&
      auth.error instanceof ApiError &&
      auth.error.status === 401
    ) {
      client.clear();
      router.replace("/login?expired=1");
    }
  }, [auth.error, client, router, signingOut]);
  const logout = useMutation({
    onMutate: () => setSigningOut(true),
    onError: () => setSigningOut(false),
    mutationFn: () => request("", { method: "DELETE" }, true),
    onSuccess: () => {
      client.clear();
      router.replace("/login");
    },
  });
  if (auth.isPending) return <Loading />;
  if (auth.error)
    return (
      <main className="mx-auto max-w-3xl p-8">
        <ErrorNotice error={auth.error} retry={() => auth.refetch()} />
      </main>
    );
  const user = auth.data!;
  const permitted =
    area === "profile"
      ? true
      : area === "admin"
        ? user.role === "admin"
        : area === "student"
          ? user.role === "student"
          : area === "staff"
            ? ["professor", "teaching_assistant"].includes(user.role)
            : false;
  return (
    <>
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:fixed focus:z-50 focus:bg-white focus:p-3"
      >
        {t("skip")}
      </a>
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 px-5 py-4">
          <Link
            href={
              user.role === "admin"
                ? "/admin"
                : user.role === "student"
                  ? "/student"
                  : "/staff"
            }
            className="text-xl font-bold"
          >
            UniAssist<span className="text-teal-700">.</span>
          </Link>
          <nav
            aria-label={t("workspace")}
            className="flex flex-wrap items-center gap-3"
          >
            <span className="text-sm muted">
              <bdi>{user.name}</bdi> · {t(user.role)}
            </span>
            <LanguageSwitch />
            <Link className="text-sm underline text-teal-800" href="/profile">
              {t("accounts.profile")}
            </Link>
            {user.role === "student" && (
              <Link
                className="text-sm underline text-teal-800"
                href="/student/invitations"
              >
                {t("teams.inbox")}
              </Link>
            )}
            {["professor", "teaching_assistant"].includes(user.role) && (
              <Link
                className="text-sm underline text-teal-800"
                href="/staff/shared-tutoring"
              >
                {t("tutor.sharedInbox")}
              </Link>
            )}
            <Button
              variant="ghost"
              disabled={logout.isPending}
              onClick={() => logout.mutate()}
            >
              {t("logout")}
            </Button>
          </nav>
        </div>
      </header>
      <div className="border-b border-amber-200 bg-amber-50 px-5 py-2 text-center text-xs text-amber-900">
        {t("demo")}
      </div>
      <main id="main" className="mx-auto max-w-7xl px-5 py-8 lg:py-12">
        <ErrorNotice error={logout.error} />
        {permitted ? (
          <Providers
            key={`${user.id}:${user.role}:${user.cohort_year}:${user.major}`}
          >
            {children(user, () => auth.refetch())}
          </Providers>
        ) : (
          <div className="panel">
            <h1>{t(user.role === "admin" ? "unavailable" : "permission")}</h1>
            <Button asChild variant="outline">
              <Link
                href={
                  user.role === "admin"
                    ? "/admin"
                    : user.role === "student"
                      ? "/student"
                      : "/staff"
                }
              >
                {t("back")}
              </Link>
            </Button>
          </div>
        )}
      </main>
      <footer className="mx-auto max-w-7xl px-5 py-6 text-xs muted">
        UniAssist · {t("timezone")}
      </footer>
    </>
  );
}
