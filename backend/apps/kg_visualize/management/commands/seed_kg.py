from django.core.management.base import BaseCommand
from django.db import transaction
from backend.apps.kg_visualize.models import Entity, Relationship


class Command(BaseCommand):
    help = 'Seed demo knowledge graph data (idempotent)'

    @transaction.atomic
    def handle(self, *args, **options):
        entities = [
            {"id": "1", "name": "人工智能", "description": "研究如何使机器模拟人类智能的科学"},
            {"id": "2", "name": "机器学习", "description": "人工智能的一个分支"},
            {"id": "3", "name": "深度学习", "description": "机器学习的一个分支"},
            {"id": "4", "name": "神经网络", "description": "受人脑结构启发的计算模型"},
            {"id": "5", "name": "计算机视觉", "description": "使计算机能够从图像中获取理解的领域"},
        ]

        for e in entities:
            Entity.objects.update_or_create(
                id=e["id"],
                defaults={
                    "name": e["name"],
                    "type": e.get("type", ""),
                    "description": e.get("description", ""),
                },
            )

        rels = [
            ("1", "2", "包含"),
            ("2", "3", "包含"),
            ("3", "4", "基于"),
            ("1", "5", "包含"),
            ("5", "3", "应用"),
        ]

        created = 0
        for s, t, rtype in rels:
            src = Entity.objects.get(id=s)
            tgt = Entity.objects.get(id=t)
            _, c = Relationship.objects.get_or_create(
                source=src, target=tgt, type=rtype, defaults={"description": ""}
            )
            if c:
                created += 1

        self.stdout.write(self.style.SUCCESS(
            f"Seeded {len(entities)} entities and ensured relationships (new: {created})"
        ))


