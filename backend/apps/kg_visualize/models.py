# -*- coding: utf-8 -*-
from django.db import models

class Entity(models.Model):
    """
    knowledge graph's entity
    """
    id = models.CharField(max_length=100, primary_key=True, verbose_name="entityID")
    name = models.CharField(max_length=200, verbose_name="entityName")
    type = models.CharField(max_length=100, verbose_name="entityType", blank=True)
    description = models.TextField(verbose_name="entityDescribe", blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="createdTime")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="updatedTime")

    class Meta:
        verbose_name = "entity"
        verbose_name_plural = "entity"
        ordering = ["-updated_at"]
        app_label = "kg_visualize"  # 显式指定应用名称

    def __str__(self):
        return f"{self.name} ({self.id})"


class Relationship(models.Model):
    """
    relations between entitys
    """
    source = models.ForeignKey(
        Entity,
        on_delete=models.CASCADE,
        related_name="out_relations",
        verbose_name="sourceEntity"
    )
    target = models.ForeignKey(
        Entity,
        on_delete=models.CASCADE,
        related_name="in_relations",
        verbose_name="targetEntity"
    )
    type = models.CharField(max_length=100, verbose_name="relationType")  # 如"包含"、"属于"
    description = models.TextField(verbose_name="relationDescribe", blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="createdTime")

    class Meta:
        verbose_name = "entityRelation"
        verbose_name_plural = "entityRelation"
        unique_together = ("source", "target", "type")  # 避免重复关系
        app_label = "kg_visualize"  # 显式指定应用名称

    def __str__(self):
        return f"{self.source.name} -[{self.type}]-> {self.target.name}"