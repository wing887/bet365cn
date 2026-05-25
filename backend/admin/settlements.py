# bet365cn — 结算管理 API（仅超管） + 取消比赛（超管+管理）
from flask import Blueprint, request, jsonify
from models import db, Match, Bet, CoinTransaction, Settlement, OperationLog, UserAccount
from auth import super_admin_required, admin_or_above, get_client_ip
from datetime import datetime
from services.settlement import calculate_settlement
from services.team_names import team_name_service

settlements_bp = Blueprint('admin_settlements', __name__)


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


@settlements_bp.route('/api/admin/settlements', methods=['GET'])
@admin_or_above
def list_settlements():
    """待结算 + 已结算列表"""
    status = request.args.get('status', 'pending')

    if status == 'pending':
        matches = Match.query.filter(
            Match.status == 'settled',
            ~Match.id.in_(
                db.session.query(Settlement.match_id).filter(
                    Settlement.status.in_(['confirmed', 'cancelled'])
                )
            )
        ).all()
    else:
        settlements = Settlement.query.filter_by(status='confirmed') \
            .order_by(Settlement.confirmed_at.desc()).limit(20).all()
        return jsonify({'settlements': [{
            'id': s.id, 'match_id': s.match_id,
            'total_bets': s.total_bets, 'total_users': s.total_users,
            'total_payout': s.total_payout, 'status': s.status,
            'confirmed_at': s.confirmed_at.isoformat() if s.confirmed_at else None,
        } for s in settlements]})

    result = []
    for m in matches:
        home_cn = team_name_service.translate(m.league_name, m.home_team)
        away_cn = team_name_service.translate(m.league_name, m.away_team)
        detail = calculate_settlement(m.id)
        if detail['total_bets'] > 0:
            result.append({
                'match_id': m.id,
                'home_team': home_cn,
                'away_team': away_cn,
                'league_name': m.league_name,
                'scores_home': m.scores_home,
                'scores_away': m.scores_away,
                'total_bets': detail['total_bets'],
                'total_users': detail['total_users'],
                'total_payout': detail['total_payout'],
                'total_win_users': detail['total_win_users'],
                'bets_detail': detail['bets_detail'][:20],
            })

    return jsonify({'pending': result})


@settlements_bp.route('/api/admin/settlements/confirm', methods=['POST'])
@super_admin_required
def confirm_settlement():
    """确认结算（仅超管）"""
    data = request.get_json() or {}
    match_id = data.get('match_id')

    if not match_id:
        return jsonify({'error': '请指定比赛'}), 400

    match = Match.query.get(match_id)
    if not match or match.status != 'settled':
        return jsonify({'error': '比赛未结束'}), 400

    existing = Settlement.query.filter_by(match_id=match_id, status='confirmed').first()
    if existing:
        return jsonify({'error': '该比赛已结算'}), 400

    detail = calculate_settlement(match_id)

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
            elif bd['result'] == 'push':
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
            action='结算确认',
            target_type='match',
            target_id=match_id,
            detail={
                'total_bets': detail['total_bets'],
                'total_payout': detail['total_payout'],
                'description': f'结算 {home_cn} vs {away_cn} 的比赛，比分 {match.scores_home}:{match.scores_away}，总注{detail["total_bets"]}笔，赔付{detail["total_payout"]}金币'
            },
        )
        db.session.commit()

        return jsonify({'success': True, 'total_payout': detail['total_payout']})

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'结算失败: {str(e)}'}), 500


@settlements_bp.route('/api/admin/matches/<int:match_id>/cancel', methods=['POST'])
@admin_or_above
def cancel_match(match_id):
    """取消比赛，退回所有下注（超管+管理）"""
    match = Match.query.get(match_id)
    if not match:
        return jsonify({'error': '比赛不存在'}), 404

    bets = Bet.query.filter_by(match_id=match_id, status='pending').all()

    try:
        refunded = 0
        for bet in bets:
            bet.status = 'refunded'
            bet.settled_at = datetime.utcnow()

            user = UserAccount.query.with_for_update().get(bet.user_id)
            if user:
                balance_before = user.coin_balance
                user.coin_balance += bet.bet_amount
                db.session.add(CoinTransaction(
                    user_id=bet.user_id,
                    amount=bet.bet_amount,
                    balance_before=balance_before,
                    balance_after=user.coin_balance,
                    type='bet_refund',
                    bet_id=bet.id,
                    note=f"比赛取消退款: {match.home_team} vs {match.away_team}",
                ))
                refunded += bet.bet_amount

        sett = Settlement(
            match_id=match_id,
            status='cancelled',
            total_bets=len(bets),
            total_users=len(set(b.user_id for b in bets)),
            confirmed_by=request.current_user_id,
            confirmed_at=datetime.utcnow(),
        )
        db.session.add(sett)

        _log_action(
            action='取消比赛',
            target_type='match',
            target_id=match_id,
            detail={
                'refunded_amount': refunded,
                'affected_bets': len(bets),
                'description': f'取消 {team_name_service.translate(match.league_name, match.home_team)} vs {team_name_service.translate(match.league_name, match.away_team)} 的比赛，退回{len(bets)}笔下注共{refunded}金币'
            },
        )
        db.session.commit()

        return jsonify({'success': True, 'refunded_amount': refunded, 'affected_bets': len(bets)})

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
