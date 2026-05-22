# bet365cn — 管理员认证 API
from flask import Blueprint, request, jsonify
from models import db, AdminAccount
from auth import check_password, create_token, get_client_ip, ROLE_SUPER_ADMIN, ROLE_ADMIN, ROLE_AGENT
from datetime import datetime

admin_auth_bp = Blueprint('admin_auth', __name__)


@admin_auth_bp.route('/api/admin/auth/login', methods=['POST'])
def login():
    """管理员登录（三级角色）"""
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

    if admin.status == 'disabled':
        return jsonify({'error': '该账号已被封禁'}), 403

    # 更新登录信息
    admin.last_login_at = datetime.utcnow()
    admin.last_login_ip = get_client_ip()
    db.session.commit()

    token = create_token(admin.id, admin.role, is_admin=True)
    return jsonify({
        'token': token,
        'admin': {
            'id': admin.id,
            'username': admin.username,
            'role': admin.role,
            'is_super_admin': admin.role == ROLE_SUPER_ADMIN,
            'is_admin': admin.role == ROLE_ADMIN,
            'is_agent': admin.role == ROLE_AGENT,
            'coin_balance': admin.coin_balance,
            'status': admin.status,
        }
    })
