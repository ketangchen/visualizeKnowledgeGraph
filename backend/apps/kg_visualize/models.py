from django.db import models

class Entity(models.Model):
    """知识图谱实体（如人物、概念、地点等）"""
    id = models.CharField(primary_key=True, max_length=50, verbose_name="实体ID")
    name = models.CharField(max_length=100, verbose_name="实体名称")
    type = models.CharField(max_length=50, verbose_name="实体类型", blank=True)  # 如"人物"、"组织"
    description = models.TextField(verbose_name="实体描述", blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        verbose_name = "知识实体"
        verbose_name_plural = "知识实体"

    def __str__(self):
        return f"{self.name} ({self.type})"

class Relationship(models.Model):
    """实体间的关系"""
    source = models.ForeignKey(
        Entity,
        on_delete=models.CASCADE,
        related_name="out_relations",
        verbose_name="源实体"
    )
    target = models.ForeignKey(
        Entity,
        on_delete=models.CASCADE,
        related_name="in_relations",
        verbose_name="目标实体"
    )
    type = models.CharField(max_length=100, verbose_name="关系类型")  # 如"包含"、"合作"
    description = models.TextField(verbose_name="关系描述", blank=True)

    class Meta:
        verbose_name = "实体关系"
        verbose_name_plural = "实体关系"

    def __str__(self):
        return f"{self.source.name} -[{self.type}]-> {self.target.name}"