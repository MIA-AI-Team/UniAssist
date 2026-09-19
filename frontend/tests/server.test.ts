import { describe, it, expect, vi } from "vitest";
vi.mock("server-only", () => ({}));
import { readBody, BodyTooLarge } from "../src/lib/server/body";

describe("bounded API request bodies", () => {
  it("preserves bytes below the limit", async () => {
    const request = new Request("http://localhost", {
      method: "POST",
      body: "hello",
    });
    expect(new TextDecoder().decode(await readBody(request, 10))).toBe("hello");
  });
  it("rejects oversized declared bodies before reading", async () => {
    const request = new Request("http://localhost", {
      method: "POST",
      headers: { "content-length": "100" },
      body: "hello",
    });
    await expect(readBody(request, 10)).rejects.toBeInstanceOf(BodyTooLarge);
  });
  it("rejects oversized bodies without Content-Length", async () => {
    const request = new Request("http://localhost", {
      method: "POST",
      body: "too long",
    });
    await expect(readBody(request, 3)).rejects.toBeInstanceOf(BodyTooLarge);
  });
});
