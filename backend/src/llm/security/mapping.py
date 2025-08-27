"""
脱敏映射存储管理
"""
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
        """恢复文本中的脱敏信息 - 改进版，支持更准确的恢复"""
        with self.lock:
            self.last_used = time.time()
            restored_text = text
            
            # 按照脱敏值长度降序排列，避免部分匹配问题
            sorted_masked = sorted(self.masked_to_original.keys(), 
                                 key=len, reverse=True)
            
            # 记录恢复操作
            restore_count = 0
            
            from loguru import logger
            logger.info(f"🔓 开始恢复脱敏信息，可用映射: {len(sorted_masked)} 个")
            logger.info(f"📝 当前待恢复文本片段: '{text[:200]}...'")
            for i, masked_value in enumerate(sorted_masked):
                logger.info(f"  映射#{i+1}: '{masked_value}' → '{self.masked_to_original[masked_value]}'")
            
            for masked_value in sorted_masked:
                original_value = self.masked_to_original[masked_value]
                
                # 检查是否存在该脱敏值
                if masked_value in restored_text:
                    logger.info(f"🔍 在文本中找到脱敏值: '{masked_value}'")
                    
                    # 使用更精确的替换策略
                    import re
                    escaped_masked = re.escape(masked_value)
                    
                    # 根据脱敏值的格式选择合适的匹配模式
                    if re.match(r'^\d+\.\d+\.[a-zA-Z0-9]+\.\d+$', masked_value):
                        # 脱敏IP地址格式（如：10.0.cac9.79, 10.0.c9aa.80）
                        pattern = escaped_masked
                        # logger.debug(f"🌐 使用脱敏IP地址模式恢复: {pattern}")
                    elif re.match(r'^\d+\.\d+\.\d+\.\d+$', masked_value):
                        # 标准IP地址格式（如：192.168.1.100）
                        pattern = escaped_masked
                        # logger.debug(f"🌐 使用标准IP地址模式恢复: {pattern}")
                    elif re.match(r'^host-\w+-+\d+$', masked_value):
                        # 主机名格式（如：host-abc123--001）
                        pattern = r'\b' + escaped_masked + r'\b'
                        # logger.debug(f"🖥️ 使用主机名模式恢复: {pattern}")
                    else:
                        # 通用格式，使用直接替换
                        pattern = escaped_masked
                        # logger.debug(f"🔧 使用通用模式恢复: {pattern}")
                    
                    new_text = re.sub(pattern, original_value, restored_text)
                    if new_text != restored_text:
                        restore_count += 1
                        restored_text = new_text
                        logger.info(f"✅ 恢复成功: '{masked_value}' → '{original_value}'")
                    else:
                        logger.warning(f"⚠️ 恢复失败，未找到匹配项: '{masked_value}' (使用模式: {pattern})")
                else:
                    # logger.info(f"⏭️ 文本中未找到脱敏值: '{masked_value}'")
                    pass
            
            if restore_count > 0:
                logger.info(f"🔓 成功恢复 {restore_count} 个脱敏值")
            else:
                # logger.debug("💭 无脱敏内容需要恢复")
                pass
            
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
    
    def get_session(self, session_id: str) -> MaskingMappingStore:
        """获取会话存储（别名方法）"""
        return self.get_session_store(session_id)
    
    def cleanup_expired_sessions(self, max_age_seconds: int = 3600):
        """清理过期会话"""
        with self.lock:
            expired_sessions = []
            for session_id, store in self.sessions.items():
                if store.cleanup_expired(max_age_seconds):
                    expired_sessions.append(session_id)
            
            for session_id in expired_sessions:
                del self.sessions[session_id] 