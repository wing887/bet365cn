#!/usr/bin/env python3
"""初始化 bet_limits 表并填入默认值（含滚球限额）"""
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
            live_max_bet_amount INTEGER NOT NULL DEFAULT 3000,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_by INTEGER REFERENCES admin_accounts(id)
        )
    ''')
    
    # 尝试添加 live_max_bet_amount 列（升级旧表）
    try:
        cur.execute('ALTER TABLE bet_limits ADD COLUMN live_max_bet_amount INTEGER NOT NULL DEFAULT 3000')
        print("已为旧表添加 live_max_bet_amount 列")
    except sqlite3.OperationalError:
        pass  # 列已存在
    
    # 默认值：赛前限额 + 滚球限额（60%）
    defaults = [
        ('ML', 5000, 3000),
        ('Spread', 5000, 3000),
        ('Totals', 5000, 3000),
        ('CS', 1000, 500),
    ]
    
    for market_type, amount, live_amount in defaults:
        # 插入或忽略（保留已有配置）
        cur.execute('''
            INSERT OR IGNORE INTO bet_limits (market_type, max_bet_amount, live_max_bet_amount)
            VALUES (?, ?, ?)
        ''', (market_type, amount, live_amount))
    
    # 修正 CS 滚球默认值（排除已手动修改的）
    cur.execute(
        "UPDATE bet_limits SET live_max_bet_amount = 500 "
        "WHERE market_type = 'CS' AND live_max_bet_amount = 3000"
    )
    
    conn.commit()
    
    # 验证
    cur.execute('SELECT market_type, max_bet_amount, live_max_bet_amount FROM bet_limits ORDER BY id')
    rows = cur.fetchall()
    print(f"bet_limits 表已初始化 ({len(rows)} 条):")
    for row in rows:
        print(f"  {row[0]:10s}  赛前 {row[1]:>5} 金币  滚球 {row[2]:>5} 金币")
    
    conn.close()

if __name__ == '__main__':
    init_bet_limits()
