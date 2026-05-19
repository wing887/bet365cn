# bet365cn — 结算管理 API
from flask import Blueprint, request, jsonify
from models import db, Match, Bet, CoinTransaction, Settlement, OperationLog
from auth import super_admin_required
from datetime import datetime
from services.settlement import calculate_settlement

settlements_bp = Blueprint('admin_settlements', __name__)


@settlements_bp.route('/api/admin/settlements', methods=['GET'])
@super_admin_required
def list_settlements():
    """待结算 + 已结算列表"""
    status = request.args.get('status', 'pending')  # pending / confirmed

    # 查出 settled 状态的比赛但未结算的
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
        settlements = Settlement.query.filter_by(status='confirmed')             .order_by(Settlement.confirmed_at.desc()).limit(20).all()
        return jsonify({'settlements': [{
            'id': s.id, 'match_id': s.match_id,
            'total_bets': s.total_bets, 'total_users': s.total_users,
            'total_payout': s.total_payout, 'status': s.status,
            'confirmed_at': s.confirmed_at.isoformat() if s.confirmed_at else None,
        } for s in settlements]})

    # 为每个 settled 比赛创建待结算记录，计算明细
    result = []
    for m in matches:
        detail = calculate_settlement(m.id)
        if detail['total_bets'] > 0:
            result.append({
                'match_id': m.id,
                'home_team': m.home_team,
                'away_team': m.away_team,
                'league_name': m.league_name,
                'scores_home': m.scores_home,
                'scores_away': m.scores_away,
                'total_bets': detail['total_bets'],
                'total_users': detail['total_users'],
                'total_payout': detail['total_payout'],
                'total_win_users': detail['total_win_users'],
                'bets_detail': detail['bets_detail'][:20],  # 最多20条
            })

    return jsonify({'pending': result})


@settlements_bp.route('/api/admin/settlements/confirm', methods=['POST'])
@super_admin_required
def confirm_settlement():
    """确认结算"""
    data = request.get_json() or {}
    match_id = data.get('match_id')

    if not match_id:
        return jsonify({'error': '请指定比赛'}), 400

    match = Match.query.get(match_id)
    if not match or match.status != 'settled':
        return jsonify({'error': '比赛未结束'}), 400

    # 检查是否已结算
    existing = Settlement.query.filter_by(
        match_id=match_id, status='confirmed'
    ).first()
    if existing:
        return jsonify({'error': '该比赛已结算'}), 400

    # 计算
    detail = calculate_settlement(match_id)

    try:
        # 更新下注状态 + 给赢家发金币
        for bd in detail['bets_detail']:
            bet = Bet.query.with_for_update().get(bd['bet_id'])
            if not bet:
                continue
            bet.status = bd['result']
            bet.settled_at = datetime.utcnow()

            if bd['result'] == 'won':
                bet.win_amount = bd['win_amount']
                # 发金币
                user_q = __import__('models').UserAccount.query.with_for_update().get(bet.user_id)
                if user_q:
                    user_q.coin_balance += bd['win_amount']
                    db.session.add(CoinTransaction(
                        user_id=bet.user_id,
                        amount=bd['win_amount'],
                        type='bet_win',
                        bet_id=bet.id,
                        note=f"中奖: {match.home_team} vs {match.away_team}",
                    ))
            elif bd['result'] == 'push':
                # 走水：退回本金
                user_q = __import__('models').UserAccount.query.with_for_update().get(bet.user_id)
                if user_q:
                    user_q.coin_balance += bet.bet_amount
                    db.session.add(CoinTransaction(
                        user_id=bet.user_id,
                        amount=bet.bet_amount,
                        type='bet_refund',
                        bet_id=bet.id,
                        note=f"退款(走水): {match.home_team} vs {match.away_team}",
                    ))

        # 创建结算记录
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

        log = OperationLog(
            admin_id=request.current_user_id,
            action='结算确认',
            target_type='match',
            target_id=match_id,
            detail={'total_bets': detail['total_bets'], 'total_payout': detail['total_payout']},
        )
        db.session.add(log)
        db.session.commit()

        return jsonify({'success': True, 'total_payout': detail['total_payout']})

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'结算失败: {str(e)}'}), 500


@settlements_bp.route('/api/admin/matches/<int:match_id>/cancel', methods=['POST'])
@super_admin_required
def cancel_match(match_id):
    """取消比赛，退回所有下注"""
    match = Match.query.get(match_id)
    if not match:
        return jsonify({'error': '比赛不存在'}), 404

    bets = Bet.query.filter_by(match_id=match_id, status='pending').all()

    try:
        refunded = 0
        for bet in bets:
            bet.status = 'refunded'
            bet.settled_at = datetime.utcnow()

            user = __import__('models').UserAccount.query.with_for_update().get(bet.user_id)
            if user:
                user.coin_balance += bet.bet_amount
                db.session.add(CoinTransaction(
                    user_id=bet.user_id,
                    amount=bet.bet_amount,
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

        log = OperationLog(
            admin_id=request.current_user_id,
            action='取消比赛',
            target_type='match',
            target_id=match_id,
            detail={'refunded_amount': refunded, 'affected_bets': len(bets)},
        )
        db.session.add(log)
        db.session.commit()

        return jsonify({'success': True, 'refunded_amount': refunded, 'affected_bets': len(bets)})

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
