"""File-backed Kubernetes knowledge graph store."""

from __future__ import annotations

import json
from collections import Counter, deque
from datetime import datetime, timezone
from typing import Any

from app.core.config import resolve_repo_path

GRAPH_VERSION = "1.0"


def graph_node_id(kind: str, namespace: str | None, name: str) -> str:
    ns = namespace or "_cluster"
    return f"{normalize_graph_kind(kind)}:{ns}:{name}"


def normalize_graph_kind(kind: Any) -> str:
    normalized = str(kind or "").strip().lower()
    aliases = {
        "deploy": "deployment",
        "deployments": "deployment",
        "pod": "pod",
        "pods": "pod",
        "svc": "service",
        "services": "service",
        "rs": "replicaset",
        "replicasets": "replicaset",
        "ing": "ingress",
        "ingresses": "ingress",
        "node": "node",
        "nodes": "node",
    }
    return aliases.get(normalized, normalized)


class FileKnowledgeGraphStore:
    def __init__(self, path: str) -> None:
        self.path = resolve_repo_path(path)

    def load(self) -> dict:
        if not self.path.exists():
            return self.empty_graph()
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return self.empty_graph()
        if not isinstance(data, dict):
            return self.empty_graph()
        data.setdefault("nodes", [])
        data.setdefault("edges", [])
        data.setdefault("metadata", {})
        return data

    def save(self, nodes: list[dict], edges: list[dict], metadata: dict | None = None) -> dict:
        graph = {
            "version": GRAPH_VERSION,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "metadata": metadata or {},
            "nodes": sorted(nodes, key=lambda item: item.get("id", "")),
            "edges": sorted(
                self._dedupe_edges(edges),
                key=lambda item: (
                    item.get("source", ""),
                    item.get("target", ""),
                    item.get("type", ""),
                ),
            ),
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(graph, ensure_ascii=False, indent=2), encoding="utf-8")
        return graph

    def query(
        self,
        resource_type: str,
        resource_name: str,
        namespace: str | None = None,
        depth: int = 2,
    ) -> dict:
        graph = self.load()
        root_id = self._find_node_id(graph, resource_type, resource_name, namespace)
        if not root_id:
            return {
                "found": False,
                "resource_type": normalize_graph_kind(resource_type),
                "resource_name": resource_name,
                "namespace": namespace,
                "graph_updated_at": graph.get("updated_at"),
                "nodes": [],
                "edges": [],
            }

        node_ids = self._neighbor_ids(graph, root_id, max(0, min(int(depth), 5)))
        nodes = [node for node in graph.get("nodes", []) if node.get("id") in node_ids]
        edges = [
            edge
            for edge in graph.get("edges", [])
            if edge.get("source") in node_ids and edge.get("target") in node_ids
        ]
        return {
            "found": True,
            "root": root_id,
            "graph_updated_at": graph.get("updated_at"),
            "nodes": nodes,
            "edges": edges,
            "summary": self.summarize({"nodes": nodes, "edges": edges}),
        }

    def summarize(self, graph: dict) -> dict:
        nodes = graph.get("nodes", [])
        edges = graph.get("edges", [])
        return {
            "nodes": len(nodes),
            "edges": len(edges),
            "node_types": dict(Counter(node.get("kind", "unknown") for node in nodes)),
            "edge_types": dict(Counter(edge.get("type", "unknown") for edge in edges)),
        }

    def metrics_coverage(self) -> dict:
        graph = self.load()
        nodes = graph.get("nodes", [])
        nodes_with_metrics = [node for node in nodes if node.get("metrics")]
        total = len(nodes)
        return {
            "graph_updated_at": graph.get("updated_at"),
            "total_nodes": total,
            "nodes_with_metrics": len(nodes_with_metrics),
            "coverage": round(len(nodes_with_metrics) / total, 4) if total else 0,
            "missing_metrics": [
                {
                    "id": node.get("id"),
                    "kind": node.get("kind"),
                    "name": node.get("name"),
                    "namespace": node.get("namespace"),
                }
                for node in nodes
                if not node.get("metrics")
            ][:100],
        }

    @staticmethod
    def empty_graph() -> dict:
        return {
            "version": GRAPH_VERSION,
            "updated_at": None,
            "metadata": {},
            "nodes": [],
            "edges": [],
        }

    @staticmethod
    def _dedupe_edges(edges: list[dict]) -> list[dict]:
        seen = set()
        deduped = []
        for edge in edges:
            key = (edge.get("source"), edge.get("target"), edge.get("type"))
            if key in seen:
                continue
            seen.add(key)
            deduped.append(edge)
        return deduped

    @staticmethod
    def _find_node_id(
        graph: dict, resource_type: str, resource_name: str, namespace: str | None
    ) -> str | None:
        kind = normalize_graph_kind(resource_type)
        candidates = [
            node
            for node in graph.get("nodes", [])
            if node.get("kind") == kind and node.get("name") == resource_name
        ]
        if namespace:
            candidates = [node for node in candidates if node.get("namespace") == namespace]
        return candidates[0]["id"] if candidates else None

    @staticmethod
    def _neighbor_ids(graph: dict, root_id: str, depth: int) -> set[str]:
        adjacency: dict[str, set[str]] = {}
        for edge in graph.get("edges", []):
            source = edge.get("source")
            target = edge.get("target")
            if not source or not target:
                continue
            adjacency.setdefault(source, set()).add(target)
            adjacency.setdefault(target, set()).add(source)

        visited = {root_id}
        queue = deque([(root_id, 0)])
        while queue:
            current, current_depth = queue.popleft()
            if current_depth >= depth:
                continue
            for neighbor in adjacency.get(current, set()):
                if neighbor in visited:
                    continue
                visited.add(neighbor)
                queue.append((neighbor, current_depth + 1))
        return visited
