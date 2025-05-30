#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import jsonify
from bson.objectid import ObjectId
from datetime import datetime
import os
import uuid
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import requests
from io import BytesIO
import base64
import re
from werkzeug.utils import secure_filename

class ContentCreator:
    """内容创作与素材管理模块"""
    
    def __init__(self, db):
        """初始化内容创作模块"""
        self.db = db
        
        # 创建素材存储目录
        self.materials_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'materials')
        if not os.path.exists(self.materials_dir):
            os.makedirs(self.materials_dir)
            
        # 创建处理后图片存储目录
        self.processed_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'processed')
        if not os.path.exists(self.processed_dir):
            os.makedirs(self.processed_dir)
    
    def create_main_image(self, username, image_file, template_id=None):
        """快速生成商品主图
        
        Args:
            username (str): 用户名
            image_file (FileStorage): 上传的图片文件
            template_id (str, optional): 模板ID
            
        Returns:
            dict: 处理结果
        """
        try:
            # 保存原始图片
            original_filename = secure_filename(image_file.filename)
            file_ext = os.path.splitext(original_filename)[1]
            unique_filename = f"{uuid.uuid4()}{file_ext}"
            original_path = os.path.join(self.materials_dir, unique_filename)
            image_file.save(original_path)
            
            # 获取模板信息
            template = None
            if template_id:
                template = self.db.image_templates.find_one({'_id': ObjectId(template_id)})
            else:
                # 使用默认模板
                template = self.db.image_templates.find_one({'is_default': True})
            
            if not template:
                # 如果没有找到模板，创建一个简单的默认处理
                processed_path = self._apply_default_template(original_path)
            else:
                # 应用选定的模板
                processed_path = self._apply_template(original_path, template)
            
            # 获取处理后的图片URL
            relative_path = os.path.relpath(processed_path, os.path.dirname(os.path.dirname(__file__)))
            image_url = f"/static/{os.path.basename(os.path.dirname(processed_path))}/{os.path.basename(processed_path)}"
            
            # 保存素材记录到数据库
            material_id = self.db.materials.insert_one({
                'username': username,
                'type': 'main_image',
                'original_path': original_path,
                'processed_path': processed_path,
                'image_url': image_url,
                'created_at': datetime.now(),
                'template_id': template_id if template_id else None
            }).inserted_id
            
            return jsonify({
                'success': True,
                'message': '主图生成成功',
                'image_url': image_url,
                'material_id': str(material_id)
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'主图生成失败: {str(e)}'
            }), 500
    
    def _apply_default_template(self, image_path):
        """应用默认模板处理图片
        
        Args:
            image_path (str): 原始图片路径
            
        Returns:
            str: 处理后图片路径
        """
        # 打开原始图片
        img = Image.open(image_path)
        
        # 调整图片大小为标准尺寸
        img = img.resize((800, 800), Image.LANCZOS)
        
        # 增强图片亮度和对比度
        from PIL import ImageEnhance
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(1.1)  # 增加亮度
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.2)  # 增加对比度
        
        # 添加简单边框
        draw = ImageDraw.Draw(img)
        draw.rectangle([(0, 0), (img.width-1, img.height-1)], outline=(255, 255, 255), width=5)
        
        # 保存处理后的图片
        processed_filename = f"main_{uuid.uuid4()}.jpg"
        processed_path = os.path.join(self.processed_dir, processed_filename)
        img.save(processed_path, quality=95)
        
        return processed_path
    
    def _apply_template(self, image_path, template):
        """应用指定模板处理图片
        
        Args:
            image_path (str): 原始图片路径
            template (dict): 模板信息
            
        Returns:
            str: 处理后图片路径
        """
        # 打开原始图片
        img = Image.open(image_path)
        
        # 应用模板配置
        template_config = template.get('config', {})
        
        # 调整图片大小
        size = template_config.get('size', (800, 800))
        img = img.resize(size, Image.LANCZOS)
        
        # 应用滤镜效果
        filter_type = template_config.get('filter', None)
        if filter_type == 'blur':
            img = img.filter(ImageFilter.GaussianBlur(radius=1))
        elif filter_type == 'sharpen':
            img = img.filter(ImageFilter.SHARPEN)
        elif filter_type == 'edge_enhance':
            img = img.filter(ImageFilter.EDGE_ENHANCE)
        
        # 添加水印文字
        watermark = template_config.get('watermark', None)
        if watermark:
            draw = ImageDraw.Draw(img)
            try:
                font = ImageFont.truetype("arial.ttf", 36)
            except:
                font = ImageFont.load_default()
            
            text_position = template_config.get('watermark_position', (20, 20))
            text_color = template_config.get('watermark_color', (255, 255, 255, 128))
            
            draw.text(text_position, watermark, fill=text_color, font=font)
        
        # 添加边框
        border = template_config.get('border', None)
        if border:
            draw = ImageDraw.Draw(img)
            border_width = border.get('width', 5)
            border_color = border.get('color', (255, 255, 255))
            draw.rectangle([(0, 0), (img.width-1, img.height-1)], outline=border_color, width=border_width)
        
        # 保存处理后的图片
        processed_filename = f"main_{uuid.uuid4()}.jpg"
        processed_path = os.path.join(self.processed_dir, processed_filename)
        img.save(processed_path, quality=95)
        
        return processed_path
    
    def remove_watermark(self, username, image_file):
        """去除图片水印
        
        Args:
            username (str): 用户名
            image_file (FileStorage): 上传的图片文件
            
        Returns:
            dict: 处理结果
        """
        try:
            # 保存原始图片
            original_filename = secure_filename(image_file.filename)
            file_ext = os.path.splitext(original_filename)[1]
            unique_filename = f"{uuid.uuid4()}{file_ext}"
            original_path = os.path.join(self.materials_dir, unique_filename)
            image_file.save(original_path)
            
            # 处理图片去水印
            processed_path = self._process_watermark_removal(original_path)
            
            # 获取处理后的图片URL
            relative_path = os.path.relpath(processed_path, os.path.dirname(os.path.dirname(__file__)))
            image_url = f"/static/{os.path.basename(os.path.dirname(processed_path))}/{os.path.basename(processed_path)}"
            
            # 保存素材记录到数据库
            material_id = self.db.materials.insert_one({
                'username': username,
                'type': 'watermark_removed',
                'original_path': original_path,
                'processed_path': processed_path,
                'image_url': image_url,
                'created_at': datetime.now()
            }).inserted_id
            
            return jsonify({
                'success': True,
                'message': '水印去除成功',
                'image_url': image_url,
                'material_id': str(material_id)
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'水印去除失败: {str(e)}'
            }), 500
    
    def _process_watermark_removal(self, image_path):
        """处理图片去水印
        
        Args:
            image_path (str): 原始图片路径
            
        Returns:
            str: 处理后图片路径
        """
        # 使用OpenCV读取图片
        img = cv2.imread(image_path)
        
        # 转换到HSV色彩空间，更容易识别水印
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        
        # 创建掩码，识别可能的水印区域（这里假设水印是浅色的）
        lower_white = np.array([0, 0, 200])
        upper_white = np.array([180, 30, 255])
        mask = cv2.inRange(hsv, lower_white, upper_white)
        
        # 使用形态学操作改进掩码
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        
        # 使用Inpaint算法去除水印
        result = cv2.inpaint(img, mask, 3, cv2.INPAINT_TELEA)
        
        # 保存处理后的图片
        processed_filename = f"nowm_{uuid.uuid4()}.jpg"
        processed_path = os.path.join(self.processed_dir, processed_filename)
        cv2.imwrite(processed_path, result)
        
        return processed_path
    
    def get_materials(self, username):
        """获取用户素材列表
        
        Args:
            username (str): 用户名
            
        Returns:
            dict: 素材列表
        """
        try:
            # 从数据库获取用户素材
            materials = list(self.db.materials.find({
                'username': username
            }).sort('created_at', -1))
            
            # 处理返回结果
            result = []
            for material in materials:
                result.append({
                    'id': str(material['_id']),
                    'type': material['type'],
                    'image_url': material.get('image_url', ''),
                    'created_at': material['created_at'].isoformat(),
                    'used': material.get('used', False)
                })
            
            return jsonify({
                'success': True,
                'materials': result
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'获取素材失败: {str(e)}'
            }), 500
    
    def add_material(self, username, file, category):
        """添加素材到素材库
        
        Args:
            username (str): 用户名
            file (FileStorage): 上传的文件
            category (str): 素材分类
            
        Returns:
            dict: 处理结果
        """
        try:
            # 保存素材文件
            original_filename = secure_filename(file.filename)
            file_ext = os.path.splitext(original_filename)[1]
            unique_filename = f"{uuid.uuid4()}{file_ext}"
            file_path = os.path.join(self.materials_dir, unique_filename)
            file.save(file_path)
            
            # 获取素材URL
            relative_path = os.path.relpath(file_path, os.path.dirname(os.path.dirname(__file__)))
            material_url = f"/static/{os.path.basename(os.path.dirname(file_path))}/{os.path.basename(file_path)}"
            
            # 保存素材记录到数据库
            material_id = self.db.materials.insert_one({
                'username': username,
                'type': 'raw',
                'category': category,
                'file_path': file_path,
                'image_url': material_url,
                'created_at': datetime.now(),
                'used': False
            }).inserted_id
            
            return jsonify({
                'success': True,
                'message': '素材添加成功',
                'material_url': material_url,
                'material_id': str(material_id)
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'素材添加失败: {str(e)}'
            }), 500
    
    def generate_description(self, username, template_id, product_data):
        """生成商品描述
        
        Args:
            username (str): 用户名
            template_id (str): 模板ID
            product_data (dict): 商品数据
            
        Returns:
            dict: 处理结果
        """
        try:
            # 获取描述模板
            template = self.db.templates.find_one({
                '_id': ObjectId(template_id),
                'type': 'description'
            })
            
            if not template:
                return jsonify({
                    'success': False,
                    'message': '描述模板不存在'
                }), 404
            
            # 替换模板中的变量
            description = template['content']
            
            # 替换基本变量
            for key, value in product_data.items():
                placeholder = '{' + key + '}'
                description = description.replace(placeholder, str(value))
            
            # 添加随机变量
            import random
            random_vars = {
                '{random_emoji}': random.choice(['😊', '👍', '🎁', '💯', '⭐', '🔥']),
                '{random_greeting}': random.choice(['亲爱的顾客', '尊敬的买家', '亲', '您好']),
                '{current_date}': datetime.now().strftime('%Y-%m-%d')
            }
            
            for key, value in random_vars.items():
                description = description.replace(key, value)
            
            return jsonify({
                'success': True,
                'description': description
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'生成描述失败: {str(e)}'
            }), 500
    
    def mark_material_used(self, username, material_id, status=True):
        """标记素材使用状态
        
        Args:
            username (str): 用户名
            material_id (str): 素材ID
            status (bool): 使用状态
            
        Returns:
            dict: 处理结果
        """
        try:
            # 更新素材使用状态
            result = self.db.materials.update_one(
                {'_id': ObjectId(material_id), 'username': username},
                {'$set': {'used': status, 'updated_at': datetime.now()}}
            )
            
            if result.matched_count == 0:
                return jsonify({
                    'success': False,
                    'message': '素材不存在或无权限修改'
                }), 404
            
            return jsonify({
                'success': True,
                'message': '素材状态更新成功'
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'更新素材状态失败: {str(e)}'
            }), 500
    
    def delete_material(self, username, material_id):
        """删除素材
        
        Args:
            username (str): 用户名
            material_id (str): 素材ID
            
        Returns:
            dict: 处理结果
        """
        try:
            # 获取素材信息
            material = self.db.materials.find_one({
                '_id': ObjectId(material_id),
                'username': username
            })
            
            if not material:
                return jsonify({
                    'success': False,
                    'message': '素材不存在或无权限删除'
                }), 404
            
            # 删除素材文件
            if 'file_path' in material and os.path.exists(material['file_path']):
                os.remove(material['file_path'])
            
            if 'original_path' in material and os.path.exists(material['original_path']):
                os.remove(material['original_path'])
                
            if 'processed_path' in material and os.path.exists(material['processed_path']):
                os.remove(material['processed_path'])
            
            # 从数据库删除记录
            self.db.materials.delete_one({'_id': ObjectId(material_id)})
            
            return jsonify({
                'success': True,
                'message': '素材删除成功'
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'删除素材失败: {str(e)}'
            }), 500 