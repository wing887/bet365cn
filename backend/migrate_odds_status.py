#!/usr/bin/env python3
"""迁移：odds 表新增 status 列 + 更新索引"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'bet365cn.db')

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # 检查列是否已存在
    cur.execute("PRAGMA table_info(odds)")
    cols = [row[1] for row in cur.fetchall()]
    
    if 'status' not in cols:
        print("添加 odds.status 列...")
        cur.execute("ALTER TABLE odds ADD COLUMN status VARCHAR(20) DEFAULT 'active'")
        conn.commit()
        print("  ✅ 已完成")
    else:
        print("  status 列已存在，跳过")
    
    # 更新现有数据
    cur.execute("UPDATE odds SET status = 'active' WHERE status IS NULL OR status = ''")
    conn.commit()
    
    # 验证
    cur.execute("SELECT status, COUNT(*) FROM odds GROUP BY status")
    rows = cur.fetchall()
    print(f"odds 表状态分布:")
    for row in rows:
        print(f"  {row[0]:12s} : {row[1]} 条")
    
    conn.close()

if __name__ == '__main__':
    migrate()
