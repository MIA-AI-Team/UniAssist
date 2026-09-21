"use client";
import { useEffect, useState } from "react";
import { useQuery, useQueryClient, useMutation } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { Link, useRouter, usePathname } from "@/i18n/navigation";
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
    client = useQueryClient(),
    pathname = usePathname();
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
  const home =
    user.role === "admin"
      ? "/admin"
      : user.role === "student"
        ? "/student"
        : "/staff";
  const inbox =
    user.role === "student" ? "/student/invitations" : "/staff/shared-tutoring";
  const navCurrent = (href: string) =>
    pathname === href || (href !== home && pathname.startsWith(href + "/"))
      ? ("page" as const)
      : undefined;
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
      <header className="workspace-header">
        <div className="workspace-width workspace-top">
          <Link
            href={
              user.role === "admin"
                ? "/admin"
                : user.role === "student"
                  ? "/student"
                  : "/staff"
            }
            className="brand"
            dir="ltr"
          >
            UniAssist<span className="text-action">.</span>
          </Link>
          <div className="workspace-utilities">
            <span className="workspace-identity">
              <bdi>{user.name}</bdi> · {t(user.role)}
            </span>
            <LanguageSwitch />
            <Button
              variant="ghost"
              disabled={logout.isPending}
              onClick={() => logout.mutate()}
            >
              {t("logout")}
            </Button>
          </div>
        </div>
        <nav
          aria-label={t("workspace")}
          className="workspace-width workspace-nav"
        >
          <Link
            href={home}
            aria-current={
              pathname.startsWith(home) && !pathname.startsWith(inbox)
                ? "page"
                : undefined
            }
          >
            {t(user.role === "admin" ? "accounts.adminTitle" : "desk.tasks")}
          </Link>
          {user.role !== "admin" && (
            <Link href={inbox} aria-current={navCurrent(inbox)}>
              {t(user.role === "student" ? "teams.inbox" : "tutor.sharedInbox")}
            </Link>
          )}
          <Link href="/profile" aria-current={navCurrent("/profile")}>
            {t("accounts.profile")}
          </Link>
        </nav>
      </header>
      <div className="demo-notice">
        <div className="workspace-width">{t("demo")}</div>
      </div>
      <main id="main" tabIndex={-1} className="workspace-width workspace-main">
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
      <footer className="workspace-width py-6 text-sm muted">
        UniAssist · {t("timezone")}
      </footer>
    </>
  );
}
