"use client";
import { useQuery } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { request } from "@/lib/api/client";
import type { components } from "@/lib/api/schema";
import { ErrorNotice, Loading, Stamp } from "./common";

export function FileMetadata({ id }: { id: number }) {
  const t = useTranslations();
  const query = useQuery({
    queryKey: ["file", id],
    queryFn: () =>
      request<components["schemas"]["FileInfoResponse"]>(`/files/${id}`),
  });
  if (query.isPending) return <Loading />;
  if (query.error)
    return <ErrorNotice error={query.error} retry={() => query.refetch()} />;
  const file = query.data!;
  return (
    <div className="stack min-w-0 text-sm [overflow-wrap:anywhere]">
      <a
        className="text-teal-800 underline"
        href={`/api/backend/files/${id}/download`}
      >
        {t("download")}: <bdi>{file.file_name}</bdi>
      </a>
      <p>
        <bdi>{file.file_type}</bdi> · {t(`accounts.file_${file.purpose}`)} ·{" "}
        {file.size_bytes == null
          ? t("accounts.unknownSize")
          : t("accounts.bytes", { count: file.size_bytes })}
      </p>
      <Stamp value={file.uploaded_at} />
    </div>
  );
}
