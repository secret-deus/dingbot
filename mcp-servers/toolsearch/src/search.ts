import type { SearchArgs, SearchCategoryGroup, SearchResponse, SearchResult, ToolCatalog, ToolCatalogEntry } from "./types.js";

const FIELD_WEIGHTS: Array<[keyof ToolCatalogEntry | "inputSchemaText" | "examplesText", number]> = [
  ["name", 10],
  ["title", 8],
  ["category", 5],
  ["tags", 5],
  ["description", 3],
  ["inputSchemaText", 2],
  ["examplesText", 2],
];

const SYNONYMS: Record<string, string[]> = {
  "k8s": ["kubernetes", "集群"],
  "kubernetes": ["k8s", "集群"],
  "日志": ["log", "logs"],
  "log": ["日志", "logs"],
  "logs": ["日志", "log"],
  "指标": ["metric", "metrics", "prometheus", "cpu", "memory"],
  "metrics": ["指标", "metric", "prometheus", "cpu", "memory"],
  "监控": ["monitor", "metrics", "指标"],
  "事件": ["event", "events"],
  "服务": ["service", "svc"],
  "端点": ["endpoint", "endpoints"],
  "权限": ["permission", "iam", "rbac"],
  "审计": ["audit", "security"],
  "定时任务": ["cron", "scheduler"],
  "巡检": ["inspect", "inspection"],
  "发布": ["deployment", "history", "rollout"],
  "回滚": ["deployment", "history", "rollout"],
  "主机": ["ecs", "instance", "instances"],
};

const READ_INTENT = ["查看", "查询", "获取", "列出", "describe", "list", "get", "inspect"];
const MUTATION_INTENT = ["更新", "重启", "删除", "扩容", "缩容", "update", "restart", "delete", "scale"];

export function searchTools(catalog: ToolCatalog, args: SearchArgs): SearchResponse {
  const limit = clampLimit(args.limit);
  const query = args.query.trim();
  if (!query) {
    return emptyResponse(query, "query is required");
  }

  const tokens = expandTokens(tokenize(query), query);
  const candidates = catalog.tools
    .filter((tool) => !args.category || tool.category === args.category)
    .filter((tool) => !args.dangerLevel || tool.dangerLevel === args.dangerLevel);

  const results = candidates
    .map((tool) => scoreTool(tool, query, tokens))
    .filter((result) => result.score > 0)
    .sort((a, b) => b.score - a.score || a.name.localeCompare(b.name))
    .slice(0, limit);

  return {
    query,
    total: results.length,
    results,
    categoryGroups: groupByCategory(results),
    relevanceLayers: buildRelevanceLayers(results),
    ...(results.length === 0 ? { reason: "no matching tools found" } : {}),
  };
}

function emptyResponse(query: string, reason: string): SearchResponse {
  return {
    query,
    total: 0,
    results: [],
    categoryGroups: [],
    relevanceLayers: [],
    reason,
  };
}

function scoreTool(tool: ToolCatalogEntry, query: string, tokens: string[]): SearchResult {
  let score = 0;
  const matchedFields = new Set<string>();
  const normalizedQuery = normalize(query);

  for (const [field, weight] of FIELD_WEIGHTS) {
    const fieldText = getFieldText(tool, field);
    const normalizedField = normalize(fieldText);
    if (!normalizedField) {
      continue;
    }

    if (normalizedField.includes(normalizedQuery)) {
      score += weight * 3;
      matchedFields.add(String(field).replace("Text", ""));
    }

    for (const token of tokens) {
      if (!token) {
        continue;
      }
      const fieldTokens = tokenize(normalizedField);
      if (fieldTokens.includes(token)) {
        score += weight * 2;
        matchedFields.add(String(field).replace("Text", ""));
      } else if (fieldTokens.some((fieldToken) => fieldToken.startsWith(token))) {
        score += weight * 1.25;
        matchedFields.add(String(field).replace("Text", ""));
      } else if (normalizedField.includes(token)) {
        score += weight;
        matchedFields.add(String(field).replace("Text", ""));
      }
    }
  }

  if (tool.dangerLevel === "read" && READ_INTENT.some((word) => normalizedQuery.includes(normalize(word)))) {
    score += 2;
  }
  if (tool.dangerLevel !== "read" && MUTATION_INTENT.some((word) => normalizedQuery.includes(normalize(word)))) {
    score += 1;
  }

  return {
    ...tool,
    score: Number(score.toFixed(2)),
    matchedFields: [...matchedFields].sort(),
  };
}

function getFieldText(tool: ToolCatalogEntry, field: keyof ToolCatalogEntry | "inputSchemaText" | "examplesText"): string {
  if (field === "inputSchemaText") {
    return JSON.stringify(tool.inputSchema);
  }
  if (field === "examplesText") {
    return tool.examples.join(" ");
  }
  const value = tool[field];
  return Array.isArray(value) ? value.join(" ") : String(value ?? "");
}

function expandTokens(tokens: string[], rawQuery: string): string[] {
  const expanded = new Set(tokens);
  const normalizedQuery = normalize(rawQuery);
  for (const [term, aliases] of Object.entries(SYNONYMS)) {
    const normalizedTerm = normalize(term);
    if (tokens.includes(normalizedTerm) || normalizedQuery.includes(normalizedTerm)) {
      for (const alias of aliases) {
        expanded.add(normalize(alias));
      }
    }
  }
  return [...expanded];
}

export function tokenize(input: string): string[] {
  const normalized = normalize(input);
  const tokens = normalized.match(/[a-z0-9]+|[\u4e00-\u9fff]+/g) ?? [];
  const expanded = new Set<string>();
  for (const token of tokens) {
    expanded.add(token);
    if (/^[\u4e00-\u9fff]+$/.test(token) && token.length > 1) {
      for (const char of token) {
        expanded.add(char);
      }
    }
  }
  return [...expanded];
}

function normalize(input: string): string {
  return input.toLowerCase().replace(/[_/]+/g, "-").replace(/\s+/g, " ").trim();
}

function clampLimit(limit: number | undefined): number {
  if (limit === undefined) {
    return 5;
  }
  return Math.min(Math.max(Math.floor(limit), 1), 20);
}

function buildRelevanceLayers(results: SearchResult[]): SearchResponse["relevanceLayers"] {
  if (results.length === 0) {
    return [];
  }

  const topScore = results[0].score;
  const layers = [
    {
      name: "direct" as const,
      title: "直接命中",
      description: "名称、标题、标签或描述与问题高度匹配，优先考虑执行。",
      results: [] as SearchResult[],
    },
    {
      name: "recommended" as const,
      title: "推荐候选",
      description: "与问题相关，适合作为补充或下一步排查工具。",
      results: [] as SearchResult[],
    },
    {
      name: "related" as const,
      title: "相关补充",
      description: "低分相关结果，仅在前两层不足时参考。",
      results: [] as SearchResult[],
    },
  ];

  for (const result of results) {
    if (result.score >= Math.max(30, topScore * 0.72)) {
      layers[0].results.push(result);
    } else if (result.score >= Math.max(10, topScore * 0.35)) {
      layers[1].results.push(result);
    } else {
      layers[2].results.push(result);
    }
  }

  return layers
    .filter((layer) => layer.results.length > 0)
    .map((layer) => ({
      name: layer.name,
      title: layer.title,
      description: layer.description,
      total: layer.results.length,
      categoryGroups: groupByCategory(layer.results),
      results: layer.results,
    }));
}

function groupByCategory(results: SearchResult[]): SearchCategoryGroup[] {
  const groups = new Map<string, SearchResult[]>();
  for (const result of results) {
    const category = result.category || "uncategorized";
    const values = groups.get(category) ?? [];
    values.push(result);
    groups.set(category, values);
  }

  return [...groups.entries()]
    .map(([category, values]) => ({
      category,
      title: categoryTitle(category),
      total: values.length,
      topScore: values[0]?.score ?? 0,
      results: values,
    }))
    .sort((a, b) => b.topScore - a.topScore || b.total - a.total || a.category.localeCompare(b.category));
}

function categoryTitle(category: string): string {
  if (category === "kubernetes") {
    return "Kubernetes";
  }
  if (category === "ecs") {
    return "ECS";
  }
  if (category === "toolsearch") {
    return "ToolSearch";
  }
  return category;
}
