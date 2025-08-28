# -*- coding: utf-8 -*-
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db import transaction, models
from .models import Entity, Relationship
import json

@csrf_exempt  # 跨域请求时关闭CSRF验证
def get_graph_data(request): #获取知识图谱完整数据：实体+关系"""
    if request.method == 'GET':
        try:
            # 获取领域参数，默认为default
            domain = request.GET.get('domain', 'default')
            
            # 查询指定领域的实体
            entities = Entity.objects.filter(domain=domain).values("id", "name", "type", "description")
            # 查询指定领域的关系
            relations = Relationship.objects.filter(domain=domain).values(
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
            return JsonResponse({"ret": 0, "data": graph_data, "domain": domain})
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
            Entity.objects.create(
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


# -----------------------------
# Entity CRUD
# -----------------------------

def _json_error(message):
    return JsonResponse({"ret": 1, "msg": message})


@csrf_exempt
@require_http_methods(["GET", "POST"])
def list_or_create_entities(request):
    if request.method == "GET":
        q = request.GET.get("q", "").strip().lower()
        queryset = Entity.objects.all()
        if q:
            queryset = queryset.filter(models.Q(id__icontains=q) | models.Q(name__icontains=q) | models.Q(description__icontains=q))
        data = list(queryset.values("id", "name", "type", "description"))
        return JsonResponse({"ret": 0, "data": data})

    # POST create
    try:
        data = json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        return _json_error("Invalid JSON")

    if not data.get("id") or not data.get("name"):
        return _json_error("'id' and 'name' are required")

    try:
        Entity.objects.create(
            id=data["id"],
            name=data["name"],
            type=data.get("type", ""),
            description=data.get("description", "")
        )
        return JsonResponse({"ret": 0, "msg": "created"})
    except Exception as e:
        return _json_error(str(e))


@csrf_exempt
@require_http_methods(["GET", "PUT", "PATCH", "DELETE"])
def entity_detail(request, entity_id: str):
    try:
        entity = Entity.objects.get(id=entity_id)
    except Entity.DoesNotExist:
        return _json_error("entity not found")

    if request.method == "GET":
        return JsonResponse({
            "ret": 0,
            "data": {
                "id": entity.id,
                "name": entity.name,
                "type": entity.type,
                "description": entity.description,
            }
        })

    if request.method in ("PUT", "PATCH"):
        try:
            data = json.loads(request.body or b"{}")
        except json.JSONDecodeError:
            return _json_error("Invalid JSON")

        name = data.get("name", entity.name)
        type_val = data.get("type", entity.type)
        description = data.get("description", entity.description)

        if not name:
            return _json_error("'name' is required")

        entity.name = name
        entity.type = type_val or ""
        entity.description = description or ""
        entity.save()
        return JsonResponse({"ret": 0, "msg": "updated"})

    # DELETE
    entity.delete()
    return JsonResponse({"ret": 0, "msg": "deleted"})


# -----------------------------
# Relationship CRUD
# -----------------------------

@csrf_exempt
@require_http_methods(["GET", "POST"])
def list_or_create_relationships(request):
    if request.method == "GET":
        source = request.GET.get("source")
        target = request.GET.get("target")
        rel_type = request.GET.get("type")

        qs = Relationship.objects.all()
        if source:
            qs = qs.filter(source_id=source)
        if target:
            qs = qs.filter(target_id=target)
        if rel_type:
            qs = qs.filter(type__icontains=rel_type)

        data = [
            {
                "id": r.id,
                "source": r.source_id,
                "target": r.target_id,
                "type": r.type,
                "description": r.description,
            }
            for r in qs
        ]
        return JsonResponse({"ret": 0, "data": data})

    # POST create relationship
    try:
        data = json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        return _json_error("Invalid JSON")

    source = data.get("source")
    target = data.get("target")
    rel_type = data.get("type")
    description = data.get("description", "")

    if not source or not target or not rel_type:
        return _json_error("'source', 'target' and 'type' are required")
    if source == target:
        return _json_error("source and target must be different")

    try:
        src = Entity.objects.get(id=source)
        tgt = Entity.objects.get(id=target)
        rel = Relationship.objects.create(source=src, target=tgt, type=rel_type, description=description)
        return JsonResponse({
            "ret": 0,
            "msg": "created",
            "data": {"id": rel.id}
        })
    except Entity.DoesNotExist:
        return _json_error("source or target entity not found")
    except Exception as e:
        return _json_error(str(e))


@csrf_exempt
@require_http_methods(["PUT", "PATCH", "DELETE"]) 
def relationship_detail(request, rel_id: int):
    try:
        rel = Relationship.objects.get(id=rel_id)
    except Relationship.DoesNotExist:
        return _json_error("relationship not found")

    if request.method in ("PUT", "PATCH"):
        try:
            data = json.loads(request.body or b"{}")
        except json.JSONDecodeError:
            return _json_error("Invalid JSON")

        update_fields = False
        if "type" in data:
            rel.type = data.get("type") or rel.type
            update_fields = True
        if "description" in data:
            rel.description = data.get("description") or ""
            update_fields = True

        if update_fields:
            rel.save()
        return JsonResponse({"ret": 0, "msg": "updated"})

    # DELETE
    rel.delete()
    return JsonResponse({"ret": 0, "msg": "deleted"})


# -----------------------------
# Import / Export
# -----------------------------

@csrf_exempt
@require_http_methods(["GET"])
def export_graph(request):
    # 获取领域参数，默认为default
    domain = request.GET.get('domain', 'default')
    
    entities = list(Entity.objects.filter(domain=domain).values("id", "name", "type", "description"))
    links = [
        {
            "id": r.id,
            "source": r.source_id,
            "target": r.target_id,
            "type": r.type,
            "description": r.description,
        }
        for r in Relationship.objects.filter(domain=domain)
    ]
    return JsonResponse({
        "ret": 0, 
        "data": {
            "nodes": entities, 
            "links": links
        },
        "domain": domain
    })


@csrf_exempt
@require_http_methods(["POST"])
@transaction.atomic
def import_graph(request):
    try:
        payload = json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        return _json_error("Invalid JSON")

    nodes = payload.get("nodes", [])
    links = payload.get("links", [])
    overwrite = bool(payload.get("overwrite", False))
    domain = payload.get("domain", "default")  # 新增：支持指定领域

    if not isinstance(nodes, list) or not isinstance(links, list):
        return _json_error("'nodes' and 'links' must be arrays")

    # 创建/更新实体（指定领域）
    for n in nodes:
        node_id = n.get("id")
        name = n.get("name")
        if not node_id or not name:
            return _json_error("each node must include 'id' and 'name'")
        defaults = {
            "name": name,
            "type": n.get("type", ""),
            "description": n.get("description", ""),
            "domain": domain,  # 设置领域
        }
        if overwrite:
            Entity.objects.update_or_create(id=node_id, domain=domain, defaults=defaults)
        else:
            Entity.objects.get_or_create(id=node_id, domain=domain, defaults=defaults)

    # 创建关系（指定领域）
    created_count = 0
    for l in links:
        source = l.get("source")
        target = l.get("target")
        rel_type = l.get("type")
        description = l.get("description", "")
        if not source or not target or not rel_type:
            return _json_error("each link must include 'source', 'target' and 'type'")
        if source == target:
            return _json_error("source and target must be different")
        try:
            src = Entity.objects.get(id=source, domain=domain)
            tgt = Entity.objects.get(id=target, domain=domain)
            _, created = Relationship.objects.get_or_create(
                source=src, target=tgt, type=rel_type, domain=domain,
                defaults={"description": description}
            )
            if created:
                created_count += 1
        except Entity.DoesNotExist:
            return _json_error("source or target entity not found for link")

    return JsonResponse({
        "ret": 0, 
        "msg": "imported", 
        "data": {
            "created_links": created_count,
            "domain": domain
        }
    })