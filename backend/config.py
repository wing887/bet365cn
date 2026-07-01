# bet365cn Backend — 配置
import os

class Config:
    """基础配置"""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'bet365cn-dev-secret-key-change-in-production')
    
    # 数据库（开发用 SQLite，生产切 PostgreSQL）
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'sqlite:///' + os.path.join(os.path.dirname(__file__), 'bet365cn.db')
    )
    
    # Redis（缓存，可选）
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    
    # JWT
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-change-me')
    JWT_ACCESS_TOKEN_EXPIRES = int(os.environ.get('JWT_EXPIRES', '14400'))  # 默认 4 小时
    
    # Odds-API.io（仅从环境变量读取，不硬编码 Key）
    _keys_str = os.environ.get('ODDS_API_KEYS', '')
    ODDS_API_KEYS = [k.strip() for k in _keys_str.split(',') if k.strip()]
    ODDS_API_BASE = 'https://api.odds-api.io/v3'
    ODDS_API_PROXY = os.environ.get('ODDS_API_PROXY', '')  # 仅从环境变量读取
    
    # CORS 白名单
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*').split(',')
    
    # 联赛配置
    LEAGUES = {
        '英超': 'england-premier-league',
        '德甲': 'germany-bundesliga',
        '西甲': 'spain-laliga',
        '意甲': 'italy-serie-a',
        '法甲': 'france-ligue-1',
        '世界杯': 'international-world-cup',
        '欧冠': 'international-clubs-uefa-champions-league',
    }
    
    # 下注配置
    MIN_BET_AMOUNT = 50
    
    # 滚球配置
    LIVE_POLL_INTERVAL = 30          # 滚球赔率拉取间隔（秒）
    LIVE_ODDS_STALE_SECONDS = 30     # 滚球赔率过期阈值（秒）
    LIVE_MAX_TRACKED_MATCHES = 15    # 最多同时跟踪的滚球比赛数
    LIVE_DEFAULT_LIMIT_RATIO = 0.6   # 滚球限额比例（相对赛前）
    
    # 新盘口类型
    LIVE_MARKET_TYPES = ['ML', 'Spread', 'Totals', 'CS', 'NG', 'TG', 'BTTS', 'HR']
    
    # 全部盘口类型 (match hga039)
    ALL_MARKET_TYPES = [
        'ML',           # 独赢 1X2
        'Spread',       # 让球 Handicap
        'Totals',       # 大小球 Over/Under
        'CS',           # 波胆 Correct Score
        '1H_ML',        # 上半场独赢
        '1H_Spread',    # 上半场让球
        '1H_Totals',    # 上半场大小球
        'Kickoff',      # 开球
        'BTTS',         # 双方球队进球
        'OddEven',      # 单/双
        'Corner_Spread',   # 角球让球
        'Corner_Totals',   # 角球大小
        'Corner_ML',       # 角球独赢
        'Corner_OddEven',  # 角球单双
        'Cards_Spread',    # 罚牌让球
        'Cards_Totals',    # 罚牌大小
        'Cards_ML',        # 罚牌独赢
        'Cards_OddEven',   # 罚牌单双
        'TeamGoals',    # 球队进球数
        'FirstLastGoal',# 最先/最后进球
        'HTFT',         # 半场/全场
        'WinMargin',    # 净胜球数
        'DoubleChance', # 双重机会
        'PlayerGoals',  # 进球球员
        'Combo_ML_OU',  # 独赢 & 进球大小
        'Combo_ML_BTTS',# 独赢 & BTTS
        'Combo_OU_BTTS',# 大小 & BTTS
    ]
    
    # 盘口中文名映射
    MARKET_NAMES_CN = {
        'ML': '独赢',
        'Spread': '让球',
        'Totals': '大/小',
        'CS': '波胆',
        '1H_ML': '上半场独赢',
        '1H_Spread': '上半场让球',
        '1H_Totals': '上半场大/小',
        'Kickoff': '开球',
        'BTTS': '双方球队进球',
        'OddEven': '单/双',
        'Corner_Spread': '角球-让球',
        'Corner_Totals': '角球-大/小',
        'Corner_ML': '角球-独赢',
        'Corner_OddEven': '角球-单/双',
        'Cards_Spread': '罚牌-让球',
        'Cards_Totals': '罚牌-大/小',
        'Cards_ML': '罚牌-独赢',
        'Cards_OddEven': '罚牌-单/双',
        'TeamGoals': '球队进球数',
        'FirstLastGoal': '最先/最后进球',
        'HTFT': '半场/全场',
        'WinMargin': '净胜球数',
        'DoubleChance': '双重机会',
        'PlayerGoals': '进球球员',
        'Combo_ML_OU': '独赢&进球大/小',
        'Combo_ML_BTTS': '独赢&双方进球',
        'Combo_OU_BTTS': '进球大/小&双方进球',
    }
    
    # 盘口分组 (前端Tab)
    MARKET_TABS = {
        'main': ['ML', 'Spread', 'Totals', '1H_Spread', '1H_Totals', '1H_ML', 'Kickoff', 'BTTS'],
        'spread_totals': ['Spread', 'Totals'],
        'corner': ['Corner_Spread', 'Corner_Totals', 'Corner_ML', 'Corner_OddEven'],
        'cards': ['Cards_Spread', 'Cards_Totals', 'Cards_ML', 'Cards_OddEven'],
        'goals': ['OddEven', 'TeamGoals', 'FirstLastGoal', 'HTFT', 'WinMargin', 'DoubleChance'],
        'combo': ['Combo_ML_OU', 'Combo_ML_BTTS', 'Combo_OU_BTTS'],
        'cs': ['CS'],
        'player': ['PlayerGoals'],
    }
    

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(os.path.dirname(__file__), 'bet365cn.db')


class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'postgresql://bet365cn:password@localhost:5432/bet365cn')
