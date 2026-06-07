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
    JWT_ACCESS_TOKEN_EXPIRES = 86400  # 24小时
    
    # Odds-API.io（双 Key 自动轮换）
    ODDS_API_KEYS = [
        key.strip() for key in os.environ.get(
            'ODDS_API_KEYS',
            'cbed45cdeb7ea196b7ba4335757cf3d4beaf6654ee2b73b30a29fd2c2b38e46b,'
            'a26c35648273b834d344da959c383d9700e75e5279d574b81a61887f16b6ea9b,'
            '5642057727ebd5163744ae40ef81b330df1f88df061463a5941cfcd25a4112c5'
        ).split(',') if key.strip()
    ]
    ODDS_API_BASE = 'https://api.odds-api.io/v3'
    ODDS_API_PROXY = os.environ.get('ODDS_API_PROXY', 'http://172.18.176.1:10808')
    
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
    

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(os.path.dirname(__file__), 'bet365cn.db')


class ProductionConfig(Config):
    DEBUG = False
    # PostgreSQL: postgresql://user:pass@host:5432/bet365cn
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'postgresql://bet365cn:password@localhost:5432/bet365cn')
