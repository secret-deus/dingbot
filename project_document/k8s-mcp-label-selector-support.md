# K8s-MCP 标签选择器支持

## 概述

为了更好地支持用户查询特定应用的Kubernetes资源，我们为k8s-mcp服务器中的核心工具添加了标签选择器支持。现在用户可以使用 `-l app=med-marketing` 这样的标签选择器来精确查询相关资源。

## 支持的工具

### ✅ 已添加标签选择器支持的工具

#### 1. k8s-get-deployments
- **工具名称**: `k8s-get-deployments`
- **新增参数**: `label_selector`, `name`
- **功能增强**: 支持获取单个Deployment详细信息
- **使用示例**: 
  ```json
  // 使用标签选择器
  {
    "namespace": "test",
    "label_selector": "app=med-marketing"
  }
  
  // 查询特定名称的deployment
  {
    "namespace": "test",
    "name": "med-marketing"
  }
  ```

#### 2. k8s-get-services
- **工具名称**: `k8s-get-services`
- **新增参数**: `label_selector`, `name`
- **功能增强**: 支持获取单个Service详细信息
- **使用示例**:
  ```json
  // 使用标签选择器
  {
    "namespace": "test", 
    "label_selector": "app=med-marketing"
  }
  
  // 查询特定名称的service
  {
    "namespace": "test",
    "name": "med-marketing"
  }
  ```

#### 3. k8s-get-endpoints
- **工具名称**: `k8s-get-endpoints`
- **新增参数**: `label_selector`
- **使用示例**:
  ```json
  {
    "namespace": "test",
    "label_selector": "app=med-marketing"
  }
  ```

#### 4. k8s-get-pods (已有支持)
- **工具名称**: `k8s-get-pods`
- **现有参数**: `label_selector`
- **使用示例**:
  ```json
  {
    "namespace": "test",
    "label_selector": "app=med-marketing"
  }
  ```

## 标签选择器语法

支持标准的Kubernetes标签选择器语法：

### 基本语法
- **单个标签**: `app=med-marketing`
- **多个标签**: `app=med-marketing,version=v1`
- **标签存在**: `app`
- **标签不存在**: `!app`
- **集合选择**: `environment in (production,qa)`
- **集合排除**: `tier notin (frontend,backend)`

### 实际使用示例

#### 查询特定应用的所有资源
```bash
# 查询med-marketing应用的deployment
{
  "namespace": "test",
  "label_selector": "app=med-marketing"
}

# 查询med-marketing应用的service
{
  "namespace": "test", 
  "label_selector": "app=med-marketing"
}

# 查询med-marketing应用的pods
{
  "namespace": "test",
  "label_selector": "app=med-marketing"
}

# 查询med-marketing应用的endpoints
{
  "namespace": "test",
  "label_selector": "app=med-marketing"
}
```

#### 查询特定名称的资源
```bash
# 查询特定名称的deployment
{
  "namespace": "test",
  "name": "med-marketing"
}

# 查询特定名称的service
{
  "namespace": "test",
  "name": "med-marketing"
}

# 查询特定名称的pod
{
  "namespace": "test",
  "name": "med-marketing-dc669449b-x6spp"
}

# 查询特定名称的endpoints
{
  "namespace": "test",
  "name": "med-marketing"
}
```

#### 复杂查询示例
```bash
# 查询特定版本的资源
{
  "namespace": "test",
  "label_selector": "app=med-marketing,version=v1.0"
}

# 查询生产环境的资源
{
  "namespace": "prod",
  "label_selector": "app=med-marketing,environment=production"
}

# 查询多个应用
{
  "namespace": "test",
  "label_selector": "app in (med-marketing,user-service)"
}
```

## 技术实现

### 1. K8sClient 层面的支持

在 `k8s_client.py` 中，以下方法已支持 `label_selector` 参数：
- `get_deployments(namespace, label_selector)`
- `get_services(namespace, label_selector)`
- `get_pods(namespace, label_selector)` (已有)
- `get_endpoints(namespace, name, label_selector)` (新增)

### 2. 工具层面的支持

每个工具的 `get_schema()` 方法都添加了 `label_selector` 参数定义：

```python
"label_selector": {
    "type": "string",
    "description": "标签选择器，例如: app=med-marketing 或 app=nginx,version=v1"
}
```

### 3. 执行层面的支持

每个工具的 `execute()` 方法都更新为传递 `label_selector` 参数：

```python
result = await self.k8s_client.get_deployments(
    namespace=namespace,
    label_selector=label_selector
)
```

## 用户使用指南

### 1. 通过聊天界面使用

用户现在可以使用自然语言查询：

```
查询test命名空间下app=med-marketing标签的所有deployment
```

```
在test空间中使用标签选择器app=med-marketing查询所有相关资源
```

```
帮我查看标签为app=med-marketing的service状态
```

### 2. 直接MCP调用

也可以直接调用MCP工具：

```json
{
  "tool": "k8s-get-deployments",
  "arguments": {
    "namespace": "test",
    "label_selector": "app=med-marketing"
  }
}
```

## 预期效果

### 解决的问题
1. **精确查询**: 不再返回整个集群的资源，只返回匹配标签的资源
2. **减少结果大小**: 避免因结果过大导致的上下文溢出问题
3. **提高查询效率**: 直接在Kubernetes API层面进行过滤

### 使用场景
1. **应用状态检查**: 查询特定应用的所有相关资源
2. **故障排查**: 快速定位特定应用的问题
3. **资源监控**: 监控特定标签的资源状态
4. **批量操作**: 对匹配标签的资源进行批量操作

## 测试验证

所有工具都已通过测试验证：
- ✅ Schema定义正确
- ✅ 参数传递正确  
- ✅ 标签选择器描述清晰
- ✅ 向后兼容性保持

## 更新日志

- **2024-01-XX**: 为 k8s-get-deployments 添加标签选择器支持
- **2024-01-XX**: 为 k8s-get-services 添加标签选择器支持  
- **2024-01-XX**: 为 k8s-get-endpoints 添加标签选择器支持
- **2024-01-XX**: 更新 k8s_client.py 中的 get_endpoints 方法支持标签选择器
- **2024-01-XX**: 完成测试验证和文档更新

## 注意事项

1. **向后兼容**: 所有更改都保持向后兼容，不影响现有功能
2. **参数可选**: `label_selector` 参数是可选的，不传递时行为与之前一致
3. **错误处理**: 保持原有的错误处理机制
4. **性能优化**: 标签选择器在Kubernetes API层面进行过滤，提高查询效率

现在用户可以使用 `app=med-marketing` 这样的标签选择器来精确查询相关资源，解决了之前查询特定资源时返回"未找到"的问题！
