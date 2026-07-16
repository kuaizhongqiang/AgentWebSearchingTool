export interface SearchResult {
  title: string;
  url: string;
  content?: string;
  engine?: string;
  score?: number;
  category?: string;
}

export interface SearchResponse {
  query: string;
  results: SearchResult[];
  unresponsive_engines?: string[];
  page?: number;
}

export interface FetchResult {
  url: string;
  status_code: number;
  title?: string;
  text?: string;
  fetched_with?: string;
}

export interface ScrapeResponse {
  results: FetchResult[];
}

export interface FilterItem {
  text: string;
  score: number;
}

export interface FilterResponse {
  query: string;
  results: FilterItem[];
}
