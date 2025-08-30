# -*- coding: utf-8 -*-
from django.urls import path
from . import views
from . import user_views

urlpatterns = [
    # Graph data (D3-friendly)
    path('data', views.get_graph_data, name='get_graph_data'),

    # Backward compatible legacy endpoint
    path('entity', views.add_entity, name='add_entity'),

    # Entity CRUD
    path('entities', views.list_or_create_entities, name='list_or_create_entities'),
    path('entities/<str:entity_id>', views.entity_detail, name='entity_detail'),

    # Relationship CRUD
    path('relationships', views.list_or_create_relationships, name='list_or_create_relationships'),
    path('relationships/<int:rel_id>', views.relationship_detail, name='relationship_detail'),

    # Import/Export
    path('export', views.export_graph, name='export_graph'),
    path('import', views.import_graph, name='import_graph'),

    # AI Chat
    path('ai-chat', views.ai_chat, name='ai_chat'),
    path('clear-all', views.clear_all_data, name='clear_all_data'),
    
    # Data Mode
    path('save-data', views.save_data_mode, name='save_data_mode'),
    
    # Statistics (commented out - function not implemented)
    # path('kg/stats', views.get_stats, name='get_stats'),
    
    # 用户管理API
    path('users/', user_views.user_list, name='user-list'),
    path('users/<int:user_id>/', user_views.user_detail, name='user-detail'),
    path('users/login/', user_views.user_login, name='user-login'),
    path('users/logout/', user_views.user_logout, name='user-logout'),
    path('users/stats/', user_views.user_stats, name='user-stats'),
    path('users/login-legacy/', user_views.login_view, name='login-legacy'),
]