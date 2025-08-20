"""
核心脱敏引擎
"""
from typing import Any, List, Dict
import json
import time
from loguru import logger
from .rules import SensitiveDataRules
from .mapping import SessionMappingManager, MaskingMappingStore
from .config import MaskingConfig

class DataMasker:
    """数据脱敏器"""
    
    def __init__(self, config: MaskingConfig = None):
        self.config = config or MaskingConfig()
        self.rules = SensitiveDataRules(self.config.encryption_key)
        self.session_manager = SessionMappingManager()
        self.enabled = self.config.masking_enabled
        
        logger.info(f"🔒 数据脱敏器初始化完成，状态: {'启用' if self.enabled else '禁用'}")
    
    def mask_tool_results(self, tool_results: List[Any], session_id: str) -> List[Any]:
        """脱敏工具结果 - 在第二阶段LLM调用前执行"""
        if not self.enabled:
            logger.debug("脱敏功能已禁用，跳过脱敏处理")
            return tool_results
        
        try:
            session_store = self.session_manager.get_session_store(session_id)
            masked_results = []
            
            logger.info(f"🔒 开始脱敏工具结果，会话ID: {session_id}")
            
            for i, result in enumerate(tool_results):
                if result is not None:
                    # 记录原始数据
                    original_json = json.dumps(result, ensure_ascii=False, default=str)
                    logger.info(f"📋 原始工具结果 #{i+1} (长度: {len(original_json)}):")
                    logger.info(f"   {original_json[:500]}{'...' if len(original_json) > 500 else ''}")
                    
                    # 执行脱敏
                    masked_result = self.rules.apply_rules(result, session_store)
                    masked_json = json.dumps(masked_result, ensure_ascii=False, default=str)
                    
                    # 记录脱敏后数据
                    logger.warning(f"🔒 脱敏后工具结果 #{i+1} (长度: {len(masked_json)}):")
                    logger.warning(f"   {masked_json[:500]}{'...' if len(masked_json) > 500 else ''}")
                    
                    masked_results.append(masked_result)
                    
                    # 统计脱敏信息
                    mapping_count = len(session_store.original_to_masked)
                    logger.info(f"   已建立 {mapping_count} 个脱敏映射")
                else:
                    masked_results.append(result)
            
            logger.success(f"✅ 工具结果脱敏完成，处理了 {len(tool_results)} 个结果")
            return masked_results
            
        except Exception as e:
            logger.error(f"❌ 工具结果脱敏失败: {e}", exc_info=True)
            return tool_results  # 失败时返回原始数据
    
    def restore_llm_response(self, response_text: str, session_id: str) -> str:
        """恢复LLM响应中的敏感信息 - 在流式输出前执行"""
        if not self.enabled:
            return response_text
        
        try:
            session_store = self.session_manager.get_session_store(session_id)
            
            # 只有当有映射关系时才进行恢复
            if not session_store.masked_to_original:
                return response_text
            
            # 记录恢复前的响应
            if self.config.debug_logging:
                logger.debug(f"🔓 恢复前响应片段: {response_text[:100]}...")
            
            restored_text = session_store.restore_text(response_text)
            
            # 检查是否有恢复操作
            if restored_text != response_text:
                mapping_count = len(session_store.masked_to_original)
                logger.info(f"🔓 响应已恢复，当前有 {mapping_count} 个脱敏映射可用")
                
                if self.config.debug_logging:
                    logger.debug(f"🔓 恢复后响应片段: {restored_text[:100]}...")
            
            return restored_text
            
        except Exception as e:
            logger.error(f"❌ LLM响应恢复失败: {e}", exc_info=True)
            return response_text  # 失败时返回原始响应
    
    def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """获取会话统计信息"""
        try:
            if session_id not in self.session_manager.sessions:
                return {"mapping_count": 0, "session_exists": False}
            
            session_store = self.session_manager.sessions[session_id]
            return {
                "mapping_count": len(session_store.original_to_masked),
                "session_exists": True,
                "created_at": session_store.created_at,
                "last_used": session_store.last_used
            }
        except Exception as e:
            logger.error(f"❌ 获取会话统计失败: {e}")
            return {"mapping_count": 0, "session_exists": False, "error": str(e)}
    
    def cleanup_session(self, session_id: str):
        """清理会话数据"""
        try:
            if session_id in self.session_manager.sessions:
                mapping_count = len(self.session_manager.sessions[session_id].original_to_masked)
                del self.session_manager.sessions[session_id]
                logger.info(f"🧹 会话 {session_id} 的脱敏数据已清理，清理了 {mapping_count} 个映射")
        except Exception as e:
            logger.error(f"❌ 清理会话数据失败: {e}")
    
    def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """获取会话统计信息"""
        try:
            session_store = self.session_manager.get_session_store(session_id)
            return {
                "session_id": session_id,
                "mapping_count": len(session_store.original_to_masked),
                "created_at": session_store.created_at,
                "last_used": session_store.last_used,
                "age_seconds": time.time() - session_store.created_at
            }
        except Exception as e:
            logger.error(f"❌ 获取会话统计失败: {e}")
            return {} 