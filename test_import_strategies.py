#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试不同的数据导入策略
演示如何处理重复导入和ID冲突问题
"""

import json
import requests
import time

# API基础URL
BASE_URL = "http://localhost:8000/api/kg"

def test_import_strategies():
    """测试不同的导入策略"""
    
    # 准备测试数据
    test_data = {
        "nodes": [
            {
                "id": "test_1",
                "name": "测试实体1",
                "type": "测试类型",
                "description": "这是一个测试实体"
            },
            {
                "id": "test_2", 
                "name": "测试实体2",
                "type": "测试类型",
                "description": "这是另一个测试实体"
            },
            {
                "id": "test_3",
                "name": "测试实体3", 
                "type": "测试类型",
                "description": "第三个测试实体"
            }
        ],
        "links": [
            {
                "source": "test_1",
                "target": "test_2", 
                "type": "关联",
                "description": "测试实体1和测试实体2的关联"
            },
            {
                "source": "test_2",
                "target": "test_3",
                "type": "关联", 
                "description": "测试实体2和测试实体3的关联"
            }
        ]
    }
    
    # 冲突数据（包含重复ID）
    conflict_data = {
        "nodes": [
            {
                "id": "test_1",  # 重复ID
                "name": "冲突实体1",
                "type": "冲突类型",
                "description": "这是冲突的实体1"
            },
            {
                "id": "test_4",
                "name": "新实体4",
                "type": "新类型",
                "description": "这是一个新实体"
            }
        ],
        "links": [
            {
                "source": "test_1",
                "target": "test_4",
                "type": "新关联",
                "description": "冲突实体1和新实体4的关联"
            }
        ]
    }
    
    print("=" * 60)
    print("数据导入策略测试")
    print("=" * 60)
    
    # 测试1: 首次导入（应该成功）
    print("\n1. 首次导入数据...")
    response = requests.post(
        f"{BASE_URL}/import",
        json={
            "nodes": test_data["nodes"],
            "links": test_data["links"],
            "domain": "test_domain",
            "strategy": "merge",
            "conflict_resolution": "auto_id"
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        print("✅ 首次导入成功")
        print(f"   创建实体: {result['data']['import_stats']['entities']['created']}")
        print(f"   创建关系: {result['data']['import_stats']['relationships']['created']}")
    else:
        print(f"❌ 首次导入失败: {response.text}")
        return
    
    # 测试2: 重复导入 - 跳过策略
    print("\n2. 重复导入 - 跳过策略...")
    response = requests.post(
        f"{BASE_URL}/import",
        json={
            "nodes": test_data["nodes"],
            "links": test_data["links"],
            "domain": "test_domain",
            "strategy": "skip",
            "conflict_resolution": "skip"
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        print("✅ 跳过策略导入成功")
        print(f"   跳过实体: {result['data']['import_stats']['entities']['skipped']}")
        print(f"   跳过关系: {result['data']['import_stats']['relationships']['skipped']}")
    else:
        print(f"❌ 跳过策略导入失败: {response.text}")
    
    # 测试3: 重复导入 - 合并策略
    print("\n3. 重复导入 - 合并策略...")
    response = requests.post(
        f"{BASE_URL}/import",
        json={
            "nodes": test_data["nodes"],
            "links": test_data["links"],
            "domain": "test_domain",
            "strategy": "merge",
            "conflict_resolution": "merge_data"
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        print("✅ 合并策略导入成功")
        print(f"   更新实体: {result['data']['import_stats']['entities']['updated']}")
        print(f"   跳过实体: {result['data']['import_stats']['entities']['skipped']}")
    else:
        print(f"❌ 合并策略导入失败: {response.text}")
    
    # 测试4: 冲突导入 - 自动ID策略
    print("\n4. 冲突导入 - 自动ID策略...")
    response = requests.post(
        f"{BASE_URL}/import",
        json={
            "nodes": conflict_data["nodes"],
            "links": conflict_data["links"],
            "domain": "test_domain",
            "strategy": "merge",
            "conflict_resolution": "auto_id"
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        print("✅ 自动ID策略导入成功")
        print(f"   冲突实体: {result['data']['import_stats']['entities']['conflicts']}")
        print(f"   创建实体: {result['data']['import_stats']['entities']['created']}")
        print(f"   ID映射: {result['data']['entity_id_mapping']}")
    else:
        print(f"❌ 自动ID策略导入失败: {response.text}")
    
    # 测试5: 查看最终数据
    print("\n5. 查看最终数据...")
    response = requests.get(f"{BASE_URL}/data?domain=test_domain")
    
    if response.status_code == 200:
        result = response.json()
        print("✅ 数据查询成功")
        print(f"   总实体数: {len(result['data']['nodes'])}")
        print(f"   总关系数: {len(result['data']['links'])}")
        
        # 显示实体列表
        print("\n   实体列表:")
        for node in result['data']['nodes']:
            print(f"     - {node['id']}: {node['name']} ({node['domain']})")
    else:
        print(f"❌ 数据查询失败: {response.text}")

def test_command_line_import():
    """测试命令行导入功能"""
    print("\n" + "=" * 60)
    print("命令行导入测试")
    print("=" * 60)
    
    print("\n请运行以下命令来测试命令行导入:")
    print("\n1. 模拟导入（不实际保存数据）:")
    print("   python manage.py import_kg_data sample_data.json --dry-run --verbose")
    
    print("\n2. 实际导入（自动ID策略）:")
    print("   python manage.py import_kg_data sample_data.json --strategy merge --conflict-resolution auto_id --verbose")
    
    print("\n3. 实际导入（跳过冲突）:")
    print("   python manage.py import_kg_data sample_data.json --strategy skip --conflict-resolution skip --verbose")
    
    print("\n4. 实际导入（合并数据）:")
    print("   python manage.py import_kg_data sample_data.json --strategy merge --conflict-resolution merge_data --verbose")

def cleanup_test_data():
    """清理测试数据"""
    print("\n" + "=" * 60)
    print("清理测试数据")
    print("=" * 60)
    
    # 这里可以添加清理测试数据的代码
    # 由于没有删除API，暂时跳过
    print("注意: 测试数据已创建在 'test_domain' 领域")
    print("如需清理，请手动删除或使用Django管理界面")

if __name__ == "__main__":
    try:
        # 测试API导入
        test_import_strategies()
        
        # 显示命令行测试说明
        test_command_line_import()
        
        # 清理说明
        cleanup_test_data()
        
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器，请确保Django服务器正在运行:")
        print("   python manage.py runserver")
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
