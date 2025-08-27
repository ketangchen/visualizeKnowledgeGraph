from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),  # Django管理后台
    path('', TemplateView.as_view(template_name='index.html')),  # 前端入口页面
    path('api/', include('apps.kg_visualize.urls')),  # 知识图谱API路由
]