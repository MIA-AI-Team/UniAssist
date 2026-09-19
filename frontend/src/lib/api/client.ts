export class ApiError extends Error {
  constructor(
    public code: string,
    public status: number,
    public detail?: unknown,
    public ambiguous = false,
  ) {
    super(code);
  }
}
export async function request<T>(
  path: string,
  init: RequestInit = {},
  sessionRoute = false,
): Promise<T> {
  const headers = new Headers(init.headers);
  if (init.body && !(init.body instanceof FormData))
    headers.set("Content-Type", "application/json");
  let response: Response;
  try {
    response = await fetch(
      sessionRoute ? "/api/session" : "/api/backend" + path,
      { ...init, headers, cache: "no-store" },
    );
  } catch {
    throw new ApiError(
      "backend_unavailable",
      503,
      undefined,
      !!init.method && init.method !== "GET",
    );
  }
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    if (response.status === 401 && !sessionRoute) {
      const locale =
        window.location.pathname.split("/")[1] === "ar" ? "ar" : "en";
      // A hard navigation deliberately destroys all in-memory academic query data.
      // eslint-disable-next-line @next/next/no-location-assign-relative-destination
      window.location.assign("/" + locale + "/login?expired=1");
    }
    throw new ApiError(
      error.code ||
        (response.status === 422 ? "invalid_input" : "request_failed"),
      response.status,
      error.detail,
      error.ambiguous,
    );
  }
  if (response.status === 204) return undefined as T;
  return response.json();
}
export async function upload(
  file: File,
  purpose: "reference" | "submission",
  taskId?: number,
) {
  const data = new FormData();
  data.set("file", file);
  data.set("purpose", purpose);
  if (taskId) data.set("task_id", String(taskId));
  return request<{ file_id: number }>("/files/upload", {
    method: "POST",
    body: data,
  });
}
