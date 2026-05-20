# bet365cn — 数据同步服务
"""
连接 odds-api.io 采集器和数据库，实现：
- sync_matches()    — 拉取比赛数据，更新 matches 表
- sync_odds()       — 拉取赔率数据，更新 odds 表
- check_settled()   — 检测已结算比赛，更新比分
"""
import logging
import time
from datetime import datetime
from models import db, Match, Odds
from services.odds_fetcher import OddsApiCollector

logger = logging.getLogger(__name__)

# 五大联赛 + 世界杯
LEAGUES = [
    ('英超', 'england-premier-league'),
    ('德甲', 'germany-bundesliga'),
    ('西甲', 'spain-laliga'),
    ('意甲', 'italy-serie-a'),
    ('法甲', 'france-ligue-1'),
    ('世界杯', 'international-world-cup'),
]

BOOKMAKERS = ['Bet365']


def _get_collector(app):
    """获取采集器实例"""
    return OddsApiCollector(
        api_keys=app.config['ODDS_API_KEYS'],
        proxy=app.config.get('ODDS_API_PROXY'),
    )


def sync_matches():
    """
    拉取五大联赛+世界杯的比赛数据（逐联赛请求，避免超时）
    频率：每 30 分钟
    """
    from flask import current_app
    app = current_app._get_current_object()
    collector = _get_collector(app)

    logger.info('开始同步比赛数据...')
    all_events = []
    for league_name, league_slug in LEAGUES:
        try:
            events = collector.fetch_events(sport='football', league_slug=league_slug)
            all_events.extend(events)
        except Exception as e:
            logger.warning(f'{league_name} 数据获取失败: {e}')
            continue

    if not all_events:
        logger.warning('所有联赛数据获取失败')
        return

    updated = 0
    new = 0
    settled = 0

    for e in all_events:
        match = Match.query.filter_by(event_id=e['event_id']).first()

        if match:
            # 更新状态和比分
            changed = False
            if match.status != e['status']:
                match.status = e['status']
                changed = True
            if match.scores_home != e['scores_home'] or match.scores_away != e['scores_away']:
                match.scores_home = e['scores_home']
                match.scores_away = e['scores_away']
                match.scores_p1_home = e['scores_p1_home']
                match.scores_p1_away = e['scores_p1_away']
                changed = True
            if changed:
                match.updated_at = datetime.utcnow()
                updated += 1
            if e['status'] == 'settled':
                settled += 1
        else:
            # 新比赛
            match = Match(
                event_id=e['event_id'],
                home_team=e['home_team'],
                away_team=e['away_team'],
                league_name=e['league_name'],
                league_slug=e['league_slug'],
                match_date=datetime.fromisoformat(e['match_date'].replace('Z', '+00:00')) if e['match_date'] else datetime.utcnow(),
                status=e['status'],
                scores_home=e['scores_home'],
                scores_away=e['scores_away'],
                scores_p1_home=e['scores_p1_home'],
                scores_p1_away=e['scores_p1_away'],
            )
            db.session.add(match)
            new += 1

    db.session.commit()
    logger.info(f'比赛同步完成: 新增 {new}, 更新 {updated}, 其中已结算 {settled}')


def sync_odds():
    """
    拉取 pending 比赛的赔率（仅限今日赛事）
    频率：每 10 分钟
    """
    from flask import current_app
    app = current_app._get_current_object()
    collector = _get_collector(app)

    # 仅今日 pending/live 的比赛（减少 API 调用量）
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    matches = Match.query.filter(
        Match.status.in_(['pending', 'live']),
        Match.match_date >= today,
    ).limit(50).all()  # 最多50场，留足余量
    logger.info(f'开始同步赔率: {len(matches)} 场今日比赛...')

    updated = 0
    for i, match in enumerate(matches):
        # 限速：每秒最多 2 个请求（200次/小时安全线）
        if i > 0 and i % 2 == 0:
            time.sleep(1.2)
        
        try:
            odds_data = collector.fetch_odds(match.event_id, BOOKMAKERS)

            for bm_name, markets in odds_data.items():
                for market_type, odds_json in markets.items():
                    # Upsert: 查找已有赔率记录
                    existing = Odds.query.filter_by(
                        match_id=match.id,
                        bookmaker=bm_name,
                        market_type=market_type,
                    ).first()

                    if existing:
                        existing.odds_data = odds_json
                        existing.updated_at = datetime.utcnow()
                    else:
                        new_odds = Odds(
                            match_id=match.id,
                            bookmaker=bm_name,
                            market_type=market_type,
                            odds_data=odds_json,
                        )
                        db.session.add(new_odds)
                    updated += 1

        except Exception as e:
            logger.warning(f'赔率获取失败 [{match.event_id}]: {e}')
            continue

    db.session.commit()
    logger.info(f'赔率同步完成: 更新 {updated} 条')


def check_settled():
    """
    检查已结束比赛，更新比分和状态
    频率：每 15 分钟
    同时创建待结算记录
    """
    from flask import current_app
    app = current_app._get_current_object()
    collector = _get_collector(app)

    # 查 pending/live 的比赛，看是否已变为 settled
    active_matches = Match.query.filter(Match.status.in_(['pending', 'live'])).all()

    # 逐联赛拉取 settled 比赛
    all_events = []
    for league_name, league_slug in LEAGUES:
        try:
            events = collector.fetch_events(sport='football', league_slug=league_slug, status_filter='settled')
            all_events.extend(events)
        except Exception as e:
            logger.warning(f'{league_name} settled 查询失败: {e}')
            continue

    if not all_events:
        logger.warning('所有联赛 settled 数据获取失败')
        return

    settled_ids = {e['event_id'] for e in all_events}
    updated = 0

    for match in active_matches:
        if match.event_id in settled_ids:
            # 找到对应事件，更新比分
            evt = next((e for e in all_events if e['event_id'] == match.event_id), None)
            if evt:
                match.status = 'settled'
                match.scores_home = evt['scores_home']
                match.scores_away = evt['scores_away']
                match.scores_p1_home = evt['scores_p1_home']
                match.scores_p1_away = evt['scores_p1_away']
                match.updated_at = datetime.utcnow()
                updated += 1

    db.session.commit()
    if updated:
        logger.info(f'检测到 {updated} 场比赛已结算')
