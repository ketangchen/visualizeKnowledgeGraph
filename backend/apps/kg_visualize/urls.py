# -*- coding: utf-8 -*-
from django.urls import path
from . import views

urlpatterns = [
    path('kg/data', views.get_graph_data, name='get_graph_data'),  # 获取图谱数据
    path('kg/entity', views.add_entity, name='add_entity'),        # 新增实体
    # 可补充：删除实体、修改关系等接口
]