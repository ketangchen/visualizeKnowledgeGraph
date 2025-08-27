# -*- coding: utf-8 -*-
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Entity, Relationship
import json

@csrf_exempt  # 跨域请求时关闭CSRF验证
def get_graph_data(request): #获取知识图谱完整数据：实体+关系"""
    if request.method == 'GET':
        try:
            # 查询所有实体
            entities = Entity.objects.all().values("id", "name", "type", "description")
            # 查询所有关系
            relations = Relationship.objects.all().values(
                "id", "source_id", "target_id", "type", "description"
            )
            # 转换为D3.js可识别的格式
            graph_data = {
                "nodes": list(entities),
                "links": [
                    {
                        "source": r["source_id"],
                        "target": r["target_id"],
                        "type": r["type"],
                        "description": r.get("description", ""),
                        "id": r["id"]
                    } for r in relations
                ]
            }
            return JsonResponse({"ret": 0, "data": graph_data})
        except Exception as e:
            return JsonResponse({"ret": 1, "msg": f"Finding data failed: {str(e)}"})
    return JsonResponse({"ret": 1, "msg": "Unsupported request method"})

@csrf_exempt  # 跨域请求时关闭CSRF验证
def add_entity(request):
    """
    add a new entity
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            # 验证数据
            if 'id' not in data or 'name' not in data:
                return JsonResponse({"ret": 1, "msg": "'id' and 'name' are required"})
            # 创建实体
            entity = Entity.objects.create(
                id=data['id'],
                name=data['name'],
                type=data.get('type', ''),
                description=data.get('description', '')
            )
            return JsonResponse({"ret": 0, "msg": "success"})
        except json.JSONDecodeError:
            return JsonResponse({"ret": 1, "msg": "Invalid JSON"})
        except Exception as e:
            return JsonResponse({"ret": 1, "msg": f"An error occurred: {str(e)}"})
    return JsonResponse({"ret": 1, "msg": "Unsupported request method"})