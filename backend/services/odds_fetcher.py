# bet365cn — Odds-API.io 数据采集器
import requests
import logging
import time
from datetime import datetime
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class OddsApiCollector:
    """odds-api.io 数据采集器"""

    def __init__(self, api_key: str, proxy: str = None):
        self.base_url = 'https://api.odds-api.io/v3'
        self.api_key = api_key
        self.proxies = {'http': proxy, 'https': proxy} if proxy else None
        self.request_count = 0
        self.rate_limit_remaining = 200

    def _fetch(self, endpoint: str, params: dict = None) -> dict:
        """发送 API 请求"""
        url = f'{self.base_url}{endpoint}'
        params = params or {}
        params['apiKey'] = self.api_key

        try:
            resp = requests.get(url, params=params, proxies=self.proxies, timeout=60)
            resp.raise_for_status()
            self.request_count += 1

            remaining = resp.headers.get('x-ratelimit-remaining')
            if remaining:
                self.rate_limit_remaining = int(remaining)

            return resp.json()
        except requests.exceptions.HTTPError as e:
            status = e.response.status_code if hasattr(e, 'response') else None
            if status == 404:
                logger.debug(f'API 404 (无数据): {endpoint}')
                return []
            logger.error(f'API 请求失败 [{status}]: {endpoint} — {e}')
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f'网络请求失败: {endpoint} — {e}')
            raise

    def fetch_events(
        self,
        sport: str = 'football',
        leagues: list = None,
        status_filter: str = None,
    ) -> List[dict]:
        """
        获取比赛列表
        leagues: [('英超', 'england-premier-league'), ...]
        status_filter: 'pending' | 'live' | None (all)
        """
        params = {'sport': sport}
        if status_filter:
            params['status'] = status_filter

        raw = self._fetch('/events', params)
        logger.info(f'API 返回 {len(raw)} 场足球比赛')

        events = []
        target_slugs = {slug for _, slug in (leagues or [])}

        for e in raw:
            slug = e.get('league', {}).get('slug', '')
            if target_slugs and slug not in target_slugs:
                continue

            status = e.get('status', '').lower()
            if status in ('cancelled',):
                continue

            scores = e.get('scores', {}) or {}
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
            })

            # 半场比分
            periods = scores.get('periods', {}) or {}
            p1 = periods.get('p1', {}) or {}
            if p1:
                events[-1]['scores_p1_home'] = p1.get('home', 0) or 0
                events[-1]['scores_p1_away'] = p1.get('away', 0) or 0

        logger.info(f'筛选后 {len(events)} 场（目标联赛）')
        return events

    def fetch_odds(
        self,
        event_id: str,
        bookmakers: list = None,
    ) -> dict:
        """
        获取单场比赛赔率
        返回: {bookmaker: {ML: ..., Spread: ..., Totals: ..., CS: ...}}
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

                if name == 'ML' and odds:
                    o = odds[0]
                    bm_result['ML'] = {
                        'home': float(o.get('home', 0)) if o.get('home', 'N/A') != 'N/A' else 0,
                        'draw': float(o.get('draw', 0)) if o.get('draw', 'N/A') != 'N/A' else 0,
                        'away': float(o.get('away', 0)) if o.get('away', 'N/A') != 'N/A' else 0,
                    }

                elif name == 'Spread' and odds:
                    o = odds[0]
                    bm_result['Spread'] = {
                        'hdp': float(o.get('hdp', 0)),
                        'home': float(o.get('home', 0)),
                        'away': float(o.get('away', 0)),
                    }

                elif name == 'Totals' and odds:
                    o = odds[0]  # 取第一条阈值
                    bm_result['Totals'] = {
                        'hdp': float(o.get('hdp', 0)),
                        'over': float(o.get('over', 0)),
                        'under': float(o.get('under', 0)),
                    }

                elif name == 'Correct Score' and odds:
                    # 按赔率排序，取前10个最低赔率
                    scores = []
                    for o in odds:
                        label = o.get('label', '')
                        odd_val = float(o.get('odds', 0))
                        if label and odd_val > 0:
                            scores.append({'label': label, 'odds': odd_val})
                    scores.sort(key=lambda x: x['odds'])
                    bm_result['CS'] = {'scores': scores[:10]}

            if bm_result:
                result[bm_name] = bm_result

        return result
