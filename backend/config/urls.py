from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic import TemplateView
from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
import os

def redirect_to_login(request):
    """重定向到首页"""
    return redirect('/frontend/index.html')

def serve_frontend_file(request, filepath):
    """通用前端文件服务函数"""
    # 检查文件是否存在
    if filepath.startswith('static/'):
        # 静态文件
        full_path = os.path.join(settings.BASE_DIR, 'frontend', filepath)
        if os.path.exists(full_path):
            return serve(request, filepath, document_root=os.path.join(settings.BASE_DIR, 'frontend'))
    else:
        # 前端页面文件
        full_path = os.path.join(settings.BASE_DIR, 'frontend', filepath)
        if os.path.exists(full_path):
            return serve(request, filepath, document_root=os.path.join(settings.BASE_DIR, 'frontend'))
    
    # 文件不存在，重定向到登录页
    return redirect('/frontend/login.html')

urlpatterns = [
    path('admin/', admin.site.urls),  # Django管理后台
    path('', redirect_to_login),  # 首页重定向到登录页面
    path('api/kg/', include('backend.apps.kg_visualize.urls')),  # 知识图谱API路径
    path('api/users/', include('backend.apps.user_management.urls')),  # 用户管理API路径
    
    # 通用前端文件路由
    re_path(r'^frontend/(?P<filepath>.*)$', serve_frontend_file, name='frontend_file'),
]

# 添加静态文件服务
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)