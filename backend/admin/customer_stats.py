# bet365cn — 客户统计 API（代理专用）
from flask import Blueprint, request, jsonify
from models import db, UserAccount, Bet, Match
from auth import agent_only, ROLE_AGENT
from datetime import datetime, timedelta
from sqlalchemy import func

customer_stats_bp = Blueprint('agent_customer_stats', __name__)


def _bet_to_dict(b):
    """下注对象转字典"""
    match = Match.query.get(b.match_id)
    return {
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
    }


@customer_stats_bp.route('/api/agent/customers/stats', methods=['GET'])
@agent_only
def customer_stats():
    """代理查看自己客户的汇总 + 列表

    可选参数:
      ?period_start=YYYY-MM-DD  # 默认本月1日
      ?period_end=YYYY-MM-DD    # 默认今天
    """
    admin = request.current_admin
    if admin.role != ROLE_AGENT:
        return jsonify({'error': '仅代理可访问'}), 403

    period_start_str = request.args.get('period_start', '')
    period_end_str = request.args.get('period_end', '')

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

    # 查询代理的所有用户
    users = UserAccount.query.filter_by(created_by_admin_id=admin.id).order_by(UserAccount.created_at.desc()).all()

    user_stats = []
    for u in users:
        # 时间段内已结算的下注
        bets_query = Bet.query.filter(
            Bet.user_id == u.id,
            Bet.status.in_(['won', 'lost', 'push']),
            Bet.placed_at >= period_start,
            Bet.placed_at <= period_end,
        )

        bet_count = bets_query.count()

        turnover = db.session.query(func.coalesce(func.sum(Bet.bet_amount), 0)).filter(
            Bet.user_id == u.id,
            Bet.status.in_(['won', 'lost', 'push']),
            Bet.placed_at >= period_start,
            Bet.placed_at <= period_end,
        ).first()[0] or 0

        win_amount = db.session.query(func.coalesce(func.sum(Bet.win_amount), 0)).filter(
            Bet.user_id == u.id,
            Bet.status == 'won',
            Bet.placed_at >= period_start,
            Bet.placed_at <= period_end,
        ).first()[0] or 0

        push_refund = db.session.query(func.coalesce(func.sum(Bet.bet_amount), 0)).filter(
            Bet.user_id == u.id,
            Bet.status == 'push',
            Bet.placed_at >= period_start,
            Bet.placed_at <= period_end,
        ).first()[0] or 0

        net = turnover - win_amount - push_refund

        user_stats.append({
            'id': u.id,
            'username': u.username,
            'nickname': u.nickname,
            'coin_balance': u.coin_balance,
            'status': u.status,
            'bet_count': bet_count,
            'turnover': turnover,
            'win_amount': win_amount,
            'push_refund': push_refund,
            'net': net,
        })

    # 汇总
    total_turnover = sum(s['turnover'] for s in user_stats)
    total_win = sum(s['win_amount'] for s in user_stats)
    total_push = sum(s['push_refund'] for s in user_stats)
    total_net = total_turnover - total_win - total_push

    return jsonify({
        'summary': {
            'total_users': len(user_stats),
            'active_users': sum(1 for s in user_stats if s['bet_count'] > 0),
            'total_bet_count': sum(s['bet_count'] for s in user_stats),
            'total_turnover': total_turnover,
            'total_win': total_win,
            'total_push': total_push,
            'total_net': total_net,
        },
        'users': user_stats,
        'period_start': period_start.strftime('%Y-%m-%d'),
        'period_end': period_end.strftime('%Y-%m-%d'),
    })


@customer_stats_bp.route('/api/agent/customers/<int:user_id>/daily', methods=['GET'])
@agent_only
def customer_daily(user_id):
    """代理查看单个客户的按天分组投注明细

    可选参数:
      ?period_start=YYYY-MM-DD
      ?period_end=YYYY-MM-DD
    返回:
      daily: [{ date, bet_count, turnover, win_amount, push_refund, net, bets: [...] }]
    """
    admin = request.current_admin

    # 权限检查：只能看自己的客户
    user = UserAccount.query.filter_by(id=user_id, created_by_admin_id=admin.id).first()
    if not user:
        return jsonify({'error': '用户不存在或无权查看'}), 403

    period_start_str = request.args.get('period_start', '')
    period_end_str = request.args.get('period_end', '')

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

    # 查询时间段内所有已结算下注
    bets = Bet.query.filter(
        Bet.user_id == user_id,
        Bet.status.in_(['won', 'lost', 'push']),
        Bet.placed_at >= period_start,
        Bet.placed_at <= period_end,
    ).order_by(Bet.placed_at.desc()).all()

    # 按天分组
    daily_map = {}
    for b in bets:
        day_key = b.placed_at.strftime('%Y-%m-%d') if b.placed_at else 'unknown'
        if day_key not in daily_map:
            daily_map[day_key] = {
                'date': day_key,
                'bet_count': 0,
                'turnover': 0,
                'win_amount': 0,
                'push_refund': 0,
                'net': 0,
                'bets': [],
            }
        daily_map[day_key]['bet_count'] += 1
        daily_map[day_key]['turnover'] += b.bet_amount
        if b.status == 'won':
            daily_map[day_key]['win_amount'] += b.win_amount
        elif b.status == 'push':
            daily_map[day_key]['push_refund'] += b.bet_amount
        daily_map[day_key]['bets'].append(_bet_to_dict(b))

    # 计算每日净输赢
    for day_data in daily_map.values():
        day_data['net'] = day_data['turnover'] - day_data['win_amount'] - day_data['push_refund']

    # 按日期降序
    daily_list = sorted(daily_map.values(), key=lambda x: x['date'], reverse=True)

    # 汇总
    total_turnover = sum(d['turnover'] for d in daily_list)
    total_win = sum(d['win_amount'] for d in daily_list)
    total_push = sum(d['push_refund'] for d in daily_list)
    total_net = total_turnover - total_win - total_push

    return jsonify({
        'user': {
            'id': user.id,
            'username': user.username,
            'nickname': user.nickname,
            'coin_balance': user.coin_balance,
            'status': user.status,
        },
        'daily': daily_list,
        'summary': {
            'total_days': len(daily_list),
            'total_bets': sum(d['bet_count'] for d in daily_list),
            'total_turnover': total_turnover,
            'total_win': total_win,
            'total_push': total_push,
            'total_net': total_net,
        },
        'period_start': period_start.strftime('%Y-%m-%d'),
        'period_end': period_end.strftime('%Y-%m-%d'),
    })
