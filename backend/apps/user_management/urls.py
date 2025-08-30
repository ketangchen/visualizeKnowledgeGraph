# -*- coding: utf-8 -*-
from django.urls import path
from . import views

app_name = 'user_management'

urlpatterns = [
    # 用户管理
    path('users/', views.user_list, name='user-list'),
    path('users/<int:user_id>/', views.user_detail, name='user-detail'),
    
    # 认证相关
    path('login/', views.user_login, name='user-login'),
    path('logout/', views.user_logout, name='user-logout'),
    
    # 统计信息
    path('stats/', views.user_stats, name='user-stats'),
    
    # 兼容原有登录接口
    path('login-legacy/', views.login_view, name='login-legacy'),
]
