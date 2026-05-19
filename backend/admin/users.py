# bet365cn — 用户管理 API
from flask import Blueprint, request, jsonify
from models import db, UserAccount, OperationLog
from auth import admin_required, hash_password
from datetime import datetime

users_bp = Blueprint('admin_users', __name__)


@users_bp.route('/api/admin/users', methods=['GET'])
@admin_required
def list_users():
    """用户列表"""
    users = UserAccount.query.order_by(UserAccount.created_at.desc()).all()
    return jsonify({'users': [{
        'id': u.id, 'username': u.username, 'nickname': u.nickname,
        'coin_balance': u.coin_balance, 'status': u.status,
        'created_at': u.created_at.isoformat() if u.created_at else None,
    } for u in users]})


@users_bp.route('/api/admin/users', methods=['POST'])
@admin_required
def create_user():
    """创建用户"""
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    if not username or not password:
        return jsonify({'error': '请填写账号和密码'}), 400

    if UserAccount.query.filter_by(username=username).first():
        return jsonify({'error': '用户名已存在'}), 409

    # 自动生成昵称
    count = UserAccount.query.count()
    nickname = f'用户{count+1:03d}'

    user = UserAccount(
        username=username,
        password_hash=hash_password(password),
        nickname=nickname,
        coin_balance=0,
    )
    db.session.add(user)
    _log(request, '创建用户', 'user', user.id, {'username': username, 'nickname': nickname})
    db.session.commit()

    return jsonify({'success': True, 'user': {'id': user.id, 'username': username, 'nickname': nickname}})


@users_bp.route('/api/admin/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    """删除用户"""
    user = UserAccount.query.get(user_id)
    if not user:
        return jsonify({'error': '用户不存在'}), 404

    _log(request, '删除用户', 'user', user_id, {'username': user.username})
    # 先清理关联数据（操作日志已在 delete_user 中处理）
    from models import Bet, CoinTransaction
    CoinTransaction.query.filter_by(user_id=user_id).delete()
    Bet.query.filter_by(user_id=user_id).delete()
    
    db.session.delete(user)
    db.session.commit()

    return jsonify({'success': True})


def _log(request, action, target_type, target_id, detail):
    """记录操作日志"""
    log = OperationLog(
        admin_id=request.current_user_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        detail=detail,
    )
    db.session.add(log)
