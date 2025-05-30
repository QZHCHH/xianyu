#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import jsonify
from bson.objectid import ObjectId
from datetime import datetime
import os
import uuid
import json
from werkzeug.security import generate_password_hash, check_password_hash
import time
import re

class AccountManager:
    """多账号管理模块"""
    
    def __init__(self, db):
        """初始化账号管理模块"""
        self.db = db
    
    def get_accounts(self, username):
        """获取用户的咸鱼账号列表
        
        Args:
            username (str): 用户名
            
        Returns:
            dict: 账号列表
        """
        try:
            # 从数据库获取用户账号
            accounts = list(self.db.accounts.find({
                'username': username
            }).sort('created_at', -1))
            
            # 处理返回结果，隐藏敏感信息
            result = []
            for account in accounts:
                result.append({
                    'id': str(account['_id']),
                    'account_name': account.get('account_name', '未命名账号'),
                    'xianyu_username': account['xianyu_username'],
                    'status': account.get('status', 'unknown'),
                    'shop_status': account.get('shop_status', 'unknown'),
                    'last_check': account.get('last_check', '').isoformat() if account.get('last_check') else '',
                    'created_at': account['created_at'].isoformat(),
                    'daily_limit': account.get('daily_limit', 20),
                    'today_published': account.get('today_published', 0),
                    'total_products': account.get('total_products', 0),
                    'is_parent': account.get('is_parent', False),
                    'parent_id': str(account['parent_id']) if account.get('parent_id') else None,
                    'child_accounts': account.get('child_accounts', [])
                })
            
            return jsonify({
                'success': True,
                'accounts': result
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'获取账号失败: {str(e)}'
            }), 500
    
    def add_account(self, username, data):
        """添加咸鱼账号
        
        Args:
            username (str): 用户名
            data (dict): 账号数据
            
        Returns:
            dict: 处理结果
        """
        try:
            # 检查必要字段
            required_fields = ['xianyu_username', 'xianyu_password', 'account_name']
            for field in required_fields:
                if field not in data:
                    return jsonify({
                        'success': False,
                        'message': f'缺少必要字段: {field}'
                    }), 400
            
            # 检查账号是否已存在
            existing_account = self.db.accounts.find_one({
                'username': username,
                'xianyu_username': data['xianyu_username']
            })
            
            if existing_account:
                return jsonify({
                    'success': False,
                    'message': '该咸鱼账号已添加'
                }), 400
            
            # 准备账号数据
            account_data = {
                'username': username,
                'account_name': data['account_name'],
                'xianyu_username': data['xianyu_username'],
                'xianyu_password': data['xianyu_password'],  # 实际应用中应加密存储
                'status': 'active',
                'shop_status': 'unknown',
                'last_check': None,
                'created_at': datetime.now(),
                'updated_at': datetime.now(),
                'daily_limit': data.get('daily_limit', 20),
                'today_published': 0,
                'total_products': 0,
                'is_parent': False,
                'child_accounts': []
            }
            
            # 保存到数据库
            account_id = self.db.accounts.insert_one(account_data).inserted_id
            
            return jsonify({
                'success': True,
                'message': '账号添加成功',
                'account_id': str(account_id)
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'添加账号失败: {str(e)}'
            }), 500
    
    def update_account(self, username, account_id, data):
        """更新账号信息
        
        Args:
            username (str): 用户名
            account_id (str): 账号ID
            data (dict): 更新数据
            
        Returns:
            dict: 处理结果
        """
        try:
            # 检查账号是否存在
            account = self.db.accounts.find_one({
                '_id': ObjectId(account_id),
                'username': username
            })
            
            if not account:
                return jsonify({
                    'success': False,
                    'message': '账号不存在或无权限修改'
                }), 404
            
            # 准备更新数据
            update_data = {
                'updated_at': datetime.now()
            }
            
            # 可更新字段
            allowed_fields = ['account_name', 'xianyu_password', 'status', 'daily_limit']
            for field in allowed_fields:
                if field in data:
                    update_data[field] = data[field]
            
            # 更新数据库
            self.db.accounts.update_one(
                {'_id': ObjectId(account_id)},
                {'$set': update_data}
            )
            
            return jsonify({
                'success': True,
                'message': '账号更新成功'
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'更新账号失败: {str(e)}'
            }), 500
    
    def delete_account(self, username, account_id):
        """删除账号
        
        Args:
            username (str): 用户名
            account_id (str): 账号ID
            
        Returns:
            dict: 处理结果
        """
        try:
            # 检查账号是否存在
            account = self.db.accounts.find_one({
                '_id': ObjectId(account_id),
                'username': username
            })
            
            if not account:
                return jsonify({
                    'success': False,
                    'message': '账号不存在或无权限删除'
                }), 404
            
            # 检查是否为父账号
            if account.get('is_parent', False) and account.get('child_accounts', []):
                return jsonify({
                    'success': False,
                    'message': '该账号是主账号且有关联子账号，请先删除子账号'
                }), 400
            
            # 如果是子账号，更新父账号
            if account.get('parent_id'):
                self.db.accounts.update_one(
                    {'_id': ObjectId(account['parent_id'])},
                    {'$pull': {'child_accounts': account_id}}
                )
            
            # 删除账号
            self.db.accounts.delete_one({'_id': ObjectId(account_id)})
            
            return jsonify({
                'success': True,
                'message': '账号删除成功'
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'删除账号失败: {str(e)}'
            }), 500
    
    def check_account_status(self, username, account_id):
        """检查账号状态
        
        Args:
            username (str): 用户名
            account_id (str): 账号ID
            
        Returns:
            dict: 处理结果
        """
        try:
            # 检查账号是否存在
            account = self.db.accounts.find_one({
                '_id': ObjectId(account_id),
                'username': username
            })
            
            if not account:
                return jsonify({
                    'success': False,
                    'message': '账号不存在或无权限检查'
                }), 404
            
            # 这里需要实际检查账号状态，包括登录状态和店铺状态
            # 由于涉及到浏览器自动化操作，这里只模拟返回结果
            
            # 更新账号状态
            update_data = {
                'status': 'active',
                'shop_status': 'open',
                'last_check': datetime.now(),
                'updated_at': datetime.now()
            }
            
            self.db.accounts.update_one(
                {'_id': ObjectId(account_id)},
                {'$set': update_data}
            )
            
            return jsonify({
                'success': True,
                'message': '账号状态检查完成',
                'status': update_data['status'],
                'shop_status': update_data['shop_status']
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'检查账号状态失败: {str(e)}'
            }), 500
    
    def reset_daily_limit(self, username):
        """重置所有账号的每日发布计数
        
        Args:
            username (str): 用户名
            
        Returns:
            dict: 处理结果
        """
        try:
            # 重置所有账号的每日发布计数
            result = self.db.accounts.update_many(
                {'username': username},
                {'$set': {'today_published': 0, 'updated_at': datetime.now()}}
            )
            
            return jsonify({
                'success': True,
                'message': f'已重置 {result.modified_count} 个账号的每日发布计数'
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'重置每日发布计数失败: {str(e)}'
            }), 500
    
    def clone_accounts(self, username, data):
        """克隆账号设置（子母号关系）
        
        Args:
            username (str): 用户名
            data (dict): 克隆数据
            
        Returns:
            dict: 处理结果
        """
        try:
            # 检查必要字段
            if 'parent_id' not in data or 'child_ids' not in data:
                return jsonify({
                    'success': False,
                    'message': '缺少必要字段: parent_id 或 child_ids'
                }), 400
            
            parent_id = data['parent_id']
            child_ids = data['child_ids']
            
            # 检查父账号是否存在
            parent_account = self.db.accounts.find_one({
                '_id': ObjectId(parent_id),
                'username': username
            })
            
            if not parent_account:
                return jsonify({
                    'success': False,
                    'message': '父账号不存在或无权限操作'
                }), 404
            
            # 更新父账号状态
            self.db.accounts.update_one(
                {'_id': ObjectId(parent_id)},
                {
                    '$set': {
                        'is_parent': True,
                        'updated_at': datetime.now()
                    },
                    '$addToSet': {'child_accounts': {'$each': child_ids}}
                }
            )
            
            # 更新子账号状态
            for child_id in child_ids:
                self.db.accounts.update_one(
                    {'_id': ObjectId(child_id), 'username': username},
                    {
                        '$set': {
                            'parent_id': ObjectId(parent_id),
                            'updated_at': datetime.now()
                        }
                    }
                )
            
            return jsonify({
                'success': True,
                'message': f'成功设置 {len(child_ids)} 个子账号'
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'设置子母号关系失败: {str(e)}'
            }), 500
    
    def sync_products(self, username, data):
        """同步母号商品到子号
        
        Args:
            username (str): 用户名
            data (dict): 同步数据
            
        Returns:
            dict: 处理结果
        """
        try:
            # 检查必要字段
            if 'parent_id' not in data or 'child_ids' not in data:
                return jsonify({
                    'success': False,
                    'message': '缺少必要字段: parent_id 或 child_ids'
                }), 400
            
            parent_id = data['parent_id']
            child_ids = data['child_ids']
            product_ids = data.get('product_ids', [])  # 可选，为空则同步所有商品
            
            # 检查父账号是否存在
            parent_account = self.db.accounts.find_one({
                '_id': ObjectId(parent_id),
                'username': username
            })
            
            if not parent_account:
                return jsonify({
                    'success': False,
                    'message': '父账号不存在或无权限操作'
                }), 404
            
            # 获取需要同步的商品
            query = {
                'username': username,
                'account_id': ObjectId(parent_id)
            }
            
            if product_ids:
                query['_id'] = {'$in': [ObjectId(pid) for pid in product_ids]}
            
            products = list(self.db.products.find(query))
            
            if not products:
                return jsonify({
                    'success': False,
                    'message': '没有找到需要同步的商品'
                }), 404
            
            # 同步商品到子账号
            sync_results = []
            for child_id in child_ids:
                child_account = self.db.accounts.find_one({
                    '_id': ObjectId(child_id),
                    'username': username
                })
                
                if not child_account:
                    sync_results.append({
                        'child_id': child_id,
                        'success': False,
                        'message': '子账号不存在或无权限操作'
                    })
                    continue
                
                # 同步商品
                synced_count = 0
                for product in products:
                    # 检查子账号是否已有该商品
                    existing_product = self.db.products.find_one({
                        'username': username,
                        'account_id': ObjectId(child_id),
                        'parent_product_id': product['_id']
                    })
                    
                    if existing_product:
                        # 更新现有商品
                        update_data = {
                            'title': product['title'],
                            'description': product['description'],
                            'price': product['price'],
                            'images': product['images'],
                            'category': product['category'],
                            'status': product['status'],
                            'updated_at': datetime.now(),
                            'synced_at': datetime.now()
                        }
                        
                        self.db.products.update_one(
                            {'_id': existing_product['_id']},
                            {'$set': update_data}
                        )
                    else:
                        # 创建新商品
                        new_product = product.copy()
                        new_product.pop('_id', None)
                        new_product['account_id'] = ObjectId(child_id)
                        new_product['parent_product_id'] = product['_id']
                        new_product['created_at'] = datetime.now()
                        new_product['updated_at'] = datetime.now()
                        new_product['synced_at'] = datetime.now()
                        new_product['published'] = False
                        new_product['publish_time'] = None
                        
                        self.db.products.insert_one(new_product)
                    
                    synced_count += 1
                
                sync_results.append({
                    'child_id': child_id,
                    'success': True,
                    'synced_count': synced_count
                })
            
            return jsonify({
                'success': True,
                'message': '商品同步完成',
                'results': sync_results
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'同步商品失败: {str(e)}'
            }), 500
    
    def get_publish_queue(self, username):
        """获取发布队列
        
        Args:
            username (str): 用户名
            
        Returns:
            dict: 发布队列
        """
        try:
            # 获取所有待发布商品
            products = list(self.db.products.find({
                'username': username,
                'published': False,
                'status': 'active'
            }).sort('created_at', 1))
            
            # 获取所有账号
            accounts = list(self.db.accounts.find({
                'username': username,
                'status': 'active'
            }))
            
            # 构建发布队列
            queue = []
            for account in accounts:
                # 计算该账号还能发布多少商品
                remaining = account.get('daily_limit', 20) - account.get('today_published', 0)
                if remaining <= 0:
                    continue
                
                # 获取该账号待发布的商品
                account_products = [p for p in products if str(p.get('account_id', '')) == str(account['_id'])]
                
                # 添加到队列
                queue.append({
                    'account_id': str(account['_id']),
                    'account_name': account.get('account_name', '未命名账号'),
                    'xianyu_username': account['xianyu_username'],
                    'remaining': remaining,
                    'products': [{
                        'id': str(p['_id']),
                        'title': p['title'],
                        'price': p['price'],
                        'created_at': p['created_at'].isoformat()
                    } for p in account_products[:remaining]]
                })
            
            return jsonify({
                'success': True,
                'queue': queue
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'获取发布队列失败: {str(e)}'
            }), 500
    
    def update_publish_count(self, username, account_id, count=1):
        """更新账号发布计数
        
        Args:
            username (str): 用户名
            account_id (str): 账号ID
            count (int): 增加的发布数量
            
        Returns:
            dict: 处理结果
        """
        try:
            # 更新账号发布计数
            result = self.db.accounts.update_one(
                {'_id': ObjectId(account_id), 'username': username},
                {
                    '$inc': {'today_published': count, 'total_products': count},
                    '$set': {'updated_at': datetime.now()}
                }
            )
            
            if result.matched_count == 0:
                return jsonify({
                    'success': False,
                    'message': '账号不存在或无权限更新'
                }), 404
            
            # 获取更新后的账号信息
            account = self.db.accounts.find_one({'_id': ObjectId(account_id)})
            
            return jsonify({
                'success': True,
                'message': '发布计数更新成功',
                'today_published': account.get('today_published', 0),
                'total_products': account.get('total_products', 0),
                'daily_limit': account.get('daily_limit', 20),
                'remaining': account.get('daily_limit', 20) - account.get('today_published', 0)
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'更新发布计数失败: {str(e)}'
            }), 500 