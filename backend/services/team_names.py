# bet365cn — 球队名翻译服务
from models import db, TeamNameMap


class TeamNameService:
    """英文球队名 → 中文翻译"""

    def __init__(self):
        self._cache = None

    def _load_cache(self):
        """加载映射表到内存缓存"""
        if self._cache is not None:
            return
        self._cache = {}
        rows = TeamNameMap.query.all()
        for r in rows:
            key = (r.league_name, r.name_en)
            self._cache[key] = r.name_cn

    def translate(self, league_name: str, name_en: str) -> str:
        """翻译，未命中返回原文"""
        self._load_cache()
        return self._cache.get((league_name, name_en), name_en)

    def translate_team_only(self, name_en: str) -> str:
        """只按球队名翻译（忽略联赛）"""
        self._load_cache()
        for (_, en), cn in self._cache.items():
            if en == name_en:
                return cn
        return name_en


# 单例
team_name_service = TeamNameService()
