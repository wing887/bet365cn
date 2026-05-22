# bet365cn — 金币操作 API（三级管理员 + 代理金币池）
from flask import Blueprint, request, jsonify
from models import db, UserAccount, CoinTransaction, OperationLog
from auth import (agent_or_above, can_modify_coins, get_client_ip,
                  ROLE_SUPER_ADMIN, ROLE_ADMIN, ROLE_AGENT)

coins_bp = Blueprint('admin_coins', __name__)


def _log_action(action, target_type, target_id, detail):
    log = OperationLog(
        admin_id=request.current_user_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        detail=detail,
        ip_address=get_client_ip(),
    )
    db.session.add(log)


@coins_bp.route('/api/admin/users/<int:user_id>/coins', methods=['POST'])
@agent_or_above
def modify_coins(user_id):
    """增减用户金币
    
    super_admin: +/- 任何人（直接操作用户余额）
    admin: +/- 代理创建的用户
    agent: 只能 + 自己创建的用户（从代理余额扣除）
    """
    data = request.get_json() or {}
    try:
        amount = int(data.get('amount', 0))
    except (ValueError, TypeError):
        return jsonify({'error': '金额无效'}), 400

    if amount == 0:
        return jsonify({'error': '金额不能为0'}), 400

    user = UserAccount.query.with_for_update().get(user_id)
    if not user:
        return jsonify({'error': '用户不存在'}), 404

    admin = request.current_admin
    allowed, error_msg = can_modify_coins(admin, user, amount)
    if not allowed:
        return jsonify({'error': error_msg}), 403

    if amount < 0 and user.coin_balance + amount < 0:
        return jsonify({'error': '扣减后余额不能为负'}), 400

    try:
        balance_before = user.coin_balance
        user.coin_balance += amount
        balance_after = user.coin_balance

        tx = CoinTransaction(
            user_id=user_id,
            amount=amount,
            balance_before=balance_before,
            balance_after=balance_after,
            type='admin_add' if amount > 0 else 'admin_deduct',
            operator_id=admin.id,
            note=f"管理员{'充值' if amount > 0 else '扣减'} {abs(amount)} 金币",
        )
        db.session.add(tx)

        # 代理：扣减自己的余额
        if admin.role == ROLE_AGENT and amount > 0:
            admin.coin_balance -= amount

        _log_action(
            action='金币操作',
            target_type='user',
            target_id=user_id,
            detail={
                'amount': amount,
                'balance_before': balance_before,
                'balance_after': balance_after,
                'username': user.username,
            },
        )
        db.session.commit()

        return jsonify({
            'success': True,
            'user_id': user_id,
            'new_balance': balance_after,
            'amount': amount,
            'agent_balance': admin.coin_balance if admin.role == ROLE_AGENT else None,
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
