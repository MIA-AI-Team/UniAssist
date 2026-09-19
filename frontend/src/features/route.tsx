"use client";
import { useTranslations } from "next-intl";
import { Workspace } from "@/components/workspace";
import { TaskList, TaskPage } from "./tasks";
import { CreateTask } from "./create-task";
import { Review } from "./review";
import { Tutor } from "./tutor";
import { SharedTutoring } from "./tutor-sharing";
import { TaskInsights } from "./insights";
import { ProjectTeams, TeamPage, InvitationInbox } from "./teams";
import { RepositoryList, RepositoryPage } from "./repositories";
import { Profile, AdminWorkspace } from "./accounts";
export function FeatureRoute({ route }: { route: string[] }) {
  const t = useTranslations();
  const [area, section, id, action] = route;
  return (
    <Workspace area={area}>
      {(user, refreshIdentity) => {
        if (area === "profile" && route.length === 1)
          return <Profile user={user} onSaved={refreshIdentity} />;
        if (area === "admin")
          return <AdminWorkspace route={route} user={user} />;
        if (
          section === "repositories" &&
          /^\d+$/.test(id) &&
          route.length === 3
        )
          return (
            <RepositoryPage
              key={route.join("/")}
              repoId={Number(id)}
              user={user}
            />
          );
        if (
          section === "teams" &&
          /^\d+$/.test(id) &&
          action === "repositories" &&
          route.length === 4
        )
          return (
            <RepositoryList
              key={route.join("/")}
              teamId={Number(id)}
              user={user}
            />
          );
        if (
          area === "student" &&
          section === "invitations" &&
          route.length === 2
        )
          return <InvitationInbox />;
        if (section === "teams" && /^\d+$/.test(id) && route.length === 3)
          return (
            <TeamPage key={route.join("/")} teamId={Number(id)} user={user} />
          );
        if (
          section === "tasks" &&
          /^\d+$/.test(id) &&
          action === "teams" &&
          route.length === 4
        )
          return (
            <ProjectTeams
              key={route.join("/")}
              taskId={Number(id)}
              user={user}
            />
          );
        if (
          area === "staff" &&
          section === "tasks" &&
          /^\d+$/.test(id) &&
          action === "insights" &&
          route.length === 4
        )
          return <TaskInsights key={id} taskId={Number(id)} />;
        if (
          area === "staff" &&
          section === "shared-tutoring" &&
          (route.length === 2 || (route.length === 3 && /^\d+$/.test(id)))
        )
          return <SharedTutoring shareId={id ? Number(id) : undefined} />;
        if (
          area === "student" &&
          section === "tasks" &&
          /^\d+$/.test(id) &&
          action === "tutor" &&
          route.length === 4
        )
          return <Tutor key={route.join("/")} taskId={Number(id)} />;
        if (route.length === 1) return <TaskList staff={area === "staff"} />;
        if (
          area === "staff" &&
          section === "tasks" &&
          id === "new" &&
          route.length === 3
        )
          return <CreateTask />;
        if (
          section === "tasks" &&
          /^\d+$/.test(id) &&
          route.length <= 4 &&
          (!action || action === "submit")
        )
          return (
            <TaskPage
              id={Number(id)}
              user={user}
              submitting={action === "submit"}
            />
          );
        if (section === "submissions" && /^\d+$/.test(id) && route.length === 3)
          return <Review id={Number(id)} user={user} />;
        return <h1>{t("notFound")}</h1>;
      }}
    </Workspace>
  );
}
