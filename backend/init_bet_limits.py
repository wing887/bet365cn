#!/usr/bin/env python3
"""初始化 bet_limits 表并填入默认值"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'bet365cn.db')

def init_bet_limits():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # 创建表（如果不存在）
    cur.execute('''
        CREATE TABLE IF NOT EXISTS bet_limits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            market_type VARCHAR(20) UNIQUE NOT NULL,
            max_bet_amount INTEGER NOT NULL DEFAULT 5000,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_by INTEGER REFERENCES admin_accounts(id)
        )
    ''')
    
    # 默认值：ML/Spread/Totals=5000, CS=1000
    defaults = [
        ('ML', 5000),
        ('Spread', 5000),
        ('Totals', 5000),
        ('CS', 1000),
    ]
    
    for market_type, amount in defaults:
        cur.execute('''
            INSERT OR IGNORE INTO bet_limits (market_type, max_bet_amount)
            VALUES (?, ?)
        ''', (market_type, amount))
    
    conn.commit()
    
    # 验证
    cur.execute('SELECT market_type, max_bet_amount FROM bet_limits ORDER BY id')
    rows = cur.fetchall()
    print(f"bet_limits 表已初始化 ({len(rows)} 条):")
    for row in rows:
        print(f"  {row[0]:10s}  最大投注 {row[1]} 金币")
    
    conn.close()

if __name__ == '__main__':
    init_bet_limits()
