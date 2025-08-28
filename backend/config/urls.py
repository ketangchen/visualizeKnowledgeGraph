from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.shortcuts import redirect

def redirect_to_kg(request):
    """重定向到完整的知识图谱页面"""
    return redirect('/static/KG.html')

urlpatterns = [
    path('admin/', admin.site.urls),  # Django管理后台
    path('', redirect_to_kg),  # 首页重定向到KG.html
    path('api/', include('backend.apps.kg_visualize.urls')),  # 知识图谱API路径
]