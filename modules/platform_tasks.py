#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import jsonify
from bson.objectid import ObjectId
from datetime import datetime, timedelta
import os
import uuid
import json
import random
import time
import threading
import schedule

class PlatformTasks:
    """平台任务自动化模块"""
    
    def __init__(self, db):
        """初始化平台任务模块"""
        self.db = db
        self.task_threads = {}
        self.running_tasks = {}
        
        # 支持的地区列表
        self.regions = {
            'beijing': '北京',
            'shanghai': '上海',
            'guangzhou': '广州',
            'shenzhen': '深圳',
            'hangzhou': '杭州',
            'random': '随机'
        }
    
    def run_daily_tasks(self, username):
        """执行日常任务
        
        Args:
            username (str): 用户名
            
        Returns:
            dict: 处理结果
        """
        try:
            # 检查是否已有正在运行的任务
            if username in self.running_tasks and self.running_tasks[username].get('daily_tasks'):
                return jsonify({
                    'success': False,
                    'message': '已有日常任务正在运行，请等待完成'
                }), 400
            
            # 获取用户账号
            accounts = list(self.db.accounts.find({
                'username': username,
                'status': 'active'
            }))
            
            if not accounts:
                return jsonify({
                    'success': False,
                    'message': '没有可用的账号'
                }), 404
            
            # 创建任务记录
            task_id = str(uuid.uuid4())
            task_record = {
                'id': task_id,
                'username': username,
                'type': 'daily_tasks',
                'status': 'running',
                'created_at': datetime.now(),
                'updated_at': datetime.now(),
                'accounts': [str(account['_id']) for account in accounts],
                'progress': 0,
                'total': len(accounts),
                'results': []
            }
            
            # 保存任务记录
            self.db.tasks.insert_one(task_record)
            
            # 启动任务线程
            thread = threading.Thread(
                target=self._run_daily_tasks_thread,
                args=(username, task_id, accounts)
            )
            thread.daemon = True
            thread.start()
            
            # 记录运行中的任务
            if username not in self.running_tasks:
                self.running_tasks[username] = {}
            self.running_tasks[username]['daily_tasks'] = task_id
            
            return jsonify({
                'success': True,
                'message': '日常任务已启动',
                'task_id': task_id
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'启动日常任务失败: {str(e)}'
            }), 500
    
    def _run_daily_tasks_thread(self, username, task_id, accounts):
        """执行日常任务线程
        
        Args:
            username (str): 用户名
            task_id (str): 任务ID
            accounts (list): 账号列表
        """
        try:
            total = len(accounts)
            results = []
            
            for i, account in enumerate(accounts):
                # 更新进度
                progress = int((i / total) * 100)
                self.db.tasks.update_one(
                    {'id': task_id},
                    {'$set': {'progress': progress, 'updated_at': datetime.now()}}
                )
                
                # 执行任务
                account_result = {
                    'account_id': str(account['_id']),
                    'account_name': account.get('account_name', '未命名账号'),
                    'tasks': []
                }
                
                # 签到打卡
                signin_result = self._execute_signin(account)
                account_result['tasks'].append({
                    'name': '签到打卡',
                    'success': signin_result['success'],
                    'message': signin_result['message']
                })
                
                # 领取红包
                redpacket_result = self._execute_redpacket(account)
                account_result['tasks'].append({
                    'name': '领取红包',
                    'success': redpacket_result['success'],
                    'message': redpacket_result['message']
                })
                
                # 参与活动
                activity_result = self._execute_activity(account)
                account_result['tasks'].append({
                    'name': '参与活动',
                    'success': activity_result['success'],
                    'message': activity_result['message']
                })
                
                # 添加结果
                results.append(account_result)
                
                # 随机延时，避免操作过快
                time.sleep(random.uniform(1, 3))
            
            # 更新任务完成状态
            self.db.tasks.update_one(
                {'id': task_id},
                {
                    '$set': {
                        'status': 'completed',
                        'progress': 100,
                        'results': results,
                        'completed_at': datetime.now(),
                        'updated_at': datetime.now()
                    }
                }
            )
            
            # 清除运行中的任务记录
            if username in self.running_tasks and self.running_tasks[username].get('daily_tasks') == task_id:
                self.running_tasks[username].pop('daily_tasks', None)
                
        except Exception as e:
            # 更新任务失败状态
            self.db.tasks.update_one(
                {'id': task_id},
                {
                    '$set': {
                        'status': 'failed',
                        'error': str(e),
                        'updated_at': datetime.now()
                    }
                }
            )
            
            # 清除运行中的任务记录
            if username in self.running_tasks and self.running_tasks[username].get('daily_tasks') == task_id:
                self.running_tasks[username].pop('daily_tasks', None)
    
    def _execute_signin(self, account):
        """执行签到打卡任务
        
        Args:
            account (dict): 账号信息
            
        Returns:
            dict: 执行结果
        """
        # 实际应用中需要使用浏览器自动化执行签到操作
        # 这里只返回模拟结果
        success = random.random() > 0.1  # 90%成功率
        
        if success:
            return {
                'success': True,
                'message': '签到成功，获得5积分'
            }
        else:
            return {
                'success': False,
                'message': '签到失败，可能已经签到过'
            }
    
    def _execute_redpacket(self, account):
        """执行领取红包任务
        
        Args:
            account (dict): 账号信息
            
        Returns:
            dict: 执行结果
        """
        # 实际应用中需要使用浏览器自动化执行领取红包操作
        # 这里只返回模拟结果
        success = random.random() > 0.2  # 80%成功率
        
        if success:
            amount = round(random.uniform(0.5, 5), 2)
            return {
                'success': True,
                'message': f'领取成功，获得{amount}元红包'
            }
        else:
            return {
                'success': False,
                'message': '领取失败，可能已经领取过或没有可用红包'
            }
    
    def _execute_activity(self, account):
        """执行参与活动任务
        
        Args:
            account (dict): 账号信息
            
        Returns:
            dict: 执行结果
        """
        # 实际应用中需要使用浏览器自动化执行参与活动操作
        # 这里只返回模拟结果
        success = random.random() > 0.3  # 70%成功率
        
        if success:
            activities = ['限时优惠', '满减活动', '新品首发', '季度大促']
            activity = random.choice(activities)
            return {
                'success': True,
                'message': f'成功参与{activity}活动'
            }
        else:
            return {
                'success': False,
                'message': '参与活动失败，可能没有符合条件的活动'
            }
    
    def get_task_status(self, username, task_id):
        """获取任务状态
        
        Args:
            username (str): 用户名
            task_id (str): 任务ID
            
        Returns:
            dict: 任务状态
        """
        try:
            # 查询任务记录
            task = self.db.tasks.find_one({
                'id': task_id,
                'username': username
            })
            
            if not task:
                return jsonify({
                    'success': False,
                    'message': '任务不存在或无权限查看'
                }), 404
            
            # 处理返回结果
            result = {
                'id': task['id'],
                'type': task['type'],
                'status': task['status'],
                'progress': task.get('progress', 0),
                'total': task.get('total', 0),
                'created_at': task['created_at'].isoformat(),
                'updated_at': task['updated_at'].isoformat(),
                'completed_at': task.get('completed_at', '').isoformat() if task.get('completed_at') else None,
                'results': task.get('results', []),
                'error': task.get('error')
            }
            
            return jsonify({
                'success': True,
                'task': result
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'获取任务状态失败: {str(e)}'
            }), 500
    
    def get_shop_stats(self, username):
        """获取店铺统计数据
        
        Args:
            username (str): 用户名
            
        Returns:
            dict: 统计数据
        """
        try:
            # 获取用户账号
            accounts = list(self.db.accounts.find({
                'username': username
            }))
            
            # 获取商品统计
            products = list(self.db.products.find({
                'username': username
            }))
            
            # 获取订单统计
            orders = list(self.db.orders.find({
                'username': username
            }))
            
            # 计算统计数据
            total_accounts = len(accounts)
            total_products = len(products)
            total_orders = len(orders)
            
            # 计算活跃账号数
            active_accounts = sum(1 for account in accounts if account.get('status') == 'active')
            
            # 计算在售商品数
            active_products = sum(1 for product in products if product.get('status') == 'active')
            
            # 计算已售商品数
            sold_products = sum(1 for product in products if product.get('status') == 'sold')
            
            # 计算今日订单数
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            today_orders = sum(1 for order in orders if order.get('created_at') >= today)
            
            # 计算本周订单数
            week_start = today - timedelta(days=today.weekday())
            week_orders = sum(1 for order in orders if order.get('created_at') >= week_start)
            
            # 计算本月订单数
            month_start = today.replace(day=1)
            month_orders = sum(1 for order in orders if order.get('created_at') >= month_start)
            
            # 计算总销售额
            total_sales = sum(order.get('price', 0) for order in orders)
            
            # 计算本月销售额
            month_sales = sum(order.get('price', 0) for order in orders if order.get('created_at') >= month_start)
            
            # 计算商品分类统计
            category_stats = {}
            for product in products:
                category = product.get('category', '未分类')
                if category not in category_stats:
                    category_stats[category] = 0
                category_stats[category] += 1
            
            # 计算订单状态统计
            status_stats = {}
            for order in orders:
                status = order.get('status', '未知状态')
                if status not in status_stats:
                    status_stats[status] = 0
                status_stats[status] += 1
            
            # 构建返回结果
            result = {
                'account_stats': {
                    'total': total_accounts,
                    'active': active_accounts,
                    'inactive': total_accounts - active_accounts
                },
                'product_stats': {
                    'total': total_products,
                    'active': active_products,
                    'sold': sold_products,
                    'inactive': total_products - active_products - sold_products,
                    'categories': category_stats
                },
                'order_stats': {
                    'total': total_orders,
                    'today': today_orders,
                    'week': week_orders,
                    'month': month_orders,
                    'status': status_stats
                },
                'sales_stats': {
                    'total': total_sales,
                    'month': month_sales,
                    'avg_order': total_sales / total_orders if total_orders > 0 else 0
                },
                'updated_at': datetime.now().isoformat()
            }
            
            return jsonify({
                'success': True,
                'stats': result
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'获取统计数据失败: {str(e)}'
            }), 500
    
    def polish_products(self, username, data):
        """擦亮商品
        
        Args:
            username (str): 用户名
            data (dict): 请求数据
            
        Returns:
            dict: 处理结果
        """
        try:
            # 检查必要字段
            if 'product_ids' not in data:
                return jsonify({
                    'success': False,
                    'message': '缺少必要字段: product_ids'
                }), 400
            
            product_ids = data['product_ids']
            
            # 检查是否已有正在运行的任务
            if username in self.running_tasks and self.running_tasks[username].get('polish'):
                return jsonify({
                    'success': False,
                    'message': '已有擦亮任务正在运行，请等待完成'
                }), 400
            
            # 创建任务记录
            task_id = str(uuid.uuid4())
            task_record = {
                'id': task_id,
                'username': username,
                'type': 'polish',
                'status': 'running',
                'created_at': datetime.now(),
                'updated_at': datetime.now(),
                'product_ids': product_ids,
                'progress': 0,
                'total': len(product_ids),
                'results': []
            }
            
            # 保存任务记录
            self.db.tasks.insert_one(task_record)
            
            # 启动任务线程
            thread = threading.Thread(
                target=self._polish_products_thread,
                args=(username, task_id, product_ids)
            )
            thread.daemon = True
            thread.start()
            
            # 记录运行中的任务
            if username not in self.running_tasks:
                self.running_tasks[username] = {}
            self.running_tasks[username]['polish'] = task_id
            
            return jsonify({
                'success': True,
                'message': f'擦亮任务已启动，共{len(product_ids)}个商品',
                'task_id': task_id
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'启动擦亮任务失败: {str(e)}'
            }), 500
    
    def _polish_products_thread(self, username, task_id, product_ids):
        """擦亮商品线程
        
        Args:
            username (str): 用户名
            task_id (str): 任务ID
            product_ids (list): 商品ID列表
        """
        try:
            total = len(product_ids)
            results = []
            
            for i, product_id in enumerate(product_ids):
                # 更新进度
                progress = int((i / total) * 100)
                self.db.tasks.update_one(
                    {'id': task_id},
                    {'$set': {'progress': progress, 'updated_at': datetime.now()}}
                )
                
                # 获取商品信息
                product = self.db.products.find_one({
                    '_id': ObjectId(product_id),
                    'username': username
                })
                
                if not product:
                    results.append({
                        'product_id': product_id,
                        'success': False,
                        'message': '商品不存在或无权限操作'
                    })
                    continue
                
                # 获取账号信息
                account = self.db.accounts.find_one({
                    '_id': product.get('account_id'),
                    'username': username
                })
                
                if not account:
                    results.append({
                        'product_id': product_id,
                        'title': product.get('title', '未知商品'),
                        'success': False,
                        'message': '关联账号不存在或无权限操作'
                    })
                    continue
                
                # 执行擦亮操作
                # 实际应用中需要使用浏览器自动化执行擦亮操作
                # 这里只更新数据库状态
                
                # 更新商品擦亮时间
                self.db.products.update_one(
                    {'_id': ObjectId(product_id)},
                    {
                        '$set': {
                            'last_polish': datetime.now(),
                            'updated_at': datetime.now()
                        }
                    }
                )
                
                # 添加结果
                results.append({
                    'product_id': product_id,
                    'title': product.get('title', '未知商品'),
                    'success': True,
                    'message': '擦亮成功'
                })
                
                # 随机延时，避免操作过快
                time.sleep(random.uniform(1, 3))
            
            # 更新任务完成状态
            self.db.tasks.update_one(
                {'id': task_id},
                {
                    '$set': {
                        'status': 'completed',
                        'progress': 100,
                        'results': results,
                        'completed_at': datetime.now(),
                        'updated_at': datetime.now()
                    }
                }
            )
            
            # 清除运行中的任务记录
            if username in self.running_tasks and self.running_tasks[username].get('polish') == task_id:
                self.running_tasks[username].pop('polish', None)
                
        except Exception as e:
            # 更新任务失败状态
            self.db.tasks.update_one(
                {'id': task_id},
                {
                    '$set': {
                        'status': 'failed',
                        'error': str(e),
                        'updated_at': datetime.now()
                    }
                }
            )
            
            # 清除运行中的任务记录
            if username in self.running_tasks and self.running_tasks[username].get('polish') == task_id:
                self.running_tasks[username].pop('polish', None)
    
    def schedule_midnight_polish(self, username, data):
        """设置0点自动擦亮
        
        Args:
            username (str): 用户名
            data (dict): 请求数据
            
        Returns:
            dict: 处理结果
        """
        try:
            # 检查必要字段
            if 'enabled' not in data:
                return jsonify({
                    'success': False,
                    'message': '缺少必要字段: enabled'
                }), 400
            
            enabled = data['enabled']
            product_ids = data.get('product_ids', [])
            
            # 更新用户设置
            self.db.user_settings.update_one(
                {'username': username},
                {
                    '$set': {
                        'midnight_polish': {
                            'enabled': enabled,
                            'product_ids': product_ids,
                            'updated_at': datetime.now()
                        }
                    }
                },
                upsert=True
            )
            
            # 如果启用，设置定时任务
            if enabled:
                # 创建定时任务
                # 实际应用中应使用更可靠的定时任务系统，如Celery
                if username not in self.task_threads:
                    self.task_threads[username] = {}
                
                # 取消已有的定时任务
                if 'midnight_polish' in self.task_threads[username]:
                    schedule.cancel_job(self.task_threads[username]['midnight_polish'])
                
                # 创建新的定时任务
                job = schedule.every().day.at("00:00").do(
                    self._run_midnight_polish,
                    username=username,
                    product_ids=product_ids
                )
                
                self.task_threads[username]['midnight_polish'] = job
                
                return jsonify({
                    'success': True,
                    'message': f'已设置0点自动擦亮，共{len(product_ids)}个商品'
                })
            else:
                # 取消定时任务
                if username in self.task_threads and 'midnight_polish' in self.task_threads[username]:
                    schedule.cancel_job(self.task_threads[username]['midnight_polish'])
                    self.task_threads[username].pop('midnight_polish', None)
                
                return jsonify({
                    'success': True,
                    'message': '已取消0点自动擦亮'
                })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'设置0点自动擦亮失败: {str(e)}'
            }), 500
    
    def _run_midnight_polish(self, username, product_ids):
        """执行0点自动擦亮
        
        Args:
            username (str): 用户名
            product_ids (list): 商品ID列表
        """
        try:
            # 创建任务记录
            task_id = str(uuid.uuid4())
            task_record = {
                'id': task_id,
                'username': username,
                'type': 'midnight_polish',
                'status': 'running',
                'created_at': datetime.now(),
                'updated_at': datetime.now(),
                'product_ids': product_ids,
                'progress': 0,
                'total': len(product_ids),
                'results': []
            }
            
            # 保存任务记录
            self.db.tasks.insert_one(task_record)
            
            # 启动任务线程
            thread = threading.Thread(
                target=self._polish_products_thread,
                args=(username, task_id, product_ids)
            )
            thread.daemon = True
            thread.start()
            
        except Exception as e:
            print(f"执行0点自动擦亮失败: {str(e)}")
    
    def set_region(self, username, data):
        """设置发布地区
        
        Args:
            username (str): 用户名
            data (dict): 请求数据
            
        Returns:
            dict: 处理结果
        """
        try:
            # 检查必要字段
            if 'region' not in data:
                return jsonify({
                    'success': False,
                    'message': '缺少必要字段: region'
                }), 400
            
            region = data['region']
            account_id = data.get('account_id')  # 可选，为空则设置用户默认地区
            
            # 检查地区是否有效
            if region not in self.regions and region != 'random':
                return jsonify({
                    'success': False,
                    'message': f'无效的地区，允许的地区: {", ".join(list(self.regions.keys()) + ["random"])}'
                }), 400
            
            if account_id:
                # 更新账号地区设置
                result = self.db.accounts.update_one(
                    {'_id': ObjectId(account_id), 'username': username},
                    {
                        '$set': {
                            'region': region,
                            'updated_at': datetime.now()
                        }
                    }
                )
                
                if result.matched_count == 0:
                    return jsonify({
                        'success': False,
                        'message': '账号不存在或无权限修改'
                    }), 404
                
                return jsonify({
                    'success': True,
                    'message': f'已设置账号发布地区为: {self.regions.get(region, "随机")}'
                })
            else:
                # 更新用户默认地区设置
                self.db.user_settings.update_one(
                    {'username': username},
                    {
                        '$set': {
                            'default_region': region,
                            'updated_at': datetime.now()
                        }
                    },
                    upsert=True
                )
                
                return jsonify({
                    'success': True,
                    'message': f'已设置默认发布地区为: {self.regions.get(region, "随机")}'
                })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'设置发布地区失败: {str(e)}'
            }), 500
    
    def get_region(self, username, account_id=None):
        """获取发布地区设置
        
        Args:
            username (str): 用户名
            account_id (str, optional): 账号ID
            
        Returns:
            dict: 地区设置
        """
        try:
            if account_id:
                # 获取账号地区设置
                account = self.db.accounts.find_one({
                    '_id': ObjectId(account_id),
                    'username': username
                })
                
                if not account:
                    return jsonify({
                        'success': False,
                        'message': '账号不存在或无权限查看'
                    }), 404
                
                region = account.get('region', 'random')
                return jsonify({
                    'success': True,
                    'region': region,
                    'region_name': self.regions.get(region, '随机')
                })
            else:
                # 获取用户默认地区设置
                settings = self.db.user_settings.find_one({'username': username})
                
                region = settings.get('default_region', 'random') if settings else 'random'
                return jsonify({
                    'success': True,
                    'region': region,
                    'region_name': self.regions.get(region, '随机')
                })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'获取发布地区失败: {str(e)}'
            }), 500
    
    def get_available_regions(self):
        """获取可用地区列表
        
        Returns:
            dict: 地区列表
        """
        try:
            regions = [{'code': code, 'name': name} for code, name in self.regions.items()]
            
            return jsonify({
                'success': True,
                'regions': regions
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'获取地区列表失败: {str(e)}'
            }), 500 