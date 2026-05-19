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
    
    # Odds-API.io
    ODDS_API_KEY = os.environ.get('ODDS_API_KEY', 'cbed45cdeb7ea196b7ba4335757cf3d4beaf6654ee2b73b30a29fd2c2b38e46b')
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
    }
    
    # 下注配置
    MIN_BET_AMOUNT = 50
    

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(os.path.dirname(__file__), 'bet365cn.db')


class ProductionConfig(Config):
    DEBUG = False
    # PostgreSQL: postgresql://user:pass@host:5432/bet365cn
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'postgresql://bet365cn:password@localhost:5432/bet365cn')
