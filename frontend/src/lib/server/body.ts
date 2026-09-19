import "server-only";

export class BodyTooLarge extends Error {}

/** Bound memory use even when a client omits Content-Length. */
export async function readBody(request: Request, limit = 26 * 1024 * 1024) {
  if (Number(request.headers.get("content-length")) > limit)
    throw new BodyTooLarge();
  if (!request.body) return undefined;
  const reader = request.body.getReader();
  const chunks: Uint8Array[] = [];
  let size = 0;
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      size += value.byteLength;
      if (size > limit) {
        await reader.cancel();
        throw new BodyTooLarge();
      }
      chunks.push(value);
    }
  } finally {
    reader.releaseLock();
  }
  const body = new Uint8Array(size);
  let offset = 0;
  for (const chunk of chunks) {
    body.set(chunk, offset);
    offset += chunk.byteLength;
  }
  return body.buffer;
}
