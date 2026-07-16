import { z } from "zod";
import type { EngineClient } from "../client.js";

export const FilterParamsSchema = z.object({
  query: z.string().min(1).describe("Query to filter by"),
  results: z.array(z.string()).min(1).max(100).describe("Document texts to filter"),
  top_k: z.number().int().min(1).max(20).optional().describe("Top K results to return"),
});

export type FilterParams = z.infer<typeof FilterParamsSchema>;

export async function handleSearchFilter(client: EngineClient, params: FilterParams) {
  const result = await client.filter(params.query, params.results, params.top_k);

  return {
    content: [
      {
        type: "text" as const,
        text: JSON.stringify(
          {
            query: result.query,
            results: result.results.map((r) => ({
              text: r.document.text,
              score: r.score,
            })),
          },
          null,
          2
        ),
      },
    ],
  };
}
