#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import csv
import json
import uuid
import pandas as pd
from datetime import datetime, timedelta
from flask import jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutError
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
                # 使用selenium替代playwright
                chrome_options = Options()
                chrome_options.add_argument("--headless")
                chrome_options.add_argument("--no-sandbox")
                chrome_options.add_argument("--disable-dev-shm-usage")
                self.browser = webdriver.Chrome(options=chrome_options)
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
    
    def collect_hot_products(self, username, data):
        """爆品采集功能
        
        Args:
            username (str): 用户名
            data (dict): 采集参数
            
        Returns:
            dict: 采集结果
        """
        try:
            # 检查必要字段
            if 'keywords' not in data and 'links' not in data:
                return jsonify({
                    'success': False,
                    'message': '缺少必要字段: keywords 或 links'
                }), 400
            
            keywords = data.get('keywords', [])
            links = data.get('links', [])
            filters = data.get('filters', {})
            
            # 设置筛选条件
            min_wants = filters.get('min_wants', 0)  # 最小想要人数
            min_sales = filters.get('min_sales', 0)  # 最小销量
            min_comments = filters.get('min_comments', 0)  # 最小评论数
            days_limit = filters.get('days_limit', 30)  # 发布时间限制(天)
            
            # 存储采集结果
            collected_products = []
            
            # 根据关键词采集
            if keywords:
                for keyword in keywords:
                    # 这里应该实现实际的爆品采集逻辑
                    # 由于需要模拟浏览器操作，这里只模拟返回结果
                    
                    # 模拟采集到的商品
                    products = self._simulate_hot_products(keyword, 5)
                    
                    # 应用筛选条件
                    filtered_products = []
                    for product in products:
                        if (product.get('wants', 0) >= min_wants and
                            product.get('sales', 0) >= min_sales and
                            product.get('comments', 0) >= min_comments):
                            
                            # 检查发布时间
                            days_ago = (datetime.now() - product.get('publish_time', datetime.now())).days
                            if days_ago <= days_limit:
                                filtered_products.append(product)
                    
                    collected_products.extend(filtered_products)
            
            # 根据链接采集
            if links:
                for link in links:
                    # 这里应该实现根据链接采集商品的逻辑
                    # 由于需要模拟浏览器操作，这里只模拟返回结果
                    
                    # 模拟采集到的商品
                    product = self._simulate_product_from_link(link)
                    
                    if product:
                        # 应用筛选条件
                        if (product.get('wants', 0) >= min_wants and
                            product.get('sales', 0) >= min_sales and
                            product.get('comments', 0) >= min_comments):
                            
                            # 检查发布时间
                            days_ago = (datetime.now() - product.get('publish_time', datetime.now())).days
                            if days_ago <= days_limit:
                                collected_products.append(product)
            
            # 保存采集结果到数据库
            for product in collected_products:
                product['username'] = username
                product['collected_at'] = datetime.now()
                product['source'] = 'hot_collection'
                self.db.collected_products.insert_one(product)
            
            return jsonify({
                'success': True,
                'message': f'成功采集 {len(collected_products)} 个爆品',
                'products': collected_products
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'爆品采集失败: {str(e)}'
            }), 500
    
    def _simulate_hot_products(self, keyword, count):
        """模拟爆品数据（实际应用中应从平台获取）
        
        Args:
            keyword (str): 搜索关键词
            count (int): 返回数量
            
        Returns:
            list: 模拟的商品列表
        """
        import random
        
        products = []
        for i in range(count):
            # 生成随机发布时间（1-30天内）
            days_ago = random.randint(1, 30)
            publish_time = datetime.now() - timedelta(days=days_ago)
            
            products.append({
                'id': str(uuid.uuid4()),
                'title': f"{keyword} 热销商品 {i+1}",
                'price': round(random.uniform(10, 1000), 2),
                'wants': random.randint(10, 500),
                'sales': random.randint(5, 100),
                'comments': random.randint(0, 50),
                'publish_time': publish_time,
                'seller': f"店铺{random.randint(1000, 9999)}",
                'link': f"https://example.com/item/{uuid.uuid4()}",
                'images': [f"https://example.com/img/{uuid.uuid4()}.jpg" for _ in range(3)]
            })
        
        return products
    
    def _simulate_product_from_link(self, link):
        """模拟从链接获取商品数据（实际应用中应从链接获取）
        
        Args:
            link (str): 商品链接
            
        Returns:
            dict: 模拟的商品数据
        """
        import random
        
        # 生成随机发布时间（1-30天内）
        days_ago = random.randint(1, 30)
        publish_time = datetime.now() - timedelta(days=days_ago)
        
        return {
            'id': str(uuid.uuid4()),
            'title': f"链接商品 {link[-8:]}",
            'price': round(random.uniform(10, 1000), 2),
            'wants': random.randint(10, 500),
            'sales': random.randint(5, 100),
            'comments': random.randint(0, 50),
            'publish_time': publish_time,
            'seller': f"店铺{random.randint(1000, 9999)}",
            'link': link,
            'images': [f"https://example.com/img/{uuid.uuid4()}.jpg" for _ in range(3)]
        }
    
    def collect_hot_shop(self, username, data):
        """爆店采集功能
        
        Args:
            username (str): 用户名
            data (dict): 采集参数
            
        Returns:
            dict: 采集结果
        """
        try:
            # 检查必要字段
            if 'shop_links' not in data:
                return jsonify({
                    'success': False,
                    'message': '缺少必要字段: shop_links'
                }), 400
            
            shop_links = data.get('shop_links', [])
            filters = data.get('filters', {})
            
            # 设置筛选条件
            min_wants = filters.get('min_wants', 0)  # 最小想要人数
            min_sales = filters.get('min_sales', 0)  # 最小销量
            min_comments = filters.get('min_comments', 0)  # 最小评论数
            days_limit = filters.get('days_limit', 30)  # 发布时间限制(天)
            
            # 存储采集结果
            collected_shops = []
            collected_products = []
            
            # 根据店铺链接采集
            for shop_link in shop_links:
                # 这里应该实现实际的店铺采集逻辑
                # 由于需要模拟浏览器操作，这里只模拟返回结果
                
                # 模拟店铺信息
                shop = self._simulate_shop_info(shop_link)
                
                # 模拟店铺商品
                shop_products = self._simulate_shop_products(shop_link, 10)
                
                # 应用筛选条件
                filtered_products = []
                for product in shop_products:
                    if (product.get('wants', 0) >= min_wants and
                        product.get('sales', 0) >= min_sales and
                        product.get('comments', 0) >= min_comments):
                        
                        # 检查发布时间
                        days_ago = (datetime.now() - product.get('publish_time', datetime.now())).days
                        if days_ago <= days_limit:
                            filtered_products.append(product)
                
                # 添加到结果
                shop['products'] = filtered_products
                shop['product_count'] = len(filtered_products)
                collected_shops.append(shop)
                collected_products.extend(filtered_products)
            
            # 保存采集结果到数据库
            for shop in collected_shops:
                shop['username'] = username
                shop['collected_at'] = datetime.now()
                self.db.collected_shops.insert_one(shop)
            
            for product in collected_products:
                product['username'] = username
                product['collected_at'] = datetime.now()
                product['source'] = 'shop_collection'
                self.db.collected_products.insert_one(product)
            
            return jsonify({
                'success': True,
                'message': f'成功采集 {len(collected_shops)} 个店铺，共 {len(collected_products)} 个商品',
                'shops': collected_shops
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'爆店采集失败: {str(e)}'
            }), 500
    
    def _simulate_shop_info(self, shop_link):
        """模拟店铺信息（实际应用中应从平台获取）
        
        Args:
            shop_link (str): 店铺链接
            
        Returns:
            dict: 模拟的店铺信息
        """
        import random
        
        # 生成随机店铺信息
        return {
            'id': str(uuid.uuid4()),
            'name': f"店铺{shop_link[-6:]}",
            'link': shop_link,
            'rating': round(random.uniform(4.0, 5.0), 1),
            'followers': random.randint(100, 10000),
            'products_count': random.randint(50, 500),
            'description': f"这是一个样例店铺描述 {shop_link[-6:]}",
            'created_at': (datetime.now() - timedelta(days=random.randint(30, 1000))).isoformat()
        }
    
    def _simulate_shop_products(self, shop_link, count):
        """模拟店铺商品（实际应用中应从平台获取）
        
        Args:
            shop_link (str): 店铺链接
            count (int): 返回数量
            
        Returns:
            list: 模拟的商品列表
        """
        import random
        
        products = []
        for i in range(count):
            # 生成随机发布时间（1-30天内）
            days_ago = random.randint(1, 30)
            publish_time = datetime.now() - timedelta(days=days_ago)
            
            products.append({
                'id': str(uuid.uuid4()),
                'title': f"店铺{shop_link[-6:]} 商品 {i+1}",
                'price': round(random.uniform(10, 1000), 2),
                'wants': random.randint(10, 500),
                'sales': random.randint(5, 100),
                'comments': random.randint(0, 50),
                'publish_time': publish_time,
                'shop_link': shop_link,
                'link': f"{shop_link}/item/{uuid.uuid4()}",
                'images': [f"https://example.com/img/{uuid.uuid4()}.jpg" for _ in range(3)]
            })
        
        return products
    
    def download_details(self, username, data):
        """详情下载功能
        
        Args:
            username (str): 用户名
            data (dict): 下载参数
            
        Returns:
            dict: 下载结果
        """
        try:
            # 检查必要字段
            if 'product_links' not in data:
                return jsonify({
                    'success': False,
                    'message': '缺少必要字段: product_links'
                }), 400
            
            product_links = data.get('product_links', [])
            download_options = data.get('options', {})
            
            # 下载选项
            download_images = download_options.get('images', True)
            download_description = download_options.get('description', True)
            modify_md5 = download_options.get('modify_md5', True)
            
            # 存储下载结果
            downloaded_products = []
            
            # 创建下载目录
            download_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'downloads', username)
            if not os.path.exists(download_dir):
                os.makedirs(download_dir)
            
            # 根据商品链接下载
            for product_link in product_links:
                # 这里应该实现实际的详情下载逻辑
                # 由于需要模拟浏览器操作，这里只模拟返回结果
                
                # 模拟商品详情
                product = self._simulate_product_details(product_link)
                
                # 创建商品目录
                product_dir = os.path.join(download_dir, product['id'])
                if not os.path.exists(product_dir):
                    os.makedirs(product_dir)
                
                # 下载图片（模拟）
                image_paths = []
                if download_images:
                    for i, image_url in enumerate(product.get('images', [])):
                        # 实际应用中应下载图片并保存
                        image_path = os.path.join(product_dir, f"image_{i+1}.jpg")
                        
                        # 模拟保存图片
                        with open(image_path, 'w') as f:
                            f.write(f"模拟图片内容: {image_url}")
                        
                        # 如果需要修改MD5
                        if modify_md5:
                            # 实际应用中应修改图片MD5
                            # 这里只是模拟
                            pass
                        
                        image_paths.append(image_path)
                
                # 保存描述
                description_path = None
                if download_description and 'description' in product:
                    description_path = os.path.join(product_dir, "description.html")
                    
                    # 保存描述
                    with open(description_path, 'w', encoding='utf-8') as f:
                        f.write(product['description'])
                
                # 保存商品信息
                info_path = os.path.join(product_dir, "info.json")
                with open(info_path, 'w', encoding='utf-8') as f:
                    json.dump({
                        'title': product.get('title', ''),
                        'price': product.get('price', 0),
                        'seller': product.get('seller', ''),
                        'link': product_link,
                        'downloaded_at': datetime.now().isoformat()
                    }, f, ensure_ascii=False, indent=2)
                
                # 添加到结果
                downloaded_products.append({
                    'id': product['id'],
                    'title': product.get('title', ''),
                    'images': len(image_paths),
                    'has_description': description_path is not None,
                    'download_path': product_dir
                })
                
                # 保存下载记录到数据库
                self.db.downloaded_products.insert_one({
                    'username': username,
                    'product_id': product['id'],
                    'product_link': product_link,
                    'download_path': product_dir,
                    'image_count': len(image_paths),
                    'has_description': description_path is not None,
                    'downloaded_at': datetime.now()
                })
            
            return jsonify({
                'success': True,
                'message': f'成功下载 {len(downloaded_products)} 个商品详情',
                'products': downloaded_products
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'详情下载失败: {str(e)}'
            }), 500
    
    def _simulate_product_details(self, product_link):
        """模拟商品详情（实际应用中应从平台获取）
        
        Args:
            product_link (str): 商品链接
            
        Returns:
            dict: 模拟的商品详情
        """
        import random
        
        product_id = str(uuid.uuid4())
        
        # 生成随机图片URL
        image_urls = [f"https://example.com/img/{uuid.uuid4()}.jpg" for _ in range(random.randint(3, 8))]
        
        # 生成随机描述
        description = f"""
        <div class="product-description">
            <h2>商品详情</h2>
            <p>这是一个示例商品描述，链接为：{product_link}</p>
            <p>商品ID: {product_id}</p>
            <div class="specs">
                <p>规格参数1: 示例值1</p>
                <p>规格参数2: 示例值2</p>
                <p>规格参数3: 示例值3</p>
            </div>
            <div class="usage">
                <h3>使用说明</h3>
                <p>这里是使用说明示例文本</p>
            </div>
        </div>
        """
        
        return {
            'id': product_id,
            'title': f"商品 {product_link[-8:]}",
            'price': round(random.uniform(10, 1000), 2),
            'seller': f"店铺{random.randint(1000, 9999)}",
            'images': image_urls,
            'description': description,
            'specs': {
                '规格参数1': '示例值1',
                '规格参数2': '示例值2',
                '规格参数3': '示例值3'
            }
        }
    
    def detect_poor_products(self, username, data):
        """差品检测功能
        
        Args:
            username (str): 用户名
            data (dict): 检测参数
            
        Returns:
            dict: 检测结果
        """
        try:
            # 获取检测条件
            min_days = data.get('min_days', 7)  # 最少上架天数
            max_sales = data.get('max_sales', 1)  # 最大销量
            max_views = data.get('max_views', 50)  # 最大浏览量
            account_ids = data.get('account_ids', [])  # 指定账号ID
            
            # 构建查询条件
            query = {
                'username': username,
                'created_at': {'$lte': datetime.now() - timedelta(days=min_days)}
            }
            
            if account_ids:
                object_ids = [ObjectId(aid) for aid in account_ids if ObjectId.is_valid(aid)]
                if object_ids:
                    query['account_id'] = {'$in': object_ids}
            
            # 从数据库获取符合条件的商品
            products = list(self.db.products.find(query))
            
            # 筛选差品
            poor_products = []
            for product in products:
                # 获取商品销量和浏览量
                # 实际应用中应从平台获取实时数据
                # 这里使用模拟数据或从数据库获取
                
                sales = self.db.orders.count_documents({
                    'product_id': product['_id']
                })
                
                views = self.db.product_views.count_documents({
                    'product_id': product['_id']
                })
                
                # 判断是否为差品
                if sales <= max_sales and views <= max_views:
                    days_online = (datetime.now() - product['created_at']).days
                    
                    poor_products.append({
                        'id': str(product['_id']),
                        'title': product.get('title', ''),
                        'price': product.get('price', 0),
                        'days_online': days_online,
                        'sales': sales,
                        'views': views,
                        'conversion_rate': round(sales / views, 4) if views > 0 else 0,
                        'account_id': str(product.get('account_id', '')),
                        'score': self._calculate_product_score(days_online, sales, views)
                    })
            
            # 按评分排序（评分越低越差）
            poor_products.sort(key=lambda x: x['score'])
            
            return jsonify({
                'success': True,
                'message': f'检测到 {len(poor_products)} 个差品',
                'poor_products': poor_products
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'差品检测失败: {str(e)}'
            }), 500
    
    def _calculate_product_score(self, days_online, sales, views):
        """计算商品评分
        
        Args:
            days_online (int): 上架天数
            sales (int): 销量
            views (int): 浏览量
            
        Returns:
            float: 商品评分（越高越好）
        """
        # 基础分
        base_score = 50
        
        # 销量加分（每售出一件加10分）
        sales_score = sales * 10
        
        # 浏览量加分（每100次浏览加1分）
        views_score = (views / 100) if views > 0 else 0
        
        # 转化率加分（销量/浏览量 * 1000）
        conversion_score = (sales / views * 1000) if views > 0 else 0
        
        # 上架时间减分（每上架7天减5分）
        time_penalty = (days_online // 7) * 5
        
        # 计算总分
        total_score = base_score + sales_score + views_score + conversion_score - time_penalty
        
        return max(0, total_score)  # 确保分数不为负
    
    def delete_poor_products(self, username, data):
        """删除差品
        
        Args:
            username (str): 用户名
            data (dict): 删除参数
            
        Returns:
            dict: 删除结果
        """
        try:
            # 检查必要字段
            if 'product_ids' not in data:
                return jsonify({
                    'success': False,
                    'message': '缺少必要字段: product_ids'
                }), 400
            
            product_ids = data.get('product_ids', [])
            
            # 转换为ObjectId
            object_ids = []
            for pid in product_ids:
                try:
                    object_ids.append(ObjectId(pid))
                except:
                    pass
            
            if not object_ids:
                return jsonify({
                    'success': False,
                    'message': '无有效的商品ID'
                }), 400
            
            # 删除商品
            result = self.db.products.delete_many({
                '_id': {'$in': object_ids},
                'username': username
            })
            
            deleted_count = result.deleted_count
            
            # 记录删除操作
            self.db.operation_logs.insert_one({
                'username': username,
                'operation': 'delete_poor_products',
                'product_ids': product_ids,
                'deleted_count': deleted_count,
                'timestamp': datetime.now()
            })
            
            return jsonify({
                'success': True,
                'message': f'成功删除 {deleted_count} 个差品',
                'deleted_count': deleted_count
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'删除差品失败: {str(e)}'
            }), 500 