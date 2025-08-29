# -*- coding: utf-8 -*-
from django.urls import path
from . import views

urlpatterns = [
    # Graph data (D3-friendly)
    path('kg/data', views.get_graph_data, name='get_graph_data'),

    # Backward compatible legacy endpoint
    path('kg/entity', views.add_entity, name='add_entity'),

    # Entity CRUD
    path('kg/entities', views.list_or_create_entities, name='list_or_create_entities'),
    path('kg/entities/<str:entity_id>', views.entity_detail, name='entity_detail'),

    # Relationship CRUD
    path('kg/relationships', views.list_or_create_relationships, name='list_or_create_relationships'),
    path('kg/relationships/<int:rel_id>', views.relationship_detail, name='relationship_detail'),

    # Import/Export
    path('kg/export', views.export_graph, name='export_graph'),
    path('kg/import', views.import_graph, name='import_graph'),

    # AI Chat
    path('kg/ai-chat', views.ai_chat, name='ai_chat'),
    path('kg/clear-all', views.clear_all_data, name='clear_all_data'),
]