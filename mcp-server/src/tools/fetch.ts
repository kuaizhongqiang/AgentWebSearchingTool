import { z } from "zod";
import type { EngineClient } from "../client.js";

export const FetchParamsSchema = z.object({
  url: z.string().url().describe("URL to fetch"),
  extract_mode: z.boolean().default(true).describe("Whether to extract main content"),
});

export type FetchParams = z.infer<typeof FetchParamsSchema>;

export async function handleWebFetch(client: EngineClient, params: FetchParams) {
  const result = await client.fetch(params.url, params.extract_mode);

  return {
    content: [
      {
        type: "text" as const,
        text: JSON.stringify(
          {
            url: result.url,
            status_code: result.status_code,
            title: result.title ?? "",
            text: result.text ?? "",
            fetched_with: result.fetched_with ?? "",
          },
          null,
          2
        ),
      },
    ],
  };
}
