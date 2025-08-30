# -*- coding: utf-8 -*-
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import User, UserLoginLog, UserPermission

class UserSerializer(serializers.ModelSerializer):
    """
    用户序列化器
    """
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    last_login_formatted = serializers.SerializerMethodField()
    date_joined_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'role', 'role_display', 'status', 'status_display',
            'phone', 'department', 'position', 'avatar',
            'last_login', 'last_login_formatted', 'last_login_ip',
            'login_count', 'date_joined', 'date_joined_formatted',
            'created_by', 'created_by_username', 'is_active'
        ]
        read_only_fields = ['id', 'last_login', 'last_login_ip', 'login_count', 'date_joined', 'created_by']
    
    def get_last_login_formatted(self, obj):
        if obj.last_login:
            return obj.last_login.strftime('%Y-%m-%d %H:%M:%S')
        return None
    
    def get_date_joined_formatted(self, obj):
        return obj.date_joined.strftime('%Y-%m-%d %H:%M:%S')


class UserCreateSerializer(serializers.ModelSerializer):
    """
    创建用户序列化器
    """
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'role', 'status',
            'phone', 'department', 'position'
        ]
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("密码确认不匹配")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        
        # 创建用户权限配置
        UserPermission.objects.create(user=user)
        
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    更新用户序列化器
    """
    class Meta:
        model = User
        fields = [
            'email', 'first_name', 'last_name', 'role', 'status',
            'phone', 'department', 'position', 'avatar', 'is_active'
        ]


class UserPasswordChangeSerializer(serializers.Serializer):
    """
    修改密码序列化器
    """
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(required=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("新密码确认不匹配")
        return attrs
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("原密码不正确")
        return value


class UserLoginSerializer(serializers.Serializer):
    """
    用户登录序列化器
    """
    username = serializers.CharField()
    password = serializers.CharField()
    
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        
        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError("用户名或密码错误")
            if not user.is_active:
                raise serializers.ValidationError("用户账户已被禁用")
            attrs['user'] = user
        else:
            raise serializers.ValidationError("用户名和密码不能为空")
        
        return attrs


class UserPermissionSerializer(serializers.ModelSerializer):
    """
    用户权限序列化器
    """
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = UserPermission
        fields = [
            'id', 'user', 'username', 'can_view_kg', 'can_edit_kg',
            'can_delete_kg', 'can_manage_users', 'can_view_logs',
            'can_export_data'
        ]
        read_only_fields = ['id', 'user']


class UserLoginLogSerializer(serializers.ModelSerializer):
    """
    登录日志序列化器
    """
    username = serializers.CharField(source='user.username', read_only=True)
    login_time_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = UserLoginLog
        fields = [
            'id', 'user', 'username', 'login_time', 'login_time_formatted',
            'login_ip', 'user_agent', 'success'
        ]
        read_only_fields = ['id', 'user', 'login_time', 'login_ip', 'user_agent', 'success']
    
    def get_login_time_formatted(self, obj):
        return obj.login_time.strftime('%Y-%m-%d %H:%M:%S')
