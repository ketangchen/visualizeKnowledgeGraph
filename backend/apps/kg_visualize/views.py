from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Entity, Relationship
import json

@csrf_exempt  # ��������ʱ�ر�CSRF��֤
def get_graph_data(request): #��ȡ֪ʶͼ���������ݣ�ʵ��+��ϵ"""
    if request.method == 'GET':
        try:
            # ��ѯ����ʵ��
            entities = Entity.objects.all().values("id", "name", "type", "description")
            # ��ѯ���й�ϵ
            relations = Relationship.objects.all().values(
                "id", "source_id", "target_id", "type", "description"
            )
            # ת��ΪD3.js��ʶ��ĸ�ʽ
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
            return JsonResponse({"ret": 1, "msg": f"Fiding data is failed!:{str(e)}"})
    return JsonResponse({"ret": 1, "msg": "unsupported request method"})