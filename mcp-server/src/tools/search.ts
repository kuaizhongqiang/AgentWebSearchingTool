import { z } from "zod";
import type { EngineClient } from "../client.js";

export const SearchParamsSchema = z.object({
  query: z.string().min(1).describe("Search query"),
  num_results: z.number().int().min(1).max(50).default(10).describe("Number of results"),
  engine: z.string().optional().default("google").describe("Search engine"),
});

export type SearchParams = z.infer<typeof SearchParamsSchema>;

export async function handleWebSearch(client: EngineClient, params: SearchParams) {
  const result = await client.search(params.query, {
    num: params.num_results,
    engine: params.engine,
  });

  return {
    content: [{
      type: "text" as const,
      text: JSON.stringify({
        query: params.query,
        results: result.results,
        unresponsive_engines: result.unresponsive_engines,
      }, null, 2),
    }],
  };
}
