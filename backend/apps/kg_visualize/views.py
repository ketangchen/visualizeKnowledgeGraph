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
        print(111111)
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
                    "content": f"你是一个知识图谱AI助手，专门帮助用户分析和管理知识图谱数据。{context}"
                },
                {
                    "role": "user",
                    "content": user_message
                }
            ],
            # max_tokens=1000,conda init
            # temperature=0.7
        )
        answer=response.choices[0].message.content
        print(f"answer is:{answer}")
        
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
    
    # 模糊搜索实体
    def fuzzy_search_entities(query):
        results = []
        query_lower = query.lower()
        for node in nodes:
            node_name = node.get('name', '').lower()
            node_id = node.get('id', '').lower()
            node_desc = node.get('description', '').lower()
            
            # 检查是否包含查询关键词
            if (query_lower in node_name or 
                query_lower in node_id or 
                query_lower in node_desc):
                results.append(node)
        return results
    
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
    
    # 实体相关查询
    if any(keyword in message for keyword in ['实体', '节点', 'entity', 'node', '什么', '哪些', '谁', '哪里']):
        # 提取可能的实体名称
        for node in nodes:
            node_name = node.get('name', '').lower()
            if node_name in message and len(node_name) > 1:
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
                    for link in related_links[:5]:  # 最多显示5个关系
                        source_name = get_entity_name(link.get('source'))
                        target_name = get_entity_name(link.get('target'))
                        response += f"  • {source_name} --[{link.get('type', '')}]--> {target_name}\n"
                    
                    if len(related_links) > 5:
                        response += f"  ... 还有 {len(related_links) - 5} 个关系"
                
                return response
        
        # 模糊搜索
        search_results = fuzzy_search_entities(message)
        if search_results:
            if len(search_results) == 1:
                node = search_results[0]
                related_links = get_entity_relations(node['id'])
                return f"🔍 找到相关实体：{node.get('name')}（{node.get('domain', 'default')}领域），有 {len(related_links)} 个相关关系"
            else:
                names = [node.get('name') for node in search_results[:5]]
                return f"🔍 找到 {len(search_results)} 个相关实体：{', '.join(names)}"
        
        if any(keyword in message for keyword in ['数量', '多少个', 'count', 'total']):
            return f"📊 当前知识图谱共有 {total_nodes} 个实体，{total_links} 个关系"
        
        if any(keyword in message for keyword in ['列表', '所有', 'list', 'all']):
            if total_nodes <= 10:
                entity_names = [node.get('name', '') for node in nodes]
                return f"📋 所有实体：{', '.join(entity_names)}"
            else:
                return f"📋 共有 {total_nodes} 个实体，数量较多。建议询问特定实体或按领域筛选"
        
        if any(keyword in message for keyword in ['领域', 'domain']):
            domain_list = [f"{domain}({count}个)" for domain, count in domain_stats.items()]
            return f"🏷️ 图谱领域分布：{', '.join(domain_list)}"
    
    # 关系相关查询
    if any(keyword in message for keyword in ['关系', '连接', 'link', 'relation', '关联']):
        if any(keyword in message for keyword in ['数量', '多少个', 'count', 'total']):
            return f"🔗 当前知识图谱共有 {total_links} 个关系"
        
        if any(keyword in message for keyword in ['类型', '关系类型', 'type']):
            relation_list = [f"{rel_type}({count}个)" for rel_type, count in relation_types.items()]
            return f"🔗 关系类型分布：{', '.join(relation_list)}"
    
    # 统计信息查询
    if any(keyword in message for keyword in ['统计', '总结', 'summary', 'statistics', '概况', '分析']):
        domain_list = [f"{domain}({count}个)" for domain, count in domain_stats.items()]
        relation_list = [f"{rel_type}({count}个)" for rel_type, count in relation_types.items()]
        
        response = f"📊 知识图谱综合分析报告：\n\n"
        response += f"📈 基础统计：\n"
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
        
        # 找出最活跃的实体
        if nodes:
            entity_activity = {}
            for node in nodes:
                entity_activity[node['id']] = len(get_entity_relations(node['id']))
            
            most_active = max(entity_activity.items(), key=lambda x: x[1])
            most_active_entity = next(n for n in nodes if n['id'] == most_active[0])
            response += f"\n⭐ 最活跃实体：{most_active_entity.get('name')} ({most_active[1]} 个关系)"
        
        return response
    
    # 路径分析查询
    if any(keyword in message for keyword in ['路径', '连接', '路径分析', 'path']):
        if selected_node:
            related_links = get_entity_relations(selected_node['id'])
            if related_links:
                response = f"🛤️ {selected_node.get('name')} 的连接路径：\n"
                for link in related_links[:8]:  # 最多显示8个路径
                    source_name = get_entity_name(link.get('source'))
                    target_name = get_entity_name(link.get('target'))
                    response += f"  • {source_name} --[{link.get('type', '')}]--> {target_name}\n"
                return response
            else:
                return f"❌ {selected_node.get('name')} 目前没有连接关系"
        else:
            return "请先选择一个实体，然后询问路径分析"
    
    # 帮助信息
    if any(keyword in message for keyword in ['帮助', 'help', '怎么用', '如何使用', '能做什么']):
        return """🤖 我是史努比AI助手，可以为您提供以下服务：

📊 数据分析：
  • 实体统计和分布分析
  • 关系类型和连接度分析
  • 领域分布和活跃度分析

🔍 智能搜索：
  • 精确实体查询
  • 模糊关键词搜索
  • 相关实体推荐

🛤️ 路径分析：
  • 实体间连接路径
  • 关系网络分析
  • 影响力分析

💡 智能建议：
  • 数据优化建议
  • 关系扩展建议
  • 领域完善建议

请告诉我您想了解什么，我会为您提供详细的分析！"""
    
    # 通用回复
    return f"🤔 我理解您的问题。当前图谱有 {total_nodes} 个实体和 {total_links} 个关系。您可以询问：\n• 特定实体信息\n• 关系分析\n• 统计概况\n• 路径分析\n\n请具体描述您想了解的内容，我会为您提供详细答案！"


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