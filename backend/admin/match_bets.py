# bet365cn — 下注核对 API（按用户查比赛下注明细）
from flask import Blueprint, request, jsonify
from models import db, UserAccount, Bet, Match
from auth import agent_or_above, ROLE_SUPER_ADMIN, ROLE_ADMIN, ROLE_AGENT
from datetime import datetime

match_bets_bp = Blueprint('admin_match_bets', __name__)


def _bet_to_dict(b):
    """下注对象转字典"""
    return {
        'id': b.id,
        'market_type': b.market_type,
        'selection': b.selection,
        'odds_value': b.odds_value,
        'bet_amount': b.bet_amount,
        'potential_win': b.potential_win,
        'status': b.status,
        'win_amount': b.win_amount,
        'placed_at': b.placed_at.isoformat() if b.placed_at else None,
    }


@match_bets_bp.route('/api/admin/users/<int:user_id>/match-bets', methods=['GET'])
@agent_or_above
def user_match_bets(user_id):
    """查询指定用户的比赛下注明细（按比赛分组）

    可选参数:
      ?period_start=YYYY-MM-DD   # 下注时间起始（默认本月1日）
      ?period_end=YYYY-MM-DD     # 下注时间截止（默认今天）
      ?status=won|lost|push|pending  # 下注状态筛选
      ?market_type=ML|Spread|Totals|CS  # 盘口筛选

    返回:
      user: 用户信息
      summary: 汇总（总注数/场次数/流水/赢/输/走水）
      matches: [{ match信息, bets[], match_summary }]
    """
    admin = request.current_admin

    # 查找用户 + 权限检查
    user = UserAccount.query.get(user_id)
    if not user:
        return jsonify({'error': '用户不存在'}), 404

    if admin.role == ROLE_AGENT:
        if user.created_by_admin_id != admin.id:
            return jsonify({'error': '无权查看该用户'}), 403

    # 解析查询参数
    period_start_str = request.args.get('period_start', '')
    period_end_str = request.args.get('period_end', '')
    status_filter = request.args.get('status', '')
    market_type_filter = request.args.get('market_type', '')

    now = datetime.utcnow()
    if period_start_str:
        try:
            period_start = datetime.strptime(period_start_str, '%Y-%m-%d')
        except ValueError:
            return jsonify({'error': '日期格式错误'}), 400
    else:
        period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    if period_end_str:
        try:
            period_end = datetime.strptime(period_end_str, '%Y-%m-%d')
            period_end = period_end.replace(hour=23, minute=59, second=59, microsecond=999999)
        except ValueError:
            return jsonify({'error': '日期格式错误'}), 400
    else:
        period_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)

    # 构建下注查询
    bets_query = Bet.query.filter(
        Bet.user_id == user_id,
        Bet.placed_at >= period_start,
        Bet.placed_at <= period_end,
    )

    valid_statuses = ['won', 'lost', 'push', 'pending']
    if status_filter and status_filter in valid_statuses:
        bets_query = bets_query.filter(Bet.status == status_filter)

    valid_markets = ['ML', 'Spread', 'Totals', 'CS']
    if market_type_filter and market_type_filter in valid_markets:
        bets_query = bets_query.filter(Bet.market_type == market_type_filter)

    bets = bets_query.order_by(Bet.placed_at.desc()).all()

    # 按比赛分组
    match_groups = {}  # match_id -> { match_info, bets[] }

    for b in bets:
        mid = b.match_id
        if mid not in match_groups:
            match = Match.query.get(mid)
            match_groups[mid] = {
                'match_id': mid,
                'home_team': match.home_team if match else '?',
                'away_team': match.away_team if match else '?',
                'league_name': match.league_name if match else '',
                'match_date': match.match_date.isoformat() if match and match.match_date else None,
                'status': match.status if match else '?',
                'scores_home': match.scores_home if match else 0,
                'scores_away': match.scores_away if match else 0,
                'bets': [],
            }
        match_groups[mid]['bets'].append(_bet_to_dict(b))

    # 计算每场比赛汇总 + 按比赛时间倒序
    match_list = []
    for mid, mg in match_groups.items():
        bet_count = len(mg['bets'])
        total_amount = sum(b['bet_amount'] for b in mg['bets'])
        won_amount = sum(b['win_amount'] for b in mg['bets'] if b['status'] == 'won')
        lost_amount = sum(b['bet_amount'] for b in mg['bets'] if b['status'] == 'lost')
        push_amount = sum(b['bet_amount'] for b in mg['bets'] if b['status'] == 'push')
        net_result = won_amount - lost_amount  # 不包括走水退款（走水不算输赢）

        mg['bet_count'] = bet_count
        mg['total_amount'] = total_amount
        mg['won_amount'] = won_amount
        mg['lost_amount'] = lost_amount
        mg['push_amount'] = push_amount
        mg['net_result'] = net_result

        match_list.append(mg)

    # 按比赛时间倒序
    match_list.sort(key=lambda m: m['match_date'] or '', reverse=True)

    # 整体汇总
    total_bets = sum(m['bet_count'] for m in match_list)
    total_amount = sum(m['total_amount'] for m in match_list)
    total_won = sum(m['won_amount'] for m in match_list)
    total_lost = sum(m['lost_amount'] for m in match_list)
    total_push = sum(m['push_amount'] for m in match_list)

    return jsonify({
        'user': {
            'id': user.id,
            'username': user.username,
            'nickname': user.nickname,
            'coin_balance': user.coin_balance,
            'status': user.status,
        },
        'summary': {
            'total_bets': total_bets,
            'total_matches': len(match_list),
            'total_amount': total_amount,
            'won_amount': total_won,
            'lost_amount': total_lost,
            'push_amount': total_push,
        },
        'matches': match_list,
        'period_start': period_start.strftime('%Y-%m-%d'),
        'period_end': period_end.strftime('%Y-%m-%d'),
    })
