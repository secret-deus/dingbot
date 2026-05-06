#!/usr/bin/env node

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import { defaultCatalogPath, getTool, loadCatalogFromFile, summarizeCatalog } from "./catalog.js";
import { searchTools } from "./search.js";
import type { ToolCatalog } from "./types.js";

const server = new McpServer({
  name: "ding-robot-toolsearch",
  version: "0.1.0",
});

let catalogPath = process.env.TOOL_CATALOG_PATH || defaultCatalogPath();
let catalog: ToolCatalog = loadCatalogFromFile(catalogPath);

function jsonContent(payload: unknown) {
  return {
    content: [
      {
        type: "text" as const,
        text: JSON.stringify(payload, null, 2),
      },
    ],
  };
}

server.registerTool(
  "toolsearch",
  {
    description: "Search the Ding Robot operations tool catalog. Returns flat results plus categoryGroups and relevanceLayers. Discovery-only; does not execute operational tools.",
    inputSchema: {
      query: z.string().min(1).describe("Natural language search query"),
      category: z.string().optional().describe("Optional category filter, such as kubernetes or ecs"),
      limit: z.number().int().min(1).max(20).optional().describe("Maximum number of results"),
      dangerLevel: z.enum(["read", "write", "dangerous"]).optional().describe("Optional risk filter"),
    },
  },
  async (args) => jsonContent(searchTools(catalog, args)),
);

server.registerTool(
  "tool_get",
  {
    description: "Return full metadata for one exact tool name. Discovery-only.",
    inputSchema: {
      name: z.string().min(1).describe("Exact tool name"),
    },
  },
  async ({ name }) => {
    const tool = getTool(catalog, name);
    return jsonContent(tool ?? { error: `tool not found: ${name}` });
  },
);

server.registerTool(
  "tool_categories",
  {
    description: "Return tool category, execution policy, and risk counts.",
    inputSchema: {},
  },
  async () => jsonContent(summarizeCatalog(catalog)),
);

server.registerTool(
  "tool_reload_catalog",
  {
    description: "Reload the local tool catalog from disk. Discovery-only.",
    inputSchema: {
      path: z.string().optional().describe("Optional catalog path override"),
    },
  },
  async ({ path }) => {
    catalogPath = path || catalogPath;
    catalog = loadCatalogFromFile(catalogPath);
    return jsonContent({ reloaded: true, path: catalogPath, total: catalog.tools.length });
  },
);

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  const categories = summarizeCatalog(catalog).categories.map((item) => `${item.name}=${item.count}`).join(", ");
  console.error(`ToolSearch MCP server started with ${catalog.tools.length} tools from ${catalogPath}; categories: ${categories}`);
}

main().catch((error) => {
  console.error("ToolSearch MCP server failed to start:", error);
  process.exit(1);
});
