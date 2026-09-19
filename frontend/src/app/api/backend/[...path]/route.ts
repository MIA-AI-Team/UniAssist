import { NextResponse } from "next/server";
import { readBody, BodyTooLarge } from "@/lib/server/body";
import {
  session,
  sameOrigin,
  upstream,
  privateHeaders,
} from "@/lib/server/session";
export const runtime = "nodejs";
const routes: [RegExp, string[]][] = [
  [/^auth\/me$/, ["GET", "PATCH"]],
  [/^admin\/users$/, ["GET"]],
  [/^admin\/users\/\d+$/, ["GET", "PATCH"]],
  [/^admin\/(audit|ai-metrics)$/, ["GET"]],
  [/^teams\/\d+\/repositories$/, ["GET", "POST"]],
  [/^repositories\/\d+$/, ["GET"]],
  [/^repositories\/\d+\/(commits|history)$/, ["GET"]],
  [/^repositories\/\d+\/(actions|snapshots)$/, ["POST"]],
  [/^repository-snapshots\/\d+(\/download)?$/, ["GET"]],
  [/^tasks\/\d+\/teams$/, ["GET", "POST"]],
  [/^teams\/\d+$/, ["GET"]],
  [/^teams\/\d+\/history$/, ["GET"]],
  [/^teams\/\d+\/actions$/, ["POST"]],
  [/^team-invitations$/, ["GET"]],
  [/^team-invitations\/\d+\/respond$/, ["POST"]],
  [/^tasks\/\d+\/grading-guidance$/, ["GET", "POST"]],
  [/^tasks\/\d+\/grading-guidance\/\d+$/, ["GET"]],
  [/^tasks\/\d+\/analytics$/, ["GET"]],
  [/^tasks\/\d+\/analytics\/reports$/, ["GET", "POST"]],
  [/^tasks\/\d+\/chat-sessions$/, ["GET", "POST"]],
  [/^chat-sessions\/\d+$/, ["GET"]],
  [/^chat-sessions\/\d+\/messages$/, ["GET", "POST"]],
  [/^chat-sessions\/\d+\/legacy-messages$/, ["GET"]],
  [/^chat-sessions\/\d+\/share-preview$/, ["GET"]],
  [/^chat-sessions\/\d+\/shares$/, ["GET", "POST"]],
  [/^chat-shares$/, ["GET"]],
  [/^chat-shares\/\d+$/, ["GET", "DELETE"]],
  [/^tasks\/\d+\/tutor-settings$/, ["GET", "PATCH"]],
  [/^auth\/register$/, ["POST"]],
  [/^tasks\/$/, ["GET", "POST"]],
  [/^tasks\/\d+$/, ["GET", "DELETE"]],
  [/^tasks\/\d+\/submissions$/, ["GET"]],
  [/^tasks\/\d+\/rubrics$/, ["GET"]],
  [/^tasks\/\d+\/rubrics\/(suggest|refine|create)$/, ["POST"]],
  [/^tasks\/\d+\/rubrics\/status$/, ["PATCH"]],
  [/^files\/upload$/, ["POST"]],
  [/^files\/\d+(\/download)?$/, ["GET"]],
  [/^submissions\/$/, ["POST"]],
  [/^submissions\/my\/\d+$/, ["GET"]],
  [/^submissions\/\d+$/, ["GET"]],
  [/^submissions\/\d+\/grade$/, ["POST"]],
  [/^submissions\/\d+\/confirm$/, ["PATCH"]],
];
async function handle(request: Request) {
  const url = new URL(request.url);
  // Only fixed, path-validated routes. No arbitrary URL, redirect or host forwarding.
  let path = url.pathname.slice("/api/backend/".length);
  if (path === "tasks" || path === "submissions") path += "/";
  if (
    !routes.some(
      ([pattern, methods]) =>
        pattern.test(path) && methods.includes(request.method),
    )
  )
    return NextResponse.json({ code: "not_found" }, { status: 404 });
  if (!["GET", "HEAD"].includes(request.method) && !sameOrigin(request))
    return NextResponse.json({ code: "permission_denied" }, { status: 403 });
  const auth = await session();
  const publicRoute = path === "auth/register";
  if (
    !publicRoute &&
    (!auth.token || !auth.expiresAt || auth.expiresAt <= Date.now() / 1000)
  ) {
    auth.destroy();
    return NextResponse.json(
      { code: "session_expired" },
      { status: 401, headers: privateHeaders },
    );
  }
  const headers = new Headers();
  if (!publicRoute) headers.set("Authorization", `Bearer ${auth.token}`);
  if (request.headers.has("content-type"))
    headers.set("Content-Type", request.headers.get("content-type")!);
  try {
    const body = request.method === "GET" ? undefined : await readBody(request);
    const response = await upstream("/" + path + url.search, {
      method: request.method,
      headers,
      body,
    });
    if (response.status === 401) auth.destroy();
    const resultHeaders = new Headers(privateHeaders);
    for (const key of ["content-type", "content-disposition", "x-error-code"])
      if (response.headers.has(key))
        resultHeaders.set(key, response.headers.get(key)!);
    if (response.status >= 300 && response.status < 400)
      return NextResponse.json({ code: "request_failed" }, { status: 502 });
    return new Response(response.status === 204 ? null : response.body, {
      status: response.status,
      headers: resultHeaders,
    });
  } catch (error) {
    if (error instanceof BodyTooLarge)
      return NextResponse.json(
        { code: "file_too_large" },
        { status: 413, headers: privateHeaders },
      );
    return NextResponse.json(
      { code: "backend_unavailable", ambiguous: request.method !== "GET" },
      { status: 503, headers: privateHeaders },
    );
  }
}
export { handle as GET, handle as POST, handle as PATCH, handle as DELETE };
