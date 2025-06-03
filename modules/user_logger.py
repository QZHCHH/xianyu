#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime
from bson.objectid import ObjectId
import json
import traceback

class UserLogger:
    """用户操作日志模块"""
    
    def __init__(self, db):
        """初始化日志模块
        
        Args:
            db: MongoDB数据库连接
        """
        self.db = db
        
    def log_action(self, username, action_type, target_type, target_id=None, details=None, status="success"):
        """记录用户操作
        
        Args:
            username (str): 用户名
            action_type (str): 操作类型，如'login', 'publish', 'delete'等
            target_type (str): 目标类型，如'product', 'order', 'account'等
            target_id (str, optional): 目标ID
            details (dict, optional): 操作详情
            status (str): 操作状态，'success'或'failed'
            
        Returns:
            str: 日志记录ID
        """
        try:
            log_entry = {
                'username': username,
                'action_type': action_type,
                'target_type': target_type,
                'target_id': target_id,
                'details': details,
                'status': status,
                'ip_address': self._get_request_ip(),
                'timestamp': datetime.now(),
                'user_agent': self._get_user_agent()
            }
            
            result = self.db.user_logs.insert_one(log_entry)
            return str(result.inserted_id)
        except Exception as e:
            # 记录日志失败不应影响主程序流程
            print(f"Failed to log user action: {str(e)}")
            traceback.print_exc()
            return None
    
    def get_user_logs(self, username=None, action_type=None, target_type=None, 
                     start_date=None, end_date=None, limit=100, skip=0):
        """获取用户操作日志
        
        Args:
            username (str, optional): 用户名过滤
            action_type (str, optional): 操作类型过滤
            target_type (str, optional): 目标类型过滤
            start_date (datetime, optional): 开始日期
            end_date (datetime, optional): 结束日期
            limit (int): 返回记录限制数量
            skip (int): 跳过记录数量
            
        Returns:
            list: 日志记录列表
        """
        try:
            # 构建查询条件
            query = {}
            
            if username:
                query['username'] = username
                
            if action_type:
                query['action_type'] = action_type
                
            if target_type:
                query['target_type'] = target_type
                
            # 处理日期范围
            if start_date or end_date:
                query['timestamp'] = {}
                
                if start_date:
                    query['timestamp']['$gte'] = start_date
                    
                if end_date:
                    query['timestamp']['$lte'] = end_date
            
            # 执行查询
            logs = list(self.db.user_logs.find(query).sort('timestamp', -1).skip(skip).limit(limit))
            
            # 处理ObjectId
            for log in logs:
                log['_id'] = str(log['_id'])
                if 'details' in log and isinstance(log['details'], dict):
                    # 处理details中可能存在的ObjectId
                    self._convert_objectid_to_str(log['details'])
            
            return logs
        except Exception as e:
            print(f"Failed to get user logs: {str(e)}")
            traceback.print_exc()
            return []
    
    def get_audit_logs(self, admin_username, target_username=None, action_type=None, 
                      start_date=None, end_date=None, limit=100, skip=0):
        """管理员获取审计日志
        
        Args:
            admin_username (str): 管理员用户名
            target_username (str, optional): 目标用户名过滤
            action_type (str, optional): 操作类型过滤
            start_date (datetime, optional): 开始日期
            end_date (datetime, optional): 结束日期
            limit (int): 返回记录限制数量
            skip (int): 跳过记录数量
            
        Returns:
            list: 日志记录列表
        """
        # 验证调用者是否为管理员
        admin = self.db.users.find_one({'username': admin_username})
        if not admin or admin.get('role') != 'admin':
            return {'success': False, 'message': '权限不足'}
        
        # 构建查询参数
        params = {}
        if target_username:
            params['username'] = target_username
        if action_type:
            params['action_type'] = action_type
            
        return self.get_user_logs(**params, start_date=start_date, 
                                end_date=end_date, limit=limit, skip=skip)
    
    def get_sensitive_action_logs(self, days=30):
        """获取敏感操作日志
        
        Args:
            days (int): 查询最近多少天的日志
            
        Returns:
            list: 敏感操作日志列表
        """
        sensitive_actions = [
            'login_failed', 'password_change', 'role_change', 
            'bulk_delete', 'account_add', 'account_delete'
        ]
        
        # 计算开始日期
        start_date = datetime.now() - datetime.timedelta(days=days)
        
        query = {
            'action_type': {'$in': sensitive_actions},
            'timestamp': {'$gte': start_date}
        }
        
        logs = list(self.db.user_logs.find(query).sort('timestamp', -1))
        
        # 处理ObjectId
        for log in logs:
            log['_id'] = str(log['_id'])
            if 'details' in log and isinstance(log['details'], dict):
                self._convert_objectid_to_str(log['details'])
                
        return logs
    
    def _get_request_ip(self):
        """获取请求IP地址
        
        Returns:
            str: IP地址
        """
        try:
            from flask import request
            if request:
                # 尝试获取X-Forwarded-For头
                if request.headers.get('X-Forwarded-For'):
                    return request.headers.get('X-Forwarded-For').split(',')[0].strip()
                # 否则获取远程地址
                return request.remote_addr
        except:
            pass
        return '0.0.0.0'
    
    def _get_user_agent(self):
        """获取用户代理信息
        
        Returns:
            str: 用户代理字符串
        """
        try:
            from flask import request
            if request:
                return request.user_agent.string
        except:
            pass
        return 'Unknown'
    
    def _convert_objectid_to_str(self, data):
        """递归转换字典中的ObjectId为字符串
        
        Args:
            data (dict): 要处理的字典
        """
        if not isinstance(data, dict):
            return
            
        for key, value in data.items():
            if isinstance(value, ObjectId):
                data[key] = str(value)
            elif isinstance(value, dict):
                self._convert_objectid_to_str(value)
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, ObjectId):
                        value[i] = str(item)
                    elif isinstance(item, dict):
                        self._convert_objectid_to_str(item) 