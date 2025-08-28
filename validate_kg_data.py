#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
知识图谱数据验证工具
用于在导入前检查数据格式和完整性
"""

import json
import sys
import os
from typing import Dict, List, Tuple, Set


class KGDataValidator:
    """知识图谱数据验证器"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.stats = {
            "nodes": {"total": 0, "valid": 0, "invalid": 0},
            "links": {"total": 0, "valid": 0, "invalid": 0}
        }
    
    def validate_file(self, file_path: str) -> bool:
        """验证JSON文件"""
        print(f"正在验证文件: {file_path}")
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            self.errors.append(f"文件不存在: {file_path}")
            return False
        
        # 读取JSON文件
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            self.errors.append(f"JSON格式错误: {e}")
            return False
        except Exception as e:
            self.errors.append(f"读取文件失败: {e}")
            return False
        
        # 验证数据结构
        return self.validate_data(data)
    
    def validate_data(self, data: Dict) -> bool:
        """验证数据结构"""
        # 检查基本结构
        if not isinstance(data, dict):
            self.errors.append("数据必须是JSON对象")
            return False
        
        if 'nodes' not in data or 'links' not in data:
            self.errors.append("数据必须包含 'nodes' 和 'links' 字段")
            return False
        
        if not isinstance(data['nodes'], list) or not isinstance(data['links'], list):
            self.errors.append("'nodes' 和 'links' 必须是数组")
            return False
        
        # 验证节点
        node_ids = self.validate_nodes(data['nodes'])
        
        # 验证关系
        self.validate_links(data['links'], node_ids)
        
        # 检查是否有错误
        return len(self.errors) == 0
    
    def validate_nodes(self, nodes: List[Dict]) -> Set[str]:
        """验证节点数据"""
        node_ids = set()
        self.stats["nodes"]["total"] = len(nodes)
        
        for i, node in enumerate(nodes):
            if not isinstance(node, dict):
                self.errors.append(f"节点 {i} 必须是对象")
                self.stats["nodes"]["invalid"] += 1
                continue
            
            # 检查必需字段
            if 'id' not in node:
                self.errors.append(f"节点 {i} 缺少 'id' 字段")
                self.stats["nodes"]["invalid"] += 1
                continue
            
            if 'name' not in node:
                self.errors.append(f"节点 {i} 缺少 'name' 字段")
                self.stats["nodes"]["invalid"] += 1
                continue
            
            node_id = node['id']
            node_name = node['name']
            
            # 检查ID类型
            if not isinstance(node_id, str):
                self.errors.append(f"节点 {i} 的 'id' 必须是字符串")
                self.stats["nodes"]["invalid"] += 1
                continue
            
            # 检查名称类型
            if not isinstance(node_name, str):
                self.errors.append(f"节点 {i} 的 'name' 必须是字符串")
                self.stats["nodes"]["invalid"] += 1
                continue
            
            # 检查ID唯一性
            if node_id in node_ids:
                self.errors.append(f"重复的节点ID: {node_id}")
                self.stats["nodes"]["invalid"] += 1
                continue
            
            # 检查ID长度
            if len(node_id) > 100:
                self.warnings.append(f"节点ID过长: {node_id} (长度: {len(node_id)})")
            
            # 检查名称长度
            if len(node_name) > 200:
                self.warnings.append(f"节点名称过长: {node_name} (长度: {len(node_name)})")
            
            # 检查可选字段
            if 'type' in node and not isinstance(node['type'], str):
                self.errors.append(f"节点 {i} 的 'type' 必须是字符串")
                self.stats["nodes"]["invalid"] += 1
                continue
            
            if 'description' in node and not isinstance(node['description'], str):
                self.errors.append(f"节点 {i} 的 'description' 必须是字符串")
                self.stats["nodes"]["invalid"] += 1
                continue
            
            node_ids.add(node_id)
            self.stats["nodes"]["valid"] += 1
        
        return node_ids
    
    def validate_links(self, links: List[Dict], node_ids: Set[str]):
        """验证关系数据"""
        self.stats["links"]["total"] = len(links)
        link_set = set()  # 用于检查重复关系
        
        for i, link in enumerate(links):
            if not isinstance(link, dict):
                self.errors.append(f"关系 {i} 必须是对象")
                self.stats["links"]["invalid"] += 1
                continue
            
            # 检查必需字段
            if 'source' not in link:
                self.errors.append(f"关系 {i} 缺少 'source' 字段")
                self.stats["links"]["invalid"] += 1
                continue
            
            if 'target' not in link:
                self.errors.append(f"关系 {i} 缺少 'target' 字段")
                self.stats["links"]["invalid"] += 1
                continue
            
            if 'type' not in link:
                self.errors.append(f"关系 {i} 缺少 'type' 字段")
                self.stats["links"]["invalid"] += 1
                continue
            
            source = link['source']
            target = link['target']
            rel_type = link['type']
            
            # 检查字段类型
            if not isinstance(source, str):
                self.errors.append(f"关系 {i} 的 'source' 必须是字符串")
                self.stats["links"]["invalid"] += 1
                continue
            
            if not isinstance(target, str):
                self.errors.append(f"关系 {i} 的 'target' 必须是字符串")
                self.stats["links"]["invalid"] += 1
                continue
            
            if not isinstance(rel_type, str):
                self.errors.append(f"关系 {i} 的 'type' 必须是字符串")
                self.stats["links"]["invalid"] += 1
                continue
            
            # 检查源和目标是否存在
            if source not in node_ids:
                self.errors.append(f"关系 {i} 的源节点不存在: {source}")
                self.stats["links"]["invalid"] += 1
                continue
            
            if target not in node_ids:
                self.errors.append(f"关系 {i} 的目标节点不存在: {target}")
                self.stats["links"]["invalid"] += 1
                continue
            
            # 检查自环
            if source == target:
                self.warnings.append(f"关系 {i} 存在自环: {source} -> {target}")
            
            # 检查重复关系
            link_key = (source, target, rel_type)
            if link_key in link_set:
                self.warnings.append(f"重复的关系: {source} -[{rel_type}]-> {target}")
            else:
                link_set.add(link_key)
            
            # 检查可选字段
            if 'description' in link and not isinstance(link['description'], str):
                self.errors.append(f"关系 {i} 的 'description' 必须是字符串")
                self.stats["links"]["invalid"] += 1
                continue
            
            self.stats["links"]["valid"] += 1
    
    def print_report(self):
        """打印验证报告"""
        print("\n" + "="*60)
        print("数据验证报告")
        print("="*60)
        
        # 统计信息
        print(f"\n节点统计:")
        print(f"  总数: {self.stats['nodes']['total']}")
        print(f"  有效: {self.stats['nodes']['valid']}")
        print(f"  无效: {self.stats['nodes']['invalid']}")
        
        print(f"\n关系统计:")
        print(f"  总数: {self.stats['links']['total']}")
        print(f"  有效: {self.stats['links']['valid']}")
        print(f"  无效: {self.stats['links']['invalid']}")
        
        # 错误信息
        if self.errors:
            print(f"\n❌ 错误 ({len(self.errors)}):")
            for error in self.errors:
                print(f"  - {error}")
        
        # 警告信息
        if self.warnings:
            print(f"\n⚠️  警告 ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  - {warning}")
        
        # 总结
        if self.errors:
            print(f"\n❌ 验证失败: 发现 {len(self.errors)} 个错误")
            return False
        elif self.warnings:
            print(f"\n⚠️  验证通过，但有 {len(self.warnings)} 个警告")
            return True
        else:
            print(f"\n✅ 验证通过: 数据格式正确")
            return True


def main():
    """主函数"""
    if len(sys.argv) != 2:
        print("用法: python validate_kg_data.py <json_file>")
        print("示例: python validate_kg_data.py sample_data.json")
        sys.exit(1)
    
    file_path = sys.argv[1]
    validator = KGDataValidator()
    
    if validator.validate_file(file_path):
        validator.print_report()
        if validator.errors:
            sys.exit(1)
        else:
            print("\n✅ 数据验证通过，可以安全导入")
    else:
        validator.print_report()
        print("\n❌ 数据验证失败，请修复错误后重试")
        sys.exit(1)


if __name__ == "__main__":
    main()
