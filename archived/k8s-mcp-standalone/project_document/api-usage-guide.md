# K8s MCP API 使用指南

本文档详细介绍K8s MCP服务器提供的所有API接口和工具使用方法。

## 📋 目录

- [基础信息](#基础信息)
- [健康检查API](#健康检查api)
- [监控API](#监控api)
- [智能功能API](#智能功能api)
- [MCP工具API](#mcp工具api)
- [Server-Sent Events](#server-sent-events)
- [错误处理](#错误处理)
- [API示例](#api示例)

## 🔧 基础信息

### 服务器地址
- **默认地址**: `http://localhost:8766`
- **协议**: HTTP/1.1
- **数据格式**: JSON
- **字符编码**: UTF-8

### 认证方式
当前版本不需要API认证，但建议在生产环境中添加适当的安全措施。

### 通用响应格式
```json
{
  "status": "success|error",
  "data": {...},
  "message": "描述信息",
  "timestamp": "2025-08-04T12:00:00Z"
}
```

## 🩺 健康检查API

### GET /health
获取服务器基本健康状态。

**请求示例:**
```bash
curl -X GET http://localhost:8766/health
```

**响应示例:**
```json
{
  "server_status": "running",
  "tools_count": 12,
  "clients_count": 3,
  "k8s_client": {
    "healthy": true,
    "cluster_info": {
      "version": "v1.24.0",
      "platform": "linux/amd64"
    }
  },
  "intelligent_mode": {
    "intelligent_mode_enabled": true,
    "knowledge_graph_available": true,
    "cluster_sync_running": true,
    "summary_generator_available": true,
    "graph_nodes_count": 45,
    "graph_edges_count": 78,
    "sync_status": {
      "last_sync": "2025-08-04T11:45:00Z",
      "sync_interval": 300,
      "health": "healthy"
    }
  },
  "monitoring": {
    "enabled": true,
    "metrics_collector": {
      "collector_running": true,
      "metrics_count": 1000,
      "uptime": 3600
    },
    "performance_monitor": {
      "alert_count": 2,
      "recent_alerts": 0
    }
  }
}
```

### GET /
获取服务器基本信息。

**响应示例:**
```json
{
  "name": "K8s MCP Server",
  "version": "1.0.0",
  "description": "Kubernetes MCP智能服务器",
  "status": "running"
}
```

## 📊 监控API

### GET /metrics
获取当前性能指标。

**请求参数:** 无

**响应示例:**
```json
{
  "timestamp": 1722764400.123,
  "metrics": {
    "system.cpu_percent": 25.5,
    "system.memory_percent": 68.2,
    "process.memory_rss_mb": 245.8,
    "api.GET_health.response_time": 0.015,
    "tool.k8s-get-pods.execution_time": 0.342,
    "intelligent.kg_nodes": 45,
    "intelligent.kg_edges": 78,
    "intelligent.sync_health_score": 1.0
  },
  "counters": {
    "http.requests.total": 1250,
    "api.GET_health.total_count": 145,
    "tool.k8s-get-pods.total_count": 89
  },
  "api_stats": {
    "GET_health": {
      "avg_response_time": 0.012,
      "max_response_time": 0.045,
      "total_requests": 145,
      "error_count": 0,
      "success_rate": 100.0
    }
  },
  "tool_stats": {
    "k8s-get-pods": {
      "avg_execution_time": 0.298,
      "max_execution_time": 1.234,
      "total_calls": 89,
      "error_count": 2,
      "success_rate": 97.8
    }
  }
}
```

### GET /metrics/history
获取指标历史数据。

**请求参数:**
- `metric_name` (可选): 指定指标名称
- `last_minutes` (可选): 最近N分钟，默认60

**请求示例:**
```bash
# 获取最近30分钟的CPU使用率历史
curl "http://localhost:8766/metrics/history?metric_name=system.cpu_percent&last_minutes=30"

# 获取最近1小时的所有指标历史
curl "http://localhost:8766/metrics/history?last_minutes=60"
```

**响应示例:**
```json
{
  "history": [
    {
      "name": "system.cpu_percent",
      "value": 25.5,
      "timestamp": 1722764400.123,
      "tags": {}
    },
    {
      "name": "system.cpu_percent",
      "value": 27.2,
      "timestamp": 1722764430.456,
      "tags": {}
    }
  ],
  "total_count": 120
}
```

### GET /metrics/summary
获取指标汇总统计。

**响应示例:**
```json
{
  "timestamp": 1722764400.123,
  "uptime_seconds": 7200,
  "total_metrics_collected": 1000,
  "api_summary": {
    "total_calls": 1250,
    "total_errors": 15,
    "error_rate": 1.2,
    "avg_response_time": 0.045
  },
  "tool_summary": {
    "total_calls": 189,
    "total_errors": 5,
    "error_rate": 2.6,
    "avg_execution_time": 0.412
  },
  "system_summary": {
    "cpu_percent": 25.5,
    "memory_percent": 68.2,
    "process_memory_mb": 245.8,
    "thread_count": 8
  },
  "intelligent_summary": {
    "kg_nodes": 45,
    "kg_edges": 78,
    "sync_health_score": 1.0,
    "last_sync_ago": 45.2
  }
}
```

### GET /performance
获取性能报告和健康评分。

**响应示例:**
```json
{
  "timestamp": 1722764400.123,
  "health_score": 92.5,
  "performance_status": "excellent",
  "summary_stats": {
    "uptime_seconds": 7200,
    "api_summary": {
      "total_calls": 1250,
      "error_rate": 1.2,
      "avg_response_time": 0.045
    },
    "system_summary": {
      "cpu_percent": 25.5,
      "memory_percent": 68.2
    }
  },
  "recent_alerts": [
    {
      "timestamp": 1722764100.0,
      "message": "API响应时间过高: GET_pods = 5.2s",
      "severity": "warning"
    }
  ],
  "alert_thresholds": {
    "api.response_time.max": 5.0,
    "system.cpu_percent.max": 80.0,
    "system.memory_percent.max": 85.0,
    "error_rate.max": 5.0,
    "sync.last_sync_ago.max": 300.0
  },
  "key_metrics": {
    "avg_api_response_time": 0.045,
    "api_error_rate": 1.2,
    "cpu_usage": 25.5,
    "memory_usage": 68.2,
    "sync_health": 1.0
  }
}
```

### GET /alerts
获取报警历史。

**请求参数:**
- `last_hours` (可选): 最近N小时，默认24

**请求示例:**
```bash
curl "http://localhost:8766/alerts?last_hours=12"
```

**响应示例:**
```json
{
  "alerts": [
    {
      "timestamp": 1722764100.0,
      "message": "CPU使用率过高: 85.5%",
      "metric_name": "system.cpu_percent",
      "metric_value": 85.5,
      "severity": "warning"
    },
    {
      "timestamp": 1722763800.0,
      "message": "API响应时间过高: GET_pods = 6.2s",
      "metric_name": "api.GET_pods.response_time",
      "metric_value": 6.2,
      "severity": "warning"
    }
  ],
  "total_count": 2
}
```

### GET /metrics/prometheus
获取Prometheus格式的指标。

**响应示例:**
```
# TYPE k8s_mcp_system_cpu_percent gauge
k8s_mcp_system_cpu_percent 25.5

# TYPE k8s_mcp_system_memory_percent gauge
k8s_mcp_system_memory_percent 68.2

# TYPE k8s_mcp_api_response_time gauge
k8s_mcp_api_response_time{endpoint="GET_health"} 0.015

# TYPE k8s_mcp_http_requests_total counter
k8s_mcp_http_requests_total 1250
```

## 🧠 智能功能API

### GET /intelligent/status
获取智能功能概览状态。

**响应示例:**
```json
{
  "intelligent_mode_enabled": true,
  "knowledge_graph_available": true,
  "cluster_sync_running": true,
  "summary_generator_available": true,
  "graph_nodes_count": 45,
  "graph_edges_count": 78,
  "sync_status": {
    "running": true,
    "last_sync": "2025-08-04T11:45:00Z",
    "sync_interval": 300,
    "health": "healthy",
    "error_count": 0
  }
}
```

### GET /intelligent/health
获取智能功能详细健康检查。

**响应示例:**
```json
{
  "intelligent_mode": true,
  "components": {
    "knowledge_graph": {
      "available": true,
      "nodes": 45,
      "edges": 78
    },
    "cluster_sync": {
      "running": true,
      "status": {
        "health": "healthy",
        "last_sync_ago_seconds": 45.2,
        "sync_interval_seconds": 300,
        "error_count": 0,
        "active_watch_threads": 3,
        "total_resources": 45,
        "total_relationships": 78
      }
    },
    "summary_generator": {
      "available": true
    }
  },
  "timestamp": "2025-08-04T12:00:00Z"
}
```

## 🔧 MCP工具API

### GET /tools
获取可用工具列表。

说明：当前实现返回的字段为 `name`、`description`、`category`、`input_schema`，不包含 `enabled` 或嵌套的 `schema` 字段。

**响应示例:**
```json
{
  "tools": [
    {
      "name": "k8s-get-pods",
      "description": "获取Pod列表",
      "category": "kubernetes",
      "input_schema": {
        "type": "object",
        "properties": {
          "namespace": {"type": "string", "description": "命名空间"},
          "label_selector": {"type": "string", "description": "标签选择器"}
        }
      }
    },
    {
      "name": "k8s-relation-query",
      "description": "资源关联查询",
      "category": "k8s",
      "input_schema": {
        "type": "object",
        "properties": {
          "query_type": {"type": "string"},
          "resource_type": {"type": "string"},
          "resource_name": {"type": "string"},
          "max_depth": {"type": "integer"}
        }
      }
    }
  ]
}
```

### POST /tools/call
调用MCP工具。

说明：当前实现的请求体字段为 `id`、`name`、`arguments`（不是 `tool`、`parameters`）。

**请求体格式:**
```json
{
  "id": "unique-request-id",
  "name": "tool-name",
  "arguments": {
    "param1": "value1",
    "param2": "value2"
  }
}
```

**基础K8s工具调用示例:**

**获取Pod列表:**
```bash
curl -X POST http://localhost:8766/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "id": "req-001",
    "name": "k8s-get-pods",
    "arguments": {
      "namespace": "default",
      "label_selector": "app=my-app"
    }
  }'
```

**响应示例:**
```json
{
  "id": "req-001",
  "success": true,
  "result": {
    "pods": [
      {
        "name": "my-app-pod-1",
        "namespace": "default",
        "status": "Running",
        "node": "worker-1",
        "created": "2025-08-04T10:00:00Z",
        "labels": {
          "app": "my-app",
          "version": "v1.0"
        }
      }
    ],
    "total_count": 1
  }
}
```

**扩缩容Deployment:**
```bash
curl -X POST http://localhost:8766/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "id": "req-002",
    "name": "k8s-scale-deployment",
    "arguments": {
      "namespace": "default",
      "name": "my-app",
      "replicas": 3
    }
  }'
```

**智能工具调用示例:**

**资源关联查询:**
```bash
curl -X POST http://localhost:8766/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "id": "req-003",
    "name": "k8s-relation-query",
    "arguments": {
      "query_type": "dependencies",
      "resource_type": "pod",
      "resource_name": "my-app-pod-1",
      "namespace": "default",
      "max_depth": 2
    }
  }'
```

**响应示例:**
```json
{
  "id": "req-003",
  "success": true,
  "result": {
    "query_info": {
      "query_type": "dependencies",
      "resource": "pod/my-app-pod-1",
      "namespace": "default",
      "max_depth": 2
    },
    "relationships": [
      {
        "source": "pod/my-app-pod-1",
        "target": "deployment/my-app",
        "relation_type": "owned_by",
        "depth": 1
      },
      {
        "source": "pod/my-app-pod-1",
        "target": "service/my-app-service",
        "relation_type": "selected_by",
        "depth": 1
      }
    ],
    "summary": {
      "total_relationships": 2,
      "max_depth_reached": 1,
      "resource_types": ["deployment", "service"]
    }
  }
}
```

**集群摘要生成:**
```bash
curl -X POST http://localhost:8766/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "id": "req-004",
    "name": "k8s-cluster-summary",
    "arguments": {
      "summary_type": "overview",
      "namespace": "default",
      "max_size_kb": 10,
      "include_anomalies": true
    }
  }'
```

**响应示例:**
```json
{
  "id": "req-004",
  "success": true,
  "result": {
    "summary_info": {
      "summary_type": "overview",
      "namespace": "default",
      "generated_at": "2025-08-04T12:00:00Z",
      "size_kb": 8.5
    },
    "cluster_overview": {
      "total_resources": 45,
      "namespaces": ["default", "kube-system"],
      "nodes_count": 3,
      "pods_count": 12,
      "services_count": 8,
      "deployments_count": 6
    },
    "key_metrics": {
      "pods": {
        "total": 12,
        "running": 10,
        "failed": 1,
        "pending": 1,
        "success_rate": 83.3
      },
      "overall_health": 85.2
    },
    "anomalies": [
      {
        "resource": "pod/failing-pod",
        "issue": "CrashLoopBackOff",
        "severity": 8,
        "description": "Pod重启次数过多"
      }
    ],
    "summary_text": "集群状态良好，共45个资源。发现1个异常Pod需要关注..."
  }
}
```

## 📡 Server-Sent Events

### GET /events
建立SSE连接以接收实时事件。

**连接示例:**
```javascript
const es = new EventSource('http://localhost:8766/events');
es.addEventListener('connected', e => console.log('connected', JSON.parse(e.data)));
es.addEventListener('tools_list', e => console.log('tools', JSON.parse(e.data)));
es.addEventListener('tool_start', e => console.log('tool_start', JSON.parse(e.data)));
es.addEventListener('tool_complete', e => console.log('tool_complete', JSON.parse(e.data)));
es.addEventListener('tool_error', e => console.error('tool_error', JSON.parse(e.data)));
es.addEventListener('heartbeat', e => {/* keep-alive */});
```

**事件类型（当前实现）:**
- `connected` - 连接建立确认
- `tools_list` - 可用工具列表
- `tool_start` - 工具开始执行
- `tool_complete` - 工具执行完成（包含序列化后的 `result`）
- `tool_error` - 工具执行出错
- `heartbeat` - 心跳（空闲时每30秒）

**事件示例（tool_complete）:**
```json
{
  "id": "req-001",
  "tool": "k8s-get-pods",
  "result": {"pods": [], "total_count": 0},
  "success": true,
  "execution_time": 0.342,
  "result_size": 128,
  "timestamp": 1722764400.123
}
```

## ❌ 错误处理

### 错误响应格式
```json
{
  "id": "req-001",
  "success": false,
  "error": {
    "code": "TOOL_EXECUTION_ERROR",
    "message": "工具执行失败",
    "details": "连接K8s API服务器超时",
    "timestamp": "2025-08-04T12:00:00Z"
  }
}
```

### 常见错误代码

| 错误代码 | HTTP状态码 | 描述 | 解决方案 |
|----------|------------|------|----------|
| `TOOL_NOT_FOUND` | 404 | 工具不存在 | 检查工具名称 |
| `INVALID_PARAMETERS` | 400 | 参数无效 | 检查参数格式 |
| `TOOL_EXECUTION_ERROR` | 500 | 工具执行失败 | 检查K8s连接 |
| `PERMISSION_DENIED` | 403 | 权限不足 | 检查RBAC配置 |
| `TIMEOUT` | 408 | 请求超时 | 增加超时时间 |
| `SERVICE_UNAVAILABLE` | 503 | 服务不可用 | 检查服务状态 |

### 监控功能禁用错误
当监控功能禁用时，访问监控API会返回503错误：
```json
{
  "detail": "监控功能未启用"
}
```

## 🔧 API示例

### 完整的监控检查脚本
```bash
#!/bin/bash

BASE_URL="http://localhost:8766"

echo "=== K8s MCP 服务器状态检查 ==="

# 1. 基础健康检查
echo "1. 检查服务器健康状态..."
curl -s "$BASE_URL/health" | jq .

# 2. 检查智能功能
echo "2. 检查智能功能状态..."
curl -s "$BASE_URL/intelligent/health" | jq .

# 3. 检查性能指标
echo "3. 检查性能指标..."
curl -s "$BASE_URL/performance" | jq .

# 4. 检查最近报警
echo "4. 检查最近报警..."
curl -s "$BASE_URL/alerts?last_hours=1" | jq .

# 5. 获取工具列表
echo "5. 获取可用工具..."
curl -s "$BASE_URL/tools" | jq '.tools[].name'
```

### 智能查询示例
```bash
#!/bin/bash

BASE_URL="http://localhost:8766"

# 查询Pod依赖关系
echo "查询Pod依赖关系..."
curl -X POST "$BASE_URL/tools/call" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "query-deps",
    "tool": "k8s-relation-query",
    "parameters": {
      "query_type": "dependencies",
      "resource_type": "pod",
      "resource_name": "nginx-pod",
      "namespace": "default",
      "max_depth": 3
    }
  }' | jq .

# 生成集群摘要
echo "生成集群摘要..."
curl -X POST "$BASE_URL/tools/call" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "cluster-summary",
    "tool": "k8s-cluster-summary",
    "parameters": {
      "summary_type": "detailed",
      "namespace": "default",
      "max_size_kb": 15,
      "include_anomalies": true,
      "include_metrics": true
    }
  }' | jq .
```

### Python客户端示例
```python
import requests
import json
from typing import Dict, Any

class K8sMCPClient:
    def __init__(self, base_url: str = "http://localhost:8766"):
        self.base_url = base_url

    def health_check(self) -> Dict[str, Any]:
        """获取健康状态"""
        response = requests.get(f"{self.base_url}/health")
        return response.json()

    def get_performance(self) -> Dict[str, Any]:
        """获取性能报告"""
        response = requests.get(f"{self.base_url}/performance")
        return response.json()

    def call_tool(self, tool_name: str, parameters: Dict[str, Any],
                  request_id: str = None) -> Dict[str, Any]:
        """调用MCP工具"""
        if request_id is None:
            import uuid
            request_id = str(uuid.uuid4())

        payload = {
            "id": request_id,
            "tool": tool_name,
            "parameters": parameters
        }

        response = requests.post(
            f"{self.base_url}/tools/call",
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload)
        )
        return response.json()

    def get_pods(self, namespace: str = "default",
                 label_selector: str = None) -> Dict[str, Any]:
        """获取Pod列表"""
        params = {"namespace": namespace}
        if label_selector:
            params["label_selector"] = label_selector

        return self.call_tool("k8s-get-pods", params)

    def query_relations(self, resource_type: str, resource_name: str,
                       query_type: str = "dependencies",
                       namespace: str = "default",
                       max_depth: int = 2) -> Dict[str, Any]:
        """查询资源关系"""
        params = {
            "query_type": query_type,
            "resource_type": resource_type,
            "resource_name": resource_name,
            "namespace": namespace,
            "max_depth": max_depth
        }
        return self.call_tool("k8s-relation-query", params)

# 使用示例
if __name__ == "__main__":
    client = K8sMCPClient()

    # 检查健康状态
    health = client.health_check()
    print(f"服务器状态: {health.get('server_status')}")

    # 获取Pod列表
    pods = client.get_pods(namespace="default")
    if pods.get('success'):
        print(f"找到 {len(pods['result']['pods'])} 个Pod")

    # 查询Pod依赖关系
    relations = client.query_relations("pod", "nginx-pod")
    if relations.get('success'):
        rel_count = relations['result']['summary']['total_relationships']
        print(f"找到 {rel_count} 个关联关系")
```

## 📚 相关文档

- [配置说明文档](configuration-guide.md)
- [部署运维指南](deployment-guide.md)
- [故障排查指南](troubleshooting-guide.md)
- [主项目文档](../README.md)

---

**💡 提示**: 所有API都支持跨域访问，可以直接在前端应用中使用。建议在生产环境中添加适当的认证和授权机制。