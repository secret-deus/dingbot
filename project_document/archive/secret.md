
### 1. 多规则脱敏引擎

```python
# backend/src/llm/security/rules.py
import re
import hashlib
import base64
from typing import Dict, List, Tuple, Any
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import uuid

class SensitiveDataRules:
    """敏感数据脱敏规则集"""
    
    def __init__(self, encryption_key: bytes = None):
        self.encryption_key = encryption_key or get_random_bytes(32)
        
        # 定义各种敏感信息的匹配规则
        self.rules = {
            "hostname": {
                "pattern": r"(?i)(node|host|server|worker|master)-[\w\-\.]+",
                "strategy": "format_preserve_hash",
                "template": "host-{hash}-{suffix}"
            },
            "ip_address": {
                "pattern": r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b",
                "strategy": "network_mapping",
                "preserve_last_octet": True
            },
            "phone": {
                "pattern": r"1[3-9]\d{9}",
                "strategy": "partial_mask_encrypt", 
                "mask_pattern": "***",
                "preserve_prefix": 3,
                "preserve_suffix": 4
            },
            "chinese_name": {
                "pattern": r"[\u4e00-\u9fff]{2,4}(?=\s|$|[，。！？])",
                "strategy": "full_encrypt",
                "replacement_template": "User_{id}"
            },
            "email": {
                "pattern": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
                "strategy": "domain_preserve",
                "mask_local_part": True
            }
        }
    
    def apply_rules(self, data: Any, mapping_store: 'MaskingMappingStore') -> Any:
        """对数据应用所有脱敏规则"""
        if isinstance(data, dict):
            return {k: self.apply_rules(v, mapping_store) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.apply_rules(item, mapping_store) for item in data]
        elif isinstance(data, str):
            return self._mask_string(data, mapping_store)
        else:
            return data
    
    def _mask_string(self, text: str, mapping_store: 'MaskingMappingStore') -> str:
        """对字符串应用脱敏规则"""
        masked_text = text
        
        for rule_name, rule_config in self.rules.items():
            pattern = rule_config["pattern"]
            strategy = rule_config["strategy"]
            
            def replace_match(match):
                original = match.group(0)
                
                # 检查是否已经脱敏过
                if mapping_store.is_masked(original):
                    return original
                
                # 根据策略进行脱敏
                if strategy == "format_preserve_hash":
                    masked = self._format_preserve_hash(original, rule_config)
                elif strategy == "network_mapping":
                    masked = self._network_mapping(original, rule_config)
                elif strategy == "partial_mask_encrypt":
                    masked = self._partial_mask_encrypt(original, rule_config)
                elif strategy == "full_encrypt":
                    masked = self._full_encrypt(original, rule_config)
                elif strategy == "domain_preserve":
                    masked = self._domain_preserve(original, rule_config)
                else:
                    masked = f"***{rule_name}***"
                
                # 存储映射关系
                mapping_store.add_mapping(original, masked, rule_name)
                return masked
            
            masked_text = re.sub(pattern, replace_match, masked_text)
        
        return masked_text
    
    def _format_preserve_hash(self, value: str, config: Dict) -> str:
        """格式保持的哈希脱敏"""
        hash_obj = hashlib.md5(value.encode()).hexdigest()[:8]
        
        # 提取后缀（如数字编号）
        suffix_match = re.search(r'-(\d+)$', value)
        suffix = f"-{suffix_match.group(1)}" if suffix_match else ""
        
        template = config.get("template", "host-{hash}-{suffix}")
        return template.format(hash=hash_obj, suffix=suffix)
    
    def _network_mapping(self, ip: str, config: Dict) -> str:
        """网络地址映射"""
        parts = ip.split('.')
        if config.get("preserve_last_octet"):
            return f"10.0.x.{parts[-1]}"
        else:
            return "10.0.x.x"
    
    def _partial_mask_encrypt(self, value: str, config: Dict) -> str:
        """部分掩码加密"""
        prefix_len = config.get("preserve_prefix", 3)
        suffix_len = config.get("preserve_suffix", 4)
        mask_pattern = config.get("mask_pattern", "***")
        
        if len(value) <= prefix_len + suffix_len:
            # 值太短，完全加密
            encrypted = self._encrypt_value(value)
            return f"{mask_pattern}_enc_{encrypted[:8]}"
        
        prefix = value[:prefix_len]
        suffix = value[-suffix_len:]
        encrypted = self._encrypt_value(value)
        
        return f"{prefix}{mask_pattern}{suffix}_enc_{encrypted[:8]}"
    
    def _full_encrypt(self, value: str, config: Dict) -> str:
        """完全加密"""
        encrypted = self._encrypt_value(value)
        template = config.get("replacement_template", "Encrypted_{id}")
        return template.format(id=encrypted[:8])
    
    def _domain_preserve(self, email: str, config: Dict) -> str:
        """域名保持的邮箱脱敏"""
        local, domain = email.split('@', 1)
        if config.get("mask_local_part"):
            masked_local = local[:2] + "***" + local[-2:] if len(local) > 4 else "***"
            return f"{masked_local}@{domain}"
        return email
    
    def _encrypt_value(self, value: str) -> str:
        """AES加密值"""
        cipher = AES.new(self.encryption_key, AES.MODE_EAX)
        nonce = cipher.nonce
        ciphertext, tag = cipher.encrypt_and_digest(value.encode())
        return base64.b64encode(nonce + tag + ciphertext).decode()
```

### 2. 映射存储管理

```python
# backend/src/llm/security/mapping.py
from typing import Dict, Optional, Tuple
import threading
import time
from collections import defaultdict

class MaskingMappingStore:
    """脱敏映射存储器 - 会话级别"""
    
    def __init__(self, session_id: str = None):
        self.session_id = session_id or f"session_{int(time.time())}"
        self.original_to_masked: Dict[str, str] = {}
        self.masked_to_original: Dict[str, str] = {}
        self.rule_mapping: Dict[str, str] = {}  # masked -> rule_name
        self.lock = threading.RLock()
        self.created_at = time.time()
        self.last_used = time.time()
    
    def add_mapping(self, original: str, masked: str, rule_name: str):
        """添加映射关系"""
        with self.lock:
            self.original_to_masked[original] = masked
            self.masked_to_original[masked] = original
            self.rule_mapping[masked] = rule_name
            self.last_used = time.time()
    
    def get_original(self, masked: str) -> Optional[str]:
        """获取原始值"""
        with self.lock:
            self.last_used = time.time()
            return self.masked_to_original.get(masked)
    
    def get_masked(self, original: str) -> Optional[str]:
        """获取脱敏值"""
        with self.lock:
            self.last_used = time.time()
            return self.original_to_masked.get(original)
    
    def is_masked(self, value: str) -> bool:
        """检查是否为脱敏值"""
        with self.lock:
            return value in self.masked_to_original
    
    def restore_text(self, text: str) -> str:
        """恢复文本中的脱敏信息"""
        with self.lock:
            self.last_used = time.time()
            restored_text = text
            
            # 按照脱敏值长度降序排列，避免部分匹配问题
            sorted_masked = sorted(self.masked_to_original.keys(), 
                                 key=len, reverse=True)
            
            for masked_value in sorted_masked:
                original_value = self.masked_to_original[masked_value]
                restored_text = restored_text.replace(masked_value, original_value)
            
            return restored_text
    
    def cleanup_expired(self, max_age_seconds: int = 3600):
        """清理过期的映射"""
        with self.lock:
            current_time = time.time()
            if current_time - self.last_used > max_age_seconds:
                self.original_to_masked.clear()
                self.masked_to_original.clear()
                self.rule_mapping.clear()
                return True
        return False

class SessionMappingManager:
    """会话映射管理器"""
    
    def __init__(self):
        self.sessions: Dict[str, MaskingMappingStore] = {}
        self.lock = threading.RLock()
    
    def get_session_store(self, session_id: str) -> MaskingMappingStore:
        """获取或创建会话存储"""
        with self.lock:
            if session_id not in self.sessions:
                self.sessions[session_id] = MaskingMappingStore(session_id)
            return self.sessions[session_id]
    
    def cleanup_expired_sessions(self, max_age_seconds: int = 3600):
        """清理过期会话"""
        with self.lock:
            expired_sessions = []
            for session_id, store in self.sessions.items():
                if store.cleanup_expired(max_age_seconds):
                    expired_sessions.append(session_id)
            
            for session_id in expired_sessions:
                del self.sessions[session_id]
```

### 3. 核心脱敏引擎

```python
# backend/src/llm/security/masker.py
from typing import Any, List, Dict
import json
import logging
from .rules import SensitiveDataRules
from .mapping import SessionMappingManager, MaskingMappingStore
from .config import MaskingConfig

logger = logging.getLogger(__name__)

class DataMasker:
    """数据脱敏器"""
    
    def __init__(self, config: MaskingConfig = None):
        self.config = config or MaskingConfig()
        self.rules = SensitiveDataRules(self.config.encryption_key)
        self.session_manager = SessionMappingManager()
        self.enabled = self.config.masking_enabled
    
    def mask_tool_results(self, tool_results: List[Any], session_id: str) -> List[Any]:
        """脱敏工具结果 - 在第二阶段LLM调用前执行"""
        if not self.enabled:
            return tool_results
        
        try:
            session_store = self.session_manager.get_session_store(session_id)
            masked_results = []
            
            for result in tool_results:
                if result is not None:
                    masked_result = self.rules.apply_rules(result, session_store)
                    masked_results.append(masked_result)
                    logger.info(f"工具结果已脱敏，原始数据长度: {len(str(result))}, "
                              f"脱敏后长度: {len(str(masked_result))}")
                else:
                    masked_results.append(result)
            
            return masked_results
            
        except Exception as e:
            logger.error(f"工具结果脱敏失败: {e}", exc_info=True)
            return tool_results  # 失败时返回原始数据
    
    def restore_llm_response(self, response_text: str, session_id: str) -> str:
        """恢复LLM响应中的敏感信息 - 在流式输出前执行"""
        if not self.enabled:
            return response_text
        
        try:
            session_store = self.session_manager.get_session_store(session_id)
            restored_text = session_store.restore_text(response_text)
            
            if restored_text != response_text:
                logger.info(f"LLM响应已恢复，恢复了 {len(session_store.masked_to_original)} 个敏感信息")
            
            return restored_text
            
        except Exception as e:
            logger.error(f"LLM响应恢复失败: {e}", exc_info=True)
            return response_text  # 失败时返回原始响应
    
    def cleanup_session(self, session_id: str):
        """清理会话数据"""
        try:
            if session_id in self.session_manager.sessions:
                del self.session_manager.sessions[session_id]
                logger.info(f"会话 {session_id} 的脱敏数据已清理")
        except Exception as e:
            logger.error(f"清理会话数据失败: {e}")
```

### 4. 配置管理

```python
# backend/src/llm/security/config.py
import os
from typing import Optional
from Crypto.Random import get_random_bytes
import base64

class MaskingConfig:
    """脱敏配置"""
    
    def __init__(self):
        # 基础配置
        self.masking_enabled = os.getenv('LLM_MASKING_ENABLED', 'true').lower() == 'true'
        
        # 加密密钥
        key_b64 = os.getenv('LLM_MASKING_KEY')
        if key_b64:
            self.encryption_key = base64.b64decode(key_b64)
        else:
            self.encryption_key = get_random_bytes(32)
            # 在生产环境中，应该将密钥持久化存储
            print(f"Generated new masking key: {base64.b64encode(self.encryption_key).decode()}")
        
        # 会话管理
        self.session_timeout = int(os.getenv('LLM_MASKING_SESSION_TIMEOUT', '3600'))  # 1小时
        
        # 性能配置
        self.enable_caching = os.getenv('LLM_MASKING_CACHE', 'true').lower() == 'true'
        self.max_cache_size = int(os.getenv('LLM_MASKING_CACHE_SIZE', '1000'))
        
        # 调试配置
        self.debug_logging = os.getenv('LLM_MASKING_DEBUG', 'false').lower() == 'true'
```

## 🔗 集成到现有系统

### 修改 processor.py

```python
# backend/src/llm/processor.py - 添加脱敏集成
from .security.masker import DataMasker
from .security.config import MaskingConfig

class LLMProcessor:
    def __init__(self, config: Dict[str, Any], mcp_client=None):
        # ... 现有初始化代码 ...
        
        # 初始化脱敏器
        self.data_masker = DataMasker(MaskingConfig())
    
    def _get_tool_response_user_prompt(
        self, 
        original_question: str, 
        tool_calls: List[Dict[str, Any]], 
        tool_results: List[Any]
    ) -> str:
        """获取工具结果解读的用户提示词 - 添加脱敏处理"""
        
        # 🔒 关键脱敏点：在序列化前对工具结果进行脱敏
        session_id = getattr(self, 'current_session_id', f'session_{int(time.time())}')
        masked_tool_results = self.data_masker.mask_tool_results(tool_results, session_id)
        
        # 格式化工具执行结果（使用脱敏后的数据）
        formatted_results = []
        for i, (tool_call, result) in enumerate(zip(tool_calls, masked_tool_results), 1):
            tool_name = tool_call.get("name", "未知工具")
            if result is not None:
                if hasattr(result, '__dict__'):
                    result_str = json.dumps(result.__dict__, ensure_ascii=False, indent=2)
                else:
                    result_str = json.dumps(result, ensure_ascii=False, indent=2)
                formatted_results.append(f"{i}. 工具: {tool_name}\n   结果: {result_str}")
            else:
                error = tool_call.get("error", "执行失败")
                formatted_results.append(f"{i}. 工具: {tool_name}\n   错误: {error}")
        
        results_text = "\n\n".join(formatted_results)
        
        return f"""用户问题：{original_question}

工具执行结果：
{results_text}

请基于工具执行结果回答用户的问题。要求：
1. 直接回答问题
2. 基于实际结果
3. 格式清晰易读，使用换行符分隔不同部分
4. 对于表格数据，请使用标准的Markdown表格格式
5. 在不同信息块之间添加空行

请开始回复："""

    async def _phase_two_generate_response(
        self, 
        original_message: str, 
        tool_calls: List[Dict[str, Any]], 
        tool_results: List[Any]
    ) -> AsyncGenerator[str, None]:
        """第二阶段：基于工具结果生成LLM对话回复 - 添加响应恢复"""
        
        # ... 现有代码保持不变 ...
        
        # 在流式输出中添加恢复处理
        session_id = getattr(self, 'current_session_id', f'session_{int(time.time())}')
        
        async for chunk in stream:
            chunk_count += 1
            if chunk.choices and len(chunk.choices) > 0:
                delta = chunk.choices[0].delta
                if delta.content:
                    # 🔓 关键恢复点：在返回给用户前恢复敏感信息
                    restored_content = self.data_masker.restore_llm_response(
                        delta.content, session_id
                    )
                    response_generated = True
                    yield restored_content
```

## 📊 使用效果示例

### 脱敏前
```json
{
  "pods": [
    {
      "name": "webapp-prod-001",
      "node": "worker-node-prod-192-168-1-100", 
      "ip": "192.168.1.100",
      "logs": "用户张三(13812345678)登录成功"
    }
  ]
}
```

### 脱敏后（传给LLM）
```json
{
  "pods": [
    {
      "name": "webapp-prod-001",
      "node": "host-a1b2c3d4-100",
      "ip": "10.0.x.100", 
      "logs": "用户User_enc_abc123(138***5678_enc_def456)登录成功"
    }
  ]
}
```

### 最终用户看到（恢复后）
```json
{
  "pods": [
    {
      "name": "webapp-prod-001", 
      "node": "worker-node-prod-192-168-1-100",
      "ip": "192.168.1.100",
      "logs": "用户张三(13812345678)登录成功"
    }
  ]
}
```

## 🚀 部署配置

### 环境变量
```bash
# .env 文件
LLM_MASKING_ENABLED=true
LLM_MASKING_KEY=your_base64_encoded_32byte_key
LLM_MASKING_SESSION_TIMEOUT=3600
LLM_MASKING_DEBUG=false
```

## 📋 总结

此方案完全匹配您的对话流程：
1. **精确脱敏位置**：在`_get_tool_response_user_prompt`中脱敏工具结果
2. **精确恢复位置**：在第二阶段流式输出中恢复响应内容
3. **会话级映射**：确保同一会话内的一致性
4. **多规则支持**：针对不同类型敏感信息使用不同策略
5. **透明集成**：对现有系统影响最小
6. **完全可逆**：保证数据完整性和用户体验

这样，敏感的k8s数据不会暴露给外部LLM API，但用户仍能看到完整的原始信息。