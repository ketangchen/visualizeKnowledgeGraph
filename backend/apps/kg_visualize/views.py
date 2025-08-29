# -*- coding: utf-8 -*-
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db import transaction, models
from .models import Entity, Relationship
import json
# 使用openai库调用ChatGPT API
import openai

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
                "nodes": [
                    {
                        "id": e["id"],
                        "name": e["name"],
                        "type": e.get("type", ""),
                        "description": e.get("description", ""),
                        "domain": e.get("domain") or "default"
                    } for e in entities
                ],
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
            existing_entity = Entity.objects.filter(id=node_id).first()
            
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
                    while Entity.objects.filter(id=new_id).exists():
                        counter += 1
                        new_id = f"{node_id}_{counter}"
                    
                    # 创建新实体
                    new_entity = Entity.objects.create(
                        id=new_id,
                        name=name,
                        type=node.get("type", ""),
                        description=node.get("description", ""),
                        domain=node.get("domain", domain)
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
                        domain=node.get("domain", domain)
                    )
                    entity_id_mapping[node_id] = node_id
                    import_stats["entities"]["created"] += 1
                except Exception as e:
                    # 如果创建失败，可能是并发问题，尝试获取现有实体
                    existing_entity = Entity.objects.filter(id=node_id).first()
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

            src = Entity.objects.get(id=mapped_source)
            tgt = Entity.objects.get(id=mapped_target)
            
            # 检查关系是否已存在
            existing_rel = Relationship.objects.filter(
                source=src, target=tgt, type=rel_type
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
                    description=description, domain=link.get("domain", domain)
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


@csrf_exempt
@require_http_methods(["POST"])
def ai_chat(request):
    """AI聊天接口"""
    try:
        data = json.loads(request.body or b"{}")
        user_message = data.get("message", "")
        graph_data = data.get("graphData", {})
        current_domain = data.get("currentDomain", "all")
        selected_node = data.get("selectedNode", None)
        selected_link = data.get("selectedLink", None)
        use_external_ai = data.get("useExternalAI", True)  # 默认使用外部AI
        
        if not user_message:
            return JsonResponse({"ret": 1, "msg": "消息不能为空"})
        
        # 生成AI回复
        ai_response = generate_ai_response(user_message, graph_data, current_domain, selected_node, selected_link, use_external_ai)
        
        return JsonResponse({
            "ret": 0,
            "response": ai_response
        })
        
    except json.JSONDecodeError:
        return JsonResponse({"ret": 1, "msg": "无效的JSON数据"})
    except Exception as e:
        return JsonResponse({"ret": 1, "msg": f"AI聊天失败: {str(e)}"})


def generate_ai_response(user_message, graph_data, current_domain, selected_node, selected_link, use_external_ai=True):
    """生成AI回复"""
    # 根据开关决定使用外部AI还是本地AI
    if not use_external_ai:
        return generate_local_ai_response(user_message, graph_data, current_domain, selected_node, selected_link)
    
    try:    
        # 设置API配置
        openai.api_key = 'sk-jaRSXNMxl1xdjOzu5e8e780c79Ee40D99aE43c0b74A90fF6'
        openai.base_url = "https://free.v36.cm/v1/"
        openai.default_headers = {"x-foo": "true"}
        
        # 构建丰富的上下文信息
        nodes = graph_data.get('nodes', [])
        links = graph_data.get('links', [])
        
        # 统计信息
        total_nodes = len(nodes)
        total_links = len(links)
        
        # 领域统计
        domain_stats = {}
        for node in nodes:
            domain = node.get('domain', 'default')
            domain_stats[domain] = domain_stats.get(domain, 0) + 1
        
        # 关系类型统计
        relation_types = {}
        for link in links:
            rel_type = link.get('type', '未知')
            relation_types[rel_type] = relation_types.get(rel_type, 0) + 1
        
        # 构建实体列表（限制数量避免过长）
        entity_list = []
        for node in nodes[:20]:  # 最多显示20个实体
            entity_info = f"{node.get('name', '')} (ID: {node.get('id', '')})"
            if node.get('description'):
                entity_info += f" - {node.get('description', '')[:50]}"
            if node.get('domain') and node.get('domain') != 'default':
                entity_info += f" [领域: {node.get('domain')}]"
            entity_list.append(entity_info)
        
        # 构建关系列表（限制数量避免过长）
        link_list = []
        for link in links[:15]:  # 最多显示15个关系
            source_name = ""
            target_name = ""
            
            # 获取源实体名称
            if isinstance(link.get('source'), dict):
                source_name = link['source'].get('name', '')
            else:
                source_id = link.get('source', '')
                source_node = next((n for n in nodes if n.get('id') == source_id), None)
                source_name = source_node.get('name', source_id) if source_node else source_id
            
            # 获取目标实体名称
            if isinstance(link.get('target'), dict):
                target_name = link['target'].get('name', '')
            else:
                target_id = link.get('target', '')
                target_node = next((n for n in nodes if n.get('id') == target_id), None)
                target_name = target_node.get('name', target_id) if target_node else target_id
            
            link_info = f"{source_name} --[{link.get('type', '')}]--> {target_name}"
            if link.get('description'):
                link_info += f" ({link.get('description', '')[:30]})"
            link_list.append(link_info)
        
        # 构建完整的上下文信息
        context = f"""
        知识图谱详细分析报告：
        
        📊 基础统计信息：
        - 总实体数量：{total_nodes} 个
        - 总关系数量：{total_links} 个
        - 当前查看领域：{current_domain if current_domain != 'all' else '所有领域'}
        
        🏷️ 领域分布：
        {chr(10).join([f"  - {domain}: {count} 个实体" for domain, count in domain_stats.items()])}
        
        🔗 关系类型分布：
        {chr(10).join([f"  - {rel_type}: {count} 个关系" for rel_type, count in relation_types.items()])}
        
        📋 实体列表（前20个）：
        {chr(10).join([f"  - {entity}" for entity in entity_list])}
        {f"{chr(10)}  ... 还有 {total_nodes - 20} 个实体" if total_nodes > 20 else ""}
        
        🔗 关系列表（前15个）：
        {chr(10).join([f"  - {link}" for link in link_list])}
        {f"{chr(10)}  ... 还有 {total_links - 15} 个关系" if total_links > 15 else ""}
        """
        
        # 添加当前选中元素信息
        if selected_node:
            selected_entity_links = [
                link for link in links 
                if (isinstance(link.get('source'), dict) and link['source'].get('id') == selected_node.get('id')) or
                   (isinstance(link.get('source'), str) and link.get('source') == selected_node.get('id')) or
                   (isinstance(link.get('target'), dict) and link['target'].get('id') == selected_node.get('id')) or
                   (isinstance(link.get('target'), str) and link.get('target') == selected_node.get('id'))
            ]
            
            context += f"""
            
        🎯 当前选中实体详情：
        - 实体名称：{selected_node.get('name', '')}
        - 实体ID：{selected_node.get('id', '')}
        - 实体类型：{selected_node.get('type', '未指定')}
        - 所属领域：{selected_node.get('domain', 'default')}
        - 实体描述：{selected_node.get('description', '无描述')}
        - 相关关系数量：{len(selected_entity_links)} 个
        """
            
            if selected_entity_links:
                context += "\n- 相关关系：\n"
                for link in selected_entity_links[:10]:  # 最多显示10个关系
                    source_name = ""
                    target_name = ""
                    
                    if isinstance(link.get('source'), dict):
                        source_name = link['source'].get('name', '')
                    else:
                        source_id = link.get('source', '')
                        source_node = next((n for n in nodes if n.get('id') == source_id), None)
                        source_name = source_node.get('name', source_id) if source_node else source_id
                    
                    if isinstance(link.get('target'), dict):
                        target_name = link['target'].get('name', '')
                    else:
                        target_id = link.get('target', '')
                        target_node = next((n for n in nodes if n.get('id') == target_id), None)
                        target_name = target_node.get('name', target_id) if target_node else target_id
                    
                    context += f"  * {source_name} --[{link.get('type', '')}]--> {target_name}\n"
        
        if selected_link:
            context += f"""
            
        🔗 当前选中关系详情：
        - 关系类型：{selected_link.get('type', '')}
        - 关系描述：{selected_link.get('description', '无描述')}
        - 所属领域：{selected_link.get('domain', 'default')}
        """
        
        # 添加AI助手能力说明
        context += f"""
        
        🤖 AI助手能力说明：
        我可以帮您：
        1. 分析知识图谱结构和内容
        2. 查找特定实体及其关系
        3. 统计各领域和关系类型的分布
        4. 提供实体间的路径分析
        5. 回答关于知识图谱的各类问题
        6. 建议数据优化和扩展方向
        
        请告诉我您想了解什么，我会基于以上信息为您提供详细的分析和建议。
        """
        
        # 调用ChatGPT API
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": f"""你是一个专业的知识图谱AI助手。你的首要任务是**优先从提供的知识图谱数据中查找和匹配实体**。

🎯 核心原则：
1. **数据优先**：所有回答必须基于提供的知识图谱数据，不要使用外部知识
2. **精确匹配**：优先在"实体列表"中查找完全匹配的实体名称
3. **模糊匹配**：如果精确匹配失败，再在实体名称、描述、ID中进行模糊搜索
4. **关系分析**：基于"关系列表"分析实体间的连接关系
5. **数据驱动**：所有统计信息必须来自提供的数据

🔍 实体查找策略：
1. **精确匹配**：在实体列表中查找完全相同的实体名称
2. **包含匹配**：查找实体名称中包含查询关键词的实体
3. **描述匹配**：在实体描述中查找相关关键词
4. **领域匹配**：根据领域信息查找相关实体
5. **ID匹配**：根据实体ID查找

📊 回答要求：
- 必须基于提供的数据进行分析
- 优先使用"实体列表"和"关系列表"中的数据
- 提供具体的实体名称、关系类型、统计数字
- 使用清晰的结构和emoji
- 当数据中没有相关信息时，明确说明"在提供的数据中未找到相关信息"

💡 回答示例：

示例1 - 实体查询：
用户问："人工智能"
你应该回答：
"🎯 在知识图谱数据中找到了实体：人工智能

📋 实体详情：
- 名称：人工智能
- 领域：ai_domain
- 描述：研究如何使机器模拟人类智能的科学

🔗 相关关系：
- 人工智能 --[包含]--> 机器学习
- 人工智能 --[包含]--> 计算机视觉
- 计算机视觉 --[应用]--> 深度学习

💡 建议：您可以询问人工智能的具体关系，或者了解其他AI相关实体。"

示例2 - 模糊查询：
用户问："AI"
你应该回答：
"🔍 基于关键词"AI"，在知识图谱数据中找到以下相关实体：

📋 匹配结果：
1. 人工智能 (ai_domain) - 研究如何使机器模拟人类智能的科学
2. 机器学习 (ai_domain) - 人工智能的一个分支
3. 深度学习 (ai_domain) - 机器学习的一个分支
4. 神经网络 (ai_domain) - 受人脑结构启发的计算模型
5. 计算机视觉 (ai_domain) - 使计算机能够从图像中获取理解的领域

🔗 关系网络：
- 人工智能包含机器学习和计算机视觉
- 机器学习包含深度学习
- 深度学习基于神经网络

💡 建议：请告诉我您想了解哪个具体实体，我可以提供更详细的信息。"

示例3 - 统计查询：
用户问："统计"
你应该回答：
"📊 基于提供的数据，知识图谱统计信息：

📈 基础数据：
• 总实体数：{total_nodes} 个
• 总关系数：{total_links} 个

🏷️ 领域分布：
{chr(10).join([f"• {domain}：{count} 个实体" for domain, count in domain_stats.items()])}

🔗 关系类型：
{chr(10).join([f"• {rel_type}：{count} 个关系" for rel_type, count in relation_types.items()])}

💡 数据来源：以上信息均来自提供的知识图谱数据。"

当前知识图谱数据：
{context}

⚠️ 重要提醒：请严格按照以上策略，优先从提供的数据中查找实体和关系，不要使用外部知识。如果数据中没有相关信息，请明确说明"在提供的数据中未找到相关信息"。
"""
                },
                {
                    "role": "user",
                    "content": f"""用户查询：{user_message}

⚠️ 重要指令：
1. **优先查找**：首先在"实体列表"中查找完全匹配的实体名称
2. **模糊匹配**：如果没有精确匹配，在实体名称、描述、ID中查找包含关键词的实体
3. **关系分析**：基于"关系列表"分析找到的实体与其他实体的连接关系
4. **数据驱动**：所有回答必须基于提供的数据，不要使用外部知识

🔍 查找步骤：
1. 检查"实体列表"中是否有完全匹配的实体名称
2. 如果没有，检查实体名称是否包含查询关键词
3. 检查实体描述是否包含查询关键词
4. 检查实体ID是否包含查询关键词
5. 基于"关系列表"分析找到实体的相关关系

📊 回答要求：
- 明确说明在数据中找到了什么
- 提供具体的实体名称、关系类型
- 使用emoji和清晰的结构
- 如果数据中没有相关信息，明确说明"在提供的数据中未找到相关信息"

请严格按照以上步骤进行查找和回答。"""
                }
            ],
            max_tokens=1500,
            temperature=0.3
        )
        answer=response.choices[0].message.content
        return answer
        
    except Exception as e:
        # 如果API调用失败，使用本地回复
        return generate_local_ai_response(user_message, graph_data, current_domain, selected_node, selected_link)


def generate_local_ai_response(user_message, graph_data, current_domain, selected_node, selected_link):
    """本地AI回复（当外部API不可用时）"""
    message = user_message.lower()
    nodes = graph_data.get('nodes', [])
    links = graph_data.get('links', [])
    
    # 统计信息
    total_nodes = len(nodes)
    total_links = len(links)
    
    # 领域统计
    domain_stats = {}
    for node in nodes:
        domain = node.get('domain', 'default')
        domain_stats[domain] = domain_stats.get(domain, 0) + 1
    
    # 关系类型统计
    relation_types = {}
    for link in links:
        rel_type = link.get('type', '未知')
        relation_types[rel_type] = relation_types.get(rel_type, 0) + 1
    
    # 智能模糊搜索实体 - 支持多种匹配策略
    def smart_search_entities(query):
        results = []
        query_lower = query.lower()
        query_words = query_lower.split()
        
        for node in nodes:
            node_name = node.get('name', '').lower()
            node_id = node.get('id', '').lower()
            node_desc = node.get('description', '').lower()
            node_type = node.get('type', '').lower()
            node_domain = node.get('domain', '').lower()
            
            score = 0
            
            # 1. 精确匹配（最高分）
            if query_lower == node_name:
                score += 100
            elif query_lower == node_id:
                score += 90
            
            # 2. 包含匹配
            if query_lower in node_name:
                score += 80
            elif query_lower in node_id:
                score += 70
            elif query_lower in node_desc:
                score += 60
            
            # 3. 分词匹配（支持部分词匹配）
            for word in query_words:
                if len(word) > 1:  # 忽略单字符
                    if word in node_name:
                        score += 40
                    elif word in node_desc:
                        score += 30
                    elif word in node_type:
                        score += 25
                    elif word in node_domain:
                        score += 20
            
            # 4. 拼音匹配（简单实现）
            if any(char in 'abcdefghijklmnopqrstuvwxyz' for char in query_lower):
                # 英文查询，检查是否有英文内容
                if any(char in 'abcdefghijklmnopqrstuvwxyz' for char in node_name):
                    score += 15
            
            # 5. 语义相似度（基于关键词）
            semantic_keywords = {
                'ai': ['人工智能', '机器学习', '深度学习', '神经网络', '算法'],
                'medical': ['医学', '医疗', '疾病', '治疗', '药物', '医院'],
                'finance': ['金融', '投资', '股票', '基金', '理财', '银行'],
                'education': ['教育', '学习', '培训', '学校', '课程'],
                'tech': ['技术', '软件', '编程', '开发', '系统']
            }
            
            for key, keywords in semantic_keywords.items():
                if key in query_lower:
                    for keyword in keywords:
                        if keyword in node_name or keyword in node_desc:
                            score += 35
                            break
            
            if score > 0:
                results.append((node, score))
        
        # 按分数排序并返回实体
        results.sort(key=lambda x: x[1], reverse=True)
        return [node for node, score in results]
    
    # 智能实体推荐
    def recommend_related_entities(entity_id, max_recommendations=5):
        """基于关系推荐相关实体"""
        related_entities = set()
        entity_relations = get_entity_relations(entity_id)
        
        for link in entity_relations:
            if isinstance(link.get('source'), dict):
                if link['source'].get('id') != entity_id:
                    related_entities.add(link['source'].get('id'))
            elif isinstance(link.get('source'), str) and link.get('source') != entity_id:
                related_entities.add(link.get('source'))
            
            if isinstance(link.get('target'), dict):
                if link['target'].get('id') != entity_id:
                    related_entities.add(link['target'].get('id'))
            elif isinstance(link.get('target'), str) and link.get('target') != entity_id:
                related_entities.add(link.get('target'))
        
        recommendations = []
        for entity_id in list(related_entities)[:max_recommendations]:
            entity = next((n for n in nodes if n.get('id') == entity_id), None)
            if entity:
                recommendations.append(entity)
        
        return recommendations
    
    # 获取实体的相关关系
    def get_entity_relations(entity_id):
        return [
            link for link in links 
            if (isinstance(link.get('source'), dict) and link['source'].get('id') == entity_id) or
               (isinstance(link.get('source'), str) and link.get('source') == entity_id) or
               (isinstance(link.get('target'), dict) and link['target'].get('id') == entity_id) or
               (isinstance(link.get('target'), str) and link.get('target') == entity_id)
        ]
    
    # 获取实体名称
    def get_entity_name(entity_id):
        if isinstance(entity_id, dict):
            return entity_id.get('name', '')
        else:
            entity = next((n for n in nodes if n.get('id') == entity_id), None)
            return entity.get('name', entity_id) if entity else entity_id
    
    # 智能实体查询 - 支持多种查询方式
    def handle_entity_query():
        # 1. 精确实体查询
        for node in nodes:
            node_name = node.get('name', '').lower()
            if node_name in message and len(node_name) > 1:
                return generate_entity_detail_response(node)
        
        # 2. 智能模糊搜索
        search_results = smart_search_entities(message)
        if search_results:
            if len(search_results) == 1:
                return generate_entity_detail_response(search_results[0])
            else:
                return generate_entity_list_response(search_results[:8])  # 最多显示8个
        
        # 3. 领域相关查询
        if any(keyword in message for keyword in ['领域', 'domain', '分类']):
            return handle_domain_query()
        
        # 4. 统计查询
        if any(keyword in message for keyword in ['数量', '多少个', 'count', 'total', '统计']):
            return handle_statistics_query()
        
        # 5. 推荐查询
        if any(keyword in message for keyword in ['推荐', '建议', '相关', '类似']):
            return handle_recommendation_query()
        
        return None
    
    def generate_entity_detail_response(node):
        """生成实体详细信息响应"""
        related_links = get_entity_relations(node['id'])
        domain = node.get('domain', 'default')
        description = node.get('description', '无描述')
        
        response = f"🎯 找到实体：{node.get('name')}（ID: {node.get('id')}）\n"
        if domain != 'default':
            response += f"📍 所属领域：{domain}\n"
        if description and description != '无描述':
            response += f"📝 描述：{description}\n"
        response += f"🔗 相关关系：{len(related_links)} 个\n"
        
        if related_links:
            relation_types = set(link.get('type', '') for link in related_links)
            response += f"📋 关系类型：{', '.join(relation_types)}\n\n"
            
            # 显示具体关系
            response += "具体关系：\n"
            for link in related_links[:6]:  # 最多显示6个关系
                source_name = get_entity_name(link.get('source'))
                target_name = get_entity_name(link.get('target'))
                response += f"  • {source_name} --[{link.get('type', '')}]--> {target_name}\n"
            
            if len(related_links) > 6:
                response += f"  ... 还有 {len(related_links) - 6} 个关系\n"
            
            # 推荐相关实体
            recommendations = recommend_related_entities(node['id'], 3)
            if recommendations:
                response += f"\n💡 相关推荐：\n"
                for rec in recommendations:
                    response += f"  • {rec.get('name')} ({rec.get('domain', 'default')})\n"
        
        return response
    
    def generate_entity_list_response(entities):
        """生成实体列表响应"""
        response = f"🔍 找到 {len(entities)} 个相关实体：\n\n"
        for i, entity in enumerate(entities, 1):
            domain = entity.get('domain', 'default')
            desc = entity.get('description', '')[:30] if entity.get('description') else ''
            response += f"{i}. {entity.get('name')} ({domain})"
            if desc:
                response += f" - {desc}..."
            response += "\n"
        
        if len(entities) > 5:
            response += f"\n💡 提示：请提供更具体的查询条件，我可以为您找到更精确的结果"
        
        return response
    
    def handle_domain_query():
        """处理领域相关查询"""
        domain_list = [f"{domain}({count}个)" for domain, count in domain_stats.items()]
        response = f"🏷️ 知识图谱领域分布：\n\n"
        for domain, count in domain_stats.items():
            percentage = (count / total_nodes) * 100
            response += f"• {domain}：{count} 个实体 ({percentage:.1f}%)\n"
        
        # 推荐最活跃的领域
        most_active_domain = max(domain_stats.items(), key=lambda x: x[1])
        response += f"\n⭐ 最活跃领域：{most_active_domain[0]} ({most_active_domain[1]} 个实体)"
        
        return response
    
    def handle_statistics_query():
        """处理统计查询"""
        response = f"📊 知识图谱统计概览：\n\n"
        response += f"📈 基础数据：\n"
        response += f"  • 总实体数：{total_nodes} 个\n"
        response += f"  • 总关系数：{total_links} 个\n"
        response += f"  • 平均连接度：{total_links/total_nodes:.1f} (每个实体的平均关系数)\n\n"
        
        response += f"🏷️ 领域分布：\n"
        for domain, count in domain_stats.items():
            percentage = (count / total_nodes) * 100
            response += f"  • {domain}：{count} 个实体 ({percentage:.1f}%)\n"
        
        response += f"\n🔗 关系类型分布：\n"
        for rel_type, count in relation_types.items():
            percentage = (count / total_links) * 100
            response += f"  • {rel_type}：{count} 个关系 ({percentage:.1f}%)\n"
        
        return response
    
    def handle_recommendation_query():
        """处理推荐查询"""
        if selected_node:
            recommendations = recommend_related_entities(selected_node['id'], 5)
            if recommendations:
                response = f"💡 基于 {selected_node.get('name')} 的推荐：\n\n"
                for i, rec in enumerate(recommendations, 1):
                    domain = rec.get('domain', 'default')
                    desc = rec.get('description', '')[:40] if rec.get('description') else ''
                    response += f"{i}. {rec.get('name')} ({domain})"
                    if desc:
                        response += f"\n   {desc}..."
                    response += "\n"
                return response
            else:
                return f"❌ {selected_node.get('name')} 目前没有相关推荐"
        else:
            # 推荐最活跃的实体
            if nodes:
                entity_activity = {}
                for node in nodes:
                    entity_activity[node['id']] = len(get_entity_relations(node['id']))
                
                most_active = max(entity_activity.items(), key=lambda x: x[1])
                most_active_entity = next(n for n in nodes if n['id'] == most_active[0])
                return f"⭐ 推荐最活跃实体：{most_active_entity.get('name')} ({most_active[1]} 个关系)"
        
        return "请先选择一个实体，我可以为您推荐相关内容"
        
    # 智能关系查询
    def handle_relation_query():
        if any(keyword in message for keyword in ['关系', '连接', 'link', 'relation', '关联']):
            if any(keyword in message for keyword in ['数量', '多少个', 'count', 'total']):
                return f"🔗 当前知识图谱共有 {total_links} 个关系"
            
            if any(keyword in message for keyword in ['类型', '关系类型', 'type']):
                return handle_relation_type_query()
            
            if any(keyword in message for keyword in ['路径', '连接', '路径分析', 'path']):
                return handle_path_analysis_query()
            
            # 默认关系统计
            return handle_relation_type_query()
        
        return None
    
    def handle_relation_type_query():
        """处理关系类型查询"""
        response = f"🔗 关系类型分析：\n\n"
        
        # 按数量排序关系类型
        sorted_relations = sorted(relation_types.items(), key=lambda x: x[1], reverse=True)
        
        for rel_type, count in sorted_relations:
            percentage = (count / total_links) * 100
            response += f"• {rel_type}：{count} 个关系 ({percentage:.1f}%)\n"
        
        # 找出最常用的关系类型
        if sorted_relations:
            most_common = sorted_relations[0]
            response += f"\n⭐ 最常用关系类型：{most_common[0]} ({most_common[1]} 个关系)"
        
        return response
    
    def handle_path_analysis_query():
        """处理路径分析查询"""
        if selected_node:
            related_links = get_entity_relations(selected_node['id'])
            if related_links:
                response = f"🛤️ {selected_node.get('name')} 的连接路径分析：\n\n"
                
                # 按关系类型分组
                relation_groups = {}
                for link in related_links:
                    rel_type = link.get('type', '未知')
                    if rel_type not in relation_groups:
                        relation_groups[rel_type] = []
                    relation_groups[rel_type].append(link)
                
                for rel_type, links in relation_groups.items():
                    response += f"📋 {rel_type} 关系 ({len(links)} 个)：\n"
                    for link in links[:4]:  # 每种类型最多显示4个
                        source_name = get_entity_name(link.get('source'))
                        target_name = get_entity_name(link.get('target'))
                        response += f"  • {source_name} --> {target_name}\n"
                    
                    if len(links) > 4:
                        response += f"  ... 还有 {len(links) - 4} 个\n"
                    response += "\n"
                
                return response
            else:
                return f"❌ {selected_node.get('name')} 目前没有连接关系"
        else:
            return "请先选择一个实体，我可以为您分析其连接路径"
    
    # 智能问答主逻辑
    def smart_qa():
        # 1. 实体查询
        entity_result = handle_entity_query()
        if entity_result:
            return entity_result
        
        # 2. 关系查询
        relation_result = handle_relation_query()
        if relation_result:
            return relation_result
        
        # 3. 通用统计查询
        if any(keyword in message for keyword in ['统计', '总结', 'summary', 'statistics', '概况', '分析']):
            return handle_statistics_query()
        
        # 4. 智能推荐
        if any(keyword in message for keyword in ['推荐', '建议', '相关', '类似', '热门']):
            return handle_recommendation_query()
        
        # 5. 帮助信息
        if any(keyword in message for keyword in ['帮助', 'help', '怎么用', '如何使用', '能做什么']):
            return get_help_info()
        
        # 6. 智能搜索（兜底）
        search_results = smart_search_entities(message)
        if search_results:
            return generate_entity_list_response(search_results[:5])
        
        # 7. 通用回复
        return get_general_response()
    
    def get_help_info():
        """获取帮助信息"""
        return """🤖 我是史努比AI助手，可以为您提供以下智能服务：

📊 数据分析：
  • 实体统计和分布分析
  • 关系类型和连接度分析
  • 领域分布和活跃度分析
  • 路径分析和网络结构

🔍 智能搜索：
  • 精确实体查询
  • 模糊关键词搜索
  • 语义相似度匹配
  • 多维度智能推荐

🛤️ 路径分析：
  • 实体间连接路径
  • 关系网络分析
  • 影响力分析
  • 关联度计算

💡 智能建议：
  • 数据优化建议
  • 关系扩展建议
  • 领域完善建议
  • 热门实体推荐

🎯 使用技巧：
  • 直接输入实体名称进行精确查询
  • 使用关键词进行模糊搜索
  • 询问"统计"获取整体分析
  • 询问"推荐"获取智能建议

请告诉我您想了解什么，我会为您提供详细的分析！"""
    
    def get_general_response():
        """通用回复"""
        return f"🤔 我理解您的问题。当前图谱有 {total_nodes} 个实体和 {total_links} 个关系。\n\n您可以尝试：\n• 直接输入实体名称（如：人工智能）\n• 询问统计信息（如：统计、分析）\n• 搜索相关内容（如：AI、医疗、金融）\n• 获取推荐（如：推荐、热门）\n\n请具体描述您想了解的内容，我会为您提供智能分析！"
    
    # 调用智能问答主逻辑
    return smart_qa()


@csrf_exempt
@require_http_methods(["POST"])
def clear_all_data(request):
    """清空所有数据"""
    try:
        # 获取当前数据作为备份
        entities = Entity.objects.all()
        relationships = Relationship.objects.all()
        
        # 构建备份数据
        backup_data = {
            "nodes": [
                {
                    "id": entity.id,
                    "name": entity.name,
                    "description": entity.description,
                    "domain": entity.domain
                }
                for entity in entities
            ],
            "links": [
                {
                    "source": rel.source_id,
                    "target": rel.target_id,
                    "type": rel.type,
                    "description": rel.description,
                    "domain": rel.domain
                }
                for rel in relationships
            ]
        }
        
        # 删除所有数据
        entities.delete()
        relationships.delete()
        
        return JsonResponse({
            "ret": 0,
            "success": True,
            "message": "数据已清空",
            "backup_data": backup_data,
            "deleted_count": {
                "entities": len(backup_data["nodes"]),
                "relationships": len(backup_data["links"])
            }
        })
        
    except Exception as e:
        return JsonResponse({
            "ret": 1,
            "success": False,
            "message": f"清空数据失败: {str(e)}"
        }, status=500)