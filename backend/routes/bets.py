# bet365cn — 下注 API
from flask import Blueprint, request, jsonify
from models import db, Match, Odds, Bet, CoinTransaction, BetLimit
from auth import login_required
from datetime import datetime

bets_bp = Blueprint('bets', __name__)


@bets_bp.route('/api/bets', methods=['POST'])
@login_required
def place_bet():
    """下注"""
    data = request.get_json() or {}
    user_id = request.current_user_id

    match_id = data.get('match_id')
    market_type = data.get('market_type')  # ML / Spread / Totals / CS
    selection = data.get('selection')      # home/draw/away | over/under | "2-1"
    bet_amount = data.get('bet_amount', 0)

    # 校验参数
    if not match_id or not market_type or not selection:
        return jsonify({'error': '参数不完整'}), 400

    try:
        bet_amount = int(bet_amount)
    except (ValueError, TypeError):
        return jsonify({'error': '下注金额无效'}), 400

    if bet_amount < 50:
        return jsonify({'error': '最低下注50金币'}), 400

    # 检查最大投注限额
    limit = BetLimit.query.filter_by(market_type=market_type).first()
    if limit and bet_amount > limit.max_bet_amount:
        return jsonify({
            'error': f'{market_type}最大投注{limit.max_bet_amount}金币'
        }), 400

    # 查比赛
    match = Match.query.get(match_id)
    if not match:
        return jsonify({'error': '比赛不存在'}), 404

    if match.status != 'pending':
        return jsonify({'error': '比赛已开始或已结束，无法下注'}), 400

    # 查赔率
    odds = Odds.query.filter_by(
        match_id=match_id, bookmaker='Bet365', market_type=market_type
    ).first()

    if not odds:
        return jsonify({'error': '该玩法暂无赔率'}), 400

    # 检查盘口是否被封
    if odds.status == 'suspended':
        return jsonify({'error': '该盘口暂时封盘，请稍后再试'}), 400
    if odds.status == 'closed':
        return jsonify({'error': '该盘口已关闭'}), 400

    # 检查赔率是否过期（超过10分钟未更新）
    from datetime import timedelta
    if odds.updated_at:
        age = datetime.utcnow() - odds.updated_at
        if age > timedelta(minutes=10):
            return jsonify({'error': '赔率已过期，请刷新后重试'}), 400

    # 计算实际赔率
    odds_value = _get_odds_value(market_type, selection, odds.odds_data)
    if odds_value <= 0:
        return jsonify({'error': '无效的投注选项'}), 400

    # 查用户余额（加行锁）
    from models import UserAccount
    user = UserAccount.query.with_for_update().get(user_id)
    if not user or user.status != 'active':
        return jsonify({'error': '账号异常'}), 403

    if user.coin_balance < bet_amount:
        return jsonify({'error': '金币不足'}), 400

    potential_win = round(bet_amount * odds_value)

    # 事务：扣金币 + 创建下注 + 记录流水
    try:
        user.coin_balance -= bet_amount

        bet = Bet(
            user_id=user_id,
            match_id=match_id,
            market_type=market_type,
            selection=selection,
            odds_value=odds_value,
            bet_amount=bet_amount,
            potential_win=potential_win,
            status='pending',
        )
        db.session.add(bet)
        db.session.flush()  # 获取 bet.id

        tx = CoinTransaction(
            user_id=user_id,
            amount=-bet_amount,
            type='bet_place',
            bet_id=bet.id,
            note=f"下注: {match.home_team} vs {match.away_team}",
        )
        db.session.add(tx)
        db.session.commit()

        return jsonify({
            'success': True,
            'bet': {
                'id': bet.id,
                'match_id': match_id,
                'market_type': market_type,
                'selection': selection,
                'odds_value': odds_value,
                'bet_amount': bet_amount,
                'potential_win': potential_win,
                'status': 'pending',
            },
            'balance': user.coin_balance,
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'下注失败: {str(e)}'}), 500


@bets_bp.route('/api/bets', methods=['GET'])
@login_required
def list_bets():
    """我的下注历史"""
    user_id = request.current_user_id
    status = request.args.get('status')  # pending/won/lost/all

    query = Bet.query.filter_by(user_id=user_id)

    if status and status != 'all':
        query = query.filter_by(status=status)

    bets = query.order_by(Bet.placed_at.desc()).limit(50).all()

    result = []
    for b in bets:
        match = Match.query.get(b.match_id)
        result.append({
            'id': b.id,
            'match_id': b.match_id,
            'match_home': match.home_team if match else '?',
            'match_away': match.away_team if match else '?',
            'league_name': match.league_name if match else '',
            'market_type': b.market_type,
            'selection': b.selection,
            'odds_value': b.odds_value,
            'bet_amount': b.bet_amount,
            'potential_win': b.potential_win,
            'status': b.status,
            'win_amount': b.win_amount,
            'placed_at': b.placed_at.isoformat() if b.placed_at else None,
            'settled_at': b.settled_at.isoformat() if b.settled_at else None,
        })

    return jsonify({'bets': result})


@bets_bp.route('/api/bets/limits', methods=['GET'])
@login_required
def get_bet_limits_public():
    """读取各盘口最大投注额（普通用户可见）"""
    limits = BetLimit.query.all()
    result = {}
    for l in limits:
        result[l.market_type.lower()] = l.max_bet_amount
    return jsonify({'limits': result})


def _get_odds_value(market_type, selection, odds_data):
    """从 odds_data JSON 中获取指定选项的赔率"""
    if market_type == 'ML':
        return float(odds_data.get(selection, 0))
    elif market_type in ('Spread', 'Totals'):
        # 嵌套结构: {"home": {"line": -0.5, "odds": 1.95}, "away": {"line": 0.5, "odds": 1.85}}
        #          {"over": {"line": 2.5, "odds": 2.00}, "under": {"line": 2.5, "odds": 1.80}}
        entry = odds_data.get(selection)
        if isinstance(entry, dict):
            return float(entry.get('odds', 0))
        return float(entry or 0)
    elif market_type == 'CS':
        scores = odds_data.get('scores', [])
        for s in scores:
            if s.get('label') == selection:
                return float(s.get('odds', 0))
    return 0
