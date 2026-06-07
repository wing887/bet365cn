#!/usr/bin/env python3
"""
数据库迁移脚本 — 滚球 v3.0
为 matches 表添加 match_minute/match_period 列
为 bet_limits 表添加 live_max_bet_amount 列

本地 SQLite 直接执行；服务器 PostgreSQL 需手动执行 SQL 部分。
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'bet365cn.db')

def migrate_sqlite():
    """本地 SQLite 迁移"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # matches 表新增列
    for col, col_type in [
        ('match_minute', 'INTEGER'),
        ('match_period', 'VARCHAR(20)'),
    ]:
        try:
            cur.execute(f'ALTER TABLE matches ADD COLUMN {col} {col_type}')
            print(f'  ✅ matches.{col} 已添加')
        except sqlite3.OperationalError as e:
            if 'duplicate column' in str(e).lower():
                print(f'  ⏭ matches.{col} 已存在')
            else:
                raise
    
    # bet_limits 表新增列
    try:
        cur.execute('ALTER TABLE bet_limits ADD COLUMN live_max_bet_amount INTEGER NOT NULL DEFAULT 3000')
        print(f'  ✅ bet_limits.live_max_bet_amount 已添加')
    except sqlite3.OperationalError as e:
        if 'duplicate column' in str(e).lower():
            print(f'  ⏭ bet_limits.live_max_bet_amount 已存在')
        else:
            raise
    
    conn.commit()
    conn.close()
    print('\nSQLite 迁移完成！')

def pg_sql():
    """服务器 PostgreSQL 迁移 SQL"""
    print("""
-- 服务器 PostgreSQL 迁移 SQL（在服务器上执行）:

ALTER TABLE matches ADD COLUMN IF NOT EXISTS match_minute INTEGER;
ALTER TABLE matches ADD COLUMN IF NOT EXISTS match_period VARCHAR(20);

ALTER TABLE bet_limits ADD COLUMN IF NOT EXISTS live_max_bet_amount INTEGER NOT NULL DEFAULT 3000;

-- 更新已有限额记录的滚球默认值
UPDATE bet_limits SET live_max_bet_amount = 3000 WHERE market_type IN ('ML','Spread','Totals') AND live_max_bet_amount = 0;
UPDATE bet_limits SET live_max_bet_amount = 500 WHERE market_type = 'CS' AND live_max_bet_amount = 0;

-- 验证
SELECT market_type, max_bet_amount, live_max_bet_amount FROM bet_limits ORDER BY market_type;
SELECT COUNT(*) as live_matches FROM matches WHERE status = 'live';
""")

if __name__ == '__main__':
    migrate_sqlite()
    print()
    pg_sql()
