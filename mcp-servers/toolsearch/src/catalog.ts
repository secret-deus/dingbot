import { existsSync, readFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import type { CategorySummary, DangerLevel, ExecutionPolicy, ToolCatalog, ToolCatalogEntry } from "./types.js";

const DEFAULT_CATALOG_RELATIVE_PATH = "config/tool_catalog.json";

export function findRepoRoot(startDir = process.cwd()): string {
  let current = resolve(startDir);
  while (current !== dirname(current)) {
    if (existsSync(join(current, DEFAULT_CATALOG_RELATIVE_PATH))) {
      return current;
    }
    current = dirname(current);
  }

  const moduleDir = dirname(fileURLToPath(import.meta.url));
  return resolve(moduleDir, "../../../..");
}

export function defaultCatalogPath(): string {
  return join(findRepoRoot(), DEFAULT_CATALOG_RELATIVE_PATH);
}

export function loadCatalogFromFile(path = defaultCatalogPath()): ToolCatalog {
  const parsed = JSON.parse(readFileSync(path, "utf8")) as ToolCatalog;
  validateCatalog(parsed);
  return parsed;
}

export function getTool(catalog: ToolCatalog, name: string): ToolCatalogEntry | undefined {
  return catalog.tools.find((tool) => tool.name === name);
}

export function summarizeCatalog(catalog: ToolCatalog): CategorySummary {
  return {
    total: catalog.tools.length,
    categories: countBy(catalog.tools, (tool) => tool.category),
    executionPolicies: countBy(catalog.tools, (tool) => tool.executionPolicy) as Array<{ name: ExecutionPolicy; count: number }>,
    dangerLevels: countBy(catalog.tools, (tool) => tool.dangerLevel) as Array<{ name: DangerLevel; count: number }>,
  };
}

function validateCatalog(catalog: ToolCatalog): void {
  if (!catalog || !Array.isArray(catalog.tools)) {
    throw new Error("Invalid tool catalog: tools must be an array");
  }

  const names = new Set<string>();
  for (const tool of catalog.tools) {
    for (const field of ["name", "title", "category", "description", "dangerLevel", "server", "executionPolicy"] as const) {
      if (!tool[field]) {
        throw new Error(`Invalid tool catalog entry: ${tool.name || "<missing>"} missing ${field}`);
      }
    }
    if (names.has(tool.name)) {
      throw new Error(`Invalid tool catalog: duplicate tool ${tool.name}`);
    }
    names.add(tool.name);
  }
}

function countBy<T extends string>(tools: ToolCatalogEntry[], picker: (tool: ToolCatalogEntry) => T): Array<{ name: T; count: number }> {
  const counts = new Map<T, number>();
  for (const tool of tools) {
    const key = picker(tool);
    counts.set(key, (counts.get(key) ?? 0) + 1);
  }
  return [...counts.entries()]
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => b.count - a.count || a.name.localeCompare(b.name));
}
