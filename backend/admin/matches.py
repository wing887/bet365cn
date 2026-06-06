# bet365cn — 比赛管理 API（仅超管）
from flask import Blueprint, request, jsonify
from models import db, Match, Bet, UserAccount, CoinTransaction, Settlement, OperationLog
from auth import super_admin_required, get_client_ip
from datetime import datetime
from services.settlement import calculate_settlement
from services.team_names import team_name_service

matches_bp = Blueprint('admin_matches', __name__)


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


@matches_bp.route('/api/admin/matches', methods=['POST'])
@super_admin_required
def create_match():
    """创建测试比赛"""
    data = request.get_json() or {}

    home_team = data.get('home_team')
    away_team = data.get('away_team')
    league_name = data.get('league_name')
    league_name_cn = data.get('league_name_cn', league_name)
    match_time = data.get('match_time')
    status = data.get('status', 'pending')
    scores_home = data.get('scores_home', 0)
    scores_away = data.get('scores_away', 0)

    if not home_team or not away_team or not league_name or not match_time:
        return jsonify({'error': '参数不完整（需要 home_team, away_team, league_name, match_time）'}), 400

    # 自动生成 event_id 和 league_slug
    import re
    league_slug = re.sub(r'[^a-z0-9]+', '-', league_name.lower()).strip('-')
    ts = datetime.utcnow().strftime('%m%d%H%M%S')
    evt = f"{home_team[:4]}{away_team[:4]}".upper().replace(' ', '')
    event_id = f"T{ts}{evt}"[:20]

    try:
        match_date = datetime.fromisoformat(match_time.replace('Z', '+00:00'))
    except ValueError:
        return jsonify({'error': 'match_time 格式无效，需要 ISO 8601'}), 400

    match = Match(
        event_id=event_id,
        home_team=home_team,
        away_team=away_team,
        league_name=league_name,
        league_slug=league_slug,
        match_date=match_date,
        status=status,
        scores_home=scores_home,
        scores_away=scores_away,
    )
    db.session.add(match)
    db.session.flush()

    home_cn = team_name_service.translate(league_name, home_team)
    away_cn = team_name_service.translate(league_name, away_team)
    _log_action(
        action='创建比赛',
        target_type='match',
        target_id=match.id,
        detail={
            'home_team': home_team,
            'away_team': away_team,
            'league': league_name,
            'status': status,
            'description': f'创建 {home_cn} vs {away_cn} ({league_name_cn}) 比赛，状态 {status}',
        },
    )
    db.session.commit()

    return jsonify({
        'success': True,
        'match': {
            'id': match.id,
            'event_id': match.event_id,
            'home_team': match.home_team,
            'away_team': match.away_team,
            'league_name': match.league_name,
            'league_slug': match.league_slug,
            'match_date': match.match_date.isoformat() + '+00:00',
            'status': match.status,
            'scores_home': match.scores_home,
            'scores_away': match.scores_away,
        }
    }), 201


@matches_bp.route('/api/admin/matches/<int:match_id>', methods=['PUT'])
@super_admin_required
def update_match(match_id):
    """更新比赛状态、比分"""
    match = Match.query.get(match_id)
    if not match:
        return jsonify({'error': '比赛不存在'}), 404

    data = request.get_json() or {}

    if 'status' in data:
        new_status = data['status']
        if new_status not in ('pending', 'live', 'settled', 'cancelled'):
            return jsonify({'error': '状态必须是 pending/live/settled/cancelled'}), 400
        old_status = match.status
        match.status = new_status

    if 'scores_home' in data:
        match.scores_home = int(data['scores_home'])
    if 'scores_away' in data:
        match.scores_away = int(data['scores_away'])
    if 'scores_p1_home' in data:
        match.scores_p1_home = int(data['scores_p1_home'])
    if 'scores_p1_away' in data:
        match.scores_p1_away = int(data['scores_p1_away'])
    if 'match_time' in data:
        try:
            match.match_date = datetime.fromisoformat(data['match_time'].replace('Z', '+00:00'))
        except ValueError:
            return jsonify({'error': 'match_time 格式无效'}), 400

    match.updated_at = datetime.utcnow()

    home_cn = team_name_service.translate(match.league_name, match.home_team)
    away_cn = team_name_service.translate(match.league_name, match.away_team)
    _log_action(
        action='更新比赛',
        target_type='match',
        target_id=match_id,
        detail={
            'changes': list(data.keys()),
            'description': f'更新 {home_cn} vs {away_cn} 比赛信息',
        },
    )
    db.session.commit()

    return jsonify({
        'success': True,
        'match': {
            'id': match.id,
            'status': match.status,
            'scores_home': match.scores_home,
            'scores_away': match.scores_away,
            'scores_p1_home': match.scores_p1_home,
            'scores_p1_away': match.scores_p1_away,
            'match_date': match.match_date.isoformat() + '+00:00',
            'updated_at': match.updated_at.isoformat() + '+00:00' if match.updated_at else None,
        }
    })


@matches_bp.route('/api/admin/matches/<int:match_id>/settle', methods=['POST'])
@super_admin_required
def settle_match(match_id):
    """结算比赛（设置比分 + 标记 settled + 执行下注结算）"""
    match = Match.query.get(match_id)
    if not match:
        return jsonify({'error': '比赛不存在'}), 404

    data = request.get_json() or {}
    scores_home = data.get('scores_home')
    scores_away = data.get('scores_away')

    if scores_home is None or scores_away is None:
        return jsonify({'error': '请提供 scores_home 和 scores_away'}), 400

    try:
        scores_home = int(scores_home)
        scores_away = int(scores_away)
    except (ValueError, TypeError):
        return jsonify({'error': '比分必须是整数'}), 400

    # 更新比赛状态和比分
    match.scores_home = scores_home
    match.scores_away = scores_away
    match.status = 'settled'
    match.updated_at = datetime.utcnow()

    # 执行结算
    detail = calculate_settlement(match_id)

    settled_count = 0
    try:
        for bd in detail['bets_detail']:
            bet = Bet.query.with_for_update().get(bd['bet_id'])
            if not bet:
                continue
            bet.status = bd['result']
            bet.settled_at = datetime.utcnow()

            user = UserAccount.query.with_for_update().get(bet.user_id)
            if not user:
                continue

            balance_before = user.coin_balance

            if bd['result'] == 'won':
                bet.win_amount = bd['win_amount']
                user.coin_balance += bd['win_amount']
                db.session.add(CoinTransaction(
                    user_id=bet.user_id,
                    amount=bd['win_amount'],
                    balance_before=balance_before,
                    balance_after=user.coin_balance,
                    type='bet_win',
                    bet_id=bet.id,
                    note=f"中奖: {match.home_team} vs {match.away_team}",
                ))
                settled_count += 1
            elif bd['result'] == 'push':
                bet.win_amount = bet.bet_amount
                user.coin_balance += bet.bet_amount
                db.session.add(CoinTransaction(
                    user_id=bet.user_id,
                    amount=bet.bet_amount,
                    balance_before=balance_before,
                    balance_after=user.coin_balance,
                    type='bet_refund',
                    bet_id=bet.id,
                    note=f"退款(走水): {match.home_team} vs {match.away_team}",
                ))
                settled_count += 1
            # lost: 不退款

        # 创建结算记录
        existing_sett = Settlement.query.filter_by(
            match_id=match_id, status='confirmed'
        ).first()
        if not existing_sett:
            sett = Settlement(
                match_id=match_id,
                status='confirmed',
                total_bets=detail['total_bets'],
                total_users=detail['total_users'],
                total_payout=detail['total_payout'],
                detail=detail,
                confirmed_by=request.current_user_id,
                confirmed_at=datetime.utcnow(),
            )
            db.session.add(sett)

        home_cn = team_name_service.translate(match.league_name, match.home_team)
        away_cn = team_name_service.translate(match.league_name, match.away_team)
        _log_action(
            action='结算比赛',
            target_type='match',
            target_id=match_id,
            detail={
                'scores': f'{scores_home}:{scores_away}',
                'total_bets': detail['total_bets'],
                'total_payout': detail['total_payout'],
                'description': f'结算 {home_cn} vs {away_cn} 比分 {scores_home}:{scores_away}，结算{detail["total_bets"]}笔，赔付{detail["total_payout"]}金币',
            },
        )
        db.session.commit()

        return jsonify({
            'success': True,
            'match_id': match_id,
            'scores': f'{scores_home}:{scores_away}',
            'settlement': {
                'total_bets': detail['total_bets'],
                'total_users': detail['total_users'],
                'total_payout': detail['total_payout'],
                'total_win_users': detail['total_win_users'],
                'bets_detail': detail['bets_detail'],
            }
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'结算失败: {str(e)}'}), 500
