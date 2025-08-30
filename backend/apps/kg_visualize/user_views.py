# -*- coding: utf-8 -*-
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import make_password
from django.db.models import Q
import json

@csrf_exempt
def user_list(request):
    """
    用户列表API
    """
    if request.method == 'GET':
        try:
            users = User.objects.all()
            user_list = []
            
            for user in users:
                user_list.append({
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'is_active': user.is_active,
                    'is_staff': user.is_staff,
                    'is_superuser': user.is_superuser,
                    'date_joined': user.date_joined.strftime('%Y-%m-%d %H:%M:%S'),
                    'last_login': user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else None,
                })
            
            return JsonResponse({
                'ret': 0,
                'msg': '获取用户列表成功',
                'data': user_list
            })
        except Exception as e:
            return JsonResponse({
                'ret': 1,
                'msg': f'获取用户列表失败: {str(e)}'
            })
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            email = data.get('email')
            password = data.get('password')
            first_name = data.get('first_name', '')
            last_name = data.get('last_name', '')
            is_staff = data.get('is_staff', False)
            is_active = data.get('is_active', True)
            
            if not username or not email or not password:
                return JsonResponse({
                    'ret': 1,
                    'msg': '用户名、邮箱和密码不能为空'
                })
            
            # 检查用户名是否已存在
            if User.objects.filter(username=username).exists():
                return JsonResponse({
                    'ret': 1,
                    'msg': '用户名已存在'
                })
            
            # 检查邮箱是否已存在
            if User.objects.filter(email=email).exists():
                return JsonResponse({
                    'ret': 1,
                    'msg': '邮箱已存在'
                })
            
            # 创建用户
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                is_staff=is_staff,
                is_active=is_active
            )
            
            return JsonResponse({
                'ret': 0,
                'msg': '用户创建成功',
                'data': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email
                }
            })
        except Exception as e:
            return JsonResponse({
                'ret': 1,
                'msg': f'创建用户失败: {str(e)}'
            })


@csrf_exempt
def user_detail(request, user_id):
    """
    用户详情、更新、删除API
    """
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({
            'ret': 1,
            'msg': '用户不存在'
        })
    
    if request.method == 'GET':
        return JsonResponse({
            'ret': 0,
            'msg': '获取用户信息成功',
            'data': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'is_active': user.is_active,
                'is_staff': user.is_staff,
                'is_superuser': user.is_superuser,
                'date_joined': user.date_joined.strftime('%Y-%m-%d %H:%M:%S'),
                'last_login': user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else None,
            }
        })
    
    elif request.method == 'PUT':
        try:
            data = json.loads(request.body)
            
            # 检查邮箱是否被其他用户使用
            if 'email' in data and data['email'] != user.email:
                if User.objects.filter(email=data['email']).exclude(id=user.id).exists():
                    return JsonResponse({
                        'ret': 1,
                        'msg': '邮箱已被其他用户使用'
                    })
            
            # 更新用户信息
            if 'email' in data:
                user.email = data['email']
            if 'first_name' in data:
                user.first_name = data['first_name']
            if 'last_name' in data:
                user.last_name = data['last_name']
            if 'is_active' in data:
                user.is_active = data['is_active']
            if 'is_staff' in data:
                user.is_staff = data['is_staff']
            
            user.save()
            
            return JsonResponse({
                'ret': 0,
                'msg': '用户信息更新成功'
            })
        except Exception as e:
            return JsonResponse({
                'ret': 1,
                'msg': f'更新用户信息失败: {str(e)}'
            })
    
    elif request.method == 'DELETE':
        try:
            # 不能删除超级用户
            if user.is_superuser:
                return JsonResponse({
                    'ret': 1,
                    'msg': '不能删除超级用户'
                })
            
            # 不能删除自己
            if request.user.is_authenticated and request.user.id == user.id:
                return JsonResponse({
                    'ret': 1,
                    'msg': '不能删除自己的账户'
                })
            
            user.delete()
            return JsonResponse({
                'ret': 0,
                'msg': '用户删除成功'
            })
        except Exception as e:
            return JsonResponse({
                'ret': 1,
                'msg': f'删除用户失败: {str(e)}'
            })


@csrf_exempt
def user_login(request):
    """
    用户登录API
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')
            
            if not username or not password:
                return JsonResponse({
                    'ret': 1,
                    'msg': '用户名和密码不能为空'
                })
            
            user = authenticate(username=username, password=password)
            
            if user is not None and user.is_active:
                login(request, user)
                return JsonResponse({
                    'ret': 0,
                    'msg': '登录成功',
                    'data': {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'is_staff': user.is_staff,
                        'is_superuser': user.is_superuser
                    }
                })
            else:
                return JsonResponse({
                    'ret': 1,
                    'msg': '用户名或密码错误'
                })
        except Exception as e:
            return JsonResponse({
                'ret': 1,
                'msg': f'登录失败: {str(e)}'
            })


@csrf_exempt
def user_logout(request):
    """
    用户登出API
    """
    if request.method == 'POST':
        logout(request)
        return JsonResponse({
            'ret': 0,
            'msg': '登出成功'
        })


@csrf_exempt
def user_stats(request):
    """
    用户统计信息API
    """
    if request.method == 'GET':
        try:
            total_users = User.objects.count()
            active_users = User.objects.filter(is_active=True).count()
            inactive_users = User.objects.filter(is_active=False).count()
            staff_users = User.objects.filter(is_staff=True).count()
            superusers = User.objects.filter(is_superuser=True).count()
            
            return JsonResponse({
                'ret': 0,
                'msg': '获取统计信息成功',
                'data': {
                    'total_users': total_users,
                    'active_users': active_users,
                    'inactive_users': inactive_users,
                    'staff_users': staff_users,
                    'superusers': superusers
                }
            })
        except Exception as e:
            return JsonResponse({
                'ret': 1,
                'msg': f'获取统计信息失败: {str(e)}'
            })


# 兼容原有的登录接口
@csrf_exempt
def login_view(request):
    """
    兼容原有的登录接口
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')
            
            if username == 'admin' and password == 'admin':
                return JsonResponse({
                    'ret': 0,
                    'msg': '登录成功',
                    'data': {
                        'username': 'admin',
                        'role': 'admin'
                    }
                })
            else:
                return JsonResponse({
                    'ret': 1,
                    'msg': '用户名或密码错误'
                })
        except json.JSONDecodeError:
            return JsonResponse({
                'ret': 1,
                'msg': '请求格式错误'
            })
    
    return JsonResponse({
        'ret': 1,
        'msg': '不支持的请求方法'
    })
