import "server-only";
import { cookies } from "next/headers";
import { getIronSession, type SessionOptions } from "iron-session";
export interface Session {
  token?: string;
  expiresAt?: number;
}
export function options(): SessionOptions {
  const password = process.env.SESSION_SECRET;
  if (!password || password.length < 32)
    throw new Error("SESSION_SECRET must contain at least 32 characters.");
  return {
    password,
    cookieName: "uniassist_session",
    ttl: 3600,
    cookieOptions: {
      httpOnly: true,
      secure:
        new URL(process.env.APP_URL || "http://localhost:3000").protocol ===
        "https:",
      sameSite: "lax",
      path: "/",
    },
  };
}
export async function session() {
  return getIronSession<Session>(await cookies(), options());
}
export function sameOrigin(request: Request) {
  const expected = new URL(process.env.APP_URL || "http://localhost:3000")
    .origin;
  return (
    request.headers.get("origin") === expected &&
    request.headers.get("sec-fetch-site") !== "cross-site"
  );
}
export const privateHeaders = { "Cache-Control": "private, no-store" };
export async function upstream(path: string, init: RequestInit = {}) {
  const base = process.env.BACKEND_INTERNAL_URL || "http://localhost:8001";
  return fetch(base + path, {
    ...init,
    cache: "no-store",
    redirect: "manual",
    signal: AbortSignal.timeout(
      Number(process.env.BACKEND_TIMEOUT_MS || 180000),
    ),
  });
}
