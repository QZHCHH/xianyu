#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pymongo import MongoClient, ASCENDING
from werkzeug.security import generate_password_hash
from datetime import datetime
import os

def init_db():
    """初始化数据库，创建集合和索引，添加初始数据"""
    print("正在初始化数据库...")
    
    # 连接数据库
    client = MongoClient('mongodb://localhost:27017/')
    db = client['xianyu_tool']
    
    # 创建用户集合
    if 'users' not in db.list_collection_names():
        print("创建用户集合...")
        db.create_collection('users')
        db.users.create_index([('username', ASCENDING)], unique=True)
        
        # 添加默认管理员账号
        admin_user = {
            'username': 'admin',
            'password': generate_password_hash('admin123'),
            'role': 'admin',
            'created_at': datetime.now()
        }
        db.users.insert_one(admin_user)
        print("已创建默认管理员账号")
    
    # 创建商品集合
    if 'products' not in db.list_collection_names():
        print("创建商品集合...")
        db.create_collection('products')
        db.products.create_index([('username', ASCENDING)])
        db.products.create_index([('status', ASCENDING)])
        db.products.create_index([('created_at', ASCENDING)])
    
    # 创建订单集合
    if 'orders' not in db.list_collection_names():
        print("创建订单集合...")
        db.create_collection('orders')
        db.orders.create_index([('username', ASCENDING)])
        db.orders.create_index([('account_id', ASCENDING)])
        db.orders.create_index([('order_id', ASCENDING)], unique=True)
        db.orders.create_index([('created_at', ASCENDING)])
    
    # 创建账号集合
    if 'accounts' not in db.list_collection_names():
        print("创建账号集合...")
        db.create_collection('accounts')
        db.accounts.create_index([('username', ASCENDING)])
    
    # 创建模板集合
    if 'templates' not in db.list_collection_names():
        print("创建模板集合...")
        db.create_collection('templates')
        db.templates.create_index([('username', ASCENDING)])
        db.templates.create_index([('type', ASCENDING)])
        
        # 添加默认回复模板
        default_templates = [
            {
                'username': 'admin',
                'type': 'reply',
                'name': '商品价格咨询',
                'content': '您好，该商品的价格是¥{price}，目前处于促销阶段，欢迎下单',
                'created_at': datetime.now()
            },
            {
                'username': 'admin',
                'type': 'reply',
                'name': '商品库存咨询',
                'content': '您好，该商品目前有货，可以直接下单，我们会尽快安排发货',
                'created_at': datetime.now()
            },
            {
                'username': 'admin',
                'type': 'reply',
                'name': '商品质量咨询',
                'content': '您好，我们的商品都经过严格质检，请您放心购买，支持收货后七天内无理由退换',
                'created_at': datetime.now()
            },
            {
                'username': 'admin',
                'type': 'description',
                'name': '基础描述模板',
                'content': '商品名称：{title}\n价格：{price}元\n商品状态：全新\n发货方式：包邮\n支付方式：支持咸鱼担保交易\n欢迎咨询！',
                'created_at': datetime.now()
            }
        ]
        db.templates.insert_many(default_templates)
        print("已创建默认模板数据")
    
    # 创建任务历史集合
    if 'publish_tasks' not in db.list_collection_names():
        print("创建发布任务集合...")
        db.create_collection('publish_tasks')
        db.publish_tasks.create_index([('username', ASCENDING)])
        db.publish_tasks.create_index([('created_at', ASCENDING)])
    
    if 'shipping_tasks' not in db.list_collection_names():
        print("创建发货任务集合...")
        db.create_collection('shipping_tasks')
        db.shipping_tasks.create_index([('username', ASCENDING)])
        db.shipping_tasks.create_index([('created_at', ASCENDING)])
    
    # 创建素材集合
    if 'materials' not in db.list_collection_names():
        print("创建素材集合...")
        db.create_collection('materials')
        db.materials.create_index([('username', ASCENDING)])
        db.materials.create_index([('type', ASCENDING)])
        db.materials.create_index([('created_at', ASCENDING)])
    
    # 创建分析数据集合
    if 'analytics' not in db.list_collection_names():
        print("创建分析数据集合...")
        db.create_collection('analytics')
        db.analytics.create_index([('username', ASCENDING)])
        db.analytics.create_index([('type', ASCENDING)])
        db.analytics.create_index([('created_at', ASCENDING)])
    
    print("数据库初始化完成")

if __name__ == "__main__":
    init_db() 