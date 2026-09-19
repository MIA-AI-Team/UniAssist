"use client";
import { useState } from "react";
import { useForm, useWatch } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { useTranslations } from "next-intl";
import { useQueryClient } from "@tanstack/react-query";
import { Link, useRouter } from "@/i18n/navigation";
import { request, upload, ApiError } from "@/lib/api/client";
import type { Task } from "@/lib/api/types";
import { Button } from "@/components/ui/button";
import { Field, ErrorNotice } from "@/components/common";
export function CreateTask() {
  const t = useTranslations(),
    router = useRouter(),
    client = useQueryClient();
  const [file, setFile] = useState<File>(),
    [fileId, setFileId] = useState<number>(),
    [error, setError] = useState<unknown>(),
    [stage, setStage] = useState(""),
    [uncertain, setUncertain] = useState(false);
  const [reconciledTasks, setReconciledTasks] = useState<Task[]>([]);
  const schema = z
    .object({
      type: z.enum(["lab", "assignment", "project"]),
      title: z.string().min(1, t("fieldInvalid")),
      description: z.string().min(1, t("fieldInvalid")),
      due_date: z.string().min(1, t("fieldInvalid")),
      scheduled_date: z.string(),
      target_cohort_year: z.string().regex(/^\d+$/, t("fieldInvalid")),
      target_major: z.string(),
      allowed_file_types: z.string().min(1, t("fieldInvalid")),
      allow_late: z.boolean(),
      require_team: z.boolean(),
      default_repo_provider: z.string(),
    })
    .superRefine((v, ctx) => {
      if (
        v.type === "lab" &&
        (!v.scheduled_date || new Date(v.due_date) < new Date(v.scheduled_date))
      )
        ctx.addIssue({
          code: "custom",
          path: ["scheduled_date"],
          message: t("errors.invalid_dates"),
        });
    });
  const form = useForm<z.infer<typeof schema>>({
    resolver: zodResolver(schema),
    defaultValues: {
      type: "assignment",
      title: "",
      description: "",
      due_date: "",
      scheduled_date: "",
      target_cohort_year: "",
      target_major: "",
      allowed_file_types: "pdf, zip",
      allow_late: false,
      require_team: true,
      default_repo_provider: "github",
    },
  });
  const type = useWatch({ control: form.control, name: "type" });
  const submit = form.handleSubmit(async (values) => {
    setError(undefined);
    try {
      let reference = fileId;
      if (values.type === "lab" && !reference) {
        if (!file) throw new ApiError("lab_fields_required", 422);
        setStage("uploading");
        reference = (await upload(file, "reference")).file_id;
        setFileId(reference);
      }
      setStage("working");
      const result = await request<{ id: number }>("/tasks/", {
        method: "POST",
        body: JSON.stringify({
          ...values,
          due_date: new Date(values.due_date).toISOString(),
          scheduled_date:
            values.type === "lab"
              ? new Date(values.scheduled_date).toISOString()
              : null,
          target_cohort_year: Number(values.target_cohort_year),
          target_major: values.target_major.trim() || null,
          allowed_file_types: values.allowed_file_types
            .split(",")
            .map((x) => x.trim().toLowerCase().replace(/^\./, ""))
            .filter(Boolean),
          reference_file_id: values.type === "lab" ? reference : null,
        }),
      });
      await client.invalidateQueries({ queryKey: ["tasks"] });
      router.push("/staff/tasks/" + result.id);
    } catch (e) {
      setError(e);
      setUncertain(e instanceof ApiError && e.ambiguous);
      if (e instanceof ApiError && Array.isArray(e.detail)) {
        for (const issue of e.detail) {
          const key = issue.loc?.at(-1) as keyof z.infer<typeof schema>;
          if (key in values) form.setError(key, { message: t("fieldInvalid") });
        }
      }
    } finally {
      setStage("");
    }
  });
  const field = (key: keyof z.infer<typeof schema>, type = "text") => (
    <Field
      label={t(
        key === "target_cohort_year"
          ? "cohort_year"
          : key === "target_major"
            ? "major"
            : key === "due_date"
              ? "due"
              : key === "scheduled_date"
                ? "scheduled"
                : key === "allowed_file_types"
                  ? "allowedTypes"
                  : key === "default_repo_provider"
                    ? "repoProvider"
                    : key,
      )}
      error={form.formState.errors[key]?.message}
    >
      <input
        type={type}
        aria-invalid={!!form.formState.errors[key]}
        {...form.register(key)}
      />
    </Field>
  );
  return (
    <div className="mx-auto max-w-3xl stack">
      <Link href="/staff" className="text-teal-800 underline">
        {t("back")}
      </Link>
      <h1>{t("createTask")}</h1>
      <p className="muted">{t("taskSetup")}</p>
      <form className="panel stack" onSubmit={submit} noValidate>
        <Field label={t("type")}>
          <select {...form.register("type")}>
            {["lab", "assignment", "project"].map((v) => (
              <option key={v} value={v}>
                {t(v)}
              </option>
            ))}
          </select>
        </Field>
        {field("title")}
        <Field
          label={t("description")}
          error={form.formState.errors.description?.message}
        >
          <textarea rows={6} dir="auto" {...form.register("description")} />
        </Field>
        <div className="grid gap-5 sm:grid-cols-2">
          {field("due_date", "datetime-local")}
          {field("target_cohort_year", "number")}
        </div>
        {field("target_major")}
        {type === "lab" && (
          <>
            {field("scheduled_date", "datetime-local")}
            <Field label={t("referenceFile")}>
              <input
                type="file"
                accept=".pdf"
                onChange={(e) => {
                  setFile(e.target.files?.[0]);
                  setFileId(undefined);
                }}
              />
            </Field>
          </>
        )}
        {type === "assignment" && (
          <>
            {field("allowed_file_types")}
            <label className="!flex items-center gap-3">
              <input type="checkbox" {...form.register("allow_late")} />
              {t("allowLate")}
            </label>
          </>
        )}
        {type === "project" && (
          <>
            {field("default_repo_provider")}
            <label className="!flex items-center gap-3">
              <input type="checkbox" {...form.register("require_team")} />
              {t("requireTeam")}
            </label>
          </>
        )}
        <ErrorNotice error={error} />
        {stage && <p role="status">{t(stage)}</p>}
        {fileId && !stage && <p>{t("uploaded")}</p>}
        {uncertain && (
          <Button
            type="button"
            variant="outline"
            onClick={async () => {
              try {
                const tasks = await request<Task[]>("/tasks/");
                client.setQueryData(["tasks", ""], tasks);
                setReconciledTasks(
                  tasks.filter(
                    (task) => task.title === form.getValues("title"),
                  ),
                );
                setUncertain(false);
              } catch (error) {
                setError(error);
              }
            }}
          >
            {t("refresh")}
          </Button>
        )}
        {reconciledTasks.map((task) => (
          <Link
            key={task.id}
            className="text-teal-800 underline"
            href={"/staff/tasks/" + task.id}
          >
            {t("openTask")}: {task.title}
          </Link>
        ))}
        <Button disabled={form.formState.isSubmitting || uncertain}>
          {t(form.formState.isSubmitting ? "working" : "createTask")}
        </Button>
      </form>
    </div>
  );
}
