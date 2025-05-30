#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import jsonify
from bson.objectid import ObjectId
from datetime import datetime
import os
import uuid
import re
import random
import jieba
import jieba.analyse

class CustomerService:
    """客户服务自动化模块"""
    
    def __init__(self, db):
        """初始化客户服务模块"""
        self.db = db
        
        # 加载自定义词典
        self.load_custom_dict()
    
    def load_custom_dict(self):
        """加载自定义词典"""
        try:
            # 加载常用电商词汇
            custom_dict_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'ecommerce_dict.txt')
            if os.path.exists(custom_dict_path):
                jieba.load_userdict(custom_dict_path)
        except Exception as e:
            print(f"加载自定义词典失败: {str(e)}")
    
    def get_messages(self, username):
        """获取用户消息列表
        
        Args:
            username (str): 用户名
            
        Returns:
            dict: 消息列表
        """
        try:
            # 从数据库获取用户消息
            messages = list(self.db.messages.find({
                'username': username
            }).sort('created_at', -1).limit(100))
            
            # 处理返回结果
            result = []
            for message in messages:
                result.append({
                    'id': str(message['_id']),
                    'buyer_id': message.get('buyer_id', ''),
                    'buyer_name': message.get('buyer_name', '未知用户'),
                    'content': message.get('content', ''),
                    'product_id': str(message['product_id']) if 'product_id' in message else None,
                    'product_title': message.get('product_title', ''),
                    'is_replied': message.get('is_replied', False),
                    'reply_content': message.get('reply_content', ''),
                    'created_at': message['created_at'].isoformat(),
                    'replied_at': message.get('replied_at', '').isoformat() if message.get('replied_at') else None
                })
            
            return jsonify({
                'success': True,
                'messages': result
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'获取消息失败: {str(e)}'
            }), 500
    
    def reply_message(self, username, data):
        """回复消息
        
        Args:
            username (str): 用户名
            data (dict): 回复数据
            
        Returns:
            dict: 处理结果
        """
        try:
            # 检查必要字段
            if 'message_id' not in data or 'content' not in data:
                return jsonify({
                    'success': False,
                    'message': '缺少必要字段: message_id 或 content'
                }), 400
            
            message_id = data['message_id']
            content = data['content']
            
            # 检查消息是否存在
            message = self.db.messages.find_one({
                '_id': ObjectId(message_id),
                'username': username
            })
            
            if not message:
                return jsonify({
                    'success': False,
                    'message': '消息不存在或无权限回复'
                }), 404
            
            # 更新消息状态
            self.db.messages.update_one(
                {'_id': ObjectId(message_id)},
                {
                    '$set': {
                        'is_replied': True,
                        'reply_content': content,
                        'replied_at': datetime.now(),
                        'updated_at': datetime.now()
                    }
                }
            )
            
            # 这里可以添加实际发送回复的逻辑
            # 由于需要浏览器自动化操作，这里只更新数据库状态
            
            return jsonify({
                'success': True,
                'message': '回复成功'
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'回复消息失败: {str(e)}'
            }), 500
    
    def get_templates(self, username):
        """获取回复模板列表
        
        Args:
            username (str): 用户名
            
        Returns:
            dict: 模板列表
        """
        try:
            # 从数据库获取用户模板
            templates = list(self.db.templates.find({
                '$or': [
                    {'username': username},
                    {'username': 'admin'}  # 包含系统默认模板
                ]
            }).sort('created_at', -1))
            
            # 处理返回结果
            result = []
            for template in templates:
                result.append({
                    'id': str(template['_id']),
                    'name': template['name'],
                    'type': template['type'],
                    'content': template['content'],
                    'is_system': template.get('username') == 'admin',
                    'created_at': template['created_at'].isoformat()
                })
            
            return jsonify({
                'success': True,
                'templates': result
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'获取模板失败: {str(e)}'
            }), 500
    
    def add_template(self, username, data):
        """添加回复模板
        
        Args:
            username (str): 用户名
            data (dict): 模板数据
            
        Returns:
            dict: 处理结果
        """
        try:
            # 检查必要字段
            required_fields = ['name', 'type', 'content']
            for field in required_fields:
                if field not in data:
                    return jsonify({
                        'success': False,
                        'message': f'缺少必要字段: {field}'
                    }), 400
            
            # 检查模板类型
            allowed_types = ['reply', 'description']
            if data['type'] not in allowed_types:
                return jsonify({
                    'success': False,
                    'message': f'无效的模板类型，允许的类型: {", ".join(allowed_types)}'
                }), 400
            
            # 准备模板数据
            template_data = {
                'username': username,
                'name': data['name'],
                'type': data['type'],
                'content': data['content'],
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
            
            # 保存到数据库
            template_id = self.db.templates.insert_one(template_data).inserted_id
            
            return jsonify({
                'success': True,
                'message': '模板添加成功',
                'template_id': str(template_id)
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'添加模板失败: {str(e)}'
            }), 500
    
    def update_template(self, username, template_id, data):
        """更新回复模板
        
        Args:
            username (str): 用户名
            template_id (str): 模板ID
            data (dict): 更新数据
            
        Returns:
            dict: 处理结果
        """
        try:
            # 检查模板是否存在
            template = self.db.templates.find_one({
                '_id': ObjectId(template_id),
                'username': username
            })
            
            if not template:
                return jsonify({
                    'success': False,
                    'message': '模板不存在或无权限修改'
                }), 404
            
            # 准备更新数据
            update_data = {
                'updated_at': datetime.now()
            }
            
            # 可更新字段
            allowed_fields = ['name', 'content']
            for field in allowed_fields:
                if field in data:
                    update_data[field] = data[field]
            
            # 更新数据库
            self.db.templates.update_one(
                {'_id': ObjectId(template_id)},
                {'$set': update_data}
            )
            
            return jsonify({
                'success': True,
                'message': '模板更新成功'
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'更新模板失败: {str(e)}'
            }), 500
    
    def delete_template(self, username, template_id):
        """删除回复模板
        
        Args:
            username (str): 用户名
            template_id (str): 模板ID
            
        Returns:
            dict: 处理结果
        """
        try:
            # 检查模板是否存在
            template = self.db.templates.find_one({
                '_id': ObjectId(template_id),
                'username': username
            })
            
            if not template:
                return jsonify({
                    'success': False,
                    'message': '模板不存在或无权限删除'
                }), 404
            
            # 删除模板
            self.db.templates.delete_one({'_id': ObjectId(template_id)})
            
            return jsonify({
                'success': True,
                'message': '模板删除成功'
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'删除模板失败: {str(e)}'
            }), 500
    
    def auto_reply_suggestion(self, username, message_id):
        """获取自动回复建议
        
        Args:
            username (str): 用户名
            message_id (str): 消息ID
            
        Returns:
            dict: 回复建议
        """
        try:
            # 获取消息内容
            message = self.db.messages.find_one({
                '_id': ObjectId(message_id),
                'username': username
            })
            
            if not message:
                return jsonify({
                    'success': False,
                    'message': '消息不存在或无权限查看'
                }), 404
            
            # 提取消息关键词
            content = message.get('content', '')
            keywords = jieba.analyse.extract_tags(content, topK=5)
            
            # 根据关键词匹配模板
            templates = list(self.db.templates.find({
                '$or': [
                    {'username': username},
                    {'username': 'admin'}
                ],
                'type': 'reply'
            }))
            
            # 计算模板匹配度
            matched_templates = []
            for template in templates:
                # 计算关键词匹配度
                template_content = template.get('content', '')
                match_count = sum(1 for keyword in keywords if keyword in template_content)
                
                if match_count > 0:
                    matched_templates.append({
                        'id': str(template['_id']),
                        'name': template['name'],
                        'content': template['content'],
                        'match_score': match_count
                    })
            
            # 按匹配度排序
            matched_templates.sort(key=lambda x: x['match_score'], reverse=True)
            
            # 如果没有匹配的模板，返回默认模板
            if not matched_templates:
                default_templates = list(self.db.templates.find({
                    'username': 'admin',
                    'type': 'reply'
                }).limit(3))
                
                matched_templates = [{
                    'id': str(template['_id']),
                    'name': template['name'],
                    'content': template['content'],
                    'match_score': 0
                } for template in default_templates]
            
            # 替换模板中的变量
            product_info = {}
            if 'product_id' in message:
                product = self.db.products.find_one({'_id': ObjectId(message['product_id'])})
                if product:
                    product_info = {
                        'title': product.get('title', ''),
                        'price': product.get('price', 0),
                        'description': product.get('description', '')
                    }
            
            for template in matched_templates:
                content = template['content']
                for key, value in product_info.items():
                    placeholder = '{' + key + '}'
                    content = content.replace(placeholder, str(value))
                
                # 替换买家名称
                buyer_name = message.get('buyer_name', '亲')
                content = content.replace('{buyer_name}', buyer_name)
                
                template['content'] = content
            
            return jsonify({
                'success': True,
                'suggestions': matched_templates[:3]  # 返回匹配度最高的3个模板
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'获取回复建议失败: {str(e)}'
            }), 500
    
    def optimize_title(self, username, data):
        """优化商品标题
        
        Args:
            username (str): 用户名
            data (dict): 标题数据
            
        Returns:
            dict: 优化结果
        """
        try:
            # 检查必要字段
            if 'original_title' not in data:
                return jsonify({
                    'success': False,
                    'message': '缺少必要字段: original_title'
                }), 400
            
            original_title = data['original_title']
            category = data.get('category', '')
            
            # 获取热门关键词
            hot_keywords = self._get_hot_keywords(category)
            
            # 分析原标题
            words = list(jieba.cut(original_title))
            
            # 优化标题
            optimized_titles = []
            
            # 方法1: 添加热门关键词
            title1 = original_title
            added_keywords = []
            for keyword in hot_keywords:
                if keyword not in original_title and len(title1) + len(keyword) <= 30:
                    title1 += f" {keyword}"
                    added_keywords.append(keyword)
                    if len(added_keywords) >= 2:
                        break
            
            optimized_titles.append({
                'title': title1,
                'method': '添加热门关键词',
                'changes': f"添加了关键词: {', '.join(added_keywords)}"
            })
            
            # 方法2: 调整词语顺序
            if len(words) >= 4:
                random.shuffle(words)
                title2 = ' '.join(words)
                optimized_titles.append({
                    'title': title2,
                    'method': '调整词语顺序',
                    'changes': '重新排序了标题中的词语'
                })
            
            # 方法3: 替换同义词
            title3 = original_title
            synonym_map = {
                '便宜': '优惠',
                '特价': '低价',
                '包邮': '免运费',
                '全新': '未使用',
                '二手': '闲置',
                '正品': '官方',
                '热销': '畅销'
            }
            
            replaced = []
            for old, new in synonym_map.items():
                if old in title3:
                    title3 = title3.replace(old, new)
                    replaced.append(f"{old}→{new}")
            
            if replaced:
                optimized_titles.append({
                    'title': title3,
                    'method': '替换同义词',
                    'changes': f"替换了: {', '.join(replaced)}"
                })
            
            return jsonify({
                'success': True,
                'original_title': original_title,
                'optimized_titles': optimized_titles
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'优化标题失败: {str(e)}'
            }), 500
    
    def _get_hot_keywords(self, category=''):
        """获取热门关键词
        
        Args:
            category (str): 商品分类
            
        Returns:
            list: 热门关键词列表
        """
        # 这里应该从数据库或API获取实时热门关键词
        # 为简化实现，这里返回预设的关键词
        general_keywords = ['正品', '包邮', '特价', '热销', '全新', '官方', '限时', '促销']
        
        category_keywords = {
            '数码': ['原装', '二手', '保修', '配件齐全', '无拆无修'],
            '服装': ['潮流', '时尚', '百搭', '舒适', '高品质'],
            '家居': ['实用', '美观', '环保', '耐用', '简约'],
            '美妆': ['正品保证', '效果好', '温和', '天然', '持久'],
            '图书': ['全新', '珍藏版', '经典', '畅销', '绝版'],
            '玩具': ['益智', '安全', '趣味', '收藏', '限量'],
            '食品': ['美味', '营养', '健康', '新鲜', '进口']
        }
        
        result = general_keywords.copy()
        if category in category_keywords:
            result.extend(category_keywords[category])
        
        random.shuffle(result)
        return result
    
    def generate_traffic_keywords(self, username, data):
        """生成流量密码关键词
        
        Args:
            username (str): 用户名
            data (dict): 请求数据
            
        Returns:
            dict: 关键词结果
        """
        try:
            # 检查必要字段
            if 'title' not in data:
                return jsonify({
                    'success': False,
                    'message': '缺少必要字段: title'
                }), 400
            
            title = data['title']
            category = data.get('category', '')
            
            # 分析标题关键词
            keywords = jieba.analyse.extract_tags(title, topK=5)
            
            # 获取长尾关键词
            long_tail_keywords = self._get_long_tail_keywords(keywords, category)
            
            # 获取热门搜索词
            hot_searches = self._get_hot_searches(category)
            
            # 生成SEO优化建议
            seo_suggestions = []
            
            # 建议1: 添加长尾关键词
            seo_suggestions.append({
                'type': '添加长尾关键词',
                'keywords': long_tail_keywords[:5],
                'reason': '长尾关键词可以精准匹配用户搜索意图，提高转化率'
            })
            
            # 建议2: 添加热门搜索词
            seo_suggestions.append({
                'type': '添加热门搜索词',
                'keywords': hot_searches[:5],
                'reason': '热门搜索词可以提高曝光率，增加流量'
            })
            
            # 建议3: 优化标题结构
            title_structure = [
                '品牌词 + 核心词 + 属性词',
                '核心词 + 品牌词 + 卖点',
                '属性词 + 核心词 + 用途词',
                '核心词 + 属性词 + 热门词'
            ]
            
            seo_suggestions.append({
                'type': '优化标题结构',
                'suggestions': title_structure,
                'reason': '合理的标题结构可以提高用户点击率和搜索匹配度'
            })
            
            return jsonify({
                'success': True,
                'title': title,
                'extracted_keywords': keywords,
                'long_tail_keywords': long_tail_keywords,
                'hot_searches': hot_searches,
                'seo_suggestions': seo_suggestions
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'生成流量密码失败: {str(e)}'
            }), 500
    
    def _get_long_tail_keywords(self, keywords, category=''):
        """获取长尾关键词
        
        Args:
            keywords (list): 核心关键词列表
            category (str): 商品分类
            
        Returns:
            list: 长尾关键词列表
        """
        # 这里应该从数据库或API获取实时长尾关键词
        # 为简化实现，这里返回预设的关键词组合
        
        suffixes = ['哪个好', '推荐', '怎么样', '多少钱', '价格', '评测', '排行榜', '正品', '便宜', '质量好']
        prefixes = ['高品质', '正品', '热销', '限时', '特价', '全新', '二手', '闲置', '精选', '优质']
        
        result = []
        for keyword in keywords:
            # 添加前缀
            for prefix in random.sample(prefixes, 2):
                result.append(f"{prefix}{keyword}")
            
            # 添加后缀
            for suffix in random.sample(suffixes, 2):
                result.append(f"{keyword}{suffix}")
        
        random.shuffle(result)
        return result
    
    def _get_hot_searches(self, category=''):
        """获取热门搜索词
        
        Args:
            category (str): 商品分类
            
        Returns:
            list: 热门搜索词列表
        """
        # 这里应该从数据库或API获取实时热门搜索词
        # 为简化实现，这里返回预设的热门搜索词
        
        general_hot_searches = [
            '正品保障', '二手闲置', '全新未拆', '限时特价',
            '包邮到家', '质量保证', '七天无理由退换', '官方授权',
            '急速发货', '超值优惠', '稀缺货源', '热销爆款'
        ]
        
        category_hot_searches = {
            '数码': ['苹果二手', '华为正品', '小米新品', '二手笔记本', '游戏主机', '无线耳机', '平板电脑'],
            '服装': ['春季新款', '时尚百搭', '潮牌折扣', '明星同款', '高品质', '舒适面料', '简约风格'],
            '家居': ['北欧风格', '简约现代', '实木家具', '收纳神器', '厨房用品', '卧室装饰', '智能家居'],
            '美妆': ['正品彩妆', '护肤套装', '大牌香水', '口红套装', '面膜精选', '防晒必备', '美妆工具'],
            '图书': ['畅销小说', '经典名著', '儿童绘本', '考试教材', '进口原版', '限量珍藏', '有声读物'],
            '玩具': ['积木拼装', '益智玩具', '毛绒公仔', '模型手办', '儿童玩具', '收藏玩具', '动漫周边'],
            '食品': ['零食大礼包', '进口食品', '营养早餐', '健康零食', '休闲小吃', '地方特产', '网红美食']
        }
        
        result = general_hot_searches.copy()
        if category in category_hot_searches:
            result.extend(category_hot_searches[category])
        
        random.shuffle(result)
        return result
    
    def analyze_customer(self, username, buyer_id):
        """分析客户行为数据
        
        Args:
            username (str): 用户名
            buyer_id (str): 买家ID
            
        Returns:
            dict: 客户分析结果
        """
        try:
            # 获取该买家的所有消息
            messages = list(self.db.messages.find({
                'username': username,
                'buyer_id': buyer_id
            }).sort('created_at', -1))
            
            # 获取该买家的所有订单
            orders = list(self.db.orders.find({
                'username': username,
                'buyer_id': buyer_id
            }).sort('created_at', -1))
            
            # 分析数据
            total_messages = len(messages)
            total_orders = len(orders)
            
            # 计算回复率
            replied_messages = sum(1 for m in messages if m.get('is_replied', False))
            reply_rate = replied_messages / total_messages if total_messages > 0 else 0
            
            # 计算转化率
            conversion_rate = total_orders / total_messages if total_messages > 0 else 0
            
            # 计算平均回复时间
            reply_times = []
            for m in messages:
                if m.get('is_replied', False) and m.get('replied_at') and m.get('created_at'):
                    reply_time = (m['replied_at'] - m['created_at']).total_seconds() / 60  # 分钟
                    reply_times.append(reply_time)
            
            avg_reply_time = sum(reply_times) / len(reply_times) if reply_times else 0
            
            # 获取最近的消息和订单
            recent_messages = [{
                'id': str(m['_id']),
                'content': m.get('content', ''),
                'created_at': m['created_at'].isoformat(),
                'is_replied': m.get('is_replied', False)
            } for m in messages[:5]]
            
            recent_orders = [{
                'id': str(o['_id']),
                'order_id': o.get('order_id', ''),
                'title': o.get('title', ''),
                'price': o.get('price', 0),
                'status': o.get('status', ''),
                'created_at': o['created_at'].isoformat()
            } for o in orders[:5]]
            
            # 获取买家信息
            buyer_info = {
                'buyer_id': buyer_id,
                'buyer_name': messages[0].get('buyer_name', '未知用户') if messages else '未知用户',
                'first_contact': messages[-1]['created_at'].isoformat() if messages else None,
                'last_contact': messages[0]['created_at'].isoformat() if messages else None,
                'total_messages': total_messages,
                'total_orders': total_orders,
                'reply_rate': reply_rate,
                'conversion_rate': conversion_rate,
                'avg_reply_time': avg_reply_time,
                'recent_messages': recent_messages,
                'recent_orders': recent_orders
            }
            
            return jsonify({
                'success': True,
                'buyer_info': buyer_info
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'分析客户数据失败: {str(e)}'
            }), 500 