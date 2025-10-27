#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试关系编辑功能
"""
import os
import sys
import django
import requests
import json

# 设置Django环境
sys.path.append('/Users/ketangchen/Library/Mobile Documents/com~apple~CloudDocs/Documents/000_20250825dev/visualizeKnowledgeGraph')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from backend.apps.kg_visualize.models import Entity, Relationship

def test_relation_edit():
    """测试关系编辑功能"""
    print("🧪 开始测试关系编辑功能...")
    
    # 1. 创建测试实体
    print("\n1. 创建测试实体...")
    entity1 = Entity.objects.create(
        id="test_entity_1",
        name="测试实体1",
        description="这是一个测试实体",
        domain="test"
    )
    entity2 = Entity.objects.create(
        id="test_entity_2", 
        name="测试实体2",
        description="这是另一个测试实体",
        domain="test"
    )
    print(f"✅ 创建实体: {entity1.name}, {entity2.name}")
    
    # 2. 创建测试关系
    print("\n2. 创建测试关系...")
    relationship = Relationship.objects.create(
        source=entity1,
        target=entity2,
        type="测试关系",
        description="这是原始的关系描述",
        domain="test"
    )
    print(f"✅ 创建关系: {relationship.type} (ID: {relationship.id})")
    print(f"   原始描述: {relationship.description}")
    
    # 3. 测试API更新关系描述
    print("\n3. 测试API更新关系描述...")
    base_url = "http://localhost:8000/api/kg"
    
    # 更新数据
    update_data = {
        "source": entity1.id,
        "target": entity2.id,
        "type": "测试关系",
        "description": "这是更新后的关系描述"
    }
    
    try:
        response = requests.put(
            f"{base_url}/relationships/{relationship.id}",
            json=update_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"API响应状态: {response.status_code}")
        print(f"API响应内容: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ret') == 0:
                print("✅ API更新成功")
            else:
                print(f"❌ API更新失败: {result.get('msg')}")
        else:
            print(f"❌ API请求失败: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器，请确保Django服务器正在运行")
        print("   运行命令: python manage.py runserver")
        return False
    except Exception as e:
        print(f"❌ API测试出错: {e}")
        return False
    
    # 4. 验证数据库中的数据
    print("\n4. 验证数据库中的数据...")
    updated_relationship = Relationship.objects.get(id=relationship.id)
    print(f"更新后的描述: {updated_relationship.description}")
    
    if updated_relationship.description == "这是更新后的关系描述":
        print("✅ 数据库更新成功")
    else:
        print("❌ 数据库更新失败")
        return False
    
    # 5. 清理测试数据
    print("\n5. 清理测试数据...")
    relationship.delete()
    entity1.delete()
    entity2.delete()
    print("✅ 测试数据已清理")
    
    print("\n🎉 关系编辑功能测试完成！")
    return True

if __name__ == "__main__":
    success = test_relation_edit()
    if success:
        print("\n✅ 所有测试通过！关系编辑功能正常工作。")
    else:
        print("\n❌ 测试失败，请检查相关功能。")
