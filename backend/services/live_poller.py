# bet365cn — 滚球实时赔率轮询器
"""
高频拉取 live 比赛的赔率和比分，更新数据库。
频率: 30秒/次（可配置），仅跟踪 status='live' 的比赛。

架构：
  live_poll() 为主入口，每30秒执行一次。
  - 查询所有 live 比赛
  - 逐个拉取赔率（odds-api.io /odds endpoint）
  - 同时更新比分/比赛时间（从 events 的 period scores 推算）
  - 写入 Odds 和 Match 表

WebSocket 升级路径：
  当 odds-api.io WebSocket 端点可用时，替换此轮询器。
  接口保持一致：都是更新 Odds + Match 表。
"""
import logging
import time
from datetime import datetime, timedelta
from models import db, Match, Odds
from services.odds_fetcher import OddsApiCollector

logger = logging.getLogger(__name__)

BOOKMAKERS = ['Bet365']

# 从比分推算比赛时间（上半场≤45，下半场45+）
def _estimate_match_minute(scores, period_scores):
    """
    根据 period scores 推算当前分钟数
    period_scores: {'p1': {'home': 1, 'away': 0}, 'p2': {'home': 0, 'away': 0}}
    返回: (match_minute, match_period)
    """
    home = scores.get('home', 0) or 0
    away = scores.get('away', 0) or 0
    periods = period_scores or {}
    
    p1 = periods.get('p1', {}) or {}
    p2 = periods.get('p2', {}) or {}
    
    p1_home = p1.get('home', 0) or 0
    p1_away = p1.get('away', 0) or 0
    p2_home = p2.get('home', 0) or 0
    p2_away = p2.get('away', 0) or 0
    
    # 如果 p2 有比分 → 下半场
    if p2_home > 0 or p2_away > 0:
        # 下半场大约过了 p2 进球×10分钟，最少45分钟
        minute = 45 + max(p2_home + p2_away, 1) * 10
        return min(minute, 90), 'second_half'
    
    # 如果 p1 有比分 → 上半场（但可能已经进入下半场还没进球）
    if p1_home > 0 or p1_away > 0:
        # 上半场
        minute = max(p1_home + p1_away, 1) * 10
        return min(minute, 45), 'first_half'
    
    # 无进球 → 用开球时间推算
    return None, None


def live_poll():
    """
    滚球赔率高频同步（30秒/次）
    - 拉取所有 live 比赛的赔率
    - 更新比分和比赛时间
    """
    from flask import current_app
    app = current_app._get_current_object()
    collector = OddsApiCollector(
        api_keys=app.config['ODDS_API_KEYS'],
        proxy=app.config.get('ODDS_API_PROXY'),
    )
    
    max_tracked = app.config.get('LIVE_MAX_TRACKED_MATCHES', 15)
    
    # 获取所有 live 比赛
    live_matches = Match.query.filter_by(status='live').order_by(
        Match.updated_at.asc()
    ).limit(max_tracked).all()
    
    if not live_matches:
        return
    
    logger.info(f'滚球同步: {len(live_matches)} 场 live 比赛')
    updated_odds = 0
    updated_match = 0
    
    for match in live_matches:
        # 限速：避免触发 API 限额
        time.sleep(0.3)
        
        try:
            # 1. 拉取赔率
            odds_data = collector.fetch_odds(match.event_id, BOOKMAKERS)
            
            for bm_name, markets in odds_data.items():
                for market_type, odds_json in markets.items():
                    market_status = odds_json.pop('status', 'active') if isinstance(odds_json, dict) else 'active'
                    
                    existing = Odds.query.filter_by(
                        match_id=match.id,
                        bookmaker=bm_name,
                        market_type=market_type,
                    ).first()
                    
                    if existing:
                        existing.odds_data = odds_json
                        existing.status = market_status
                        existing.updated_at = datetime.utcnow()
                    else:
                        new_odds = Odds(
                            match_id=match.id,
                            bookmaker=bm_name,
                            market_type=market_type,
                            odds_data=odds_json,
                            status=market_status,
                        )
                        db.session.add(new_odds)
                    updated_odds += 1
            
            # 2. 拉取比赛状态（比分+时间）
            events = collector.fetch_events(
                sport='football',
                league_slug=match.league_slug,
                status_filter='live',
            )
            
            for evt in events:
                if evt['event_id'] == match.event_id:
                    # 更新比分
                    if (match.scores_home != evt['scores_home'] or 
                        match.scores_away != evt['scores_away'] or
                        match.scores_p1_home != evt['scores_p1_home'] or
                        match.scores_p1_away != evt['scores_p1_away']):
                        match.scores_home = evt['scores_home']
                        match.scores_away = evt['scores_away']
                        match.scores_p1_home = evt['scores_p1_home']
                        match.scores_p1_away = evt['scores_p1_away']
                        updated_match += 1
                    
                    # 推算比赛时间
                    # 通过开球时间估算（API period scores 可能不精确）
                    if match.match_date:
                        elapsed = (datetime.utcnow() - match.match_date).total_seconds()
                        # 足球比赛约105分钟（含中场休息15分钟）
                        if 0 < elapsed < 6300:  # ≤105分钟
                            minute = int(elapsed / 60)
                            # 减去中场休息
                            if minute > 45:
                                half_time_elapsed = minute - 15  # 下半场实际时间
                                if half_time_elapsed > 45:
                                    minute = min(90, half_time_elapsed)
                                else:
                                    minute = max(46, half_time_elapsed)
                            match.match_minute = min(90, max(1, minute))
                            match.match_period = 'first_half' if match.match_minute <= 45 else 'second_half'
                    
                    match.updated_at = datetime.utcnow()
                    break
            
        except Exception as e:
            logger.warning(f'滚球同步失败 [{match.event_id}]: {e}')
            continue
    
    db.session.commit()
    logger.info(f'滚球同步完成: 赔率 {updated_odds} 条, 比分 {updated_match} 场')
