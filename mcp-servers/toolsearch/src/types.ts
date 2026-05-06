export type DangerLevel = "read" | "write" | "dangerous";
export type ExecutionPolicy = "executable" | "catalog_only" | "external_mcp";

export interface JsonSchema {
  type: string;
  properties?: Record<string, unknown>;
  required?: string[];
  [key: string]: unknown;
}

export interface ToolCatalogEntry {
  name: string;
  title: string;
  category: string;
  description: string;
  tags: string[];
  dangerLevel: DangerLevel;
  server: string;
  executionPolicy: ExecutionPolicy;
  inputSchema: JsonSchema;
  examples: string[];
  source?: Record<string, unknown>;
}

export interface ToolCatalog {
  version: string;
  generatedAt?: string;
  source?: string[];
  tools: ToolCatalogEntry[];
}

export interface SearchArgs {
  query: string;
  category?: string;
  limit?: number;
  dangerLevel?: DangerLevel;
}

export interface SearchResult extends ToolCatalogEntry {
  score: number;
  matchedFields: string[];
}

export interface SearchCategoryGroup {
  category: string;
  title: string;
  total: number;
  topScore: number;
  results: SearchResult[];
}

export interface SearchRelevanceLayer {
  name: "direct" | "recommended" | "related";
  title: string;
  description: string;
  total: number;
  categoryGroups: SearchCategoryGroup[];
  results: SearchResult[];
}

export interface SearchResponse {
  query: string;
  total: number;
  results: SearchResult[];
  categoryGroups: SearchCategoryGroup[];
  relevanceLayers: SearchRelevanceLayer[];
  reason?: string;
}

export interface CategorySummary {
  categories: Array<{ name: string; count: number }>;
  executionPolicies: Array<{ name: ExecutionPolicy; count: number }>;
  dangerLevels: Array<{ name: DangerLevel; count: number }>;
  total: number;
}
