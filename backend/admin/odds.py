# bet365cn — 赔率管理 API（仅超管）
from flask import Blueprint, request, jsonify
from models import db, Odds, Match, OperationLog
from auth import super_admin_required, get_client_ip
from datetime import datetime

odds_bp = Blueprint('admin_odds', __name__)

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


@odds_bp.route('/api/admin/odds', methods=['POST'])
@super_admin_required
def create_odds():
    """创建赔率数据"""
    data = request.get_json() or {}

    match_id = data.get('match_id')
    market_type = data.get('market_type')
    status = data.get('status', 'active')
    odds_data_input = data.get('data')
    updated_at_str = data.get('updated_at')
    bookmaker = data.get('bookmaker', 'Bet365')

    if not match_id or not market_type or not odds_data_input:
        return jsonify({'error': '参数不完整（需要 match_id, market_type, data）'}), 400

    if market_type not in VALID_MARKET_TYPES:
        return jsonify({'error': f'无效的盘口类型: {market_type}，支持: {VALID_MARKET_TYPES}'}), 400

    if status not in ('active', 'suspended', 'closed'):
        return jsonify({'error': '状态必须是 active/suspended/closed'}), 400

    # 检查比赛是否存在
    match = Match.query.get(match_id)
    if not match:
        return jsonify({'error': '比赛不存在'}), 404

    # 检查是否已存在该盘口
    existing = Odds.query.filter_by(
        match_id=match_id, market_type=market_type, bookmaker=bookmaker
    ).first()
    if existing:
        return jsonify({'error': f'该比赛已有 {market_type} 赔率数据（id={existing.id}），请使用 PUT 更新'}), 409

    # 解析 updated_at
    try:
        updated_at = datetime.fromisoformat(updated_at_str.replace('Z', '+00:00')) if updated_at_str else datetime.utcnow()
    except ValueError:
        return jsonify({'error': 'updated_at 格式无效'}), 400

    odds = Odds(
        match_id=match_id,
        bookmaker=bookmaker,
        market_type=market_type,
        odds_data=odds_data_input,
        status=status,
        updated_at=updated_at,
    )
    db.session.add(odds)
    db.session.flush()

    _log_action(
        action='创建赔率',
        target_type='odds',
        target_id=odds.id,
        detail={
            'match_id': match_id,
            'market_type': market_type,
            'status': status,
            'description': f'为比赛 {match.home_team} vs {match.away_team} 创建 {market_type} 赔率',
        },
    )
    db.session.commit()

    return jsonify({
        'success': True,
        'odds': {
            'id': odds.id,
            'match_id': odds.match_id,
            'bookmaker': odds.bookmaker,
            'market_type': odds.market_type,
            'status': odds.status,
            'data': odds.odds_data,
            'updated_at': odds.updated_at.isoformat() + '+00:00' if odds.updated_at else None,
        }
    }), 201


@odds_bp.route('/api/admin/odds/<int:odds_id>', methods=['PUT'])
@super_admin_required
def update_odds(odds_id):
    """更新赔率（按 odds ID）"""
    odds = Odds.query.get(odds_id)
    if not odds:
        return jsonify({'error': '赔率数据不存在'}), 404

    data = request.get_json() or {}

    if 'status' in data:
        new_status = data['status']
        if new_status not in ('active', 'suspended', 'closed'):
            return jsonify({'error': '状态必须是 active/suspended/closed'}), 400
        odds.status = new_status

    if 'data' in data:
        odds.odds_data = data['data']

    if 'updated_at' in data:
        try:
            odds.updated_at = datetime.fromisoformat(data['updated_at'].replace('Z', '+00:00'))
        except ValueError:
            return jsonify({'error': 'updated_at 格式无效'}), 400
    else:
        odds.updated_at = datetime.utcnow()

    if 'bookmaker' in data:
        odds.bookmaker = data['bookmaker']

    match = Match.query.get(odds.match_id)
    _log_action(
        action='更新赔率',
        target_type='odds',
        target_id=odds_id,
        detail={
            'match_id': odds.match_id,
            'market_type': odds.market_type,
            'changes': list(data.keys()),
            'description': f'更新 {match.home_team if match else "?"} vs {match.away_team if match else "?"} {odds.market_type} 赔率',
        },
    )
    db.session.commit()

    return jsonify({
        'success': True,
        'odds': {
            'id': odds.id,
            'match_id': odds.match_id,
            'bookmaker': odds.bookmaker,
            'market_type': odds.market_type,
            'status': odds.status,
            'data': odds.odds_data,
            'updated_at': odds.updated_at.isoformat() + '+00:00' if odds.updated_at else None,
        }
    })


@odds_bp.route('/api/admin/odds/match/<int:match_id>/<market_type>', methods=['PUT'])
@super_admin_required
def update_odds_by_match(match_id, market_type):
    """按比赛ID + 盘口类型更新赔率状态"""
    if market_type not in VALID_MARKET_TYPES:
        return jsonify({'error': f'无效的盘口类型: {market_type}'}), 400

    data = request.get_json() or {}

    odds = Odds.query.filter_by(
        match_id=match_id, market_type=market_type, bookmaker='Bet365'
    ).first()

    if not odds:
        return jsonify({'error': f'该比赛没有 {market_type} 赔率数据'}), 404

    if 'status' in data:
        new_status = data['status']
        if new_status not in ('active', 'suspended', 'closed'):
            return jsonify({'error': '状态必须是 active/suspended/closed'}), 400
        odds.status = new_status

    if 'data' in data:
        odds.odds_data = data['data']

    if 'updated_at' in data:
        try:
            odds.updated_at = datetime.fromisoformat(data['updated_at'].replace('Z', '+00:00'))
        except ValueError:
            return jsonify({'error': 'updated_at 格式无效'}), 400
    else:
        odds.updated_at = datetime.utcnow()

    match = Match.query.get(match_id)
    _log_action(
        action='更新赔率',
        target_type='odds',
        target_id=odds.id,
        detail={
            'match_id': match_id,
            'market_type': market_type,
            'changes': list(data.keys()),
            'description': f'更新 {match.home_team if match else "?"} vs {match.away_team if match else "?"} {market_type} 赔率',
        },
    )
    db.session.commit()

    return jsonify({
        'success': True,
        'odds': {
            'id': odds.id,
            'match_id': odds.match_id,
            'bookmaker': odds.bookmaker,
            'market_type': odds.market_type,
            'status': odds.status,
            'data': odds.odds_data,
            'updated_at': odds.updated_at.isoformat() + '+00:00' if odds.updated_at else None,
        }
    })
