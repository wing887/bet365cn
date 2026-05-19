# bet365cn — 比赛 API
from flask import Blueprint, request, jsonify
from models import db, Match, Odds
from auth import login_required
from datetime import datetime
from services.team_names import team_name_service

matches_bp = Blueprint('matches', __name__)


def _translate_match(match):
    """翻译队名 + 序列化"""
    return {
        'id': match.id,
        'home_team': team_name_service.translate(match.league_name, match.home_team),
        'away_team': team_name_service.translate(match.league_name, match.away_team),
        'league_name': match.league_name,
        'league_slug': match.league_slug,
        'match_date': match.match_date.isoformat() if match.match_date else None,
        'status': match.status,
        'scores_home': match.scores_home,
        'scores_away': match.scores_away,
    }


@matches_bp.route('/api/matches', methods=['GET'])
@login_required
def list_matches():
    """比赛列表"""
    status = request.args.get('status')  # pending / live / settled / all
    date_str = request.args.get('date')  # YYYY-MM-DD，默认今天

    query = Match.query

    # 状态筛选
    if status and status != 'all':
        query = query.filter_by(status=status)

    # 日期筛选（仅限今日）
    if date_str:
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            next_day = datetime(date_obj.year, date_obj.month, date_obj.day) +                        __import__('datetime').timedelta(days=1)
            query = query.filter(Match.match_date >= date_obj, Match.match_date < next_day)
        except ValueError:
            pass

    # 排序：即将开始 > 进行中 > 已结束
    matches = query.order_by(
        Match.status == 'live',
        Match.status == 'pending',
        Match.match_date.asc()
    ).limit(30).all()

    return jsonify({'matches': [_translate_match(m) for m in matches]})


@matches_bp.route('/api/matches/<int:match_id>', methods=['GET'])
@login_required
def match_detail(match_id):
    """比赛详情（含赔率）"""
    match = Match.query.get(match_id)
    if not match:
        return jsonify({'error': '比赛不存在'}), 404

    result = _translate_match(match)

    # 附加赔率
    odds_list = Odds.query.filter_by(match_id=match.id, bookmaker='Bet365').all()
    odds_data = {}
    for o in odds_list:
        odds_data[o.market_type] = {
            'bookmaker': o.bookmaker,
            'market_type': o.market_type,
            'data': o.odds_data,
            'updated_at': o.updated_at.isoformat() if o.updated_at else None,
        }
    result['odds'] = odds_data

    return jsonify(result)
