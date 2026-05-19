# bet365cn — 用户认证 API
from flask import Blueprint, request, jsonify
from models import db, UserAccount
from auth import hash_password, check_password, create_token, login_required

user_auth_bp = Blueprint('user_auth', __name__)


@user_auth_bp.route('/api/auth/login', methods=['POST'])
def login():
    """用户登录"""
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not username or not password:
        return jsonify({'error': '请输入账号和密码'}), 400

    user = UserAccount.query.filter_by(username=username).first()
    if not user:
        return jsonify({'error': '账号不存在'}), 401

    if user.status != 'active':
        return jsonify({'error': '账号已被禁用'}), 403

    if not check_password(password, user.password_hash):
        return jsonify({'error': '密码错误'}), 401

    token = create_token(user.id, 'user', is_admin=False)
    return jsonify({
        'token': token,
        'user': {
            'id': user.id,
            'username': user.username,
            'nickname': user.nickname,
            'coin_balance': user.coin_balance,
        }
    })


@user_auth_bp.route('/api/auth/change-password', methods=['POST'])
@login_required
def change_password():
    """修改密码"""
    data = request.get_json() or {}
    old_password = data.get('old_password', '')
    new_password = data.get('new_password', '')

    if not old_password or not new_password:
        return jsonify({'error': '请填写原密码和新密码'}), 400

    if len(new_password) < 4:
        return jsonify({'error': '新密码至少4位'}), 400

    user = UserAccount.query.get(request.current_user_id)
    if not check_password(old_password, user.password_hash):
        return jsonify({'error': '原密码错误'}), 403

    user.password_hash = hash_password(new_password)
    db.session.commit()

    return jsonify({'message': '密码修改成功'})
