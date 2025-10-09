# MCP工具调用422错误问题分析与修复

**日期**: 2025-09-30  
**问题**: SSE工具调用失败，状态码422  
**工具**: `k8s-get-nodes`

---

## 🐛 错误现象

### 错误日志
```
2025-09-30 13:41:02 | ERROR   | ❌ POST请求失败: 状态码=422, 响应={
  "detail": [{
    "type": "dict_type",
    "loc": ["body", "arguments"],
    "msg": "Input should be a valid dictionary",
    "input": [{}, {}]
  }]
}
```

### 核心问题
**期望格式**: `{"arguments": {}}` (字典/对象)  
**实际发送**: `{"arguments": [{}, {}]}` (数组包含两个空字典)

---

## 🔍 问题分析

### 1. 服务器端验证模型
**位置**: `k8s-mcp/src/k8s_mcp/server.py:29-33`

```python
class ToolCallRequest(BaseModel):
    """工具调用请求"""
    id: str
    name: str
    arguments: Dict[str, Any]  # ✅ 必须是字典类型
```

**Pydantic验证规则**:
- `arguments` 字段必须是 `Dict[str, Any]` 类型
- 如果传入非字典类型（如列表），验证失败，返回422错误

### 2. 客户端调用代码
**位置**: `backend/src/scheduler/task_executor.py:247`

```python
nodes = await self.mcp_client.call_tool("k8s-get-nodes", {})
#                                                         ^^
#                                                    正确：传入空字典
```

**客户端发送逻辑**:  
**位置**: `backend/src/mcp/enhanced_client.py:712-716`

```python
request_data = {
    "id": request_id,
    "name": name,
    "arguments": parameters  # parameters 应该是字典
}
```

### 3. 问题定位

**可能原因**:
1. ❌ **参数被错误处理** - 某处代码将参数转换成了列表
2. ❌ **多次调用合并错误** - 参数被错误地收集到数组中
3. ❌ **序列化问题** - JSON序列化时格式出错
4. ❌ **类型转换错误** - 字典被意外转换成列表

---

## 🛠️ 修复方案

### 方案1: 添加参数类型验证 ✅ **已实施**

#### 修改1: 在工具调用入口检查
**文件**: `backend/src/mcp/enhanced_client.py:1054-1058`

```python
async def call_tool(self, name: str, parameters: Dict[str, Any], ...) -> Any:
    """调用工具"""
    # ✅ 入口参数类型检查
    logger.info(f"📥 call_tool 入口 - 工具={name}, 参数类型={type(parameters)}, 参数值={parameters}")
    if not isinstance(parameters, dict):
        logger.error(f"❌ call_tool 入口参数类型错误！期望dict，实际{type(parameters)}")
        raise MCPException("INVALID_PARAMETERS", f"参数必须是字典类型，当前是{type(parameters)}")
```

#### 修改2: 在SSE发送前检查
**文件**: `backend/src/mcp/enhanced_client.py:718-725`

```python
# ✅ 调试日志：检查参数类型
logger.info(f"发送SSE工具调用请求: {name}, ID: {request_id}")
logger.info(f"🔍 参数类型检查: type={type(parameters)}, value={parameters}")

# ✅ 参数类型验证
if not isinstance(parameters, dict):
    logger.error(f"❌ 参数类型错误！期望dict，实际{type(parameters)}")
    raise MCPException("INVALID_PARAMETERS", f"参数必须是字典类型，当前是{type(parameters)}")
```

---

## 🧪 测试验证

### 验证步骤

1. **重启后端服务**:
```bash
# 确保修复生效
poetry run python backend/main.py
```

2. **触发健康监控任务**:
```bash
# 手动触发或等待定时任务
# 观察日志中的参数类型输出
```

3. **检查日志输出**:
```
✅ 正常情况:
📥 call_tool 入口 - 工具=k8s-get-nodes, 参数类型=<class 'dict'>, 参数值={}
🔍 参数类型检查: type=<class 'dict'>, value={}

❌ 异常情况:
📥 call_tool 入口 - 工具=k8s-get-nodes, 参数类型=<class 'list'>, 参数值=[{}, {}]
❌ call_tool 入口参数类型错误！期望dict，实际<class 'list'>
```

### 直接测试工具调用
```python
# 测试脚本
import asyncio
from backend.src.mcp.enhanced_client import EnhancedMCPClient

async def test():
    client = EnhancedMCPClient()
    
    # ✅ 正确调用
    result = await client.call_tool("k8s-get-nodes", {})
    print("成功:", result)
    
    # ❌ 错误调用（会被拦截）
    try:
        result = await client.call_tool("k8s-get-nodes", [{}, {}])
    except Exception as e:
        print("错误被捕获:", e)

asyncio.run(test())
```

---

## 📊 根本原因分析

### 可疑代码区域

#### 1. 参数合并逻辑
**位置**: `backend/src/mcp/enhanced_client.py:1070-1073`

```python
if tool_config.default_parameters:
    merged_params = tool_config.default_parameters.copy()
    merged_params.update(parameters)
    parameters = merged_params
```

**检查点**:
- ✅ `default_parameters` 是字典
- ✅ `merged_params.update()` 保持字典类型
- ✅ 不会产生列表

#### 2. 批量工具调用
**搜索**: 是否有地方将多个工具参数收集到数组中？

```bash
# 搜索可疑模式
grep -r "arguments.*\[" backend/src/mcp/
grep -r "parameters.*append" backend/src/mcp/
```

#### 3. JSON序列化
**检查**: aiohttp的 `json=request_data` 是否正确序列化？

```python
# 正常情况
request_data = {"arguments": {}}
# JSON: {"arguments": {}}  ✅

# 异常情况（需要查找原因）
request_data = {"arguments": [{}, {}]}
# JSON: {"arguments": [{}, {}]}  ❌
```

---

## 🎯 后续行动

### 立即行动
1. ✅ **已添加类型检查** - 防止错误参数传递
2. ⏳ **观察日志输出** - 定位参数变成列表的位置
3. ⏳ **复现问题** - 触发健康监控任务

### 深度调查
1. **检查所有 `call_tool` 调用点**:
```bash
grep -r "call_tool" backend/src/scheduler/
grep -r "call_tool" backend/src/api/
```

2. **检查参数处理链路**:
```
调用处 → EnhancedMCPClient.call_tool → 
MCPServerConnection.call_tool → 
_call_tool_sse → 
POST请求 → 
服务器端验证
```

3. **添加更多调试日志**:
```python
# 在关键节点记录参数状态
logger.debug(f"Step1: {type(params)}, {params}")
logger.debug(f"Step2: {type(params)}, {params}")
```

---

## 💡 防止类似问题

### 代码规范

1. **类型注解强制**:
```python
def call_tool(name: str, parameters: Dict[str, Any]) -> Any:
    """明确参数类型"""
```

2. **运行时验证**:
```python
assert isinstance(parameters, dict), "参数必须是字典"
```

3. **单元测试覆盖**:
```python
def test_call_tool_invalid_params():
    with pytest.raises(MCPException):
        await client.call_tool("tool", [{}])  # 应该抛出异常
```

### 监控告警
```python
# 添加参数类型监控
if not isinstance(parameters, dict):
    metrics.increment("mcp.invalid_params")
    alert_manager.send("参数类型错误告警")
```

---

## 📝 修改文件清单

| 文件 | 修改内容 | 状态 |
|------|---------|------|
| `backend/src/mcp/enhanced_client.py` | 添加入口参数类型检查 (1054-1058行) | ✅ 完成 |
| `backend/src/mcp/enhanced_client.py` | 添加SSE发送前类型检查 (718-725行) | ✅ 完成 |
| `BUG-FIX-MCP-422-ERROR.md` | 创建问题分析文档 | ✅ 完成 |

---

## 🔚 结论

### 问题根源
**参数类型被错误地转换为列表** `[{}, {}]`，导致Pydantic验证失败。

### 解决方案
1. ✅ 添加双层类型检查，早期发现问题
2. ⏳ 通过日志定位参数变成列表的具体位置
3. ⏳ 修复根本原因

### 预期效果
- **短期**: 通过类型检查阻止错误参数传递，避免422错误
- **长期**: 找到并修复参数类型转换的根本原因

---

**修复时间**: 2025-09-30 14:00:00  
**修复状态**: ✅ 类型检查已添加，等待日志验证  
**下一步**: 观察生产日志，定位参数变成列表的具体代码位置


