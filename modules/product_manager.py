#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import csv
import json
import uuid
import pandas as pd
from datetime import datetime
from flask import jsonify
from playwright.sync_api import sync_playwright, TimeoutError
import threading
import time
from bson import ObjectId

class ProductManager:
    def __init__(self, db):
        self.db = db
        self.browser = None
        self.browser_lock = threading.Lock()
        self.max_retry = 3
    
    def _get_browser(self):
        """获取浏览器实例，懒加载模式"""
        with self.browser_lock:
            if self.browser is None:
                playwright = sync_playwright().start()
                self.browser = playwright.chromium.launch(headless=True)
            return self.browser
    
    def get_products(self, username):
        """获取用户的所有商品"""
        try:
            products = list(self.db.products.find({'username': username}))
            for product in products:
                product['_id'] = str(product['_id'])
            
            return jsonify({
                'success': True,
                'products': products
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'获取商品失败: {str(e)}'
            }), 500
    
    def add_product(self, username, product_data):
        """添加单个商品"""
        try:
            product_data['username'] = username
            product_data['created_at'] = datetime.now()
            product_data['updated_at'] = datetime.now()
            product_data['status'] = 'draft'  # 草稿状态
            
            result = self.db.products.insert_one(product_data)
            
            return jsonify({
                'success': True,
                'product_id': str(result.inserted_id),
                'message': '商品添加成功'
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'商品添加失败: {str(e)}'
            }), 500
    
    def update_product(self, username, product_id, product_data):
        """更新商品信息"""
        try:
            product_data['updated_at'] = datetime.now()
            
            # 确保用户只能更新自己的商品
            result = self.db.products.update_one(
                {'_id': ObjectId(product_id), 'username': username},
                {'$set': product_data}
            )
            
            if result.matched_count == 0:
                return jsonify({
                    'success': False,
                    'message': '商品不存在或无权限修改'
                }), 404
            
            return jsonify({
                'success': True,
                'message': '商品更新成功'
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'商品更新失败: {str(e)}'
            }), 500
    
    def delete_product(self, username, product_id):
        """删除商品"""
        try:
            # 确保用户只能删除自己的商品
            result = self.db.products.delete_one({
                '_id': ObjectId(product_id),
                'username': username
            })
            
            if result.deleted_count == 0:
                return jsonify({
                    'success': False,
                    'message': '商品不存在或无权限删除'
                }), 404
            
            return jsonify({
                'success': True,
                'message': '商品删除成功'
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'商品删除失败: {str(e)}'
            }), 500
    
    def import_products(self, username, file):
        """从Excel或CSV导入商品信息"""
        try:
            filename = file.filename
            temp_path = f"/tmp/{uuid.uuid4()}{os.path.splitext(filename)[1]}"
            file.save(temp_path)
            
            # 根据文件类型读取数据
            if filename.endswith('.csv'):
                df = pd.read_csv(temp_path)
            elif filename.endswith(('.xls', '.xlsx')):
                df = pd.read_excel(temp_path)
            else:
                os.remove(temp_path)
                return jsonify({
                    'success': False,
                    'message': '不支持的文件格式，请上传CSV或Excel文件'
                }), 400
                
            # 检查必需字段
            required_fields = ['title', 'price', 'description']
            for field in required_fields:
                if field not in df.columns:
                    os.remove(temp_path)
                    return jsonify({
                        'success': False,
                        'message': f'缺少必要字段: {field}'
                    }), 400
            
            # 批量导入
            products = []
            for _, row in df.iterrows():
                product = {
                    'username': username,
                    'title': row['title'],
                    'price': float(row['price']),
                    'description': row['description'],
                    'status': 'draft',
                    'created_at': datetime.now(),
                    'updated_at': datetime.now()
                }
                
                # 添加可选字段
                optional_fields = ['category', 'images', 'tags']
                for field in optional_fields:
                    if field in df.columns and not pd.isna(row[field]):
                        if field == 'images' or field == 'tags':
                            try:
                                product[field] = json.loads(row[field])
                            except:
                                # 如果不是JSON格式，尝试按逗号分隔
                                product[field] = row[field].split(',')
                        else:
                            product[field] = row[field]
                
                products.append(product)
            
            # 批量插入数据库
            if products:
                self.db.products.insert_many(products)
                
            os.remove(temp_path)
            
            return jsonify({
                'success': True,
                'message': f'成功导入 {len(products)} 个商品',
                'count': len(products)
            })
        except Exception as e:
            # 确保临时文件被删除
            if 'temp_path' in locals() and os.path.exists(temp_path):
                os.remove(temp_path)
            
            return jsonify({
                'success': False,
                'message': f'商品导入失败: {str(e)}'
            }), 500
    
    def batch_publish(self, username, data):
        """批量发布商品"""
        product_ids = data.get('product_ids', [])
        account_id = data.get('account_id')
        delay = data.get('delay', 0)  # 延迟秒数
        region = data.get('region', 'random')  # 发布地区
        
        if not product_ids:
            return jsonify({
                'success': False,
                'message': '未提供商品ID列表'
            }), 400
            
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
        
        # 异步执行发布任务
        def publish_task():
            results = []
            for product_id in product_ids:
                try:
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
                    
                    # 执行发布操作
                    result = self._publish_product(account, product, region)
                    results.append({
                        'product_id': product_id,
                        'success': result['success'],
                        'message': result['message'],
                        'item_id': result.get('item_id')
                    })
                    
                    # 更新数据库中商品状态
                    update_data = {
                        'status': 'published' if result['success'] else 'failed',
                        'updated_at': datetime.now()
                    }
                    
                    if result['success'] and 'item_id' in result:
                        update_data['item_id'] = result['item_id']
                    
                    self.db.products.update_one(
                        {'_id': ObjectId(product_id)},
                        {'$set': update_data}
                    )
                    
                    # 应用延迟
                    if delay > 0:
                        time.sleep(delay)
                        
                except Exception as e:
                    results.append({
                        'product_id': product_id,
                        'success': False,
                        'message': f'发布失败: {str(e)}'
                    })
            
            # 将结果保存到任务历史
            self.db.publish_tasks.insert_one({
                'username': username,
                'account_id': account_id,
                'product_ids': product_ids,
                'results': results,
                'created_at': datetime.now()
            })
        
        # 启动异步任务
        thread = threading.Thread(target=publish_task)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'message': f'已开始发布 {len(product_ids)} 个商品，请稍后查看结果',
            'task_id': str(uuid.uuid4())
        })
    
    def _publish_product(self, account, product, region):
        """使用Playwright自动化发布单个商品"""
        try:
            browser = self._get_browser()
            page = browser.new_page()
            
            # 设置超时时间
            page.set_default_timeout(60000)  # 60秒
            
            # 登录咸鱼
            login_result = self._login_xianyu(page, account['username'], account['password'])
            if not login_result['success']:
                page.close()
                return login_result
            
            # 前往发布页面
            page.goto('https://2.taobao.com/publish/publish.htm')
            page.wait_for_load_state('networkidle')
            
            # 填写商品信息
            page.fill('#title', product['title'])
            page.fill('#desc', product['description'])
            page.fill('#price', str(product['price']))
            
            # 选择分类
            if 'category' in product:
                # 根据分类路径点击分类选择器
                categories = product['category'].split('>')
                page.click('#J_Item_Cate')
                
                for category in categories:
                    # 等待分类列表加载
                    page.wait_for_selector('.J_FishCateList')
                    # 选择对应分类
                    page.click(f'text="{category.strip()}"')
            
            # 上传图片
            if 'images' in product and product['images']:
                for image_url in product['images'][:9]:  # 最多9张图片
                    # 如果是本地路径
                    if os.path.exists(image_url):
                        file_input = page.query_selector('input[type="file"]')
                        file_input.set_input_files(image_url)
                    else:
                        # 如果是URL，需要先下载再上传
                        pass  # 实现略复杂，这里省略
            
            # 设置地区
            if region != 'random':
                page.click('#J_FishRegion')
                page.wait_for_selector('.city-container')
                
                # 选择对应城市
                region_mapping = {
                    'beijing': '北京',
                    'shanghai': '上海',
                    'guangzhou': '广州',
                    'shenzhen': '深圳',
                    'hangzhou': '杭州'
                }
                
                if region in region_mapping:
                    page.click(f'text="{region_mapping[region]}"')
                else:
                    # 随机选择一个城市
                    cities = page.query_selector_all('.city-item')
                    import random
                    random_city = random.choice(cities)
                    random_city.click()
            
            # 点击发布按钮
            page.click('#J_PublishSubmit')
            
            # 等待发布结果
            try:
                # 等待成功提示
                page.wait_for_selector('.publish-success', timeout=10000)
                # 获取商品ID
                item_url = page.evaluate('() => document.querySelector(".btn-view").href')
                item_id = item_url.split('=')[-1]
                
                result = {
                    'success': True,
                    'message': '商品发布成功',
                    'item_id': item_id
                }
            except TimeoutError:
                # 检查是否有错误提示
                error_msg = page.evaluate('() => document.querySelector(".publish-error-msg")?.innerText || "未知错误"')
                
                result = {
                    'success': False,
                    'message': f'商品发布失败: {error_msg}'
                }
            
            page.close()
            return result
        except Exception as e:
            return {
                'success': False,
                'message': f'自动化发布过程出错: {str(e)}'
            }
    
    def _login_xianyu(self, page, username, password):
        """登录咸鱼账号"""
        try:
            # 访问咸鱼登录页
            page.goto('https://login.taobao.com/member/login.jhtml')
            page.wait_for_load_state('networkidle')
            
            # 切换到账号密码登录
            try:
                page.click('text="密码登录"')
            except:
                pass  # 可能已经是密码登录模式
            
            # 输入用户名和密码
            page.fill('#fm-login-id', username)
            page.fill('#fm-login-password', password)
            
            # 点击登录按钮
            page.click('button[type="submit"]')
            
            # 处理可能的滑块验证
            try:
                # 检查是否出现滑块验证
                if page.query_selector('#nc_1_n1z') is not None:
                    # 滑块验证需要更复杂的处理，这里简化处理
                    slider = page.query_selector('#nc_1_n1z')
                    box = slider.bounding_box()
                    
                    # 模拟滑动
                    page.mouse.move(box['x'], box['y'] + box['height'] / 2)
                    page.mouse.down()
                    page.mouse.move(box['x'] + 300, box['y'] + box['height'] / 2, steps=30)
                    page.mouse.up()
                    
                    # 等待验证结果
                    page.wait_for_timeout(2000)
            except:
                pass  # 忽略滑块处理错误
            
            # 等待登录成功
            try:
                # 等待重定向完成
                page.wait_for_load_state('networkidle', timeout=10000)
                
                # 检查是否登录成功
                if 'login.taobao.com' not in page.url:
                    return {'success': True, 'message': '登录成功'}
                else:
                    error_msg = page.evaluate('() => document.querySelector(".login-error")?.innerText || "登录失败，请检查账号密码"')
                    return {'success': False, 'message': error_msg}
            except:
                return {'success': False, 'message': '登录超时或发生未知错误'}
            
        except Exception as e:
            return {'success': False, 'message': f'登录过程出错: {str(e)}'}
    
    def get_hot_products(self, username, keywords=None):
        """获取热门商品"""
        try:
            # 这里实现爬取热门商品的逻辑
            browser = self._get_browser()
            page = browser.new_page()
            
            # 构建搜索URL
            search_url = 'https://2.taobao.com/search.htm?'
            if keywords:
                search_url += f'q={keywords}&'
            
            # 添加热门排序参数
            search_url += 'search_type=item&app=listing&orderType=coefp_desc'
            
            # 访问搜索页面
            page.goto(search_url)
            page.wait_for_load_state('networkidle')
            
            # 提取商品信息
            products = []
            product_cards = page.query_selector_all('.item-info')
            
            for card in product_cards[:20]:  # 取前20个结果
                try:
                    title_el = card.query_selector('.item-title')
                    title = title_el.text_content() if title_el else "无标题"
                    
                    price_el = card.query_selector('.price')
                    price = float(price_el.text_content().replace('¥', '').strip()) if price_el else 0
                    
                    want_count_el = card.query_selector('.want-count')
                    want_count = int(want_count_el.text_content().replace('人想要', '').strip()) if want_count_el else 0
                    
                    link_el = card.query_selector('a.item-link')
                    link = link_el.get_attribute('href') if link_el else ''
                    item_id = ''
                    if link:
                        item_id = link.split('itemid=')[-1].split('&')[0]
                    
                    image_el = card.query_selector('img.item-pic')
                    image = image_el.get_attribute('src') if image_el else ''
                    
                    products.append({
                        'title': title,
                        'price': price,
                        'want_count': want_count,
                        'item_id': item_id,
                        'image': image,
                        'link': f'https:{link}' if link.startswith('//') else link
                    })
                except Exception as e:
                    continue
            
            page.close()
            
            return jsonify({
                'success': True,
                'products': products
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'获取热门商品失败: {str(e)}'
            }), 500 