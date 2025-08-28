# 知识图谱数据导入指南

## 概述

本指南介绍如何使用改进的知识图谱数据导入功能，解决重复导入和ID冲突问题，确保所有数据都能被保存而不会覆盖之前的数据。

## 问题解决

### 1. 重复文件导入问题
- **问题**: 多次导入相同文件导致数据重复或冲突
- **解决方案**: 提供多种导入策略（跳过、合并、覆盖、创建新ID）

### 2. ID冲突问题
- **问题**: 导入数据中的ID与已有数据冲突
- **解决方案**: 提供多种冲突解决策略（自动生成新ID、合并数据、跳过）

## 导入策略

### API导入

#### 基本用法
```bash
POST /api/kg/import
Content-Type: application/json

{
  "nodes": [...],
  "links": [...],
  "domain": "your_domain",
  "strategy": "merge",
  "conflict_resolution": "auto_id"
}
```

#### 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `nodes` | array | 必需 | 实体节点数组 |
| `links` | array | 必需 | 关系连接数组 |
| `domain` | string | "default" | 数据领域标识 |
| `strategy` | string | "merge" | 导入策略 |
| `conflict_resolution` | string | "auto_id" | 冲突解决策略 |

#### 导入策略选项

| 策略 | 说明 |
|------|------|
| `merge` | 合并数据，补充缺失字段 |
| `skip` | 跳过已存在的数据 |
| `overwrite` | 覆盖现有数据 |
| `create_new` | 创建新数据 |

#### 冲突解决策略

| 策略 | 说明 |
|------|------|
| `auto_id` | 自动生成新ID（推荐） |
| `merge_data` | 合并数据字段 |
| `skip` | 跳过冲突数据 |

### 命令行导入

#### 基本用法
```bash
python manage.py import_kg_data <file_path> [options]
```

#### 参数说明
```bash
python manage.py import_kg_data sample_data.json \
  --domain ai_domain \
  --strategy merge \
  --conflict-resolution auto_id \
  --verbose
```

#### 选项说明

| 选项 | 说明 |
|------|------|
| `--domain` | 指定数据领域 |
| `--strategy` | 导入策略 |
| `--conflict-resolution` | 冲突解决策略 |
| `--dry-run` | 模拟导入，不实际保存 |
| `--verbose` | 详细输出 |

## 使用示例

### 示例1: 首次导入数据
```python
import requests

data = {
    "nodes": [
        {"id": "1", "name": "人工智能", "type": "技术领域"},
        {"id": "2", "name": "机器学习", "type": "技术分支"}
    ],
    "links": [
        {"source": "1", "target": "2", "type": "包含"}
    ],
    "domain": "ai_domain",
    "strategy": "merge",
    "conflict_resolution": "auto_id"
}

response = requests.post("http://localhost:8000/api/kg/import", json=data)
print(response.json())
```

### 示例2: 处理重复导入
```python
# 重复导入相同数据，使用跳过策略
data["strategy"] = "skip"
data["conflict_resolution"] = "skip"

response = requests.post("http://localhost:8000/api/kg/import", json=data)
result = response.json()
print(f"跳过实体: {result['data']['import_stats']['entities']['skipped']}")
print(f"跳过关系: {result['data']['import_stats']['relationships']['skipped']}")
```

### 示例3: 合并数据
```python
# 合并策略，补充缺失字段
data["strategy"] = "merge"
data["conflict_resolution"] = "merge_data"

response = requests.post("http://localhost:8000/api/kg/import", json=data)
result = response.json()
print(f"更新实体: {result['data']['import_stats']['entities']['updated']}")
```

### 示例4: 自动ID冲突解决
```python
# 冲突数据，自动生成新ID
conflict_data = {
    "nodes": [
        {"id": "1", "name": "冲突实体", "type": "新类型"}  # ID已存在
    ],
    "links": [],
    "domain": "ai_domain",
    "strategy": "merge",
    "conflict_resolution": "auto_id"
}

response = requests.post("http://localhost:8000/api/kg/import", json=conflict_data)
result = response.json()
print(f"ID映射: {result['data']['entity_id_mapping']}")
# 输出: {"1": "1_1"} - 原ID "1" 映射到新ID "1_1"
```

## 命令行示例

### 1. 模拟导入
```bash
python manage.py import_kg_data sample_data.json --dry-run --verbose
```

### 2. 实际导入（推荐）
```bash
python manage.py import_kg_data sample_data.json \
  --strategy merge \
  --conflict-resolution auto_id \
  --verbose
```

### 3. 跳过重复数据
```bash
python manage.py import_kg_data sample_data.json \
  --strategy skip \
  --conflict-resolution skip \
  --verbose
```

## 导入结果说明

### API响应格式
```json
{
  "ret": 0,
  "msg": "import completed",
  "data": {
    "import_stats": {
      "entities": {
        "created": 5,
        "updated": 2,
        "skipped": 1,
        "conflicts": 1
      },
      "relationships": {
        "created": 8,
        "skipped": 2,
        "errors": 0
      },
      "conflicts": [
        {
          "type": "entity_id_conflict",
          "original_id": "1",
          "message": "Entity ID '1' already exists, will generate new ID"
        }
      ]
    },
    "entity_id_mapping": {
      "1": "1_1",
      "2": "2"
    },
    "domain": "ai_domain",
    "strategy": "merge",
    "conflict_resolution": "auto_id"
  }
}
```

### 命令行输出示例
```
==================================================
IMPORT RESULTS
==================================================

Entities:
  Created: 5
  Updated: 2
  Skipped: 1
  Conflicts: 1

Relationships:
  Created: 8
  Skipped: 2

==================================================
```

## 最佳实践

### 1. 数据准备
- 确保数据格式正确（JSON格式）
- 验证必需字段（id, name, source, target, type）
- 使用有意义的ID命名

### 2. 导入策略选择
- **首次导入**: 使用 `merge` + `auto_id`
- **重复导入**: 使用 `skip` + `skip`
- **数据更新**: 使用 `merge` + `merge_data`
- **完全覆盖**: 使用 `overwrite` + `auto_id`

### 3. 领域管理
- 使用不同的 `domain` 值来组织数据
- 避免跨领域的数据冲突
- 便于数据管理和清理

### 4. 错误处理
- 检查导入统计信息
- 查看冲突详情
- 验证ID映射关系

## 故障排除

### 常见问题

1. **JSON格式错误**
   - 检查JSON语法
   - 验证必需字段

2. **ID冲突**
   - 使用 `auto_id` 策略
   - 检查ID映射结果

3. **关系创建失败**
   - 确保源和目标实体存在
   - 检查领域匹配

4. **导入速度慢**
   - 分批导入大量数据
   - 使用命令行工具

### 调试技巧

1. **使用dry-run模式**
   ```bash
   python manage.py import_kg_data data.json --dry-run --verbose
   ```

2. **检查导入统计**
   ```python
   result = response.json()
   print(json.dumps(result['data']['import_stats'], indent=2))
   ```

3. **验证数据完整性**
   ```python
   response = requests.get("http://localhost:8000/api/kg/data?domain=your_domain")
   data = response.json()
   print(f"实体数: {len(data['data']['nodes'])}")
   print(f"关系数: {len(data['data']['links'])}")
   ```

## 测试

运行测试脚本验证导入功能：
```bash
python test_import_strategies.py
```

这将测试各种导入策略和冲突解决方案。
