import { z } from "zod";
import type { EngineClient } from "../client.js";

export const SearchResultSchema = z.object({
  title: z.string(),
  url: z.string(),
  content: z.string().optional(),
  engine: z.string().optional(),
  score: z.number().optional(),
  category: z.string().optional(),
});

export type SearchResult = z.infer<typeof SearchResultSchema>;

export const SearchParamsSchema = z.object({
  query: z.string().min(1).describe("Search query"),
  num_results: z.number().int().min(1).max(50).default(10).describe("Number of results to return"),
  engine: z.string().optional().default("google").describe("Search engine to use"),
});

export type SearchParams = z.infer<typeof SearchParamsSchema>;

export async function handleWebSearch(client: EngineClient, params: SearchParams) {
  const result = await client.search(params.query, {
    num: params.num_results,
    engine: params.engine,
  });

  return {
    content: [
      {
        type: "text" as const,
        text: JSON.stringify(
          {
            query: params.query,
            results: result.results,
            unresponsive_engines: result.unresponsive_engines,
          },
          null,
          2
        ),
      },
    ],
  };
}
