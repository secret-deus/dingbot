import test from "node:test";
import assert from "node:assert/strict";
import { resolve } from "node:path";
import { getTool, loadCatalogFromFile, summarizeCatalog } from "./catalog.js";
import { searchTools } from "./search.js";

const catalogPath = resolve(process.cwd(), "../../config/tool_catalog.json");

test("loads the normalized 68-tool catalog", () => {
  const catalog = loadCatalogFromFile(catalogPath);
  assert.equal(catalog.tools.length, 68);
  assert.equal(getTool(catalog, "k8s-get-logs")?.executionPolicy, "executable");
  assert.equal(getTool(catalog, "k8s-get-endpoints")?.executionPolicy, "executable");
  assert.equal(getTool(catalog, "k8s-relation-query")?.executionPolicy, "executable");
  assert.equal(getTool(catalog, "k8s-sync-knowledge-graph")?.executionPolicy, "executable");
  assert.equal(getTool(catalog, "k8s-get-statefulsets")?.executionPolicy, "executable");
  assert.equal(getTool(catalog, "k8s-get-cluster-metrics")?.executionPolicy, "executable");
  assert.equal(getTool(catalog, "k8s-delete-resource")?.dangerLevel, "dangerous");
  assert.equal(getTool(catalog, "k8s-scale-deployment")?.dangerLevel, "write");
  assert.equal(getTool(catalog, "k8s-get-deployment-history")?.executionPolicy, "executable");
  assert.equal(getTool(catalog, "ecs-describe-instance-monitor-data")?.executionPolicy, "executable");
  assert.equal(getTool(catalog, "aliyun-swas-list-instances")?.category, "aliyun");
  assert.equal(getTool(catalog, "aliyun-swas-list-instances")?.executionPolicy, "executable");
});

test("ranks pod log queries first", () => {
  const catalog = loadCatalogFromFile(catalogPath);
  const result = searchTools(catalog, { query: "查看 pod 日志", limit: 3 });
  assert.equal(result.results[0]?.name, "k8s-get-logs");
  assert.ok(result.results[0]?.matchedFields.includes("tags"));
  assert.equal(result.categoryGroups[0]?.category, "kubernetes");
  assert.equal(result.relevanceLayers[0]?.name, "direct");
  assert.equal(result.relevanceLayers[0]?.categoryGroups[0]?.results[0]?.name, "k8s-get-logs");
});

test("supports category filtering", () => {
  const catalog = loadCatalogFromFile(catalogPath);
  const result = searchTools(catalog, { query: "监控 cpu", category: "ecs", limit: 3 });
  assert.equal(result.results[0]?.name, "ecs-describe-instance-monitor-data");
  assert.ok(result.results.every((tool) => tool.category === "ecs"));
});

test("returns a valid empty response for no match", () => {
  const catalog = loadCatalogFromFile(catalogPath);
  const result = searchTools(catalog, { query: "zzzzzzzz-unmatched-term" });
  assert.equal(result.total, 0);
  assert.equal(result.results.length, 0);
  assert.equal(result.categoryGroups.length, 0);
  assert.equal(result.relevanceLayers.length, 0);
  assert.equal(result.reason, "no matching tools found");
});

test("returns categorized and layered search results", () => {
  const catalog = loadCatalogFromFile(catalogPath);
  const result = searchTools(catalog, { query: "重启 deployment 或删除 pod", limit: 10 });
  assert.ok(result.categoryGroups.length >= 1);
  assert.ok(result.relevanceLayers.length >= 1);
  assert.ok(result.relevanceLayers.every((layer) => layer.total === layer.results.length));
  assert.ok(result.relevanceLayers.every((layer) => layer.categoryGroups.length >= 1));
  assert.equal(result.results[0]?.name, result.relevanceLayers[0]?.results[0]?.name);
});

test("summarizes categories and execution policies", () => {
  const catalog = loadCatalogFromFile(catalogPath);
  const summary = summarizeCatalog(catalog);
  assert.equal(summary.total, 68);
  assert.deepEqual(summary.categories.find((item) => item.name === "aliyun"), { name: "aliyun", count: 13 });
  assert.deepEqual(summary.categories.find((item) => item.name === "ecs"), { name: "ecs", count: 3 });
  assert.deepEqual(summary.categories.find((item) => item.name === "kubernetes"), { name: "kubernetes", count: 52 });
  assert.equal(summary.executionPolicies.find((item) => item.name === "catalog_only"), undefined);
  assert.deepEqual(summary.executionPolicies.find((item) => item.name === "executable"), { name: "executable", count: 68 });
});
