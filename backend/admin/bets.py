# bet365cn — 下注记录管理 API（仅超管，测试用）
from flask import Blueprint, request, jsonify
from models import db, Bet, Match, UserAccount, CoinTransaction, OperationLog
from auth import super_admin_required, get_client_ip
from datetime import datetime

bets_bp = Blueprint('admin_bets', __name__)

VALID_MARKET_TYPES = ['ML', 'Spread', 'Totals', 'CS']


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


@bets_bp.route('/api/admin/bets', methods=['POST'])
@super_admin_required
def create_bet():
    """手动创建下注记录（测试用，不扣用户余额）"""
    data = request.get_json() or {}

    user_id = data.get('user_id')
    match_id = data.get('match_id')
    market_type = data.get('market_type')
    selection = data.get('selection')
    bet_amount = data.get('bet_amount')
    odds_value = data.get('odds_value')
    status = data.get('status', 'pending')

    if not user_id or not match_id or not market_type or not selection or not bet_amount:
        return jsonify({'error': '参数不完整（需要 user_id, match_id, market_type, selection, bet_amount）'}), 400

    if market_type not in VALID_MARKET_TYPES:
        return jsonify({'error': f'无效的盘口类型: {market_type}'}), 400

    if status not in ('pending', 'won', 'lost', 'push', 'refunded'):
        return jsonify({'error': '状态必须是 pending/won/lost/push/refunded'}), 400

    try:
        bet_amount = int(bet_amount)
    except (ValueError, TypeError):
        return jsonify({'error': 'bet_amount 必须是整数'}), 400

    if odds_value is not None:
        try:
            odds_value = float(odds_value)
        except (ValueError, TypeError):
            return jsonify({'error': 'odds_value 必须是数字'}), 400
    else:
        return jsonify({'error': '请提供 odds_value'}), 400

    # 检查用户
    user = UserAccount.query.get(user_id)
    if not user:
        return jsonify({'error': '用户不存在'}), 404

    # 检查比赛
    match = Match.query.get(match_id)
    if not match:
        return jsonify({'error': '比赛不存在'}), 404

    potential_win = round(bet_amount * odds_value)
    win_amount = data.get('win_amount', 0)

    # 如果状态是 won/lost/push/refunded，自动设置 settled_at
    settled_at = None
    if status in ('won', 'lost', 'push', 'refunded'):
        settled_at = datetime.utcnow()
        if status == 'won' and not data.get('win_amount'):
            win_amount = potential_win
        elif status == 'push':
            win_amount = bet_amount

    bet = Bet(
        user_id=user_id,
        match_id=match_id,
        market_type=market_type,
        selection=selection,
        odds_value=odds_value,
        bet_amount=bet_amount,
        potential_win=potential_win,
        status=status,
        win_amount=win_amount,
        settled_at=settled_at,
    )
    db.session.add(bet)
    db.session.flush()

    # 如果是 won/push 状态，自动创建流水记录
    if status == 'won' and win_amount > 0:
        balance_before = user.coin_balance
        user.coin_balance += win_amount
        db.session.add(CoinTransaction(
            user_id=user_id,
            amount=win_amount,
            balance_before=balance_before,
            balance_after=user.coin_balance,
            type='bet_win',
            bet_id=bet.id,
            note=f"中奖: {match.home_team} vs {match.away_team}",
        ))
    elif status == 'push':
        balance_before = user.coin_balance
        user.coin_balance += bet_amount
        db.session.add(CoinTransaction(
            user_id=user_id,
            amount=bet_amount,
            balance_before=balance_before,
            balance_after=user.coin_balance,
            type='bet_refund',
            bet_id=bet.id,
            note=f"退款(走水): {match.home_team} vs {match.away_team}",
        ))

    _log_action(
        action='手动创建下注',
        target_type='bet',
        target_id=bet.id,
        detail={
            'user_id': user_id,
            'match_id': match_id,
            'market_type': market_type,
            'selection': selection,
            'bet_amount': bet_amount,
            'odds_value': odds_value,
            'status': status,
            'description': f'手动创建 {user.username} 对 {match.home_team} vs {match.away_team} 的 {market_type}/{selection} 下注，{bet_amount}金币，状态 {status}',
        },
    )
    db.session.commit()

    return jsonify({
        'success': True,
        'bet': {
            'id': bet.id,
            'user_id': bet.user_id,
            'match_id': bet.match_id,
            'market_type': bet.market_type,
            'selection': bet.selection,
            'odds_value': bet.odds_value,
            'bet_amount': bet.bet_amount,
            'potential_win': bet.potential_win,
            'status': bet.status,
            'win_amount': bet.win_amount,
            'placed_at': bet.placed_at.isoformat() + '+00:00' if bet.placed_at else None,
            'settled_at': bet.settled_at.isoformat() + '+00:00' if bet.settled_at else None,
        }
    }), 201
