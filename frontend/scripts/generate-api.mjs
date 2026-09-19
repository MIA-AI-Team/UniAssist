import openapiTS, { astToString } from "openapi-typescript";
import { writeFile } from "node:fs/promises";
const url = process.env.API_SCHEMA_URL || "http://localhost:8001/openapi.json";
const response = await fetch(url);
if (!response.ok) throw new Error(`OpenAPI fetch failed: ${response.status}`);
const schema = await response.json();
await writeFile(
  new URL("../../backend/openapi.json", import.meta.url),
  JSON.stringify(schema, null, 2) + "\n",
);
await writeFile(
  new URL("../src/lib/api/schema.d.ts", import.meta.url),
  astToString(await openapiTS(schema)),
);
console.log("Generated transport types and OpenAPI snapshot from", url);
