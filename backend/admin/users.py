# bet365cn — 用户管理 API（三级管理员）
from flask import Blueprint, request, jsonify
from models import db, UserAccount, CoinTransaction, Bet, OperationLog
from auth import (agent_or_above, can_manage_user, can_view_user,
                  hash_password, get_client_ip,
                  ROLE_SUPER_ADMIN, ROLE_ADMIN, ROLE_AGENT)

users_bp = Blueprint('admin_users', __name__)


def _log_action(action, target_type, target_id, detail):
    """记录操作日志"""
    log = OperationLog(
        admin_id=request.current_user_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        detail=detail,
        ip_address=get_client_ip(),
    )
    db.session.add(log)


def _user_to_dict(u):
    """用户对象转字典"""
    return {
        'id': u.id,
        'username': u.username,
        'nickname': u.nickname,
        'coin_balance': u.coin_balance,
        'status': u.status,
        'last_login_at': u.last_login_at.isoformat() if u.last_login_at else None,
        'created_by_admin_id': u.created_by_admin_id,
        'created_at': u.created_at.isoformat() if u.created_at else None,
    }


@users_bp.route('/api/admin/users', methods=['GET'])
@agent_or_above
def list_users():
    """用户列表（按权限过滤）+ 搜索
    参数: ?q=关键词（搜索 username 或 nickname）
    """
    q = request.args.get('q', '').strip()
    admin = request.current_admin

    query = UserAccount.query

    # 代理只能看自己创建的用户
    if admin.role == ROLE_AGENT:
        query = query.filter_by(created_by_admin_id=admin.id)

    # 搜索
    if q:
        query = query.filter(
            db.or_(
                UserAccount.username.contains(q),
                UserAccount.nickname.contains(q),
            )
        )

    users = query.order_by(UserAccount.created_at.desc()).all()
    return jsonify({'users': [_user_to_dict(u) for u in users]})


@users_bp.route('/api/admin/users', methods=['POST'])
@agent_or_above
def create_user():
    """创建用户（三级管理员均可创建）"""
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    if not username or not password:
        return jsonify({'error': '请填写账号和密码'}), 400

    if UserAccount.query.filter_by(username=username).first():
        return jsonify({'error': '用户名已存在'}), 409

    # 自动生成昵称
    count = UserAccount.query.count()
    nickname = f'用户{count + 1:03d}'

    user = UserAccount(
        username=username,
        password_hash=hash_password(password),
        nickname=nickname,
        coin_balance=0,
        created_by_admin_id=request.current_user_id,
    )
    db.session.add(user)
    _log_action(
        action='创建用户',
        target_type='user',
        target_id=user.id,
        detail={'username': username, 'nickname': nickname, 'description': f'创建用户「{nickname}」(账号: {username})'},
    )
    db.session.commit()

    return jsonify({'success': True, 'user': {'id': user.id, 'username': username, 'nickname': nickname}})


@users_bp.route('/api/admin/users/<int:user_id>', methods=['DELETE'])
@agent_or_above
def delete_user(user_id):
    """删除用户"""
    user = UserAccount.query.get(user_id)
    if not user:
        return jsonify({'error': '用户不存在'}), 404

    if not can_manage_user(request.current_admin, user):
        return jsonify({'error': '无权删除该用户'}), 403

    _log_action(
        action='删除用户',
        target_type='user',
        target_id=user_id,
        detail={'username': user.username, 'nickname': user.nickname, 'description': f'删除用户「{user.nickname}」(账号: {user.username})'},
    )

    # 级联清理关联数据
    CoinTransaction.query.filter_by(user_id=user_id).delete()
    Bet.query.filter_by(user_id=user_id).delete()
    db.session.delete(user)
    db.session.commit()

    return jsonify({'success': True})


@users_bp.route('/api/admin/users/<int:user_id>/ban', methods=['POST'])
@agent_or_above
def toggle_ban(user_id):
    """封禁/解封用户"""
    data = request.get_json() or {}
    action = data.get('action', 'ban')  # 'ban' | 'unban'

    user = UserAccount.query.get(user_id)
    if not user:
        return jsonify({'error': '用户不存在'}), 404

    if not can_manage_user(request.current_admin, user):
        return jsonify({'error': '无权操作该用户'}), 403

    if action == 'ban':
        user.status = 'disabled'
    elif action == 'unban':
        user.status = 'active'
    else:
        return jsonify({'error': '无效操作'}), 400

    _log_action(
        action='封禁用户' if action == 'ban' else '解封用户',
        target_type='user',
        target_id=user_id,
        detail={'username': user.username, 'nickname': user.nickname, 'description': f'{"封禁" if action == "ban" else "解封"}用户「{user.nickname}」(账号: {user.username})'},
    )
    db.session.commit()

    return jsonify({'success': True, 'status': user.status})
