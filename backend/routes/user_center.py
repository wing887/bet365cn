# bet365cn — 用户中心 API
from flask import Blueprint, request, jsonify
from models import db, CoinTransaction, UserAccount
from auth import login_required

user_center_bp = Blueprint('user_center', __name__)


@user_center_bp.route('/api/transactions', methods=['GET'])
@login_required
def list_transactions():
    """金币流水"""
    user_id = request.current_user_id
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    query = CoinTransaction.query.filter_by(user_id=user_id)
    total = query.count()
    txs = query.order_by(CoinTransaction.created_at.desc())               .offset((page - 1) * per_page).limit(per_page).all()

    return jsonify({
        'transactions': [{
            'id': tx.id,
            'amount': tx.amount,
            'type': tx.type,
            'note': tx.note,
            'created_at': tx.created_at.isoformat() if tx.created_at else None,
        } for tx in txs],
        'total': total,
        'page': page,
        'per_page': per_page,
    })


@user_center_bp.route('/api/profile', methods=['GET'])
@login_required
def profile():
    """个人信息"""
    user = UserAccount.query.get(request.current_user_id)
    if not user:
        return jsonify({'error': '用户不存在'}), 404

    return jsonify({
        'id': user.id,
        'username': user.username,
        'nickname': user.nickname,
        'coin_balance': user.coin_balance,
        'status': user.status,
        'created_at': user.created_at.isoformat() if user.created_at else None,
    })
