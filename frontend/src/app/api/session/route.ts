import { NextResponse } from "next/server";
import {
  session,
  sameOrigin,
  upstream,
  privateHeaders,
} from "@/lib/server/session";
export const runtime = "nodejs";
export async function GET() {
  const auth = await session();
  if (!auth.token || !auth.expiresAt || auth.expiresAt <= Date.now() / 1000) {
    auth.destroy();
    return NextResponse.json(
      { code: "session_expired" },
      { status: 401, headers: privateHeaders },
    );
  }
  try {
    const response = await upstream("/auth/me", {
      headers: { Authorization: `Bearer ${auth.token}` },
    });
    if (response.status === 401) auth.destroy();
    return new Response(await response.text(), {
      status: response.status,
      headers: { ...privateHeaders, "Content-Type": "application/json" },
    });
  } catch {
    return NextResponse.json(
      { code: "backend_unavailable" },
      { status: 503, headers: privateHeaders },
    );
  }
}
export async function POST(request: Request) {
  if (!sameOrigin(request))
    return NextResponse.json({ code: "permission_denied" }, { status: 403 });
  try {
    const response = await upstream("/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: await request.text(),
    });
    const data = await response.json();
    if (!response.ok)
      return NextResponse.json(data, {
        status: response.status,
        headers: privateHeaders,
      });
    const exp = JSON.parse(
      Buffer.from(data.access_token.split(".")[1], "base64url").toString(),
    ).exp;
    const ttl = Math.floor(exp - Date.now() / 1000);
    if (!Number.isFinite(ttl) || ttl <= 0)
      return NextResponse.json({ code: "session_expired" }, { status: 401 });
    const auth = await session();
    auth.updateConfig({ ...authOptions(ttl) });
    auth.token = data.access_token;
    auth.expiresAt = exp;
    await auth.save();
    return NextResponse.json(
      { id: data.user_id, role: data.role, name: data.name },
      { headers: privateHeaders },
    );
  } catch {
    return NextResponse.json(
      { code: "backend_unavailable" },
      { status: 503, headers: privateHeaders },
    );
  }
}
import { options } from "@/lib/server/session";
function authOptions(ttl: number) {
  const config = options();
  return {
    ...config,
    ttl,
    cookieOptions: { ...config.cookieOptions, maxAge: ttl },
  };
}
export async function DELETE(request: Request) {
  if (!sameOrigin(request))
    return NextResponse.json({ code: "permission_denied" }, { status: 403 });
  (await session()).destroy();
  return new Response(null, { status: 204, headers: privateHeaders });
}
