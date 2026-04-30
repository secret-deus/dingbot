#!/usr/bin/env python3
"""
MCP配置备份清理脚本
只保留最新的5个mcp_config备份文件，删除多余的旧备份
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import argparse

def cleanup_mcp_backups(backup_dir: str, keep_count: int = 5, dry_run: bool = False):
    """
    清理MCP配置备份文件
    
    Args:
        backup_dir: 备份目录路径
        keep_count: 保留的备份文件数量
        dry_run: 是否为演练模式（不实际删除）
    """
    backup_path = Path(backup_dir)
    
    if not backup_path.exists():
        print(f"❌ 备份目录不存在: {backup_path}")
        return
    
    # 查找所有mcp_config备份文件
    backup_files = list(backup_path.glob("mcp_config_*.json"))
    
    if not backup_files:
        print(f"📁 备份目录中没有找到mcp_config备份文件: {backup_path}")
        return
    
    # 按修改时间排序，最新的在前
    backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    
    print(f"📊 找到 {len(backup_files)} 个mcp_config备份文件")
    print(f"🎯 保留最新的 {keep_count} 个备份")
    
    # 显示所有备份文件的信息
    print("\n📋 备份文件列表（按时间排序，最新在前）:")
    for i, backup_file in enumerate(backup_files):
        file_time = datetime.fromtimestamp(backup_file.stat().st_mtime)
        file_size = backup_file.stat().st_size
        size_kb = file_size / 1024
        status = "🟢 保留" if i < keep_count else "🔴 删除"
        print(f"  {i+1:2d}. {backup_file.name:30s} | {file_time.strftime('%Y-%m-%d %H:%M:%S')} | {size_kb:6.1f}KB | {status}")
    
    # 需要删除的文件
    files_to_delete = backup_files[keep_count:]
    
    if not files_to_delete:
        print(f"\n✅ 备份文件数量正好，无需删除任何文件")
        return
    
    print(f"\n🗑️  需要删除 {len(files_to_delete)} 个旧备份文件:")
    
    if dry_run:
        print("🧪 演练模式 - 将会删除以下文件:")
        for file_to_delete in files_to_delete:
            print(f"  - {file_to_delete.name}")
        print(f"\n💡 添加 --execute 参数来实际执行删除操作")
        return
    
    # 执行删除
    deleted_count = 0
    total_size_freed = 0
    
    for file_to_delete in files_to_delete:
        try:
            file_size = file_to_delete.stat().st_size
            file_to_delete.unlink()
            deleted_count += 1
            total_size_freed += file_size
            print(f"  ✅ 已删除: {file_to_delete.name}")
        except Exception as e:
            print(f"  ❌ 删除失败: {file_to_delete.name} - {e}")
    
    size_freed_kb = total_size_freed / 1024
    print(f"\n🎉 清理完成!")
    print(f"   删除文件: {deleted_count} 个")
    print(f"   释放空间: {size_freed_kb:.1f}KB")
    print(f"   保留备份: {len(backup_files) - deleted_count} 个")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="清理MCP配置备份文件，只保留最新的N个备份",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 演练模式（不实际删除）
  python scripts/cleanup_mcp_backups.py
  
  # 实际执行删除，保留5个备份
  python scripts/cleanup_mcp_backups.py --execute
  
  # 自定义保留数量
  python scripts/cleanup_mcp_backups.py --execute --keep 3
  
  # 指定备份目录
  python scripts/cleanup_mcp_backups.py --execute --backup-dir /path/to/backups
        """
    )
    
    parser.add_argument(
        '--backup-dir', 
        default='backend/config/backups',
        help='备份目录路径 (默认: backend/config/backups)'
    )
    
    parser.add_argument(
        '--keep', 
        type=int, 
        default=5,
        help='保留的备份文件数量 (默认: 5)'
    )
    
    parser.add_argument(
        '--execute', 
        action='store_true',
        help='实际执行删除操作（默认为演练模式）'
    )
    
    args = parser.parse_args()
    
    # 验证参数
    if args.keep < 1:
        print("❌ 错误: 保留数量必须至少为1")
        sys.exit(1)
    
    print("🧹 MCP配置备份清理工具")
    print("=" * 50)
    print(f"备份目录: {args.backup_dir}")
    print(f"保留数量: {args.keep}")
    print(f"执行模式: {'实际执行' if args.execute else '演练模式'}")
    print("=" * 50)
    
    # 执行清理
    cleanup_mcp_backups(
        backup_dir=args.backup_dir,
        keep_count=args.keep,
        dry_run=not args.execute
    )

if __name__ == "__main__":
    main() 