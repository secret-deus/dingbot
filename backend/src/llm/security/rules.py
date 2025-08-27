"""
多规则脱敏引擎
"""
import re
import hashlib
import base64
from typing import Dict, List, Tuple, Any
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import uuid
from .surname_dict import SurnameDict

class SensitiveDataRules:
    """敏感数据脱敏规则集"""
    
    def __init__(self, encryption_key: bytes = None):
        self.encryption_key = encryption_key or get_random_bytes(32)
        
        # 初始化姓氏词典
        self.surname_dict = SurnameDict()
        
        # 定义各种敏感信息的匹配规则
        self.rules = {
            "hostname": {
                "pattern": r"(?i)(worker|master|node|host|server)[-\w\d\-\.]+\d{1,3}[-\d\-]*\d+",
                "strategy": "format_preserve_hash",
                "template": "host-{hash}--{suffix}"
            },
            "ip_address": {
                "pattern": r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b",
                "strategy": "network_mapping",
                "preserve_last_octet": True,
                "use_unique_mapping": True
            },
            "phone": {
                "pattern": r"1[3-9]\d{9}",
                "strategy": "partial_mask_encrypt", 
                "mask_pattern": "***",
                "preserve_prefix": 3,
                "preserve_suffix": 4
            },
            "chinese_name": {
                "strategy": "name_mask_dict",
                "preserve_first": True,
                "use_surname_dict": True
            },
            "email": {
                "pattern": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
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
        from loguru import logger
        
        # logger.error(f"🔍 开始脱敏字符串: '{text[:200]}...'")
        masked_text = text
        total_replacements = 0
        
        # 先处理基于词典的姓名脱敏
        chinese_name_rule = self.rules.get("chinese_name")
        if chinese_name_rule and chinese_name_rule["strategy"] == "name_mask_dict":
            names_found = self.surname_dict.find_names_in_text(masked_text)
            # logger.error(f"📋 词典匹配找到 {len(names_found)} 个姓名:")
            
            # 从后向前替换，避免位置偏移
            for name, start, end in reversed(names_found):
                logger.error(f"   匹配项: '{name}' (位置: {start}-{end})")
                
                # 检查是否已经脱敏过
                if mapping_store.is_masked(name):
                    logger.error(f"⏭️ 跳过已脱敏项: '{name}'")
                    continue
                
                # 进行姓名脱敏
                masked = self._name_mask(name, chinese_name_rule)
                
                # 替换文本
                masked_text = masked_text[:start] + masked + masked_text[end:]
                
                # 存储映射关系
                mapping_store.add_mapping(name, masked, "chinese_name")
                total_replacements += 1
                # logger.error(f"✅ 脱敏完成: '{name}' → '{masked}' (规则: chinese_name)")
        
        # 处理其他基于正则表达式的规则
        for rule_name, rule_config in self.rules.items():
            if rule_name == "chinese_name":
                continue  # 已经处理过了
                
            pattern = rule_config.get("pattern")
            if not pattern:
                continue
                
            strategy = rule_config["strategy"]
            
            # 先检查是否有匹配
            matches = list(re.finditer(pattern, masked_text))
            # logger.error(f"📋 规则 '{rule_name}' 匹配了 {len(matches)} 项:")
            for match in matches:
                logger.error(f"   匹配项: '{match.group(0)}' (位置: {match.start()}-{match.end()})")
            
            def replace_match(match):
                nonlocal total_replacements
                original = match.group(0)
                
                # 检查是否已经脱敏过
                if mapping_store.is_masked(original):
                    logger.error(f"⏭️ 跳过已脱敏项: '{original}'")
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
                elif strategy == "name_mask":
                    masked = self._name_mask(original, rule_config)
                else:
                    masked = f"***{rule_name}***"
                
                # 存储映射关系
                mapping_store.add_mapping(original, masked, rule_name)
                total_replacements += 1
                # logger.error(f"✅ 脱敏完成: '{original}' → '{masked}' (规则: {rule_name})")
                return masked
            
            masked_text = re.sub(pattern, replace_match, masked_text)
        
        logger.error(f"📊 脱敏完成: 总共替换了 {total_replacements} 项")
        logger.error(f"🔒 最终脱敏结果: '{masked_text[:200]}...'")
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
        """网络地址映射 - 改进版，使用唯一映射避免恢复冲突"""
        parts = ip.split('.')
        
        if config.get("use_unique_mapping", False):
            # 生成基于原IP的唯一标识符
            hash_obj = hashlib.md5(ip.encode()).hexdigest()[:4]
            
            if config.get("preserve_last_octet"):
                # 格式: 10.0.{hash}.{last_octet}
                return f"10.0.{hash_obj}.{parts[-1]}"
            else:
                # 格式: 10.0.{hash}.x
                return f"10.0.{hash_obj}.x"
        else:
            # 原有的简单映射方式
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
    
    def _name_mask(self, name: str, config: Dict) -> str:
        """中文姓名脱敏 - 保留姓氏，名字用xx替代"""
        if len(name) <= 1:
            return "x"
        
        if config.get("preserve_first", True):
            # 保留第一个字（姓氏），其余用x替代
            return name[0] + "x" * (len(name) - 1)
        else:
            # 全部用x替代
            return "x" * len(name)
    
    def _encrypt_value(self, value: str) -> str:
        """AES加密值"""
        cipher = AES.new(self.encryption_key, AES.MODE_EAX)
        nonce = cipher.nonce
        ciphertext, tag = cipher.encrypt_and_digest(value.encode())
        return base64.b64encode(nonce + tag + ciphertext).decode() 