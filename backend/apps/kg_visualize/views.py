from django.http import JsonResponse
from .models import Entity, Relationship
from django.views.decorators.csrf import csrf_exempt
import json


@csrf_exempt  # 开发环境临时关闭CSRF验证
def get_graph_data(request):
    """获取知识图谱完整数据（实体+关系）"""
    if request.method == 'GET':
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
    return JsonResponse({"ret": 1, "msg": "不支持的请求方法"})


@csrf_exempt
def add_entity(request):
    """新增实体"""
    if request.method == 'POST':
        data = json.loads(request.body)
        required_fields = ["id", "name"]
        if not all(field in data for field in required_fields):
            return JsonResponse({"ret": 1, "msg": "缺少必要字段（id或name）"})

        try:
            Entity.objects.create(
                id=data["id"],
                name=data["name"],
                type=data.get("type", ""),
                description=data.get("description", "")
            )
            return JsonResponse({"ret": 0, "msg": "实体创建成功"})
        except Exception as e:
            return JsonResponse({"ret": 1, "msg": f"创建失败：{str(e)}"})
    return JsonResponse({"ret": 1, "msg": "不支持的请求方法"})