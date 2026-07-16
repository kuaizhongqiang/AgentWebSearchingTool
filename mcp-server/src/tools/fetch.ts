import { z } from "zod";
import type { EngineClient } from "../client.js";

export const FetchParamsSchema = z.object({
  url: z.string().url().describe("URL to fetch"),
  extract_mode: z.boolean().default(true).describe("Extract main content"),
});

export type FetchParams = z.infer<typeof FetchParamsSchema>;

export async function handleWebFetch(client: EngineClient, params: FetchParams) {
  const result = await client.fetch(params.url, params.extract_mode);
  return {
    content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }],
  };
}
