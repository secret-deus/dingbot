#!/usr/bin/env python3
"""
LLM配置迁移脚本
支持环境变量到文件配置的迁移，以及配置备份和恢复
"""

import os
import sys
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import argparse

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger
from dotenv import load_dotenv

def setup_logging():
    """设置日志"""
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO"
    )

def load_environment():
    """加载环境变量"""
    env_files = ["config.env", ".env", "backend/config.env"]
    
    for env_file in env_files:
        if os.path.exists(env_file):
            load_dotenv(env_file, override=True)
            logger.info(f"✅ 加载环境变量文件: {env_file}")
            return env_file
    
    logger.warning("⚠️ 未找到环境变量文件，使用系统环境变量")
    return None

def read_env_config() -> Dict[str, Any]:
    """读取环境变量配置"""
    config_data = {
        "enabled": os.getenv("LLM_ENABLED", "true").lower() == "true",
        "provider": os.getenv("LLM_PROVIDER", "openai"),
        "model": os.getenv("LLM_MODEL", "gpt-3.5-turbo"),
        "api_key": os.getenv("LLM_API_KEY", ""),
        "base_url": os.getenv("LLM_BASE_URL"),
        "organization": os.getenv("LLM_ORGANIZATION"),
        "api_version": os.getenv("LLM_API_VERSION"),
        "deployment_name": os.getenv("LLM_DEPLOYMENT_NAME"),
        "timeout": int(os.getenv("LLM_TIMEOUT", "30")),
        "max_retries": int(os.getenv("LLM_MAX_RETRIES", "3")),
        "temperature": float(os.getenv("LLM_TEMPERATURE", "0.7")),
        "max_tokens": int(os.getenv("LLM_MAX_TOKENS", "2000")),
        "stream": os.getenv("LLM_STREAM", "false").lower() == "true"
    }
    
    # 移除空值但保留重要字段
    filtered_config = {}
    important_fields = {"enabled", "provider", "model", "timeout", "max_retries", "temperature", "max_tokens", "stream"}
    
    for key, value in config_data.items():
        if key in important_fields:
            filtered_config[key] = value
        elif value is not None and value != "":
            filtered_config[key] = value
    
    return filtered_config

def create_provider_config(env_config: Dict[str, Any]) -> Dict[str, Any]:
    """从环境变量配置创建提供商配置"""
    provider_id = env_config.get("provider", "openai")
    
    provider_config = {
        "id": provider_id,
        "name": get_provider_display_name(provider_id),
        "enabled": env_config.get("enabled", True),
        "model": env_config.get("model", "gpt-3.5-turbo"),
        "temperature": env_config.get("temperature", 0.7),
        "max_tokens": env_config.get("max_tokens", 2000),
        "timeout": env_config.get("timeout", 30),
        "max_retries": env_config.get("max_retries", 3),
        "stream": env_config.get("stream", False)
    }
    
    # 添加特定提供商的字段
    if env_config.get("api_key"):
        provider_config["api_key"] = env_config["api_key"]
    if env_config.get("base_url"):
        provider_config["base_url"] = env_config["base_url"]
    if env_config.get("organization"):
        provider_config["organization"] = env_config["organization"]
    if env_config.get("api_version"):
        provider_config["api_version"] = env_config["api_version"]
    if env_config.get("deployment_name"):
        provider_config["deployment_name"] = env_config["deployment_name"]
    
    return provider_config

def get_provider_display_name(provider_id: str) -> str:
    """获取提供商显示名称"""
    names = {
        "openai": "OpenAI",
        "azure": "Azure OpenAI",
        "zhipu": "智谱AI",
        "qwen": "通义千问",
        "deepseek": "DeepSeek",
        "moonshot": "Moonshot AI",
        "ollama": "Ollama",
        "custom": "自定义API"
    }
    return names.get(provider_id, provider_id.title())

def create_config_from_env(env_config: Dict[str, Any]) -> Dict[str, Any]:
    """从环境变量创建完整配置"""
    provider_config = create_provider_config(env_config)
    
    config = {
        "version": "1.0",
        "name": "LLM配置",
        "description": f"从环境变量迁移生成于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "default_provider": env_config.get("provider", "openai"),
        "providers": [provider_config],
        "global_settings": {
            "timeout": env_config.get("timeout", 30),
            "max_retries": env_config.get("max_retries", 3),
            "enable_cache": True,
            "cache_timeout": 300
        }
    }
    
    return config

def backup_existing_config(config_file: Path) -> Optional[Path]:
    """备份现有配置文件"""
    if not config_file.exists():
        return None
        
    backup_dir = config_file.parent / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    backup_filename = f"llm_config_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    backup_path = backup_dir / backup_filename
    
    shutil.copy2(config_file, backup_path)
    logger.info(f"✅ 已备份现有配置: {backup_path}")
    
    return backup_path

def migrate_to_file_config(target_file: str = "config/llm_config.json", force: bool = False) -> bool:
    """将环境变量配置迁移到文件配置"""
    config_file = Path(target_file)
    
    # 检查目标文件是否存在
    if config_file.exists() and not force:
        logger.warning(f"⚠️ 配置文件已存在: {config_file}")
        logger.info("使用 --force 参数强制覆盖现有配置")
        return False
    
    # 备份现有配置
    if config_file.exists():
        backup_path = backup_existing_config(config_file)
        if backup_path:
            logger.info(f"📦 已创建备份: {backup_path}")
    
    # 创建目标目录
    config_file.parent.mkdir(parents=True, exist_ok=True)
    
    # 读取环境变量配置
    env_config = read_env_config()
    logger.info(f"📖 读取到环境变量配置: {env_config.get('provider', 'unknown')} - {env_config.get('model', 'unknown')}")
    
    # 创建文件配置
    file_config = create_config_from_env(env_config)
    
    # 保存配置文件
    try:
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(file_config, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ 配置迁移成功: {config_file}")
        
        # 创建迁移记录
        migration_log = {
            "migration_type": "env_to_file",
            "source": "environment_variables",
            "target": str(config_file),
            "timestamp": datetime.now().isoformat(),
            "env_config": env_config,
            "status": "success"
        }
        
        migration_log_file = config_file.parent / "migration.log"
        with open(migration_log_file, "w", encoding="utf-8") as f:
            json.dump(migration_log, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📝 迁移记录: {migration_log_file}")
        return True
        
    except Exception as e:
        logger.error(f"❌ 保存配置文件失败: {e}")
        return False

def rollback_to_env_config(config_file: str = "config/llm_config.json") -> bool:
    """回退到环境变量配置（删除文件配置）"""
    config_path = Path(config_file)
    
    if not config_path.exists():
        logger.info("✅ 配置文件不存在，已经是环境变量模式")
        return True
    
    # 创建回退备份
    backup_path = backup_existing_config(config_path)
    
    try:
        config_path.unlink()
        logger.info(f"✅ 已删除配置文件: {config_file}")
        logger.info("🔄 系统将回退到环境变量配置模式")
        
        if backup_path:
            logger.info(f"📦 配置已备份到: {backup_path}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 删除配置文件失败: {e}")
        return False

def list_backups(config_dir: str = "config") -> None:
    """列出所有配置备份"""
    backup_dir = Path(config_dir) / "backups"
    
    if not backup_dir.exists():
        logger.info("📂 备份目录不存在")
        return
    
    backup_files = list(backup_dir.glob("*.json"))
    
    if not backup_files:
        logger.info("📂 没有找到配置备份")
        return
    
    logger.info("📋 配置备份列表:")
    for backup_file in sorted(backup_files, reverse=True):
        stat = backup_file.stat()
        size_mb = stat.st_size / (1024 * 1024)
        modified_time = datetime.fromtimestamp(stat.st_mtime)
        
        logger.info(f"  📄 {backup_file.name}")
        logger.info(f"     大小: {size_mb:.2f} MB")
        logger.info(f"     时间: {modified_time.strftime('%Y-%m-%d %H:%M:%S')}")

def restore_backup(backup_name: str, config_dir: str = "config") -> bool:
    """从备份恢复配置"""
    backup_dir = Path(config_dir) / "backups"
    backup_file = backup_dir / backup_name
    config_file = Path(config_dir) / "llm_config.json"
    
    if not backup_file.exists():
        logger.error(f"❌ 备份文件不存在: {backup_file}")
        return False
    
    try:
        # 备份当前配置
        if config_file.exists():
            current_backup = backup_existing_config(config_file)
            logger.info(f"📦 当前配置已备份: {current_backup}")
        
        # 恢复备份
        shutil.copy2(backup_file, config_file)
        logger.info(f"✅ 已从备份恢复配置: {backup_name}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 恢复备份失败: {e}")
        return False

def validate_config(config_file: str = "config/llm_config.json") -> bool:
    """验证配置文件"""
    config_path = Path(config_file)
    
    if not config_path.exists():
        logger.warning(f"⚠️ 配置文件不存在: {config_file}")
        return False
    
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = json.load(f)
        
        # 基本结构验证
        required_fields = ["version", "name", "providers"]
        missing_fields = [field for field in required_fields if field not in config_data]
        
        if missing_fields:
            logger.error(f"❌ 配置文件缺少必要字段: {missing_fields}")
            return False
        
        # 提供商验证
        providers = config_data.get("providers", [])
        if not providers:
            logger.warning("⚠️ 配置文件没有提供商配置")
            return False
        
        enabled_providers = [p for p in providers if p.get("enabled", True)]
        logger.info(f"✅ 配置验证通过")
        logger.info(f"📊 总提供商: {len(providers)}, 已启用: {len(enabled_providers)}")
        
        # 显示提供商信息
        for provider in providers:
            status = "✅" if provider.get("enabled", True) else "❌"
            logger.info(f"  {status} {provider.get('name', provider.get('id', 'Unknown'))}: {provider.get('model', 'N/A')}")
        
        return True
        
    except json.JSONDecodeError as e:
        logger.error(f"❌ 配置文件JSON格式错误: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ 配置文件验证失败: {e}")
        return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="LLM配置迁移工具")
    
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # 迁移命令
    migrate_parser = subparsers.add_parser("migrate", help="将环境变量配置迁移到文件")
    migrate_parser.add_argument("--target", default="config/llm_config.json", help="目标配置文件路径")
    migrate_parser.add_argument("--force", action="store_true", help="强制覆盖现有配置文件")
    
    # 回退命令
    rollback_parser = subparsers.add_parser("rollback", help="回退到环境变量配置")
    rollback_parser.add_argument("--config", default="config/llm_config.json", help="要删除的配置文件路径")
    
    # 备份命令
    backup_parser = subparsers.add_parser("list-backups", help="列出所有配置备份")
    backup_parser.add_argument("--dir", default="config", help="配置目录")
    
    # 恢复命令
    restore_parser = subparsers.add_parser("restore", help="从备份恢复配置")
    restore_parser.add_argument("backup_name", help="备份文件名")
    restore_parser.add_argument("--dir", default="config", help="配置目录")
    
    # 验证命令
    validate_parser = subparsers.add_parser("validate", help="验证配置文件")
    validate_parser.add_argument("--config", default="config/llm_config.json", help="配置文件路径")
    
    # 状态命令
    status_parser = subparsers.add_parser("status", help="显示配置状态")
    
    args = parser.parse_args()
    
    # 设置日志
    setup_logging()
    
    # 加载环境变量
    load_environment()
    
    if args.command == "migrate":
        success = migrate_to_file_config(args.target, args.force)
        sys.exit(0 if success else 1)
        
    elif args.command == "rollback":
        success = rollback_to_env_config(args.config)
        sys.exit(0 if success else 1)
        
    elif args.command == "list-backups":
        list_backups(args.dir)
        
    elif args.command == "restore":
        success = restore_backup(args.backup_name, args.dir)
        sys.exit(0 if success else 1)
        
    elif args.command == "validate":
        success = validate_config(args.config)
        sys.exit(0 if success else 1)
        
    elif args.command == "status":
        logger.info("📊 LLM配置状态检查")
        
        # 检查环境变量
        env_config = read_env_config()
        logger.info(f"🌍 环境变量配置: {env_config.get('provider', 'unknown')} - {env_config.get('model', 'unknown')}")
        
        # 检查文件配置
        config_file = Path("config/llm_config.json")
        if config_file.exists():
            logger.info("📁 文件配置: 存在")
            validate_config(str(config_file))
        else:
            logger.info("📁 文件配置: 不存在（使用环境变量模式）")
            
        # 检查迁移记录
        migration_log = config_file.parent / "migration.log" if config_file.parent.exists() else None
        if migration_log and migration_log.exists():
            logger.info(f"📝 迁移记录: 存在 ({migration_log})")
        else:
            logger.info("📝 迁移记录: 不存在")
            
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 