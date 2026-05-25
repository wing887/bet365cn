# bet365cn — 代理管理 API（超管 + 管理）
from flask import Blueprint, request, jsonify
from models import db, AdminAccount, UserAccount, Bet
from auth import admin_or_above, ROLE_AGENT
from datetime import datetime
from sqlalchemy import func

agents_bp = Blueprint('admin_agents', __name__)


@agents_bp.route('/api/admin/agents', methods=['GET'])
@admin_or_above
def list_agents():
    """代理列表（含统计聚合）

    可选参数:
      ?period_start=YYYY-MM-DD  # 流水统计起始（默认本月1日）
      ?period_end=YYYY-MM-DD    # 流水统计截止（默认今天）
      ?q=关键词                # 搜索代理用户名
    """
    period_start_str = request.args.get('period_start', '')
    period_end_str = request.args.get('period_end', '')
    q = request.args.get('q', '').strip()

    # 解析时间范围，默认本月
    now = datetime.utcnow()
    if period_start_str:
        try:
            period_start = datetime.strptime(period_start_str, '%Y-%m-%d')
        except ValueError:
            return jsonify({'error': '日期格式错误，请使用 YYYY-MM-DD'}), 400
    else:
        period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    if period_end_str:
        try:
            period_end = datetime.strptime(period_end_str, '%Y-%m-%d')
            period_end = period_end.replace(hour=23, minute=59, second=59, microsecond=999999)
        except ValueError:
            return jsonify({'error': '日期格式错误，请使用 YYYY-MM-DD'}), 400
    else:
        period_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)

    # 查询代理列表
    query = AdminAccount.query.filter_by(role=ROLE_AGENT)
    if q:
        query = query.filter(AdminAccount.username.contains(q))
    agents = query.order_by(AdminAccount.created_at.desc()).all()

    result = []
    for a in agents:
        # 下游用户数
        user_count = UserAccount.query.filter_by(created_by_admin_id=a.id).count()

        # 活跃用户数（近7天有下注）
        seven_days_ago = now.replace(hour=0, minute=0, second=0, microsecond=0)
        from datetime import timedelta
        seven_days_ago = seven_days_ago - timedelta(days=7)

        active_user_ids = db.session.query(Bet.user_id).filter(
            Bet.placed_at >= seven_days_ago,
            Bet.status.in_(['won', 'lost', 'push'])
        ).distinct().subquery()

        active_users = UserAccount.query.filter(
            UserAccount.created_by_admin_id == a.id,
            UserAccount.id.in_(db.session.query(active_user_ids.c.user_id))
        ).count()

        # 流水统计（该时间段内：won/lost/push 状态的 bet_amount 之和）
        user_ids_subq = db.session.query(UserAccount.id).filter_by(created_by_admin_id=a.id).subquery()
        turnover_row = db.session.query(func.coalesce(func.sum(Bet.bet_amount), 0)).filter(
            Bet.user_id.in_(db.session.query(user_ids_subq.c.id)),
            Bet.status.in_(['won', 'lost', 'push']),
            Bet.placed_at >= period_start,
            Bet.placed_at <= period_end,
        ).first()
        turnover = turnover_row[0] if turnover_row else 0

        result.append({
            'id': a.id,
            'username': a.username,
            'role': a.role,
            'coin_balance': a.coin_balance,
            'status': a.status,
            'last_login_at': a.last_login_at.isoformat() if a.last_login_at else None,
            'created_at': a.created_at.isoformat() if a.created_at else None,
            'user_count': user_count,
            'active_users_7d': active_users,
            'turnover': turnover,
        })

    return jsonify({
        'agents': result,
        'period_start': period_start.strftime('%Y-%m-%d'),
        'period_end': period_end.strftime('%Y-%m-%d'),
    })


@agents_bp.route('/api/admin/agents/<int:agent_id>', methods=['GET'])
@admin_or_above
def agent_detail(agent_id):
    """代理详情（含用户列表+统计）

    可选参数:
      ?period_start=YYYY-MM-DD
      ?period_end=YYYY-MM-DD
    """
    period_start_str = request.args.get('period_start', '')
    period_end_str = request.args.get('period_end', '')

    agent = AdminAccount.query.filter_by(id=agent_id, role=ROLE_AGENT).first()
    if not agent:
        return jsonify({'error': '代理不存在'}), 404

    # 时间范围
    now = datetime.utcnow()
    from datetime import timedelta
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

    # 下游用户列表
    users = UserAccount.query.filter_by(created_by_admin_id=agent_id).order_by(UserAccount.created_at.desc()).all()

    user_stats = []
    for u in users:
        bets = Bet.query.filter(
            Bet.user_id == u.id,
            Bet.status.in_(['won', 'lost', 'push']),
            Bet.placed_at >= period_start,
            Bet.placed_at <= period_end,
        )

        bet_count = bets.count()

        turnover_row = db.session.query(func.coalesce(func.sum(Bet.bet_amount), 0)).filter(
            Bet.user_id == u.id,
            Bet.status.in_(['won', 'lost', 'push']),
            Bet.placed_at >= period_start,
            Bet.placed_at <= period_end,
        ).first()
        turnover = turnover_row[0] or 0

        win_row = db.session.query(func.coalesce(func.sum(Bet.win_amount), 0)).filter(
            Bet.user_id == u.id,
            Bet.status == 'won',
            Bet.placed_at >= period_start,
            Bet.placed_at <= period_end,
        ).first()
        win_amount = win_row[0] or 0

        push_row = db.session.query(func.coalesce(func.sum(Bet.bet_amount), 0)).filter(
            Bet.user_id == u.id,
            Bet.status == 'push',
            Bet.placed_at >= period_start,
            Bet.placed_at <= period_end,
        ).first()
        push_refund = push_row[0] or 0

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

    # 代理汇总
    total_turnover = sum(s['turnover'] for s in user_stats)
    total_win = sum(s['win_amount'] for s in user_stats)
    total_push = sum(s['push_refund'] for s in user_stats)
    total_net = total_turnover - total_win - total_push

    return jsonify({
        'agent': {
            'id': agent.id,
            'username': agent.username,
            'role': agent.role,
            'coin_balance': agent.coin_balance,
            'status': agent.status,
            'last_login_at': agent.last_login_at.isoformat() if agent.last_login_at else None,
            'created_at': agent.created_at.isoformat() if agent.created_at else None,
        },
        'summary': {
            'total_users': len(user_stats),
            'active_users': sum(1 for s in user_stats if s['bet_count'] > 0),
            'total_turnover': total_turnover,
            'total_win': total_win,
            'total_push': total_push,
            'total_net': total_net,
        },
        'users': user_stats,
        'period_start': period_start.strftime('%Y-%m-%d'),
        'period_end': period_end.strftime('%Y-%m-%d'),
    })
