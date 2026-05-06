import test from "node:test";
import assert from "node:assert/strict";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

test("serves ToolSearch tools over stdio MCP", async () => {
  const client = new Client({ name: "toolsearch-test-client", version: "0.1.0" });
  const transport = new StdioClientTransport({
    command: process.execPath,
    args: ["dist/src/index.js"],
    cwd: process.cwd(),
    stderr: "pipe",
  });

  try {
    await client.connect(transport);
    const tools = await client.listTools();
    const names = tools.tools.map((tool) => tool.name);
    assert.ok(names.includes("toolsearch"));
    assert.ok(names.includes("tool_get"));
    assert.ok(names.includes("tool_categories"));
    assert.ok(names.includes("tool_reload_catalog"));

    const result = await client.callTool({
      name: "toolsearch",
      arguments: { query: "查看 pod 日志", limit: 1 },
    });
    assert.ok(Array.isArray(result.content));
    const firstContent = result.content[0] as { type: string; text: string };
    assert.equal(firstContent.type, "text");
    const payload = JSON.parse(firstContent.text);
    assert.equal(payload.results[0].name, "k8s-get-logs");
    assert.equal(payload.categoryGroups[0].category, "kubernetes");
    assert.equal(payload.relevanceLayers[0].name, "direct");
  } finally {
    await client.close();
  }
});
