# bet365cn — 比赛 API
from flask import Blueprint, request, jsonify
from models import db, Match, Odds, TeamNameMap
from auth import login_required
from datetime import datetime, timedelta
from sqlalchemy import case
from services.team_names import team_name_service

matches_bp = Blueprint('matches', __name__)

# 联赛名中英文对照
LEAGUE_NAME_CN = {
    'England - Premier League': '英超',
    'Spain - LaLiga': '西甲',
    'Germany - Bundesliga': '德甲',
    'Italy - Serie A': '意甲',
    'France - Ligue 1': '法甲',
    'International - World Cup': '世界杯',
    'International Clubs - UEFA Champions League': '欧冠',
}

# 五大联赛 + 欧冠 slug
TOP5_LEAGUES = [
    'england-premier-league', 'spain-laliga', 'germany-bundesliga',
    'italy-serie-a', 'france-ligue-1', 'international-clubs-uefa-champions-league',
]


def _get_logo_id(league_name: str, team_name: str):
    """根据联赛名 + 球队英文名查 logo_id（精确+模糊匹配）"""
    row = TeamNameMap.query.filter_by(league_name=league_name, name_en=team_name).first()
    if row and row.logo_id:
        return row.logo_id

    all_rows = TeamNameMap.query.filter_by(league_name=league_name).all()
    tn = team_name.lower().replace('.', '').replace('é', 'e')

    for r in all_rows:
        en = r.name_en.lower().replace('.', '').replace('é', 'e')
        if en in tn or tn in en:
            if r.logo_id:
                return r.logo_id

    stop_words = {'fc', 'sc', 'ac', 'ss', 'us', 'rc', 'cf', 'ud', 'cfc', 'ssc', 'rcd',
                  'sv', 'tsg', 'vfl', 'vfb', 'fsv', 'afc', 'hsc', 'osc', 'calcio',
                  'club', 'de', 'del', 'la', 'el', 'das', 'racing'}
    tn_words = set(tn.split()) - stop_words

    best_id = None
    best_score = 0
    for r in all_rows:
        en = r.name_en.lower().replace('.', '').replace('é', 'e')
        en_words = set(en.split()) - stop_words
        common = tn_words & en_words
        if not common:
            continue
        has_core = any(len(w) >= 4 for w in common)
        score = len(common) + (1 if has_core else 0)
        if score >= 2 and score > best_score and r.logo_id:
            best_score = score
            best_id = r.logo_id

    if best_id:
        return best_id
    return None


def _translate_match(match):
    """翻译队名 + 序列化"""
    home_cn = team_name_service.translate(match.league_name, match.home_team)
    away_cn = team_name_service.translate(match.league_name, match.away_team)
    return {
        'id': match.id,
        'home_team': home_cn,
        'away_team': away_cn,
        'home_logo_id': _get_logo_id(match.league_name, match.home_team),
        'away_logo_id': _get_logo_id(match.league_name, match.away_team),
        'league_name': match.league_name,
        'league_name_cn': LEAGUE_NAME_CN.get(match.league_name, match.league_name),
        'league_slug': match.league_slug,
        'match_date': (match.match_date.isoformat() + '+00:00') if match.match_date else None,
        'status': match.status,
        'scores_home': match.scores_home,
        'scores_away': match.scores_away,
    }


@matches_bp.route('/api/matches', methods=['GET'])
@login_required
def list_matches():
    """比赛列表"""
    status = request.args.get('status')  # pending / live / settled / all
    leagues = request.args.get('leagues')  # comma-separated league slugs
    date_str = request.args.get('date')

    # 基础查询：排除世界杯（未开赛）
    query = Match.query.filter(Match.league_name != 'International - World Cup')

    # 联赛筛选
    if leagues:
        league_slugs = [s.strip() for s in leagues.split(',') if s.strip()]
        if league_slugs:
            query = query.filter(Match.league_slug.in_(league_slugs))

    # 状态筛选
    if status and status != 'all':
        query = query.filter_by(status=status)

    # 已结束比赛的时间范围
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    five_days_ago = today_start - timedelta(days=5)

    if status == 'settled':
        # 五大联赛：过去5天；其他：只当天
        query = query.filter(Match.match_date >= five_days_ago)
    elif status and status != 'all':
        # pending/live：只看未来+今天的
        pass
    else:
        # all 模式：settled 只显示当天
        pass

    # 排序：进行中 → 即将开始(按时间升序) → 已结束(按时间降序)
    sort_order = case(
        (Match.status == 'live', 0),
        (Match.status == 'pending', 1),
        else_=2
    )
    matches = query.order_by(
        sort_order,
        Match.match_date.asc()
    ).limit(50).all()

    # all 模式下：过滤 settled 只保留当天
    if not status or status == 'all':
        matches = [m for m in matches if m.status != 'settled' or m.match_date >= today_start]
    # 已结束：五大联赛5天，其他当天
    if status == 'settled':
        matches = [
            m for m in matches
            if m.league_slug in TOP5_LEAGUES or m.match_date >= today_start
        ]

    # 批量查赔率
    match_ids = [m.id for m in matches]
    odds_match_ids = set()
    if match_ids:
        rows = Odds.query.filter(
            Odds.match_id.in_(match_ids),
            Odds.bookmaker.like('Bet365%')
        ).with_entities(Odds.match_id).distinct().all()
        odds_match_ids = {r[0] for r in rows}

    result = []
    for m in matches:
        item = _translate_match(m)
        item['has_odds'] = m.id in odds_match_ids
        result.append(item)

    return jsonify({'matches': result})


@matches_bp.route('/api/matches/<int:match_id>', methods=['GET'])
@login_required
def match_detail(match_id):
    """比赛详情（含赔率）"""
    match = Match.query.get(match_id)
    if not match:
        return jsonify({'error': '比赛不存在'}), 404

    result = _translate_match(match)

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
