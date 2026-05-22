"""
bet365cn — 数据库迁移脚本 v2.0
三级管理员体系升级

用法：
  cd backend
  ./venv/bin/python migrate_v2.py
"""
import sqlite3
import hashlib
import os
import sys


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def get_db_path():
    """获取数据库路径"""
    # 默认路径
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'bet365cn.db')
    if not os.path.exists(db_path):
        # 尝试 instance 目录
        alt = os.path.join(os.path.dirname(__file__), 'bet365cn.db')
        if os.path.exists(alt):
            return alt
        print(f"[错误] 数据库不存在: {db_path}")
        print("请确认 backend/instance/bet365cn.db 或 backend/bet365cn.db 存在")
        sys.exit(1)
    return db_path


def migrate(db_path: str):
    print(f"[信息] 数据库: {db_path}")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # ===== 1. admin_accounts 表改动 =====
    print("[1/5] 升级 admin_accounts 表...")
    existing_cols = [c[1] for c in cur.execute("PRAGMA table_info(admin_accounts)").fetchall()]

    if 'coin_balance' not in existing_cols:
        cur.execute("ALTER TABLE admin_accounts ADD COLUMN coin_balance INTEGER DEFAULT 0")
        print("  + coin_balance")
    if 'status' not in existing_cols:
        cur.execute("ALTER TABLE admin_accounts ADD COLUMN status TEXT DEFAULT 'active'")
        print("  + status")
    if 'last_login_at' not in existing_cols:
        cur.execute("ALTER TABLE admin_accounts ADD COLUMN last_login_at TIMESTAMP")
        print("  + last_login_at")
    if 'last_login_ip' not in existing_cols:
        cur.execute("ALTER TABLE admin_accounts ADD COLUMN last_login_ip TEXT")
        print("  + last_login_ip")

    # 旧 role='admin' 保持不变（等同于新体系的"管理"）
    # super_admin 保持不变
    cur.execute("UPDATE admin_accounts SET status='active' WHERE status IS NULL")
    cur.execute("UPDATE admin_accounts SET coin_balance=0 WHERE coin_balance IS NULL")

    # ===== 2. user_accounts 表改动 =====
    print("[2/5] 升级 user_accounts 表...")
    existing_cols = [c[1] for c in cur.execute("PRAGMA table_info(user_accounts)").fetchall()]

    if 'created_by_admin_id' not in existing_cols:
        cur.execute("ALTER TABLE user_accounts ADD COLUMN created_by_admin_id INTEGER REFERENCES admin_accounts(id)")
        print("  + created_by_admin_id")
    if 'last_login_at' not in existing_cols:
        cur.execute("ALTER TABLE user_accounts ADD COLUMN last_login_at TIMESTAMP")
        print("  + last_login_at")

    # 尝试给 nickname 加索引（可能已存在）
    try:
        cur.execute("CREATE INDEX IF NOT EXISTS ix_user_nickname ON user_accounts(nickname)")
        print("  + nickname 索引")
    except Exception:
        pass  # 可能已存在

    # ===== 3. coin_transactions 表改动 =====
    print("[3/5] 升级 coin_transactions 表...")
    existing_cols = [c[1] for c in cur.execute("PRAGMA table_info(coin_transactions)").fetchall()]

    if 'balance_before' not in existing_cols:
        cur.execute("ALTER TABLE coin_transactions ADD COLUMN balance_before INTEGER")
        print("  + balance_before")
    if 'balance_after' not in existing_cols:
        cur.execute("ALTER TABLE coin_transactions ADD COLUMN balance_after INTEGER")
        print("  + balance_after")

    # ===== 4. operation_logs 表改动 =====
    print("[4/5] 升级 operation_logs 表...")
    existing_cols = [c[1] for c in cur.execute("PRAGMA table_info(operation_logs)").fetchall()]

    if 'ip_address' not in existing_cols:
        cur.execute("ALTER TABLE operation_logs ADD COLUMN ip_address TEXT")
        print("  + ip_address")

    # ===== 5. 确保 superadmin 存在 =====
    print("[5/5] 确保超级管理员存在...")
    cur.execute("SELECT id FROM admin_accounts WHERE username='superadmin'")
    existing_superadmin = cur.fetchone()

    if not existing_superadmin:
        cur.execute(
            "INSERT INTO admin_accounts (username, password_hash, role, coin_balance, status) "
            "VALUES (?, ?, 'super_admin', 0, 'active')",
            ('superadmin', hash_password('admin123'))
        )
        print("  + 创建 superadmin / admin123")
    else:
        # 确保 role 正确
        cur.execute(
            "UPDATE admin_accounts SET role='super_admin' WHERE username='superadmin' AND role!='super_admin'"
        )
        print("  superadmin 已存在，已确认角色")

    # ===== 提交 =====
    conn.commit()

    # 打印汇总
    cur.execute("SELECT id, username, role, status, coin_balance FROM admin_accounts")
    admins = cur.fetchall()
    print(f"\n[完成] 管理员列表 ({len(admins)} 个):")
    for a in admins:
        print(f"  [{a[0]}] {a[1]} | 角色={a[2]} | 状态={a[3]} | 余额={a[4]}")

    conn.close()
    print("\n迁移完成！")


if __name__ == '__main__':
    db_path = get_db_path()
    migrate(db_path)
