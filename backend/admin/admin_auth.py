# bet365cn — 管理员认证 API
from flask import Blueprint, request, jsonify
from models import db, AdminAccount
from auth import check_password, create_token

admin_auth_bp = Blueprint('admin_auth', __name__)


@admin_auth_bp.route('/api/admin/auth/login', methods=['POST'])
def login():
    """管理员登录"""
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not username or not password:
        return jsonify({'error': '请输入账号和密码'}), 400

    admin = AdminAccount.query.filter_by(username=username).first()
    if not admin:
        return jsonify({'error': '账号不存在'}), 401

    if not check_password(password, admin.password_hash):
        return jsonify({'error': '密码错误'}), 401

    token = create_token(admin.id, admin.role, is_admin=True)
    return jsonify({
        'token': token,
        'admin': {
            'id': admin.id,
            'username': admin.username,
            'role': admin.role,
            'is_super_admin': admin.role == 'super_admin',
        }
    })
