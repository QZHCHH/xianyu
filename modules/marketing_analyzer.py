#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import jsonify
from bson.objectid import ObjectId
from datetime import datetime, timedelta
import os
import uuid
import json
import random
import numpy as np
from collections import Counter

class MarketingAnalyzer:
    """高级营销分析模块"""
    
    def __init__(self, db):
        """初始化营销分析模块"""
        self.db = db
    
    def get_hot_analysis(self, username, category=None):
        """获取热销商品分析
        
        Args:
            username (str): 用户名
            category (str, optional): 商品分类
            
        Returns:
            dict: 热销商品分析结果
        """
        try:
            # 构建查询条件
            query = {}
            if category:
                query['category'] = category
            
            # 获取热销商品数据
            # 实际应用中应从平台API获取实时数据
            # 这里模拟返回结果
            
            # 生成模拟数据
            hot_products = self._generate_hot_products(category, 20)
            
            # 分析热销商品特征
            features = self._analyze_product_features(hot_products)
            
            # 计算关键指标
            avg_price = sum(p['price'] for p in hot_products) / len(hot_products)
            avg_likes = sum(p['likes'] for p in hot_products) / len(hot_products)
            avg_sales = sum(p['sales'] for p in hot_products) / len(hot_products)
            
            # 计算价格区间分布
            price_ranges = {
                '0-50元': 0,
                '50-100元': 0,
                '100-200元': 0,
                '200-500元': 0,
                '500元以上': 0
            }
            
            for p in hot_products:
                price = p['price']
                if price < 50:
                    price_ranges['0-50元'] += 1
                elif price < 100:
                    price_ranges['50-100元'] += 1
                elif price < 200:
                    price_ranges['100-200元'] += 1
                elif price < 500:
                    price_ranges['200-500元'] += 1
                else:
                    price_ranges['500元以上'] += 1
            
            # 构建返回结果
            result = {
                'hot_products': hot_products,
                'features': features,
                'stats': {
                    'avg_price': avg_price,
                    'avg_likes': avg_likes,
                    'avg_sales': avg_sales,
                    'price_ranges': price_ranges
                },
                'category': category,
                'updated_at': datetime.now().isoformat()
            }
            
            return jsonify({
                'success': True,
                'analysis': result
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'获取热销商品分析失败: {str(e)}'
            }), 500
    
    def _generate_hot_products(self, category=None, count=20):
        """生成模拟热销商品数据
        
        Args:
            category (str, optional): 商品分类
            count (int): 商品数量
            
        Returns:
            list: 热销商品列表
        """
        # 定义不同分类的商品标题模板
        title_templates = {
            '数码': [
                '{brand}二手{product}，{condition}成色，{storage}内存，{color}色',
                '{condition}{brand}{product} {storage}G {color}色 {feature}',
                '【{condition}】{brand}{product} {color}色 {storage}G {feature}',
                '{brand}正品{product} {condition}品 {color}色 {feature}'
            ],
            '服装': [
                '{brand}{product} {size}码 {color}色 {condition}',
                '【{brand}】{product} {size}码 {color} {feature}',
                '{condition}{brand}{product} {size}码 {feature}',
                '{brand}正品{product} {size}码 {color} {feature}'
            ],
            '家居': [
                '{brand}{product} {color}色 {size} {condition}',
                '【{brand}】{product} {color} {size} {feature}',
                '{condition}{brand}{product} {size} {feature}',
                '{brand}正品{product} {color} {size} {feature}'
            ],
            '美妆': [
                '{brand}{product} {volume}ml {condition}',
                '【{brand}】{product} {volume}ml {feature}',
                '{condition}{brand}{product} {volume}ml {feature}',
                '{brand}正品{product} {volume}ml {feature}'
            ]
        }
        
        # 定义不同分类的商品属性
        product_attributes = {
            '数码': {
                'brands': ['苹果', '华为', '小米', '三星', 'OPPO', 'vivo'],
                'products': ['手机', '平板', '笔记本', '耳机', '智能手表'],
                'conditions': ['全新', '95新', '9成新', '8成新', '二手'],
                'storages': ['64G', '128G', '256G', '512G', '1T'],
                'colors': ['黑色', '白色', '金色', '银色', '蓝色', '红色'],
                'features': ['无拆修', '配件齐全', '保修期内', '官换机', '国行']
            },
            '服装': {
                'brands': ['优衣库', '耐克', '阿迪达斯', 'H&M', 'ZARA', '无印良品'],
                'products': ['T恤', '卫衣', '牛仔裤', '外套', '连衣裙', '羽绒服'],
                'conditions': ['全新', '9成新', '8成新', '7成新', '有瑕疵'],
                'sizes': ['S', 'M', 'L', 'XL', 'XXL', '均码'],
                'colors': ['黑色', '白色', '蓝色', '灰色', '红色', '粉色'],
                'features': ['标签在', '限量款', '正品保证', '百搭款', '舒适面料']
            },
            '家居': {
                'brands': ['宜家', '无印良品', '欧普', '美的', '海尔', '西门子'],
                'products': ['沙发', '床垫', '餐桌', '衣柜', '台灯', '电视柜'],
                'conditions': ['全新', '9成新', '8成新', '7成新', '有瑕疵'],
                'sizes': ['小号', '中号', '大号', '1.5米', '1.8米', '2米'],
                'colors': ['原木色', '白色', '黑色', '灰色', '棕色', '米色'],
                'features': ['环保材质', '简约风格', '北欧设计', '实木', '多功能']
            },
            '美妆': {
                'brands': ['兰蔻', '雅诗兰黛', '资生堂', '欧莱雅', '香奈儿', '迪奥'],
                'products': ['面霜', '精华液', '口红', '眼霜', '粉底液', '香水'],
                'conditions': ['全新', '9成新', '8成新', '试用装', '小样'],
                'volumes': ['30', '50', '100', '150', '200', '500'],
                'features': ['保湿', '抗老', '美白', '控油', '防晒', '持久']
            }
        }
        
        # 如果没有指定分类，随机选择一个
        if not category or category not in title_templates:
            category = random.choice(list(title_templates.keys()))
        
        # 生成热销商品
        hot_products = []
        for i in range(count):
            # 选择标题模板
            template = random.choice(title_templates[category])
            
            # 选择属性值
            attrs = product_attributes[category]
            brand = random.choice(attrs['brands'])
            product = random.choice(attrs['products'])
            condition = random.choice(attrs['conditions'])
            color = random.choice(attrs['colors'])
            feature = random.choice(attrs['features'])
            
            # 根据分类设置特定属性
            if category == '数码':
                storage = random.choice(attrs['storages'])
                title = template.format(brand=brand, product=product, condition=condition, 
                                      storage=storage, color=color, feature=feature)
                price = random.randint(500, 5000)
            elif category == '服装':
                size = random.choice(attrs['sizes'])
                title = template.format(brand=brand, product=product, condition=condition, 
                                      size=size, color=color, feature=feature)
                price = random.randint(50, 500)
            elif category == '家居':
                size = random.choice(attrs['sizes'])
                title = template.format(brand=brand, product=product, condition=condition, 
                                      size=size, color=color, feature=feature)
                price = random.randint(100, 2000)
            else:  # 美妆
                volume = random.choice(attrs['volumes'])
                title = template.format(brand=brand, product=product, condition=condition, 
                                      volume=volume, feature=feature)
                price = random.randint(100, 1000)
            
            # 生成其他数据
            likes = random.randint(10, 1000)
            sales = random.randint(5, 200)
            conversion_rate = round(random.uniform(0.05, 0.3), 2)
            
            # 添加商品
            hot_products.append({
                'id': str(uuid.uuid4()),
                'title': title,
                'price': price,
                'likes': likes,
                'sales': sales,
                'conversion_rate': conversion_rate,
                'category': category,
                'brand': brand,
                'product': product,
                'condition': condition
            })
        
        # 按销量排序
        hot_products.sort(key=lambda x: x['sales'], reverse=True)
        
        return hot_products
    
    def _analyze_product_features(self, products):
        """分析商品特征
        
        Args:
            products (list): 商品列表
            
        Returns:
            dict: 特征分析结果
        """
        # 提取标题中的关键词
        all_words = []
        for p in products:
            words = p['title'].replace('，', ' ').replace('【', ' ').replace('】', ' ').split()
            all_words.extend(words)
        
        # 统计词频
        word_counts = Counter(all_words)
        top_keywords = word_counts.most_common(10)
        
        # 统计品牌分布
        brands = [p.get('brand', '') for p in products]
        brand_counts = Counter(brands)
        top_brands = brand_counts.most_common(5)
        
        # 统计商品类型分布
        product_types = [p.get('product', '') for p in products]
        product_type_counts = Counter(product_types)
        top_product_types = product_type_counts.most_common(5)
        
        # 统计成色分布
        conditions = [p.get('condition', '') for p in products]
        condition_counts = Counter(conditions)
        condition_distribution = condition_counts.most_common()
        
        # 返回特征分析结果
        return {
            'top_keywords': [{'word': word, 'count': count} for word, count in top_keywords],
            'top_brands': [{'brand': brand, 'count': count} for brand, count in top_brands],
            'top_product_types': [{'type': ptype, 'count': count} for ptype, count in top_product_types],
            'condition_distribution': [{'condition': cond, 'count': count} for cond, count in condition_distribution]
        }
    
    def get_conversion_analysis(self, username, product_id=None):
        """获取转化率分析
        
        Args:
            username (str): 用户名
            product_id (str, optional): 商品ID
            
        Returns:
            dict: 转化率分析结果
        """
        try:
            # 如果指定了商品ID，分析单个商品
            if product_id:
                product = self.db.products.find_one({
                    '_id': ObjectId(product_id),
                    'username': username
                })
                
                if not product:
                    return jsonify({
                        'success': False,
                        'message': '商品不存在或无权限查看'
                    }), 404
                
                # 获取该商品的浏览和订单数据
                views = list(self.db.product_views.find({
                    'product_id': ObjectId(product_id)
                }))
                
                orders = list(self.db.orders.find({
                    'product_id': ObjectId(product_id)
                }))
                
                # 计算转化率指标
                total_views = len(views)
                total_orders = len(orders)
                conversion_rate = total_orders / total_views if total_views > 0 else 0
                
                # 计算平均浏览时间
                view_times = [v.get('duration', 0) for v in views if 'duration' in v]
                avg_view_time = sum(view_times) / len(view_times) if view_times else 0
                
                # 计算平均转化时间（从首次浏览到下单）
                conversion_times = []
                for order in orders:
                    if 'first_view_time' in order and 'created_at' in order:
                        time_diff = (order['created_at'] - order['first_view_time']).total_seconds() / 3600  # 小时
                        conversion_times.append(time_diff)
                
                avg_conversion_time = sum(conversion_times) / len(conversion_times) if conversion_times else 0
                
                # 构建单个商品分析结果
                result = {
                    'product_id': product_id,
                    'title': product.get('title', ''),
                    'price': product.get('price', 0),
                    'stats': {
                        'total_views': total_views,
                        'total_orders': total_orders,
                        'conversion_rate': conversion_rate,
                        'avg_view_time': avg_view_time,
                        'avg_conversion_time': avg_conversion_time
                    },
                    'updated_at': datetime.now().isoformat()
                }
                
                return jsonify({
                    'success': True,
                    'analysis': result
                })
            
            # 否则分析用户所有商品
            else:
                # 获取用户所有商品
                products = list(self.db.products.find({
                    'username': username
                }))
                
                if not products:
                    return jsonify({
                        'success': False,
                        'message': '没有找到商品数据'
                    }), 404
                
                # 生成模拟数据（实际应用中应从数据库获取真实数据）
                product_analysis = []
                for product in products[:20]:  # 限制分析数量
                    # 模拟数据
                    views = random.randint(50, 500)
                    orders = random.randint(1, views // 10)
                    conversion_rate = orders / views if views > 0 else 0
                    avg_view_time = random.uniform(30, 180)  # 秒
                    avg_conversion_time = random.uniform(1, 48)  # 小时
                    
                    product_analysis.append({
                        'product_id': str(product['_id']),
                        'title': product.get('title', ''),
                        'price': product.get('price', 0),
                        'stats': {
                            'total_views': views,
                            'total_orders': orders,
                            'conversion_rate': conversion_rate,
                            'avg_view_time': avg_view_time,
                            'avg_conversion_time': avg_conversion_time
                        }
                    })
                
                # 按转化率排序
                product_analysis.sort(key=lambda x: x['stats']['conversion_rate'], reverse=True)
                
                # 计算整体统计数据
                total_views = sum(p['stats']['total_views'] for p in product_analysis)
                total_orders = sum(p['stats']['total_orders'] for p in product_analysis)
                overall_conversion_rate = total_orders / total_views if total_views > 0 else 0
                
                # 构建整体分析结果
                result = {
                    'product_analysis': product_analysis,
                    'overall_stats': {
                        'total_products': len(product_analysis),
                        'total_views': total_views,
                        'total_orders': total_orders,
                        'overall_conversion_rate': overall_conversion_rate
                    },
                    'updated_at': datetime.now().isoformat()
                }
                
                return jsonify({
                    'success': True,
                    'analysis': result
                })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'获取转化率分析失败: {str(e)}'
            }), 500
    
    def generate_matrix_strategy(self, username, data):
        """生成智能矩阵上架策略
        
        Args:
            username (str): 用户名
            data (dict): 请求数据
            
        Returns:
            dict: 上架策略
        """
        try:
            # 检查必要字段
            if 'product_ids' not in data:
                return jsonify({
                    'success': False,
                    'message': '缺少必要字段: product_ids'
                }), 400
            
            product_ids = data['product_ids']
            
            # 获取商品信息
            products = []
            for pid in product_ids:
                product = self.db.products.find_one({
                    '_id': ObjectId(pid),
                    'username': username
                })
                
                if product:
                    products.append(product)
            
            if not products:
                return jsonify({
                    'success': False,
                    'message': '没有找到有效的商品'
                }), 404
            
            # 生成上架时间策略
            time_strategy = self._generate_time_strategy(len(products))
            
            # 生成地区策略
            region_strategy = self._generate_region_strategy(len(products))
            
            # 生成价格策略
            price_strategy = self._generate_price_strategy(products)
            
            # 分配策略到商品
            matrix_plan = []
            for i, product in enumerate(products):
                # 获取该商品的策略
                time_slot = time_strategy[i % len(time_strategy)]
                region = region_strategy[i % len(region_strategy)]
                price_adjustment = price_strategy.get(str(product['_id']), 0)
                
                # 计算调整后价格
                original_price = product.get('price', 0)
                adjusted_price = round(original_price * (1 + price_adjustment), 2)
                
                # 添加到计划
                matrix_plan.append({
                    'product_id': str(product['_id']),
                    'title': product.get('title', ''),
                    'original_price': original_price,
                    'adjusted_price': adjusted_price,
                    'price_adjustment': f"{price_adjustment * 100:+.1f}%",
                    'publish_time': time_slot['time'],
                    'time_reason': time_slot['reason'],
                    'region': region['region'],
                    'region_name': region['name'],
                    'region_reason': region['reason']
                })
            
            # 构建返回结果
            result = {
                'matrix_plan': matrix_plan,
                'time_strategy': time_strategy,
                'region_strategy': region_strategy,
                'price_strategy': [
                    {'adjustment': f"{adj * 100:+.1f}%", 'reason': reason}
                    for adj, reason in [
                        (0, '保持原价'),
                        (0.05, '小幅提价，测试价格弹性'),
                        (-0.05, '小幅降价，提高转化率'),
                        (0.1, '中幅提价，提高利润'),
                        (-0.1, '中幅降价，促进销售')
                    ]
                ],
                'updated_at': datetime.now().isoformat()
            }
            
            return jsonify({
                'success': True,
                'strategy': result
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'生成矩阵策略失败: {str(e)}'
            }), 500
    
    def _generate_time_strategy(self, count):
        """生成上架时间策略
        
        Args:
            count (int): 商品数量
            
        Returns:
            list: 时间策略列表
        """
        # 定义高流量时间段
        time_slots = [
            {'time': '07:30-08:30', 'reason': '早晨上班前高峰期，用户活跃度高'},
            {'time': '12:00-13:00', 'reason': '午休时间，用户浏览量大'},
            {'time': '18:00-19:00', 'reason': '下班高峰期，用户活跃度高'},
            {'time': '20:00-21:00', 'reason': '晚间黄金时段，用户购买意愿强'},
            {'time': '21:30-22:30', 'reason': '睡前浏览高峰，用户决策时间充足'},
            {'time': '10:00-11:00', 'reason': '上午工作间隙，浏览量适中'},
            {'time': '15:00-16:00', 'reason': '下午茶时间，用户注意力较为集中'},
            {'time': '22:30-23:30', 'reason': '深夜时段，竞争较少'}
        ]
        
        # 如果商品数量少于时间段数量，选择最佳时间段
        if count <= len(time_slots):
            return time_slots[:count]
        
        # 否则重复使用时间段
        return time_slots
    
    def _generate_region_strategy(self, count):
        """生成地区策略
        
        Args:
            count (int): 商品数量
            
        Returns:
            list: 地区策略列表
        """
        # 定义地区策略
        regions = [
            {'region': 'beijing', 'name': '北京', 'reason': '一线城市，消费能力强，适合高价值商品'},
            {'region': 'shanghai', 'name': '上海', 'reason': '一线城市，时尚消费中心，适合品牌商品'},
            {'region': 'guangzhou', 'name': '广州', 'reason': '南方消费中心，商品流通活跃'},
            {'region': 'shenzhen', 'name': '深圳', 'reason': '科技消费中心，适合数码产品'},
            {'region': 'hangzhou', 'name': '杭州', 'reason': '电商消费活跃，网购氛围浓厚'},
            {'region': 'random', 'name': '随机', 'reason': '系统随机分配，覆盖更广泛的市场'}
        ]
        
        # 如果商品数量少于地区数量，选择主要地区
        if count <= len(regions):
            return regions[:count]
        
        # 否则重复使用地区
        return regions
    
    def _generate_price_strategy(self, products):
        """生成价格策略
        
        Args:
            products (list): 商品列表
            
        Returns:
            dict: 价格策略
        """
        # 定义价格调整选项
        adjustments = [0, 0.05, -0.05, 0.1, -0.1]
        
        # 为每个商品随机分配价格调整
        price_strategy = {}
        for product in products:
            adjustment = random.choice(adjustments)
            price_strategy[str(product['_id'])] = adjustment
        
        return price_strategy 