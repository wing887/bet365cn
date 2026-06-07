# bet365cn — 系统配置 API（仅超管）
from flask import Blueprint, request, jsonify
from models import db, BetLimit, Odds, Match
from auth import super_admin_required
from datetime import datetime
from services.team_names import team_name_service

config_bp = Blueprint('admin_config', __name__)

MARKET_TYPES = ['ML', 'Spread', 'Totals', 'CS']
MARKET_LABELS = {'ML': '胜平负', 'Spread': '让球盘', 'Totals': '大小球', 'CS': '波胆'}


@config_bp.route('/api/admin/config/bet-limits', methods=['GET'])
@super_admin_required
def get_bet_limits():
    """读取各盘口最大投注额（含滚球限额）"""
    limits = BetLimit.query.all()
    result = {}
    for l in limits:
        result[l.market_type.lower()] = {
            'market_type': l.market_type,
            'label': MARKET_LABELS.get(l.market_type, l.market_type),
            'max_bet_amount': l.max_bet_amount,
            'live_max_bet_amount': l.live_max_bet_amount or int(l.max_bet_amount * 0.6),
            'updated_at': l.updated_at.isoformat() if l.updated_at else None,
        }
    return jsonify({'limits': result})


@config_bp.route('/api/admin/config/bet-limits', methods=['PUT'])
@super_admin_required
def update_bet_limits():
    """批量更新各盘口最大投注额（支持赛前+滚球独立设置）"""
    data = request.get_json() or {}
    
    updated = []
    for mt in MARKET_TYPES:
        key = mt.lower()
        live_key = f'{key}_live'
        
        # 赛前限额
        if key in data:
            amount = data[key]
            try:
                amount = int(amount)
            except (ValueError, TypeError):
                return jsonify({'error': f'{mt} 的值无效，必须是整数'}), 400
            if amount < 1:
                return jsonify({'error': f'{mt} 的最大投注不能小于1'}), 400
            
            limit = BetLimit.query.filter_by(market_type=mt).first()
            if not limit:
                limit = BetLimit(market_type=mt, max_bet_amount=amount)
                db.session.add(limit)
            else:
                limit.max_bet_amount = amount
                limit.updated_by = request.current_user_id
            updated.append({'market_type': mt, 'max_bet_amount': amount})
        
        # 滚球限额
        if live_key in data:
            amount = data[live_key]
            try:
                amount = int(amount)
            except (ValueError, TypeError):
                return jsonify({'error': f'{mt} 滚球限额无效，必须是整数'}), 400
            if amount < 1:
                return jsonify({'error': f'{mt} 滚球限额不能小于1'}), 400
            
            limit = BetLimit.query.filter_by(market_type=mt).first()
            if not limit:
                limit = BetLimit(market_type=mt, max_bet_amount=5000, live_max_bet_amount=amount)
                db.session.add(limit)
            else:
                limit.live_max_bet_amount = amount
                limit.updated_by = request.current_user_id
            updated.append({'market_type': mt, 'live_max_bet_amount': amount})
    
    if not updated:
        return jsonify({'error': '没有提供任何有效参数'}), 400
    
    db.session.commit()
    return jsonify({
        'success': True,
        'updated': updated,
        'message': f'已更新 {len(updated)} 项投注限额配置',
    })


# ============================================================
# 盘口封盘/开盘中 API（仅超管）
# ============================================================

@config_bp.route('/api/admin/config/market-status/<int:match_id>', methods=['GET'])
@super_admin_required
def get_market_status(match_id):
    """读取某场比赛所有盘口的封盘状态"""
    match = Match.query.get(match_id)
    if not match:
        return jsonify({'error': '比赛不存在'}), 404

    odds_list = Odds.query.filter_by(match_id=match_id).all()
    home_cn = team_name_service.translate(match.league_name, match.home_team)
    away_cn = team_name_service.translate(match.league_name, match.away_team)

    markets = []
    for o in odds_list:
        markets.append({
            'id': o.id,
            'market_type': o.market_type,
            'label': MARKET_LABELS.get(o.market_type, o.market_type),
            'status': o.status,
            'updated_at': o.updated_at.isoformat() if o.updated_at else None,
        })

    return jsonify({
        'match': {
            'id': match.id,
            'home_team': home_cn,
            'away_team': away_cn,
            'league_name': match.league_name,
            'status': match.status,
        },
        'markets': markets,
    })


@config_bp.route('/api/admin/config/market-status/<int:match_id>/<market_type>', methods=['PUT'])
@super_admin_required
def set_market_status(match_id, market_type):
    """手动设置某场比赛某个盘口的封盘状态"""
    data = request.get_json() or {}
    new_status = data.get('status')

    if new_status not in ('active', 'suspended', 'closed'):
        return jsonify({'error': '状态必须是 active / suspended / closed'}), 400

    if market_type not in MARKET_TYPES:
        return jsonify({'error': f'无效的盘口类型: {market_type}'}), 400

    odds = Odds.query.filter_by(match_id=match_id, market_type=market_type).first()
    if not odds:
        return jsonify({'error': '该盘口没有赔率数据'}), 404

    old_status = odds.status
    odds.status = new_status
    odds.updated_at = datetime.utcnow()
    db.session.commit()

    return jsonify({
        'success': True,
        'match_id': match_id,
        'market_type': market_type,
        'old_status': old_status,
        'new_status': new_status,
        'message': f'{MARKET_LABELS.get(market_type, market_type)} 已{"封盘" if new_status != "active" else "开盘"}',
    })
