# bet365cn — 球队名翻译服务
from models import db, TeamNameMap
import logging

logger = logging.getLogger(__name__)

STOP_WORDS = {'fc', 'sc', 'ac', 'ss', 'us', 'rc', 'cf', 'ud', 'cfc', 'ssc', 'rcd',
              'sv', 'tsg', 'vfl', 'vfb', 'fsv', 'afc', 'hsc', 'osc', 'calcio',
              'club', 'de', 'del', 'la', 'el', 'das', 'racing'}


def _normalize(s: str) -> str:
    return s.lower().replace('.', '').replace('é', 'e').replace('ö', 'o').replace('ü', 'u').replace('ä', 'a').strip()


class TeamNameService:
    """英文球队名 → 中文翻译（精确+模糊匹配）"""

    def __init__(self):
        self._cache = None
        self._by_league = {}  # {league_name: [(name_en, name_cn), ...]}

    def _load_cache(self):
        if self._cache is not None:
            return
        self._cache = {}
        self._by_league = {}
        rows = TeamNameMap.query.all()
        for r in rows:
            key = (r.league_name, r.name_en)
            self._cache[key] = r.name_cn
            if r.league_name not in self._by_league:
                self._by_league[r.league_name] = []
            self._by_league[r.league_name].append((r.name_en, r.name_cn))

    def _fuzzy_match(self, league_name: str, name_en: str) -> str:
        """模糊匹配：在指定联赛中查找最接近的队名"""
        candidates = self._by_league.get(league_name, [])
        if not candidates:
            return name_en

        tn = _normalize(name_en)
        tn_words = set(tn.split()) - STOP_WORDS

        best = None
        best_score = 0

        for en, cn in candidates:
            en_norm = _normalize(en)
            if en_norm in tn or tn in en_norm:
                return cn
            en_words = set(en_norm.split()) - STOP_WORDS
            common = tn_words & en_words
            if not common:
                continue
            # 共同词中必须有长度≥4的核心词
            has_core = any(len(w) >= 4 for w in common)
            score = len(common) + (1 if has_core else 0)
            if score >= 2 and score > best_score:
                best_score = score
                best = cn

        if best:
            return best
        return name_en

    def translate(self, league_name: str, name_en: str) -> str:
        """翻译，精确 → 模糊，都未命中返回原文"""
        self._load_cache()
        result = self._cache.get((league_name, name_en))
        if result:
            return result
        return self._fuzzy_match(league_name, name_en)

    def translate_team_only(self, name_en: str) -> str:
        """只按球队名翻译（忽略联赛）"""
        self._load_cache()
        for (_, en), cn in self._cache.items():
            if en == name_en:
                return cn
        return name_en


# 单例
team_name_service = TeamNameService()
