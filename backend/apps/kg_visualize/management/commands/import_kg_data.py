from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.core.files import File
from backend.apps.kg_visualize.models import Entity, Relationship
import json
import os
import sys


class Command(BaseCommand):
    help = 'Import knowledge graph data from JSON file with conflict resolution'

    def add_arguments(self, parser):
        parser.add_argument(
            'file_path',
            type=str,
            help='Path to the JSON file containing graph data'
        )
        parser.add_argument(
            '--domain',
            type=str,
            default='default',
            help='Domain for the imported data (default: default)'
        )
        parser.add_argument(
            '--strategy',
            type=str,
            choices=['merge', 'skip', 'overwrite', 'create_new'],
            default='merge',
            help='Import strategy for handling conflicts (default: merge)'
        )
        parser.add_argument(
            '--conflict-resolution',
            type=str,
            choices=['auto_id', 'merge_data', 'skip'],
            default='auto_id',
            help='Conflict resolution strategy for entity ID conflicts (default: auto_id)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Perform a dry run without actually importing data'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Enable verbose output'
        )

    def handle(self, *args, **options):
        file_path = options['file_path']
        domain = options['domain']
        strategy = options['strategy']
        conflict_resolution = options['conflict_resolution']
        dry_run = options['dry_run']
        verbose = options['verbose']

        # 检查文件是否存在
        if not os.path.exists(file_path):
            raise CommandError(f"File not found: {file_path}")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise CommandError(f"Invalid JSON file: {e}")
        except Exception as e:
            raise CommandError(f"Error reading file: {e}")

        # 验证数据格式
        if not isinstance(data, dict) or 'nodes' not in data or 'links' not in data:
            raise CommandError("Invalid data format. Expected {'nodes': [...], 'links': [...]}")

        nodes = data['nodes']
        links = data['links']

        if not isinstance(nodes, list) or not isinstance(links, list):
            raise CommandError("'nodes' and 'links' must be arrays")

        if verbose:
            self.stdout.write(f"Found {len(nodes)} nodes and {len(links)} links")
            self.stdout.write(f"Domain: {domain}")
            self.stdout.write(f"Strategy: {strategy}")
            self.stdout.write(f"Conflict resolution: {conflict_resolution}")
            if dry_run:
                self.stdout.write("DRY RUN MODE - No data will be imported")

        # 执行导入
        if dry_run:
            stats = self._dry_run_import(nodes, links, domain, strategy, conflict_resolution, verbose)
        else:
            stats = self._perform_import(nodes, links, domain, strategy, conflict_resolution, verbose)

        # 输出结果
        self._print_results(stats, verbose)

    def _dry_run_import(self, nodes, links, domain, strategy, conflict_resolution, verbose):
        """执行模拟导入，不实际保存数据"""
        stats = {
            "entities": {"created": 0, "updated": 0, "skipped": 0, "conflicts": 0},
            "relationships": {"created": 0, "skipped": 0, "errors": 0},
            "conflicts": []
        }

        # 模拟实体导入
        for node in nodes:
            node_id = node.get("id")
            name = node.get("name")
            
            if not node_id or not name:
                stats["entities"]["errors"] += 1
                continue

            existing_entity = Entity.objects.filter(id=node_id, domain=domain).first()
            
            if existing_entity:
                if conflict_resolution == "skip":
                    stats["entities"]["skipped"] += 1
                elif conflict_resolution == "merge_data":
                    # 检查是否需要更新
                    if (not existing_entity.type and node.get("type")) or \
                       (not existing_entity.description and node.get("description")):
                        stats["entities"]["updated"] += 1
                    else:
                        stats["entities"]["skipped"] += 1
                elif conflict_resolution == "auto_id":
                    stats["entities"]["conflicts"] += 1
                    stats["entities"]["created"] += 1
            else:
                stats["entities"]["created"] += 1

        # 模拟关系导入
        for link in links:
            source = link.get("source")
            target = link.get("target")
            rel_type = link.get("type")
            
            if not source or not target or not rel_type or source == target:
                stats["relationships"]["errors"] += 1
                continue

            # 检查源和目标实体是否存在
            src_exists = Entity.objects.filter(id=source, domain=domain).exists()
            tgt_exists = Entity.objects.filter(id=target, domain=domain).exists()
            
            if not src_exists or not tgt_exists:
                stats["relationships"]["errors"] += 1
                continue

            # 检查关系是否已存在
            src = Entity.objects.get(id=source, domain=domain)
            tgt = Entity.objects.get(id=target, domain=domain)
            existing_rel = Relationship.objects.filter(
                source=src, target=tgt, type=rel_type, domain=domain
            ).first()
            
            if existing_rel:
                if strategy == "skip":
                    stats["relationships"]["skipped"] += 1
                elif strategy == "merge":
                    stats["relationships"]["created"] += 1  # 算作更新
            else:
                stats["relationships"]["created"] += 1

        return stats

    @transaction.atomic
    def _perform_import(self, nodes, links, domain, strategy, conflict_resolution, verbose):
        """执行实际导入"""
        stats = {
            "entities": {"created": 0, "updated": 0, "skipped": 0, "conflicts": 0},
            "relationships": {"created": 0, "skipped": 0, "errors": 0},
            "conflicts": []
        }

        entity_id_mapping = {}

        # 处理实体导入
        for node in nodes:
            node_id = node.get("id")
            name = node.get("name")
            
            if not node_id or not name:
                stats["entities"]["errors"] += 1
                continue

            try:
                existing_entity = Entity.objects.filter(id=node_id, domain=domain).first()
                
                if existing_entity:
                    if conflict_resolution == "skip":
                        stats["entities"]["skipped"] += 1
                        entity_id_mapping[node_id] = node_id
                        if verbose:
                            self.stdout.write(f"  Skipped entity: {node_id}")
                    elif conflict_resolution == "merge_data":
                        updated = False
                        if not existing_entity.type and node.get("type"):
                            existing_entity.type = node.get("type")
                            updated = True
                        if not existing_entity.description and node.get("description"):
                            existing_entity.description = node.get("description")
                            updated = True
                        if updated:
                            existing_entity.save()
                            stats["entities"]["updated"] += 1
                            if verbose:
                                self.stdout.write(f"  Updated entity: {node_id}")
                        else:
                            stats["entities"]["skipped"] += 1
                            if verbose:
                                self.stdout.write(f"  Skipped entity (no changes): {node_id}")
                        entity_id_mapping[node_id] = node_id
                    elif conflict_resolution == "auto_id":
                        stats["entities"]["conflicts"] += 1
                        counter = 1
                        new_id = f"{node_id}_{counter}"
                        while Entity.objects.filter(id=new_id, domain=domain).exists():
                            counter += 1
                            new_id = f"{node_id}_{counter}"
                        
                        new_entity = Entity.objects.create(
                            id=new_id,
                            name=name,
                            type=node.get("type", ""),
                            description=node.get("description", ""),
                            domain=domain
                        )
                        entity_id_mapping[node_id] = new_id
                        stats["entities"]["created"] += 1
                        if verbose:
                            self.stdout.write(f"  Created entity with new ID: {node_id} -> {new_id}")
                else:
                    Entity.objects.create(
                        id=node_id,
                        name=name,
                        type=node.get("type", ""),
                        description=node.get("description", ""),
                        domain=domain
                    )
                    entity_id_mapping[node_id] = node_id
                    stats["entities"]["created"] += 1
                    if verbose:
                        self.stdout.write(f"  Created entity: {node_id}")
                        
            except Exception as e:
                stats["entities"]["errors"] += 1
                if verbose:
                    self.stdout.write(f"  Error creating entity {node_id}: {e}")

        # 处理关系导入
        for link in links:
            source = link.get("source")
            target = link.get("target")
            rel_type = link.get("type")
            description = link.get("description", "")
            
            if not source or not target or not rel_type or source == target:
                stats["relationships"]["errors"] += 1
                continue

            try:
                mapped_source = entity_id_mapping.get(source)
                mapped_target = entity_id_mapping.get(target)
                
                if not mapped_source or not mapped_target:
                    stats["relationships"]["errors"] += 1
                    continue

                src = Entity.objects.get(id=mapped_source, domain=domain)
                tgt = Entity.objects.get(id=mapped_target, domain=domain)
                
                existing_rel = Relationship.objects.filter(
                    source=src, target=tgt, type=rel_type, domain=domain
                ).first()
                
                if existing_rel:
                    if strategy == "skip":
                        stats["relationships"]["skipped"] += 1
                        if verbose:
                            self.stdout.write(f"  Skipped relationship: {source} -> {target}")
                    elif strategy == "merge":
                        if not existing_rel.description and description:
                            existing_rel.description = description
                            existing_rel.save()
                            stats["relationships"]["created"] += 1
                            if verbose:
                                self.stdout.write(f"  Updated relationship: {source} -> {target}")
                        else:
                            stats["relationships"]["skipped"] += 1
                            if verbose:
                                self.stdout.write(f"  Skipped relationship (no changes): {source} -> {target}")
                else:
                    Relationship.objects.create(
                        source=src, target=tgt, type=rel_type, 
                        description=description, domain=domain
                    )
                    stats["relationships"]["created"] += 1
                    if verbose:
                        self.stdout.write(f"  Created relationship: {source} -> {target}")
                        
            except Entity.DoesNotExist:
                stats["relationships"]["errors"] += 1
                if verbose:
                    self.stdout.write(f"  Error: Entity not found for relationship {source} -> {target}")
            except Exception as e:
                stats["relationships"]["errors"] += 1
                if verbose:
                    self.stdout.write(f"  Error creating relationship {source} -> {target}: {e}")

        return stats

    def _print_results(self, stats, verbose):
        """打印导入结果"""
        self.stdout.write("\n" + "="*50)
        self.stdout.write("IMPORT RESULTS")
        self.stdout.write("="*50)
        
        # 实体统计
        self.stdout.write("\nEntities:")
        self.stdout.write(f"  Created: {stats['entities']['created']}")
        self.stdout.write(f"  Updated: {stats['entities']['updated']}")
        self.stdout.write(f"  Skipped: {stats['entities']['skipped']}")
        self.stdout.write(f"  Conflicts: {stats['entities']['conflicts']}")
        if stats['entities']['errors'] > 0:
            self.stdout.write(f"  Errors: {stats['entities']['errors']}")

        # 关系统计
        self.stdout.write("\nRelationships:")
        self.stdout.write(f"  Created: {stats['relationships']['created']}")
        self.stdout.write(f"  Skipped: {stats['relationships']['skipped']}")
        if stats['relationships']['errors'] > 0:
            self.stdout.write(f"  Errors: {stats['relationships']['errors']}")

        # 冲突详情
        if stats['conflicts'] and verbose:
            self.stdout.write("\nConflicts:")
            for conflict in stats['conflicts']:
                self.stdout.write(f"  - {conflict['type']}: {conflict['message']}")

        self.stdout.write("\n" + "="*50)
