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
            # 获取领域参数，默认为all（返回所有领域）
            domain = request.GET.get('domain', 'all')
            
            # 查询实体（如果指定了特定领域则过滤，否则返回所有）
            if domain == 'all':
                entities = Entity.objects.all().values("id", "name", "type", "description", "domain")
                relations = Relationship.objects.all().values(
                    "id", "source_id", "target_id", "type", "description", "domain"
                )
            else:
                entities = Entity.objects.filter(domain=domain).values("id", "name", "type", "description", "domain")
                relations = Relationship.objects.filter(domain=domain).values(
                    "id", "source_id", "target_id", "type", "description", "domain"
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
                        "id": r["id"],
                        "domain": r.get("domain") or "default"
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
                description=data.get('description', ''),
                domain=data.get('domain', 'default')
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
        data = list(queryset.values("id", "name", "type", "description", "domain"))
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
            description=data.get("description", ""),
            domain=data.get("domain", "default")
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
                "domain": entity.domain,
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
        domain = data.get("domain", entity.domain)

        if not name:
            return _json_error("'name' is required")

        entity.name = name
        entity.type = type_val or ""
        entity.description = description or ""
        entity.domain = domain or "default"
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
                "domain": r.domain,
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
    domain = data.get("domain", "default")

    if not source or not target or not rel_type:
        return _json_error("'source', 'target' and 'type' are required")
    if source == target:
        return _json_error("source and target must be different")

    try:
        src = Entity.objects.get(id=source)
        tgt = Entity.objects.get(id=target)
        rel = Relationship.objects.create(source=src, target=tgt, type=rel_type, description=description, domain=domain)
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
        if "domain" in data:
            rel.domain = data.get("domain") or "default"
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
    # 获取领域参数，默认为all（导出所有领域）
    domain = request.GET.get('domain', 'all')
    
    if domain == 'all':
        entities = list(Entity.objects.all().values("id", "name", "type", "description", "domain"))
        links = [
            {
                "id": r.id,
                "source": r.source_id,
                "target": r.target_id,
                "type": r.type,
                "description": r.description,
            }
            for r in Relationship.objects.all()
        ]
    else:
        entities = list(Entity.objects.filter(domain=domain).values("id", "name", "type", "description", "domain"))
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
    """
    改进的数据导入函数，支持：
    1. 重复数据检测和处理
    2. ID冲突解决（自动生成新ID或合并数据）
    3. 详细的导入报告
    4. 数据合并策略
    """
    try:
        payload = json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        return _json_error("Invalid JSON")

    nodes = payload.get("nodes", [])
    links = payload.get("links", [])
    import_strategy = payload.get("strategy", "merge")  # merge, skip, overwrite, create_new
    domain = payload.get("domain", "default")
    conflict_resolution = payload.get("conflict_resolution", "auto_id")  # auto_id, merge_data, skip

    if not isinstance(nodes, list) or not isinstance(links, list):
        return _json_error("'nodes' and 'links' must be arrays")

    # 导入统计
    import_stats = {
        "entities": {"created": 0, "updated": 0, "skipped": 0, "conflicts": 0, "errors": 0},
        "relationships": {"created": 0, "skipped": 0, "errors": 0},
        "conflicts": []
    }

    # 处理实体导入
    entity_id_mapping = {}  # 用于记录ID映射关系
    
    for node in nodes:
        node_id = node.get("id")
        name = node.get("name")
        
        if not node_id or not name:
            import_stats["entities"]["errors"] += 1
            continue

        try:
            # 检查是否存在相同ID的实体
            existing_entity = Entity.objects.filter(id=node_id, domain=domain).first()
            
            if existing_entity:
                # 处理冲突
                if conflict_resolution == "skip":
                    import_stats["entities"]["skipped"] += 1
                    entity_id_mapping[node_id] = node_id
                    continue
                elif conflict_resolution == "merge_data":
                    # 合并数据：保留现有数据，补充缺失字段
                    updated = False
                    if not existing_entity.type and node.get("type"):
                        existing_entity.type = node.get("type")
                        updated = True
                    if not existing_entity.description and node.get("description"):
                        existing_entity.description = node.get("description")
                        updated = True
                    if updated:
                        existing_entity.save()
                        import_stats["entities"]["updated"] += 1
                    else:
                        import_stats["entities"]["skipped"] += 1
                    entity_id_mapping[node_id] = node_id
                    continue
                elif conflict_resolution == "auto_id":
                    # 自动生成新ID
                    import_stats["entities"]["conflicts"] += 1
                    import_stats["conflicts"].append({
                        "type": "entity_id_conflict",
                        "original_id": node_id,
                        "message": f"Entity ID '{node_id}' already exists, will generate new ID"
                    })
                    
                    # 生成新ID
                    counter = 1
                    new_id = f"{node_id}_{counter}"
                    while Entity.objects.filter(id=new_id, domain=domain).exists():
                        counter += 1
                        new_id = f"{node_id}_{counter}"
                    
                    # 创建新实体
                    new_entity = Entity.objects.create(
                        id=new_id,
                        name=name,
                        type=node.get("type", ""),
                        description=node.get("description", ""),
                        domain=domain
                    )
                    entity_id_mapping[node_id] = new_id
                    import_stats["entities"]["created"] += 1
                    continue
            else:
                # 创建新实体
                try:
                    Entity.objects.create(
                        id=node_id,
                        name=name,
                        type=node.get("type", ""),
                        description=node.get("description", ""),
                        domain=domain
                    )
                    entity_id_mapping[node_id] = node_id
                    import_stats["entities"]["created"] += 1
                except Exception as e:
                    # 如果创建失败，可能是并发问题，尝试获取现有实体
                    existing_entity = Entity.objects.filter(id=node_id, domain=domain).first()
                    if existing_entity:
                        entity_id_mapping[node_id] = node_id
                        import_stats["entities"]["skipped"] += 1
                    else:
                        import_stats["entities"]["errors"] += 1
                        import_stats["conflicts"].append({
                            "type": "entity_creation_error",
                            "entity_id": node_id,
                            "message": str(e)
                        })
                
        except Exception as e:
            import_stats["entities"]["errors"] += 1
            import_stats["conflicts"].append({
                "type": "entity_creation_error",
                "entity_id": node_id,
                "message": str(e)
            })

    # 处理关系导入
    for link in links:
        source = link.get("source")
        target = link.get("target")
        rel_type = link.get("type")
        description = link.get("description", "")
        
        if not source or not target or not rel_type:
            import_stats["relationships"]["errors"] += 1
            continue
            
        if source == target:
            import_stats["relationships"]["errors"] += 1
            continue

        try:
            # 使用映射后的ID
            mapped_source = entity_id_mapping.get(source)
            mapped_target = entity_id_mapping.get(target)
            
            if not mapped_source or not mapped_target:
                import_stats["relationships"]["errors"] += 1
                continue

            src = Entity.objects.get(id=mapped_source, domain=domain)
            tgt = Entity.objects.get(id=mapped_target, domain=domain)
            
            # 检查关系是否已存在
            existing_rel = Relationship.objects.filter(
                source=src, target=tgt, type=rel_type, domain=domain
            ).first()
            
            if existing_rel:
                if import_strategy == "skip":
                    import_stats["relationships"]["skipped"] += 1
                elif import_strategy == "merge":
                    # 合并关系描述
                    if not existing_rel.description and description:
                        existing_rel.description = description
                        existing_rel.save()
                        import_stats["relationships"]["created"] += 1  # 算作更新
                    else:
                        import_stats["relationships"]["skipped"] += 1
            else:
                # 创建新关系
                Relationship.objects.create(
                    source=src, target=tgt, type=rel_type, 
                    description=description, domain=domain
                )
                import_stats["relationships"]["created"] += 1
                
        except Entity.DoesNotExist:
            import_stats["relationships"]["errors"] += 1
            import_stats["conflicts"].append({
                "type": "relationship_entity_not_found",
                "source": source,
                "target": target,
                "message": "Source or target entity not found"
            })
        except Exception as e:
            import_stats["relationships"]["errors"] += 1
            import_stats["conflicts"].append({
                "type": "relationship_creation_error",
                "source": source,
                "target": target,
                "message": str(e)
            })

    return JsonResponse({
        "ret": 0,
        "msg": "import completed",
        "data": {
            "import_stats": import_stats,
            "entity_id_mapping": entity_id_mapping,
            "domain": domain,
            "strategy": import_strategy,
            "conflict_resolution": conflict_resolution
        }
    })