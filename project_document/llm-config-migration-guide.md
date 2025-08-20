# LLM配置迁移指南

本指南将帮助您从环境变量配置平滑迁移到基于文件的配置管理系统，同时保持完全的向后兼容性。

## 概述

### 配置方式对比

| 特性 | 环境变量配置 | 文件配置 |
|------|-------------|---------|
| **易用性** | 简单，适合单一配置 | 灵活，支持多提供商 |
| **扩展性** | 有限 | 强大，支持复杂配置 |
| **版本控制** | 困难 | 容易 |
| **备份恢复** | 手动 | 自动 |
| **热重载** | 需要重启 | 支持热重载 |
| **前端编辑** | 不支持 | 完整支持 |

### 迁移策略

系统提供三种迁移方式：

1. **自动迁移**：首次启动时自动检测并迁移
2. **手动迁移**：使用迁移脚本主动迁移
3. **混合模式**：保持环境变量作为fallback

## 自动迁移

### 启动时迁移

当您启动应用时，系统会自动检查是否需要迁移：

```bash
# 启动应用
cd backend
python main.py
```

系统会输出类似以下日志：

```
🔄 开始配置迁移检查...
📦 检测到首次启动或配置缺失，开始自动迁移...
✅ LLM配置迁移成功！已从环境变量创建配置文件
📝 迁移记录已保存到: config/migration.log
✅ 配置文件验证通过，包含 1 个提供商
🎯 配置迁移检查完成
```

### 迁移结果

迁移完成后，您将获得：

- **配置文件**：`config/llm_config.json`
- **迁移记录**：`config/migration.log`
- **自动备份**：`config/backups/` 目录下的备份文件

## 手动迁移

### 使用迁移脚本

我们提供了功能完整的迁移脚本 `scripts/migrate_llm_config.py`：

#### 1. 迁移到文件配置

```bash
# 基本迁移
python scripts/migrate_llm_config.py migrate

# 指定目标文件
python scripts/migrate_llm_config.py migrate --target custom/path/config.json

# 强制覆盖现有配置
python scripts/migrate_llm_config.py migrate --force
```

#### 2. 检查配置状态

```bash
python scripts/migrate_llm_config.py status
```

输出示例：
```
📊 LLM配置状态检查
🌍 环境变量配置: openai - gpt-3.5-turbo
📁 文件配置: 存在
✅ 配置验证通过
📊 总提供商: 1, 已启用: 1
  ✅ OpenAI: gpt-3.5-turbo
📝 迁移记录: 存在 (config/migration.log)
```

#### 3. 验证配置文件

```bash
python scripts/migrate_llm_config.py validate
```

#### 4. 管理备份

```bash
# 列出所有备份
python scripts/migrate_llm_config.py list-backups

# 从备份恢复
python scripts/migrate_llm_config.py restore llm_config_backup_20240115_143022.json
```

#### 5. 回退到环境变量

```bash
python scripts/migrate_llm_config.py rollback
```

## 配置文件格式

### 环境变量格式

```env
# config.env
LLM_ENABLED=true
LLM_PROVIDER=openai
LLM_MODEL=gpt-3.5-turbo
LLM_API_KEY=your_api_key_here
LLM_BASE_URL=
LLM_TIMEOUT=30
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2000
```

### 迁移后的JSON格式

```json
{
  "version": "1.0",
  "name": "LLM配置",
  "description": "从环境变量迁移生成于 2024-01-15 14:30:22",
  "default_provider": "openai",
  "providers": [
    {
      "id": "openai",
      "name": "OpenAI",
      "enabled": true,
      "model": "gpt-3.5-turbo",
      "api_key": "your_api_key_here",
      "temperature": 0.7,
      "max_tokens": 2000,
      "timeout": 30,
      "max_retries": 3,
      "stream": false
    }
  ],
  "global_settings": {
    "timeout": 30,
    "max_retries": 3,
    "enable_cache": true,
    "cache_timeout": 300
  }
}
```

## 向后兼容性

### 配置优先级

系统采用以下优先级顺序：

1. **文件配置**：`config/llm_config.json`（最高优先级）
2. **环境变量**：作为fallback（保持兼容性）

### 混合模式支持

即使迁移到文件配置后，环境变量仍然可以作为补充：

- 如果文件配置中缺少某个字段，系统会自动从环境变量中读取
- 删除配置文件可立即回退到纯环境变量模式
- 不需要修改现有的部署脚本

## 迁移最佳实践

### 1. 迁移前准备

```bash
# 备份当前环境变量配置
cp config.env config.env.backup

# 检查当前配置状态
python scripts/migrate_llm_config.py status
```

### 2. 执行迁移

```bash
# 执行迁移（自动创建备份）
python scripts/migrate_llm_config.py migrate

# 验证迁移结果
python scripts/migrate_llm_config.py validate
```

### 3. 迁移后验证

```bash
# 启动应用验证
python main.py

# 检查API功能
curl http://localhost:8000/api/v2/llm/config/current
```

### 4. 清理（可选）

迁移成功后，您可以选择：

- 保留 `config.env` 作为备份
- 注释掉 `config.env` 中的LLM相关配置
- 完全删除LLM环境变量（不推荐）

## 故障排除

### 常见问题

#### 1. 迁移失败

**症状**：迁移脚本报错或配置文件未生成

**解决方案**：
```bash
# 检查环境变量是否正确设置
python scripts/migrate_llm_config.py status

# 检查目录权限
ls -la config/

# 手动创建目录
mkdir -p config/backups
```

#### 2. 配置验证失败

**症状**：配置文件存在但验证不通过

**解决方案**：
```bash
# 检查JSON格式
python -m json.tool config/llm_config.json

# 重新迁移
python scripts/migrate_llm_config.py migrate --force
```

#### 3. 回退问题

**症状**：无法回退到环境变量模式

**解决方案**：
```bash
# 手动删除配置文件
rm config/llm_config.json

# 或使用脚本
python scripts/migrate_llm_config.py rollback
```

### 应急恢复

如果遇到严重问题，可以按以下步骤恢复：

1. **完全回退**：
```bash
python scripts/migrate_llm_config.py rollback
```

2. **恢复备份**：
```bash
# 查看可用备份
python scripts/migrate_llm_config.py list-backups

# 恢复指定备份
python scripts/migrate_llm_config.py restore backup_filename.json
```

3. **重置到默认环境变量配置**：
```bash
# 删除所有配置文件
rm -rf config/llm_config.json config/migration.log

# 重启应用（使用环境变量）
python main.py
```

## 高级功能

### 批量迁移

如果您有多个环境，可以使用脚本批量迁移：

```bash
#!/bin/bash
# batch_migrate.sh

environments=("dev" "staging" "prod")

for env in "${environments[@]}"; do
    echo "迁移 $env 环境..."
    
    # 加载特定环境的配置
    source config/$env.env
    
    # 执行迁移
    python scripts/migrate_llm_config.py migrate --target config/llm_config_$env.json
    
    echo "$env 环境迁移完成"
done
```

### 配置模板

您可以创建标准化的配置模板：

```json
{
  "version": "1.0",
  "name": "标准LLM配置模板",
  "description": "适用于生产环境的LLM配置",
  "default_provider": "openai",
  "providers": [
    {
      "id": "openai",
      "name": "OpenAI",
      "enabled": true,
      "model": "gpt-4",
      "temperature": 0.7,
      "max_tokens": 2000,
      "timeout": 30,
      "max_retries": 3
    },
    {
      "id": "azure",
      "name": "Azure OpenAI",
      "enabled": false,
      "model": "gpt-4",
      "deployment_name": "gpt-4-deployment",
      "api_version": "2023-12-01-preview"
    }
  ]
}
```

## 支持与反馈

如果您在迁移过程中遇到问题：

1. 查看 `config/migration.log` 获取详细信息
2. 使用 `python scripts/migrate_llm_config.py status` 检查状态
3. 参考本指南的故障排除部分
4. 如需技术支持，请提供迁移日志和配置状态信息

---

**注意**：迁移是可逆的过程，您随时可以回退到环境变量配置。我们建议在生产环境中先在测试环境验证迁移过程。 