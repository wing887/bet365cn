# bet365cn — 管理员认证 API
from flask import Blueprint, request, jsonify
from models import db, AdminAccount
from auth import check_password, create_token, get_client_ip, ROLE_SUPER_ADMIN, ROLE_ADMIN, ROLE_AGENT
from auth import check_login_rate_limit, record_login_failure, clear_login_attempts
from auth import blacklist_token, decode_token
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

    if not check_login_rate_limit(username):
        return jsonify({'error': '登录尝试次数过多，请15分钟后再试'}), 429

    admin = AdminAccount.query.filter_by(username=username).first()
    if not admin:
        record_login_failure(username)
        return jsonify({'error': '账号不存在'}), 401

    result = check_password(password, admin.password_hash)
    if not result:
        record_login_failure(username)
        return jsonify({'error': '密码错误'}), 401

    # 旧 SHA256 密码自动升级为 bcrypt
    if isinstance(result, str):
        admin.password_hash = result
        db.session.commit()

    if admin.status == 'disabled':
        return jsonify({'error': '该账号已被封禁'}), 403

    # 更新登录信息
    admin.last_login_at = datetime.utcnow()
    admin.last_login_ip = get_client_ip()
    clear_login_attempts(username)
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


@admin_auth_bp.route('/api/admin/auth/logout', methods=['POST'])
def logout():
    """管理员登出"""
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header[7:]
        try:
            payload = decode_token(token)
            expires_at = datetime.utcfromtimestamp(payload['exp'])
            blacklist_token(token, expires_at)
        except Exception:
            pass
    return jsonify({'success': True})
