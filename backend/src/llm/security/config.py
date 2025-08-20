"""
脱敏配置管理
"""
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