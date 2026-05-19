# bet365cn — 金币操作 API
from flask import Blueprint, request, jsonify
from models import db, UserAccount, CoinTransaction, OperationLog
from auth import admin_required

coins_bp = Blueprint('admin_coins', __name__)


@coins_bp.route('/api/admin/users/<int:user_id>/coins', methods=['POST'])
@admin_required
def modify_coins(user_id):
    """增减用户金币"""
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

    if amount < 0 and user.coin_balance + amount < 0:
        return jsonify({'error': '扣减后余额不能为负'}), 400

    try:
        user.coin_balance += amount

        tx = CoinTransaction(
            user_id=user_id,
            amount=amount,
            type='admin_add' if amount > 0 else 'admin_deduct',
            operator_id=request.current_user_id,
            note=f"管理员{'充值' if amount > 0 else '扣减'} {abs(amount)} 金币",
        )
        db.session.add(tx)

        log = OperationLog(
            admin_id=request.current_user_id,
            action='金币操作',
            target_type='user',
            target_id=user_id,
            detail={'amount': amount, 'new_balance': user.coin_balance},
        )
        db.session.add(log)
        db.session.commit()

        return jsonify({
            'success': True,
            'user_id': user_id,
            'new_balance': user.coin_balance,
            'amount': amount,
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
