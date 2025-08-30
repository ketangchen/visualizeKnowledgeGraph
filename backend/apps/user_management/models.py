# -*- coding: utf-8 -*-
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

class User(AbstractUser):
    """
    扩展的用户模型
    """
    ROLE_CHOICES = [
        ('admin', '管理员'),
        ('user', '普通用户'),
        ('viewer', '只读用户'),
    ]
    
    STATUS_CHOICES = [
        ('active', '激活'),
        ('inactive', '禁用'),
        ('pending', '待激活'),
    ]
    
    # 扩展字段
    role = models.CharField(
        max_length=20, 
        choices=ROLE_CHOICES, 
        default='user',
        verbose_name="用户角色"
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='active',
        verbose_name="用户状态"
    )
    phone = models.CharField(
        max_length=20, 
        blank=True, 
        null=True,
        verbose_name="手机号"
    )
    department = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        verbose_name="部门"
    )
    position = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        verbose_name="职位"
    )
    avatar = models.CharField(
        max_length=255, 
        blank=True, 
        null=True,
        verbose_name="头像URL"
    )
    last_login_ip = models.GenericIPAddressField(
        blank=True, 
        null=True,
        verbose_name="最后登录IP"
    )
    login_count = models.PositiveIntegerField(
        default=0,
        verbose_name="登录次数"
    )
    created_by = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        blank=True, 
        null=True,
        verbose_name="创建者"
    )
    
    class Meta:
        verbose_name = "用户"
        verbose_name_plural = "用户"
        ordering = ['-date_joined']
        app_label = "user_management"
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    @property
    def is_admin(self):
        return self.role == 'admin'
    
    @property
    def is_viewer(self):
        return self.role == 'viewer'
    
    def can_edit(self):
        return self.role in ['admin', 'user']
    
    def can_delete(self):
        return self.role == 'admin'


class UserLoginLog(models.Model):
    """
    用户登录日志
    """
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        verbose_name="用户"
    )
    login_time = models.DateTimeField(
        auto_now_add=True,
        verbose_name="登录时间"
    )
    login_ip = models.GenericIPAddressField(
        verbose_name="登录IP"
    )
    user_agent = models.TextField(
        blank=True,
        verbose_name="用户代理"
    )
    success = models.BooleanField(
        default=True,
        verbose_name="登录成功"
    )
    
    class Meta:
        verbose_name = "登录日志"
        verbose_name_plural = "登录日志"
        ordering = ['-login_time']
        app_label = "user_management"
    
    def __str__(self):
        return f"{self.user.username} - {self.login_time}"


class UserPermission(models.Model):
    """
    用户权限配置
    """
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE,
        verbose_name="用户"
    )
    can_view_kg = models.BooleanField(
        default=True,
        verbose_name="查看知识图谱"
    )
    can_edit_kg = models.BooleanField(
        default=False,
        verbose_name="编辑知识图谱"
    )
    can_delete_kg = models.BooleanField(
        default=False,
        verbose_name="删除知识图谱"
    )
    can_manage_users = models.BooleanField(
        default=False,
        verbose_name="管理用户"
    )
    can_view_logs = models.BooleanField(
        default=False,
        verbose_name="查看日志"
    )
    can_export_data = models.BooleanField(
        default=False,
        verbose_name="导出数据"
    )
    
    class Meta:
        verbose_name = "用户权限"
        verbose_name_plural = "用户权限"
        app_label = "user_management"
    
    def __str__(self):
        return f"{self.user.username} 的权限配置"
