#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import io
import qrcode
import base64
from flask import jsonify
from datetime import datetime
from bson import ObjectId
from playwright.sync_api import sync_playwright
import threading
import time

class OrderProcessor:
    def __init__(self, db):
        self.db = db
        self.browser = None
        self.browser_lock = threading.Lock()
    
    def _get_browser(self):
        """获取浏览器实例，懒加载模式"""
        with self.browser_lock:
            if self.browser is None:
                playwright = sync_playwright().start()
                self.browser = playwright.chromium.launch(headless=True)
            return self.browser
    
    def get_orders(self, username):
        """获取用户的所有订单"""
        try:
            orders = list(self.db.orders.find({'username': username}).sort('created_at', -1))
            for order in orders:
                order['_id'] = str(order['_id'])
                if 'account_id' in order and order['account_id']:
                    order['account_id'] = str(order['account_id'])
            
            return jsonify({
                'success': True,
                'orders': orders
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'获取订单失败: {str(e)}'
            }), 500
    
    def fetch_orders(self, username, account_id):
        """从咸鱼平台抓取订单"""
        try:
            # 验证账号是否存在
            account = self.db.accounts.find_one({
                '_id': ObjectId(account_id),
                'username': username
            })
            
            if not account:
                return {
                    'success': False,
                    'message': '账号不存在或无权限使用'
                }
            
            # 执行订单抓取
            browser = self._get_browser()
            page = browser.new_page()
            
            # 登录咸鱼
            from modules.product_manager import ProductManager
            product_manager = ProductManager(self.db)
            login_result = product_manager._login_xianyu(page, account['username'], account['password'])
            
            if not login_result['success']:
                page.close()
                return login_result
            
            # 访问订单页面
            page.goto('https://sell.2.taobao.com/auction/merchandise/soldlist.htm')
            page.wait_for_load_state('networkidle')
            
            # 抓取订单信息
            orders = []
            order_rows = page.query_selector_all('.order-item')
            
            for row in order_rows:
                try:
                    order_id_el = row.query_selector('.order-id')
                    order_id = order_id_el.text_content().strip() if order_id_el else ''
                    
                    # 检查订单是否已存在
                    existing_order = self.db.orders.find_one({
                        'order_id': order_id,
                        'account_id': account_id
                    })
                    
                    if existing_order:
                        continue
                    
                    title_el = row.query_selector('.item-title')
                    title = title_el.text_content().strip() if title_el else '未知商品'
                    
                    price_el = row.query_selector('.item-price')
                    price = float(price_el.text_content().replace('¥', '').strip()) if price_el else 0
                    
                    status_el = row.query_selector('.order-status')
                    status = status_el.text_content().strip() if status_el else '未知状态'
                    
                    buyer_el = row.query_selector('.buyer-name')
                    buyer = buyer_el.text_content().strip() if buyer_el else '未知买家'
                    
                    time_el = row.query_selector('.order-time')
                    order_time = time_el.text_content().strip() if time_el else ''
                    
                    # 保存到数据库
                    order_data = {
                        'username': username,
                        'account_id': account_id,
                        'order_id': order_id,
                        'title': title,
                        'price': price,
                        'status': status,
                        'buyer': buyer,
                        'order_time': order_time,
                        'created_at': datetime.now(),
                        'updated_at': datetime.now(),
                        'shipped': False
                    }
                    
                    self.db.orders.insert_one(order_data)
                    orders.append(order_data)
                except Exception as e:
                    continue
            
            page.close()
            
            return {
                'success': True,
                'message': f'成功获取 {len(orders)} 个新订单',
                'orders': orders
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'获取订单失败: {str(e)}'
            }
    
    def ship_orders(self, username, data):
        """发货处理"""
        try:
            order_ids = data.get('order_ids', [])
            logistics_company = data.get('logistics_company')
            logistics_number = data.get('logistics_number')
            
            if not order_ids:
                return jsonify({
                    'success': False,
                    'message': '未提供订单ID列表'
                }), 400
            
            # 获取订单所属账号ID
            first_order = self.db.orders.find_one({
                '_id': ObjectId(order_ids[0]),
                'username': username
            })
            
            if not first_order:
                return jsonify({
                    'success': False,
                    'message': '订单不存在或无权限操作'
                }), 404
            
            account_id = first_order.get('account_id')
            
            # 验证账号是否存在
            account = self.db.accounts.find_one({
                '_id': ObjectId(account_id),
                'username': username
            })
            
            if not account:
                return jsonify({
                    'success': False,
                    'message': '账号不存在或无权限使用'
                }), 404
            
            # 异步执行发货任务
            def shipping_task():
                results = []
                browser = self._get_browser()
                page = browser.new_page()
                
                # 登录咸鱼
                from modules.product_manager import ProductManager
                product_manager = ProductManager(self.db)
                login_result = product_manager._login_xianyu(page, account['username'], account['password'])
                
                if not login_result['success']:
                    page.close()
                    return
                
                for order_id_str in order_ids:
                    try:
                        order = self.db.orders.find_one({
                            '_id': ObjectId(order_id_str),
                            'username': username
                        })
                        
                        if not order:
                            results.append({
                                'order_id': order_id_str,
                                'success': False,
                                'message': '订单不存在或无权限操作'
                            })
                            continue
                        
                        # 咸鱼订单号
                        xianyu_order_id = order.get('order_id')
                        
                        # 访问订单详情页
                        page.goto(f'https://sell.2.taobao.com/auction/merchandise/soldOrderDetail.htm?orderId={xianyu_order_id}')
                        page.wait_for_load_state('networkidle')
                        
                        # 点击发货按钮
                        ship_button = page.query_selector('button.ship-btn')
                        if ship_button:
                            ship_button.click()
                            page.wait_for_selector('div.logistics-panel')
                            
                            # 选择物流公司
                            page.click('div.logistics-company-select')
                            page.wait_for_selector('ul.company-list')
                            
                            # 查找并选择匹配的物流公司
                            companies = page.query_selector_all('li.company-item')
                            company_found = False
                            
                            for company in companies:
                                company_name = company.text_content().strip()
                                if logistics_company in company_name:
                                    company.click()
                                    company_found = True
                                    break
                            
                            if not company_found:
                                # 选择第一个公司
                                companies[0].click()
                            
                            # 输入物流单号
                            page.fill('input.logistics-number-input', logistics_number)
                            
                            # 点击确认发货
                            page.click('button.confirm-ship-btn')
                            
                            # 等待操作结果
                            page.wait_for_timeout(2000)
                            
                            # 检查是否发货成功
                            if '已发货' in page.content():
                                # 更新数据库
                                self.db.orders.update_one(
                                    {'_id': ObjectId(order_id_str)},
                                    {'$set': {
                                        'shipped': True,
                                        'logistics_company': logistics_company,
                                        'logistics_number': logistics_number,
                                        'ship_time': datetime.now(),
                                        'updated_at': datetime.now()
                                    }}
                                )
                                
                                results.append({
                                    'order_id': order_id_str,
                                    'success': True,
                                    'message': '发货成功'
                                })
                            else:
                                results.append({
                                    'order_id': order_id_str,
                                    'success': False,
                                    'message': '发货操作未成功'
                                })
                        else:
                            results.append({
                                'order_id': order_id_str,
                                'success': False,
                                'message': '该订单状态不支持发货'
                            })
                        
                        # 间隔一下，避免操作过快
                        time.sleep(2)
                    except Exception as e:
                        results.append({
                            'order_id': order_id_str,
                            'success': False,
                            'message': f'发货过程出错: {str(e)}'
                        })
                
                page.close()
                
                # 将结果保存到任务历史
                self.db.shipping_tasks.insert_one({
                    'username': username,
                    'account_id': account_id,
                    'order_ids': order_ids,
                    'results': results,
                    'created_at': datetime.now()
                })
            
            # 启动异步任务
            thread = threading.Thread(target=shipping_task)
            thread.daemon = True
            thread.start()
            
            return jsonify({
                'success': True,
                'message': f'已开始处理 {len(order_ids)} 个订单的发货，请稍后查看结果'
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'发货处理失败: {str(e)}'
            }), 500
    
    def generate_qrcode(self, username, data):
        """生成商品二维码"""
        try:
            product_id = data.get('product_id')
            
            if not product_id:
                return jsonify({
                    'success': False,
                    'message': '未提供商品ID'
                }), 400
            
            # 获取商品信息
            product = self.db.products.find_one({
                '_id': ObjectId(product_id),
                'username': username
            })
            
            if not product:
                return jsonify({
                    'success': False,
                    'message': '商品不存在或无权限操作'
                }), 404
            
            # 检查商品是否已发布
            if 'item_id' not in product:
                return jsonify({
                    'success': False,
                    'message': '商品尚未发布，无法生成二维码'
                }), 400
            
            # 构建二维码链接
            qr_url = f"https://2.taobao.com/item.htm?id={product['item_id']}"
            
            # 生成二维码图像
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(qr_url)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            # 将图像转为base64
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            qr_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            # 保存二维码记录
            qr_data = {
                'username': username,
                'product_id': product_id,
                'url': qr_url,
                'title': product.get('title', ''),
                'price': product.get('price', 0),
                'created_at': datetime.now()
            }
            
            self.db.qrcodes.insert_one(qr_data)
            
            return jsonify({
                'success': True,
                'qrcode': f"data:image/png;base64,{qr_base64}",
                'url': qr_url,
                'title': product.get('title', ''),
                'price': product.get('price', 0)
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'生成二维码失败: {str(e)}'
            }), 500
    
    def fetch_all_orders(self, username):
        """抓取所有账号的订单"""
        try:
            # 获取用户的所有账号
            accounts = list(self.db.accounts.find({'username': username}))
            
            results = []
            for account in accounts:
                account_id = str(account['_id'])
                result = self.fetch_orders(username, account_id)
                results.append({
                    'account': account.get('username'),
                    'account_id': account_id,
                    'success': result['success'],
                    'message': result.get('message', ''),
                    'count': len(result.get('orders', []))
                })
            
            return jsonify({
                'success': True,
                'results': results
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'抓取订单失败: {str(e)}'
            }), 500 