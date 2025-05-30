#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
import os
import json
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
import uuid
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import time
from modules.product_manager import ProductManager
from modules.order_processor import OrderProcessor
from modules.customer_service import CustomerService
from modules.platform_tasks import PlatformTasks
from modules.content_creator import ContentCreator
from modules.account_manager import AccountManager
from modules.marketing_analyzer import MarketingAnalyzer

# 配置应用
app = Flask(__name__)
CORS(app)

# 配置JWT
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET', 'xianyu-tool-auto-secret-key')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 86400  # 1天过期
jwt = JWTManager(app)

# 配置日志
if not os.path.exists('logs'):
    os.mkdir('logs')
handler = RotatingFileHandler('logs/app.log', maxBytes=10000000, backupCount=10)
handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
handler.setLevel(logging.INFO)
app.logger.addHandler(handler)
app.logger.setLevel(logging.INFO)

# 连接数据库
client = MongoClient('mongodb://localhost:27017/')
db = client['xianyu_tool_auto']

# 初始化各模块
product_manager = ProductManager(db)
order_processor = OrderProcessor(db)
customer_service = CustomerService(db)
platform_tasks = PlatformTasks(db)
content_creator = ContentCreator(db)
account_manager = AccountManager(db)
marketing_analyzer = MarketingAnalyzer(db)

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok', 'timestamp': datetime.now().isoformat()})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    user = db.users.find_one({'username': username})
    
    if not user or not check_password_hash(user['password'], password):
        return jsonify({'success': False, 'message': '用户名或密码错误'}), 401
    
    access_token = create_access_token(identity=username)
    return jsonify({'success': True, 'token': access_token, 'user': {
        'username': user['username'],
        'role': user['role'],
        'id': str(user['_id'])
    }})

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if db.users.find_one({'username': username}):
        return jsonify({'success': False, 'message': '用户名已存在'}), 400
    
    user_id = db.users.insert_one({
        'username': username,
        'password': generate_password_hash(password),
        'role': 'user',
        'created_at': datetime.now()
    }).inserted_id
    
    access_token = create_access_token(identity=username)
    return jsonify({'success': True, 'token': access_token, 'user': {
        'username': username,
        'role': 'user',
        'id': str(user_id)
    }})

# 产品管理API路由
@app.route('/api/products', methods=['GET'])
@jwt_required()
def get_products():
    username = get_jwt_identity()
    return product_manager.get_products(username)

@app.route('/api/products', methods=['POST'])
@jwt_required()
def add_product():
    username = get_jwt_identity()
    data = request.json
    return product_manager.add_product(username, data)

@app.route('/api/products/<product_id>', methods=['PUT'])
@jwt_required()
def update_product(product_id):
    username = get_jwt_identity()
    data = request.json
    return product_manager.update_product(username, product_id, data)

@app.route('/api/products/<product_id>', methods=['DELETE'])
@jwt_required()
def delete_product(product_id):
    username = get_jwt_identity()
    return product_manager.delete_product(username, product_id)

@app.route('/api/products/upload', methods=['POST'])
@jwt_required()
def upload_products():
    username = get_jwt_identity()
    file = request.files['file']
    return product_manager.import_products(username, file)

@app.route('/api/products/batch/publish', methods=['POST'])
@jwt_required()
def batch_publish():
    username = get_jwt_identity()
    data = request.json
    return product_manager.batch_publish(username, data)

@app.route('/api/products/hot', methods=['GET'])
@jwt_required()
def get_hot_products():
    username = get_jwt_identity()
    keywords = request.args.get('keywords')
    return product_manager.get_hot_products(username, keywords)

@app.route('/api/products/hot-collection', methods=['POST'])
@jwt_required()
def collect_hot_products():
    username = get_jwt_identity()
    data = request.json
    return product_manager.collect_hot_products(username, data)

@app.route('/api/products/shop-collection', methods=['POST'])
@jwt_required()
def collect_hot_shop():
    username = get_jwt_identity()
    data = request.json
    return product_manager.collect_hot_shop(username, data)

@app.route('/api/products/download-details', methods=['POST'])
@jwt_required()
def download_details():
    username = get_jwt_identity()
    data = request.json
    return product_manager.download_details(username, data)

@app.route('/api/products/detect-poor', methods=['POST'])
@jwt_required()
def detect_poor_products():
    username = get_jwt_identity()
    data = request.json
    return product_manager.detect_poor_products(username, data)

@app.route('/api/products/delete-poor', methods=['POST'])
@jwt_required()
def delete_poor_products():
    username = get_jwt_identity()
    data = request.json
    return product_manager.delete_poor_products(username, data)

# 订单处理API路由
@app.route('/api/orders', methods=['GET'])
@jwt_required()
def get_orders():
    username = get_jwt_identity()
    return order_processor.get_orders(username)

@app.route('/api/orders/ship', methods=['POST'])
@jwt_required()
def ship_orders():
    username = get_jwt_identity()
    data = request.json
    return order_processor.ship_orders(username, data)

@app.route('/api/orders/qrcode', methods=['POST'])
@jwt_required()
def generate_qrcode():
    username = get_jwt_identity()
    data = request.json
    return order_processor.generate_qrcode(username, data)

# 客户服务API路由
@app.route('/api/messages', methods=['GET'])
@jwt_required()
def get_messages():
    username = get_jwt_identity()
    return customer_service.get_messages(username)

@app.route('/api/messages/reply', methods=['POST'])
@jwt_required()
def reply_message():
    username = get_jwt_identity()
    data = request.json
    return customer_service.reply_message(username, data)

@app.route('/api/templates', methods=['GET'])
@jwt_required()
def get_templates():
    username = get_jwt_identity()
    return customer_service.get_templates(username)

@app.route('/api/templates', methods=['POST'])
@jwt_required()
def add_template():
    username = get_jwt_identity()
    data = request.json
    return customer_service.add_template(username, data)

@app.route('/api/templates/<template_id>', methods=['PUT'])
@jwt_required()
def update_template(template_id):
    username = get_jwt_identity()
    data = request.json
    return customer_service.update_template(username, template_id, data)

@app.route('/api/templates/<template_id>', methods=['DELETE'])
@jwt_required()
def delete_template(template_id):
    username = get_jwt_identity()
    return customer_service.delete_template(username, template_id)

@app.route('/api/messages/<message_id>/suggestions', methods=['GET'])
@jwt_required()
def get_reply_suggestions(message_id):
    username = get_jwt_identity()
    return customer_service.auto_reply_suggestion(username, message_id)

@app.route('/api/titles/optimize', methods=['POST'])
@jwt_required()
def optimize_title():
    username = get_jwt_identity()
    data = request.json
    return customer_service.optimize_title(username, data)

@app.route('/api/keywords/traffic', methods=['POST'])
@jwt_required()
def generate_traffic_keywords():
    username = get_jwt_identity()
    data = request.json
    return customer_service.generate_traffic_keywords(username, data)

@app.route('/api/customers/<buyer_id>/analyze', methods=['GET'])
@jwt_required()
def analyze_customer(buyer_id):
    username = get_jwt_identity()
    return customer_service.analyze_customer(username, buyer_id)

# 平台任务API路由
@app.route('/api/tasks/daily', methods=['POST'])
@jwt_required()
def run_daily_tasks():
    username = get_jwt_identity()
    return platform_tasks.run_daily_tasks(username)

@app.route('/api/tasks/polish', methods=['POST'])
@jwt_required()
def polish_products():
    username = get_jwt_identity()
    data = request.json
    return platform_tasks.polish_products(username, data)

@app.route('/api/tasks/<task_id>', methods=['GET'])
@jwt_required()
def get_task_status(task_id):
    username = get_jwt_identity()
    return platform_tasks.get_task_status(username, task_id)

@app.route('/api/tasks/midnight-polish', methods=['POST'])
@jwt_required()
def schedule_midnight_polish():
    username = get_jwt_identity()
    data = request.json
    return platform_tasks.schedule_midnight_polish(username, data)

@app.route('/api/stats', methods=['GET'])
@jwt_required()
def get_shop_stats():
    username = get_jwt_identity()
    return platform_tasks.get_shop_stats(username)

# 内容创作API路由
@app.route('/api/images/main', methods=['POST'])
@jwt_required()
def create_main_image():
    username = get_jwt_identity()
    if 'image' not in request.files:
        return jsonify({'success': False, 'message': '没有上传图片'}), 400
    file = request.files['image']
    template_id = request.form.get('template_id')
    return content_creator.create_main_image(username, file, template_id)

@app.route('/api/images/watermark', methods=['POST'])
@jwt_required()
def remove_watermark():
    username = get_jwt_identity()
    if 'image' not in request.files:
        return jsonify({'success': False, 'message': '没有上传图片'}), 400
    file = request.files['image']
    return content_creator.remove_watermark(username, file)

@app.route('/api/materials', methods=['GET'])
@jwt_required()
def get_materials():
    username = get_jwt_identity()
    return content_creator.get_materials(username)

@app.route('/api/materials', methods=['POST'])
@jwt_required()
def add_material():
    username = get_jwt_identity()
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': '没有上传文件'}), 400
    file = request.files['file']
    category = request.form.get('category')
    return content_creator.add_material(username, file, category)

@app.route('/api/materials/<material_id>', methods=['DELETE'])
@jwt_required()
def delete_material(material_id):
    username = get_jwt_identity()
    return content_creator.delete_material(username, material_id)

@app.route('/api/materials/<material_id>/used', methods=['PUT'])
@jwt_required()
def mark_material_used(material_id):
    username = get_jwt_identity()
    status = request.json.get('status', True)
    return content_creator.mark_material_used(username, material_id, status)

@app.route('/api/descriptions/generate', methods=['POST'])
@jwt_required()
def generate_description():
    username = get_jwt_identity()
    data = request.json
    return content_creator.generate_description(username, data.get('template_id'), data.get('product_data', {}))

# 账号管理API路由
@app.route('/api/accounts', methods=['GET'])
@jwt_required()
def get_accounts():
    username = get_jwt_identity()
    return account_manager.get_accounts(username)

@app.route('/api/accounts', methods=['POST'])
@jwt_required()
def add_account():
    username = get_jwt_identity()
    data = request.json
    return account_manager.add_account(username, data)

@app.route('/api/accounts/clone', methods=['POST'])
@jwt_required()
def clone_accounts():
    username = get_jwt_identity()
    data = request.json
    return account_manager.clone_accounts(username, data)

@app.route('/api/accounts/<account_id>', methods=['PUT'])
@jwt_required()
def update_account(account_id):
    username = get_jwt_identity()
    data = request.json
    return account_manager.update_account(username, account_id, data)

@app.route('/api/accounts/<account_id>', methods=['DELETE'])
@jwt_required()
def delete_account(account_id):
    username = get_jwt_identity()
    return account_manager.delete_account(username, account_id)

@app.route('/api/accounts/<account_id>/status', methods=['GET'])
@jwt_required()
def check_account_status(account_id):
    username = get_jwt_identity()
    return account_manager.check_account_status(username, account_id)

@app.route('/api/accounts/reset-daily', methods=['POST'])
@jwt_required()
def reset_daily_limit():
    username = get_jwt_identity()
    return account_manager.reset_daily_limit(username)

@app.route('/api/accounts/sync', methods=['POST'])
@jwt_required()
def sync_products():
    username = get_jwt_identity()
    data = request.json
    return account_manager.sync_products(username, data)

@app.route('/api/accounts/publish-queue', methods=['GET'])
@jwt_required()
def get_publish_queue():
    username = get_jwt_identity()
    return account_manager.get_publish_queue(username)

@app.route('/api/accounts/<account_id>/publish-count', methods=['PUT'])
@jwt_required()
def update_publish_count(account_id):
    username = get_jwt_identity()
    count = request.json.get('count', 1)
    return account_manager.update_publish_count(username, account_id, count)

# 营销分析API路由
@app.route('/api/analytics/hot', methods=['GET'])
@jwt_required()
def get_hot_analysis():
    username = get_jwt_identity()
    category = request.args.get('category')
    return marketing_analyzer.get_hot_analysis(username, category)

@app.route('/api/analytics/conversion', methods=['GET'])
@jwt_required()
def get_conversion_analysis():
    username = get_jwt_identity()
    product_id = request.args.get('product_id')
    return marketing_analyzer.get_conversion_analysis(username, product_id)

@app.route('/api/analytics/matrix', methods=['POST'])
@jwt_required()
def generate_matrix_strategy():
    username = get_jwt_identity()
    data = request.json
    return marketing_analyzer.generate_matrix_strategy(username, data)

@app.route('/api/regions', methods=['GET'])
@jwt_required()
def get_available_regions():
    return platform_tasks.get_available_regions()

@app.route('/api/regions/set', methods=['POST'])
@jwt_required()
def set_region():
    username = get_jwt_identity()
    data = request.json
    return platform_tasks.set_region(username, data)

@app.route('/api/regions/<account_id>', methods=['GET'])
@jwt_required()
def get_region(account_id=None):
    username = get_jwt_identity()
    return platform_tasks.get_region(username, account_id)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False) 