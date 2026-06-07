# bet365cn — Odds-API.io 数据采集器
import requests
import logging
import time
from datetime import datetime
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class OddsApiCollector:
    """odds-api.io 数据采集器（双 Key 自动轮换）"""

    def __init__(self, api_keys: list, proxy: str = None):
        self.base_url = 'https://api.odds-api.io/v3'
        self.api_keys = api_keys
        self.current_key_idx = 0
        self.proxies = {'http': proxy, 'https': proxy} if proxy else None
        self.request_count = 0
        self.rate_limit_remaining = 200

    def _get_key(self) -> str:
        return self.api_keys[self.current_key_idx]

    def _switch_key(self) -> bool:
        if self.current_key_idx < len(self.api_keys) - 1:
            self.current_key_idx += 1
            return True
        return False

    def _fetch(self, endpoint: str, params: dict = None) -> dict:
        """发送 API 请求（支持 Key 轮换 + 401 自动切换）"""
        url = f'{self.base_url}{endpoint}'
        params = params or {}
        
        for attempt in range(len(self.api_keys)):
            params['apiKey'] = self._get_key()
            
            try:
                resp = requests.get(url, params=params, proxies=self.proxies, timeout=60)
                
                if resp.status_code == 401:
                    if self._switch_key():
                        continue
                    raise Exception('所有 API key 已失效')
                
                resp.raise_for_status()
                self.request_count += 1
                
                remaining = resp.headers.get('x-ratelimit-remaining')
                if remaining:
                    self.rate_limit_remaining = int(remaining)
                
                return resp.json()
                
            except requests.exceptions.HTTPError as e:
                status = e.response.status_code if hasattr(e, 'response') else None
                if status == 404:
                    return []
                if status == 429:
                    raise
                raise
            except requests.exceptions.RequestException:
                raise

    def fetch_events(
        self,
        sport: str = 'football',
        league_slug: str = None,
        status_filter: str = None,
    ) -> List[dict]:
        """
        获取比赛列表（单联赛单次请求，避免超时）
        league_slug: 'england-premier-league' 等
        status_filter: 'pending' | 'live' | None (all)
        """
        params = {'sport': sport}
        if league_slug:
            params['league'] = league_slug  # API 原生过滤，响应仅 ~3KB，1秒内完成
        if status_filter:
            params['status'] = status_filter

        raw = self._fetch('/events', params)
        logger.info(f'API 返回 {len(raw)} 场比赛 [{league_slug or "all"}]')

        events = []
        for e in raw:
            status = e.get('status', '').lower()
            if status in ('cancelled',):
                continue

            scores = e.get('scores', {}) or {}
            slug = e.get('league', {}).get('slug', '')
            events.append({
                'event_id': str(e['id']),
                'home_team': e['home'],
                'away_team': e['away'],
                'league_name': e.get('league', {}).get('name', ''),
                'league_slug': slug,
                'match_date': e.get('date', ''),
                'status': status,
                'scores_home': scores.get('home', 0) or 0,
                'scores_away': scores.get('away', 0) or 0,
                'scores_p1_home': 0,
                'scores_p1_away': 0,
                'match_minute': None,  # live_poller 负责估算
                'match_period': None,
            })

            # 半场比分
            periods = scores.get('periods', {}) or {}
            p1 = periods.get('p1', {}) or {}
            if p1:
                events[-1]['scores_p1_home'] = p1.get('home', 0) or 0
                events[-1]['scores_p1_away'] = p1.get('away', 0) or 0

        logger.info(f'有效比赛 {len(events)} 场 [{league_slug or "all"}]')
        return events

    def fetch_odds(
        self,
        event_id: str,
        bookmakers: list = None,
    ) -> dict:
        """
        获取单场比赛赔率
        返回: {bookmaker: {ML: {data:..., status:...}, Spread: ..., Totals: ..., CS: ...}}
        status: 'active' | 'suspended' | 'closed'
        """
        if bookmakers is None:
            bookmakers = ['Bet365']

        params = {
            'eventId': event_id,
            'bookmakers': ','.join(bookmakers),
        }

        raw = self._fetch('/odds', params)
        if not raw:
            return {}

        result = {}
        bm_data = raw.get('bookmakers', {}) or {}

        for bm_name, markets in bm_data.items():
            if not markets:
                continue
            bm_result = {}

            for market in markets:
                name = market.get('name', '')
                odds = market.get('odds', [])
                # 检测市场状态（API 可能返回 status 字段，如 'TRADING' 或 'SUSPENDED'）
                market_status = market.get('status', 'TRADING')

                if name == 'ML' and odds:
                    o = odds[0]
                    home_val = o.get('home', 'N/A')
                    draw_val = o.get('draw', 'N/A')
                    away_val = o.get('away', 'N/A')
                    # 全部 N/A = 封盘
                    if home_val == 'N/A' and draw_val == 'N/A' and away_val == 'N/A':
                        market_status = 'suspended'
                    else:
                        market_status = 'active'
                    bm_result['ML'] = {
                        'home': float(home_val) if home_val != 'N/A' else 0,
                        'draw': float(draw_val) if draw_val != 'N/A' else 0,
                        'away': float(away_val) if away_val != 'N/A' else 0,
                        'status': market_status,
                    }

                elif name == 'Spread' and odds:
                    o = odds[0]
                    home_val = o.get('home', 'N/A')
                    away_val = o.get('away', 'N/A')
                    if home_val == 'N/A' and away_val == 'N/A':
                        market_status = 'suspended'
                    else:
                        market_status = 'active'
                    bm_result['Spread'] = {
                        'hdp': float(o.get('hdp', 0)),
                        'home': float(home_val) if home_val != 'N/A' else 0,
                        'away': float(away_val) if away_val != 'N/A' else 0,
                        'status': market_status,
                    }

                elif name == 'Totals' and odds:
                    o = odds[0]
                    over_val = o.get('over', 'N/A')
                    under_val = o.get('under', 'N/A')
                    if over_val == 'N/A' and under_val == 'N/A':
                        market_status = 'suspended'
                    else:
                        market_status = 'active'
                    bm_result['Totals'] = {
                        'hdp': float(o.get('hdp', 0)),
                        'over': float(over_val) if over_val != 'N/A' else 0,
                        'under': float(under_val) if under_val != 'N/A' else 0,
                        'status': market_status,
                    }

                elif name == 'Correct Score' and odds:
                    scores = []
                    for o in odds:
                        label = o.get('label', '')
                        odd_val_str = o.get('odds', 'N/A')
                        odd_val = float(odd_val_str) if odd_val_str != 'N/A' else 0
                        if label and odd_val > 0:
                            scores.append({'label': label, 'odds': odd_val})
                    if scores:
                        scores.sort(key=lambda x: x['odds'])
                        bm_result['CS'] = {
                            'scores': scores[:10],
                            'status': 'active',
                        }
                    else:
                        bm_result['CS'] = {
                            'scores': [],
                            'status': 'suspended',
                        }

            if bm_result:
                result[bm_name] = bm_result

        return result
