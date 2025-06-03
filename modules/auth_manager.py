#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from functools import wraps
from flask import jsonify, request
from flask_jwt_extended import get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
import re
import time
import hashlib
from datetime import datetime, timedelta

class AuthManager:
    """权限管理模块"""
    
    def __init__(self, db, user_logger):
        """初始化权限管理模块
        
        Args:
            db: MongoDB数据库连接
            user_logger: 用户日志记录模块实例
        """
        self.db = db
        self.user_logger = user_logger
        self.login_attempts = {}  # 用于跟踪登录尝试次数
        self.max_attempts = 5     # 最大尝试次数
        self.lockout_time = 15    # 锁定时间(分钟)
        
        # 权限定义
        self.permissions = {
            'admin': [
                'user_manage', 'role_manage', 'system_config',
                'log_view', 'all_accounts_view', 'all_products_view',
                'all_orders_view', 'all_data_export'
            ],
            'manager': [
                'product_manage', 'order_manage', 'account_manage',
                'marketing_analyze', 'data_export', 'customer_service'
            ],
            'operator': [
                'product_view', 'product_edit', 'order_process',
                'customer_reply', 'content_create'
            ],
            'viewer': [
                'product_view', 'order_view', 'stats_view'
            ]
        }
    
    def login(self, username, password, ip_address=None):
        """用户登录
        
        Args:
            username (str): 用户名
            password (str): 密码
            ip_address (str, optional): 登录IP地址
            
        Returns:
            dict: 登录结果
        """
        # 检查是否被锁定
        if self._is_locked_out(username, ip_address):
            self.user_logger.log_action(
                username, 'login_attempt', 'user', 
                details={'ip': ip_address, 'reason': 'locked_out'},
                status='failed'
            )
            return {
                'success': False, 
                'message': '账号已被锁定，请稍后再试',
                'locked': True,
                'remaining': self._get_lockout_remaining(username, ip_address)
            }
        
        # 查找用户
        user = self.db.users.find_one({'username': username})
        
        if not user or not check_password_hash(user['password'], password):
            # 记录失败尝试
            self._record_failed_attempt(username, ip_address)
            
            # 记录日志
            self.user_logger.log_action(
                username, 'login_failed', 'user',
                details={'ip': ip_address},
                status='failed'
            )
            
            # 检查是否达到最大尝试次数
            attempts = self._get_attempts_count(username, ip_address)
            if attempts >= self.max_attempts:
                return {
                    'success': False,
                    'message': '登录失败次数过多，账号已被锁定',
                    'locked': True,
                    'remaining': self.lockout_time * 60
                }
            else:
                return {
                    'success': False,
                    'message': '用户名或密码错误',
                    'attempts': attempts,
                    'max_attempts': self.max_attempts
                }
        
        # 登录成功，重置失败尝试
        self._reset_failed_attempts(username, ip_address)
        
        # 记录登录日志
        self.user_logger.log_action(
            username, 'login', 'user',
            details={'ip': ip_address},
            status='success'
        )
        
        # 更新最后登录时间
        self.db.users.update_one(
            {'_id': user['_id']},
            {'$set': {'last_login': datetime.now()}}
        )
        
        return {
            'success': True,
            'user': {
                'id': str(user['_id']),
                'username': user['username'],
                'role': user['role'],
                'permissions': self.get_permissions(user['role'])
            }
        }
    
    def register(self, username, password, email=None, role='user'):
        """注册新用户
        
        Args:
            username (str): 用户名
            password (str): 密码
            email (str, optional): 邮箱
            role (str): 角色，默认为'user'
            
        Returns:
            dict: 注册结果
        """
        # 检查用户名是否已存在
        if self.db.users.find_one({'username': username}):
            return {
                'success': False,
                'message': '用户名已存在'
            }
        
        # 检查邮箱是否已存在
        if email and self.db.users.find_one({'email': email}):
            return {
                'success': False,
                'message': '邮箱已被注册'
            }
        
        # 验证密码强度
        if not self._validate_password(password):
            return {
                'success': False,
                'message': '密码必须包含至少8个字符，包括数字、字母和特殊字符'
            }
        
        # 创建用户
        user = {
            'username': username,
            'password': generate_password_hash(password),
            'role': role,
            'created_at': datetime.now(),
            'status': 'active'
        }
        
        if email:
            user['email'] = email
        
        # 保存用户
        result = self.db.users.insert_one(user)
        
        # 记录日志
        self.user_logger.log_action(
            username, 'register', 'user',
            target_id=str(result.inserted_id),
            status='success'
        )
        
        return {
            'success': True,
            'message': '注册成功',
            'user_id': str(result.inserted_id)
        }
    
    def change_password(self, username, old_password, new_password):
        """修改密码
        
        Args:
            username (str): 用户名
            old_password (str): 旧密码
            new_password (str): 新密码
            
        Returns:
            dict: 操作结果
        """
        # 查找用户
        user = self.db.users.find_one({'username': username})
        
        if not user or not check_password_hash(user['password'], old_password):
            # 记录日志
            self.user_logger.log_action(
                username, 'password_change', 'user',
                status='failed'
            )
            return {
                'success': False,
                'message': '原密码错误'
            }
        
        # 验证新密码强度
        if not self._validate_password(new_password):
            return {
                'success': False,
                'message': '新密码必须包含至少8个字符，包括数字、字母和特殊字符'
            }
        
        # 更新密码
        self.db.users.update_one(
            {'_id': user['_id']},
            {'$set': {
                'password': generate_password_hash(new_password),
                'updated_at': datetime.now()
            }}
        )
        
        # 记录日志
        self.user_logger.log_action(
            username, 'password_change', 'user',
            status='success'
        )
        
        return {
            'success': True,
            'message': '密码修改成功'
        }
    
    def update_user_role(self, admin_username, target_username, new_role):
        """更新用户角色
        
        Args:
            admin_username (str): 管理员用户名
            target_username (str): 目标用户名
            new_role (str): 新角色
            
        Returns:
            dict: 操作结果
        """
        # 验证管理员权限
        admin = self.db.users.find_one({'username': admin_username})
        if not admin or admin['role'] != 'admin':
            # 记录日志
            self.user_logger.log_action(
                admin_username, 'role_change', 'user',
                target_id=target_username,
                details={'new_role': new_role},
                status='failed'
            )
            return {
                'success': False,
                'message': '权限不足'
            }
        
        # 查找目标用户
        target_user = self.db.users.find_one({'username': target_username})
        if not target_user:
            return {
                'success': False,
                'message': '用户不存在'
            }
        
        # 检查角色是否有效
        if new_role not in self.permissions:
            return {
                'success': False,
                'message': '无效的角色'
            }
        
        # 更新角色
        self.db.users.update_one(
            {'_id': target_user['_id']},
            {'$set': {
                'role': new_role,
                'updated_at': datetime.now()
            }}
        )
        
        # 记录日志
        self.user_logger.log_action(
            admin_username, 'role_change', 'user',
            target_id=target_username,
            details={'old_role': target_user['role'], 'new_role': new_role},
            status='success'
        )
        
        return {
            'success': True,
            'message': '用户角色更新成功'
        }
    
    def has_permission(self, username, permission):
        """检查用户是否拥有特定权限
        
        Args:
            username (str): 用户名
            permission (str): 权限名称
            
        Returns:
            bool: 是否拥有权限
        """
        user = self.db.users.find_one({'username': username})
        if not user:
            return False
        
        user_role = user['role']
        user_permissions = self.get_permissions(user_role)
        
        return permission in user_permissions
    
    def get_permissions(self, role):
        """获取角色的权限列表
        
        Args:
            role (str): 角色名称
            
        Returns:
            list: 权限列表
        """
        if role in self.permissions:
            return self.permissions[role]
        return []
    
    def require_permission(self, permission):
        """权限检查装饰器
        
        Args:
            permission (str): 需要的权限
            
        Returns:
            function: 装饰器函数
        """
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                username = get_jwt_identity()
                if not self.has_permission(username, permission):
                    return jsonify({
                        'success': False,
                        'message': '权限不足'
                    }), 403
                return f(*args, **kwargs)
            return decorated_function
        return decorator
    
    def _validate_password(self, password):
        """验证密码强度
        
        Args:
            password (str): 密码
            
        Returns:
            bool: 密码是否符合要求
        """
        # 至少8个字符，包含数字、字母和特殊字符
        if len(password) < 8:
            return False
        
        # 检查是否包含数字
        if not re.search(r'\d', password):
            return False
        
        # 检查是否包含字母
        if not re.search(r'[a-zA-Z]', password):
            return False
        
        # 检查是否包含特殊字符
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False
        
        return True
    
    def _get_login_key(self, username, ip_address):
        """获取登录尝试的键
        
        Args:
            username (str): 用户名
            ip_address (str): IP地址
            
        Returns:
            str: 登录键
        """
        if ip_address:
            return f"{username}:{ip_address}"
        return username
    
    def _record_failed_attempt(self, username, ip_address):
        """记录失败的登录尝试
        
        Args:
            username (str): 用户名
            ip_address (str): IP地址
        """
        key = self._get_login_key(username, ip_address)
        
        if key not in self.login_attempts:
            self.login_attempts[key] = {
                'count': 1,
                'first_attempt': time.time(),
                'last_attempt': time.time()
            }
        else:
            self.login_attempts[key]['count'] += 1
            self.login_attempts[key]['last_attempt'] = time.time()
    
    def _reset_failed_attempts(self, username, ip_address):
        """重置失败的登录尝试
        
        Args:
            username (str): 用户名
            ip_address (str): IP地址
        """
        key = self._get_login_key(username, ip_address)
        if key in self.login_attempts:
            del self.login_attempts[key]
    
    def _get_attempts_count(self, username, ip_address):
        """获取失败尝试次数
        
        Args:
            username (str): 用户名
            ip_address (str): IP地址
            
        Returns:
            int: 失败尝试次数
        """
        key = self._get_login_key(username, ip_address)
        if key in self.login_attempts:
            return self.login_attempts[key]['count']
        return 0
    
    def _is_locked_out(self, username, ip_address):
        """检查是否被锁定
        
        Args:
            username (str): 用户名
            ip_address (str): IP地址
            
        Returns:
            bool: 是否被锁定
        """
        key = self._get_login_key(username, ip_address)
        
        if key in self.login_attempts:
            attempts = self.login_attempts[key]
            if attempts['count'] >= self.max_attempts:
                # 检查锁定时间是否已过
                lockout_seconds = self.lockout_time * 60
                elapsed = time.time() - attempts['last_attempt']
                
                if elapsed < lockout_seconds:
                    return True
                else:
                    # 锁定时间已过，重置尝试次数
                    self._reset_failed_attempts(username, ip_address)
                    return False
        
        return False
    
    def _get_lockout_remaining(self, username, ip_address):
        """获取剩余锁定时间(秒)
        
        Args:
            username (str): 用户名
            ip_address (str): IP地址
            
        Returns:
            int: 剩余锁定时间(秒)
        """
        key = self._get_login_key(username, ip_address)
        
        if key in self.login_attempts:
            attempts = self.login_attempts[key]
            if attempts['count'] >= self.max_attempts:
                lockout_seconds = self.lockout_time * 60
                elapsed = time.time() - attempts['last_attempt']
                
                if elapsed < lockout_seconds:
                    return int(lockout_seconds - elapsed)
        
        return 0 