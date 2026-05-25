# bet365cn — 管理员管理 API（超管 + 管理）
from flask import Blueprint, request, jsonify
from models import db, AdminAccount, OperationLog
from auth import (admin_or_above, super_admin_required,
                  hash_password, get_client_ip, can_create_role, can_ban_admin,
                  ROLE_SUPER_ADMIN, ROLE_ADMIN, ROLE_AGENT)

admins_bp = Blueprint('admin_admins', __name__)


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


@admins_bp.route('/api/admin/admins', methods=['GET'])
@admin_or_above
def list_admins():
    """管理员列表（按权限过滤）
    super_admin → 看到全部管理员
    admin → 只能看到 agent
    """
    if request.current_user_role == ROLE_SUPER_ADMIN:
        admins = AdminAccount.query.order_by(AdminAccount.created_at.desc()).all()
    else:
        admins = AdminAccount.query.filter_by(role=ROLE_AGENT).order_by(AdminAccount.created_at.desc()).all()

    return jsonify({'admins': [{
        'id': a.id, 'username': a.username, 'role': a.role,
        'coin_balance': a.coin_balance,
        'status': a.status,
        'last_login_at': a.last_login_at.isoformat() if a.last_login_at else None,
        'last_login_ip': a.last_login_ip,
        'created_at': a.created_at.isoformat() if a.created_at else None,
    } for a in admins]})


@admins_bp.route('/api/admin/admins', methods=['POST'])
@admin_or_above
def create_admin():
    """创建管理员/代理
    super_admin 可创建 admin 或 agent
    admin 只能创建 agent
    """
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    role = data.get('role', ROLE_AGENT).strip()

    if not username or not password:
        return jsonify({'error': '请填写账号和密码'}), 400

    if role not in (ROLE_ADMIN, ROLE_AGENT):
        return jsonify({'error': '角色只能是 admin 或 agent'}), 400

    if not can_create_role(request.current_admin, role):
        return jsonify({'error': f'无权创建 {role} 角色'}), 403

    if AdminAccount.query.filter_by(username=username).first():
        return jsonify({'error': '管理员账号已存在'}), 409

    admin = AdminAccount(
        username=username,
        password_hash=hash_password(password),
        role=role,
        coin_balance=0,
        created_by=request.current_user_id,
    )
    db.session.add(admin)

    _log_action(
        action='创建管理员',
        target_type='admin',
        target_id=admin.id,
        detail={'username': username, 'role': role, 'description': f'创建{role}角色管理员「{username}」'},
    )
    db.session.commit()

    return jsonify({'success': True, 'admin': {'id': admin.id, 'username': username, 'role': role}})


@admins_bp.route('/api/admin/admins/<int:admin_id>', methods=['DELETE'])
@admin_or_above
def delete_admin(admin_id):
    """删除管理员（不可删除超管，不可删除自己）"""
    target = AdminAccount.query.get(admin_id)
    if not target:
        return jsonify({'error': '管理员不存在'}), 404

    if target.role == ROLE_SUPER_ADMIN:
        return jsonify({'error': '不能删除超级管理员'}), 403

    if target.id == request.current_user_id:
        return jsonify({'error': '不能删除自己'}), 403

    # admin 只能删 agent
    if request.current_user_role == ROLE_ADMIN and target.role != ROLE_AGENT:
        return jsonify({'error': '无权删除该管理员'}), 403

    _log_action(
        action='删除管理员',
        target_type='admin',
        target_id=admin_id,
        detail={'username': target.username, 'role': target.role, 'description': f'删除{target.role}角色管理员「{target.username}」'},
    )
    db.session.delete(target)
    db.session.commit()

    return jsonify({'success': True})


@admins_bp.route('/api/admin/admins/<int:admin_id>/ban', methods=['POST'])
@admin_or_above
def toggle_ban(admin_id):
    """封禁/解封管理员"""
    data = request.get_json() or {}
    action = data.get('action', 'ban')  # 'ban' | 'unban'

    target = AdminAccount.query.get(admin_id)
    if not target:
        return jsonify({'error': '管理员不存在'}), 404

    if not can_ban_admin(request.current_admin, target):
        return jsonify({'error': '无权封禁该管理员'}), 403

    if target.id == request.current_user_id:
        return jsonify({'error': '不能封禁自己'}), 403

    if action == 'ban':
        target.status = 'disabled'
    elif action == 'unban':
        target.status = 'active'
    else:
        return jsonify({'error': '无效操作'}), 400

    _log_action(
        action='封禁管理员' if action == 'ban' else '解封管理员',
        target_type='admin',
        target_id=admin_id,
        detail={'username': target.username, 'role': target.role, 'description': f'{"封禁" if action == "ban" else "解封"}{target.role}角色管理员「{target.username}」'},
    )
    db.session.commit()

    return jsonify({'success': True, 'status': target.status})


@admins_bp.route('/api/admin/agents/<int:agent_id>/coins', methods=['POST'])
@admin_or_above
def recharge_agent(agent_id):
    """超管/管理给代理充值/扣余额"""
    data = request.get_json() or {}
    try:
        amount = int(data.get('amount', 0))
    except (ValueError, TypeError):
        return jsonify({'error': '金额无效'}), 400

    if amount == 0:
        return jsonify({'error': '金额不能为0'}), 400

    agent = AdminAccount.query.with_for_update().get(agent_id)
    if not agent:
        return jsonify({'error': '代理不存在'}), 404

    if agent.role != ROLE_AGENT:
        return jsonify({'error': '只能给代理充值'}), 400

    if amount < 0 and agent.coin_balance + amount < 0:
        return jsonify({'error': '扣减后余额不能为负'}), 400

    balance_before = agent.coin_balance
    agent.coin_balance += amount

    _log_action(
        action='代理充值' if amount > 0 else '扣减代理余额',
        target_type='agent',
        target_id=agent_id,
        detail={
            'username': agent.username, 'amount': amount,
            'balance_before': balance_before, 'balance_after': agent.coin_balance,
            'description': f'为代理「{agent.username}」{"充值" if amount > 0 else "扣减"}{abs(amount)}金币，操作前余额{balance_before}，操作后余额{agent.coin_balance}'
        },
    )
    db.session.commit()

    return jsonify({
        'success': True,
        'agent_id': agent_id,
        'new_balance': agent.coin_balance,
        'amount': amount,
    })
