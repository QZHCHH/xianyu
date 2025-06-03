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
from modules.user_logger import UserLogger
from modules.auth_manager import AuthManager

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

# 初始化用户日志模块
user_logger = UserLogger(db)

# 初始化权限管理模块
auth_manager = AuthManager(db, user_logger)

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
    
    # 获取客户端IP
    ip_address = request.remote_addr
    if request.headers.get('X-Forwarded-For'):
        ip_address = request.headers.get('X-Forwarded-For').split(',')[0].strip()
    
    # 使用权限管理模块进行登录
    login_result = auth_manager.login(username, password, ip_address)
    
    if not login_result['success']:
        return jsonify(login_result), 401
    
    # 生成JWT令牌
    access_token = create_access_token(identity=username)
    
    # 返回用户信息和令牌
    return jsonify({
        'success': True,
        'token': access_token,
        'user': login_result['user']
    })

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')
    
    # 使用权限管理模块进行注册
    register_result = auth_manager.register(username, password, email)
    
    if not register_result['success']:
        return jsonify(register_result), 400
    
    # 生成JWT令牌
    access_token = create_access_token(identity=username)
    
    # 返回用户信息和令牌
    return jsonify({
        'success': True,
        'token': access_token,
        'user': {
            'username': username,
            'role': 'user',
            'id': register_result['user_id'],
            'permissions': auth_manager.get_permissions('user')
        }
    })

@app.route('/api/password/change', methods=['POST'])
@jwt_required()
def change_password():
    username = get_jwt_identity()
    data = request.json
    old_password = data.get('old_password')
    new_password = data.get('new_password')
    
    # 使用权限管理模块修改密码
    result = auth_manager.change_password(username, old_password, new_password)
    
    if not result['success']:
        return jsonify(result), 400
        
    return jsonify(result)

@app.route('/api/users/role', methods=['PUT'])
@jwt_required()
def update_user_role():
    admin_username = get_jwt_identity()
    data = request.json
    target_username = data.get('username')
    new_role = data.get('role')
    
    # 使用权限管理模块更新用户角色
    result = auth_manager.update_user_role(admin_username, target_username, new_role)
    
    if not result['success']:
        return jsonify(result), 403
        
    return jsonify(result)

@app.route('/api/logs', methods=['GET'])
@jwt_required()
def get_user_logs():
    username = get_jwt_identity()
    
    # 检查权限
    if not auth_manager.has_permission(username, 'log_view'):
        return jsonify({
            'success': False,
            'message': '权限不足'
        }), 403
    
    # 获取查询参数
    target_username = request.args.get('username')
    action_type = request.args.get('action_type')
    target_type = request.args.get('target_type')
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    limit = int(request.args.get('limit', 100))
    skip = int(request.args.get('skip', 0))
    
    # 转换日期
    start_date = None
    end_date = None
    
    if start_date_str:
        try:
            start_date = datetime.fromisoformat(start_date_str)
        except ValueError:
            pass
            
    if end_date_str:
        try:
            end_date = datetime.fromisoformat(end_date_str)
        except ValueError:
            pass
    
    # 获取日志
    logs = user_logger.get_audit_logs(
        username, target_username, action_type,
        start_date, end_date, limit, skip
    )
    
    return jsonify({
        'success': True,
        'logs': logs
    })

# 产品管理API路由
@app.route('/api/products', methods=['GET'])
@jwt_required()
def get_products():
    username = get_jwt_identity()
    
    # 记录日志
    user_logger.log_action(username, 'view', 'products')
    
    return product_manager.get_products(username)

@app.route('/api/products', methods=['POST'])
@jwt_required()
def add_product():
    username = get_jwt_identity()
    data = request.json
    
    # 检查权限
    if not auth_manager.has_permission(username, 'product_edit'):
        return jsonify({
            'success': False,
            'message': '权限不足'
        }), 403
    
    result = product_manager.add_product(username, data)
    
    # 记录日志
    response_data = json.loads(result.get_data(as_text=True))
    if response_data.get('success'):
        user_logger.log_action(
            username, 'add', 'product',
            target_id=response_data.get('product_id'),
            details={'title': data.get('title')}
        )
    
    return result

@app.route('/api/products/<product_id>', methods=['PUT'])
@jwt_required()
def update_product(product_id):
    username = get_jwt_identity()
    data = request.json
    
    # 检查权限
    if not auth_manager.has_permission(username, 'product_edit'):
        return jsonify({
            'success': False,
            'message': '权限不足'
        }), 403
    
    result = product_manager.update_product(username, product_id, data)
    
    # 记录日志
    response_data = json.loads(result.get_data(as_text=True))
    if response_data.get('success'):
        user_logger.log_action(
            username, 'update', 'product',
            target_id=product_id,
            details={'title': data.get('title')}
        )
    
    return result

@app.route('/api/products/<product_id>', methods=['DELETE'])
@jwt_required()
def delete_product(product_id):
    username = get_jwt_identity()
    
    # 检查权限
    if not auth_manager.has_permission(username, 'product_edit'):
        return jsonify({
            'success': False,
            'message': '权限不足'
        }), 403
    
    # 获取商品信息用于日志记录
    product = db.products.find_one({'_id': uuid.UUID(product_id)})
    product_title = product.get('title') if product else None
    
    result = product_manager.delete_product(username, product_id)
    
    # 记录日志
    response_data = json.loads(result.get_data(as_text=True))
    if response_data.get('success'):
        user_logger.log_action(
            username, 'delete', 'product',
            target_id=product_id,
            details={'title': product_title}
        )
    
    return result

@app.route('/api/products/upload', methods=['POST'])
@jwt_required()
def upload_products():
    username = get_jwt_identity()
    
    # 检查权限
    if not auth_manager.has_permission(username, 'product_edit'):
        return jsonify({
            'success': False,
            'message': '权限不足'
        }), 403
    
    file = request.files['file']
    result = product_manager.import_products(username, file)
    
    # 记录日志
    response_data = json.loads(result.get_data(as_text=True))
    if response_data.get('success'):
        user_logger.log_action(
            username, 'import', 'products',
            details={'count': response_data.get('count'), 'filename': file.filename}
        )
    
    return result

@app.route('/api/products/batch/publish', methods=['POST'])
@jwt_required()
def batch_publish():
    username = get_jwt_identity()
    
    # 检查权限
    if not auth_manager.has_permission(username, 'product_edit'):
        return jsonify({
            'success': False,
            'message': '权限不足'
        }), 403
    
    data = request.json
    result = product_manager.batch_publish(username, data)
    
    # 记录日志
    response_data = json.loads(result.get_data(as_text=True))
    if response_data.get('success'):
        user_logger.log_action(
            username, 'publish', 'products',
            details={'count': len(data.get('product_ids', []))}
        )
    
    return result

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

# 添加用户管理路由
@app.route('/api/users', methods=['GET'])
@jwt_required()
def get_users():
    username = get_jwt_identity()
    
    # 检查权限
    if not auth_manager.has_permission(username, 'user_manage'):
        return jsonify({
            'success': False,
            'message': '权限不足'
        }), 403
    
    # 获取查询参数
    role = request.args.get('role')
    status = request.args.get('status')
    
    # 构建查询条件
    query = {}
    if role:
        query['role'] = role
    if status:
        query['status'] = status
    
    # 执行查询
    users = list(db.users.find(query, {'password': 0}))
    
    # 处理ObjectId
    for user in users:
        user['_id'] = str(user['_id'])
    
    # 记录日志
    user_logger.log_action(
        username, 'view', 'users',
        details={'count': len(users)}
    )
    
    return jsonify({
        'success': True,
        'users': users
    })

@app.route('/api/users/<user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    username = get_jwt_identity()
    
    # 检查权限
    if not auth_manager.has_permission(username, 'user_manage') and username != user_id:
        return jsonify({
            'success': False,
            'message': '权限不足'
        }), 403
    
    # 查询用户
    user = db.users.find_one({'_id': uuid.UUID(user_id)}, {'password': 0})
    
    if not user:
        return jsonify({
            'success': False,
            'message': '用户不存在'
        }), 404
    
    # 处理ObjectId
    user['_id'] = str(user['_id'])
    
    # 记录日志
    user_logger.log_action(
        username, 'view', 'user',
        target_id=user_id
    )
    
    return jsonify({
        'success': True,
        'user': user
    })

@app.route('/api/users/<user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    username = get_jwt_identity()
    
    # 检查权限
    if not auth_manager.has_permission(username, 'user_manage') and username != user_id:
        return jsonify({
            'success': False,
            'message': '权限不足'
        }), 403
    
    data = request.json
    
    # 不允许普通用户修改自己的角色
    if username == user_id and 'role' in data and not auth_manager.has_permission(username, 'user_manage'):
        return jsonify({
            'success': False,
            'message': '权限不足，无法修改角色'
        }), 403
    
    # 更新用户信息
    update_data = {
        'updated_at': datetime.now()
    }
    
    allowed_fields = ['email', 'status']
    if auth_manager.has_permission(username, 'user_manage'):
        allowed_fields.extend(['role'])
    
    for field in allowed_fields:
        if field in data:
            update_data[field] = data[field]
    
    db.users.update_one(
        {'_id': uuid.UUID(user_id)},
        {'$set': update_data}
    )
    
    # 记录日志
    user_logger.log_action(
        username, 'update', 'user',
        target_id=user_id,
        details=update_data
    )
    
    return jsonify({
        'success': True,
        'message': '用户信息更新成功'
    })

@app.route('/api/users/<user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    username = get_jwt_identity()
    
    # 检查权限
    if not auth_manager.has_permission(username, 'user_manage'):
        return jsonify({
            'success': False,
            'message': '权限不足'
        }), 403
    
    # 不允许删除自己
    if username == user_id:
        return jsonify({
            'success': False,
            'message': '不能删除自己的账号'
        }), 400
    
    # 获取用户信息用于日志记录
    user = db.users.find_one({'_id': uuid.UUID(user_id)})
    if not user:
        return jsonify({
            'success': False,
            'message': '用户不存在'
        }), 404
    
    # 删除用户
    db.users.delete_one({'_id': uuid.UUID(user_id)})
    
    # 记录日志
    user_logger.log_action(
        username, 'delete', 'user',
        target_id=user_id,
        details={'deleted_username': user.get('username')}
    )
    
    return jsonify({
        'success': True,
        'message': '用户删除成功'
    })

@app.route('/api/users/permissions', methods=['GET'])
@jwt_required()
def get_user_permissions():
    username = get_jwt_identity()
    
    # 获取用户角色
    user = db.users.find_one({'username': username})
    if not user:
        return jsonify({
            'success': False,
            'message': '用户不存在'
        }), 404
    
    # 获取权限列表
    permissions = auth_manager.get_permissions(user['role'])
    
    return jsonify({
        'success': True,
        'role': user['role'],
        'permissions': permissions
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True) 