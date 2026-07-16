import { z } from "zod";
import type { EngineClient } from "../client.js";

export const ScrapeParamsSchema = z.object({
  urls: z.array(z.string().url()).min(1).max(20).describe("URLs to scrape"),
  extract_mode: z.boolean().default(true).describe("Extract main content"),
});

export type ScrapeParams = z.infer<typeof ScrapeParamsSchema>;

export async function handleWebScrape(client: EngineClient, params: ScrapeParams) {
  const result = await client.scrape(params.urls, params.extract_mode);
  return {
    content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }],
  };
}
