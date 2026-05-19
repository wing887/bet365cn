# bet365cn Backend — 数据模型（SQLAlchemy）
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


# ============================================================
# 管理员账号表（super_admin / admin）
# ============================================================
class AdminAccount(db.Model):
    __tablename__ = 'admin_accounts'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='admin')  # 'super_admin' | 'admin'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('admin_accounts.id'), nullable=True)
    
    # Relationships
    coin_operations = db.relationship('CoinTransaction', backref='operator', lazy='dynamic',
                                       foreign_keys='CoinTransaction.operator_id')
    operation_logs = db.relationship('OperationLog', backref='admin', lazy='dynamic')


# ============================================================
# 用户账号表
# ============================================================
class UserAccount(db.Model):
    __tablename__ = 'user_accounts'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    nickname = db.Column(db.String(50), nullable=False)  # "用户001"
    coin_balance = db.Column(db.Integer, default=0, nullable=False)
    status = db.Column(db.String(20), default='active')  # 'active' | 'disabled'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    bets = db.relationship('Bet', backref='user', lazy='dynamic')
    transactions = db.relationship('CoinTransaction', backref='user', lazy='dynamic',
                                    foreign_keys='CoinTransaction.user_id')


# ============================================================
# 比赛表（缓存 odds-api.io 数据）
# ============================================================
class Match(db.Model):
    __tablename__ = 'matches'
    
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.String(20), unique=True, nullable=False, index=True)  # API event ID
    home_team = db.Column(db.String(100), nullable=False)
    away_team = db.Column(db.String(100), nullable=False)
    league_name = db.Column(db.String(100), nullable=False)
    league_slug = db.Column(db.String(100), nullable=False, index=True)
    match_date = db.Column(db.DateTime, nullable=False, index=True)
    status = db.Column(db.String(20), default='pending', index=True)  # pending/live/settled/cancelled
    scores_home = db.Column(db.Integer, default=0)
    scores_away = db.Column(db.Integer, default=0)
    scores_p1_home = db.Column(db.Integer, default=0)
    scores_p1_away = db.Column(db.Integer, default=0)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    odds = db.relationship('Odds', backref='match', lazy='dynamic')
    bets = db.relationship('Bet', backref='match_rel', lazy='dynamic')
    settlements = db.relationship('Settlement', backref='match', lazy='dynamic')


# ============================================================
# 赔率表
# ============================================================
class Odds(db.Model):
    __tablename__ = 'odds'
    
    id = db.Column(db.Integer, primary_key=True)
    match_id = db.Column(db.Integer, db.ForeignKey('matches.id'), nullable=False, index=True)
    bookmaker = db.Column(db.String(20), nullable=False)  # 'Bet365' | 'Sbobet'
    market_type = db.Column(db.String(20), nullable=False)  # 'ML' | 'Spread' | 'Totals' | 'CS'
    # JSON: ML → {home, draw, away} | Spread → {hdp, home, away} | Totals → {hdp, over, under} | CS → [{label, odds}...]
    odds_data = db.Column(db.JSON, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.Index('ix_odds_match_market', 'match_id', 'market_type', 'bookmaker'),
    )


# ============================================================
# 下注表
# ============================================================
class Bet(db.Model):
    __tablename__ = 'bets'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user_accounts.id'), nullable=False, index=True)
    match_id = db.Column(db.Integer, db.ForeignKey('matches.id'), nullable=False, index=True)
    market_type = db.Column(db.String(20), nullable=False)  # 'ML' | 'Spread' | 'Totals' | 'CS'
    selection = db.Column(db.String(20), nullable=False)  # 'home'/'draw'/'away' | 'over'/'under' | '2-1'...
    odds_value = db.Column(db.Float, nullable=False)  # 下注时的赔率
    bet_amount = db.Column(db.Integer, nullable=False)  # 下注金币数
    potential_win = db.Column(db.Integer, nullable=False)  # 预估奖励
    status = db.Column(db.String(20), default='pending', index=True)  # pending/won/lost/push/refunded
    win_amount = db.Column(db.Integer, default=0)  # 实际赢取金额
    placed_at = db.Column(db.DateTime, default=datetime.utcnow)
    settled_at = db.Column(db.DateTime, nullable=True)
    
    __table_args__ = (
        db.Index('ix_bets_user_status', 'user_id', 'status'),
        db.Index('ix_bets_match_status', 'match_id', 'status'),
    )


# ============================================================
# 金币流水表
# ============================================================
class CoinTransaction(db.Model):
    __tablename__ = 'coin_transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user_accounts.id'), nullable=False, index=True)
    amount = db.Column(db.Integer, nullable=False)  # 正=加 | 负=减
    type = db.Column(db.String(20), nullable=False)  # admin_add/admin_deduct/bet_place/bet_win/bet_refund
    operator_id = db.Column(db.Integer, db.ForeignKey('admin_accounts.id'), nullable=True)  # 操作人（管理员）
    bet_id = db.Column(db.Integer, db.ForeignKey('bets.id'), nullable=True)  # 关联下注
    note = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.Index('ix_coin_tx_user_time', 'user_id', 'created_at'),
    )


# ============================================================
# 结算记录表
# ============================================================
class Settlement(db.Model):
    __tablename__ = 'settlements'
    
    id = db.Column(db.Integer, primary_key=True)
    match_id = db.Column(db.Integer, db.ForeignKey('matches.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # 'pending' | 'confirmed' | 'cancelled'
    total_bets = db.Column(db.Integer, default=0)  # 总注数
    total_users = db.Column(db.Integer, default=0)  # 参与用户数
    total_payout = db.Column(db.Integer, default=0)  # 总赔付金额
    detail = db.Column(db.JSON, default=dict)  # 结算明细
    confirmed_by = db.Column(db.Integer, db.ForeignKey('admin_accounts.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    confirmed_at = db.Column(db.DateTime, nullable=True)


# ============================================================
# 操作日志表
# ============================================================
class OperationLog(db.Model):
    __tablename__ = 'operation_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('admin_accounts.id'), nullable=False, index=True)
    action = db.Column(db.String(50), nullable=False)  # 操作类型
    target_type = db.Column(db.String(30))  # user/admin/match
    target_id = db.Column(db.Integer)
    detail = db.Column(db.JSON, default=dict)  # 操作详情
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ============================================================
# 球队名映射表
# ============================================================
class TeamNameMap(db.Model):
    __tablename__ = 'team_names'
    
    id = db.Column(db.Integer, primary_key=True)
    league_name = db.Column(db.String(100), nullable=False)
    name_en = db.Column(db.String(100), nullable=False)  # API 英文名
    name_cn = db.Column(db.String(50), nullable=False)   # 中文名
    
    __table_args__ = (
        db.UniqueConstraint('league_name', 'name_en', name='uq_team_name'),
    )
