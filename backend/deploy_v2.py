"""bet365cn 服务器部署 v3 — 直接 git fetch + reset"""
import paramiko, time

def deploy():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('125.65.79.20', port=22, username='cy', password='cy123456')
    chan = client.invoke_shell()
    time.sleep(2)
    chan.recv(65536)

    def run(cmd, wait=3):
        chan.send(cmd + '\n')
        time.sleep(wait)
        return chan.recv(65536).decode('utf-8', errors='replace')

    def sudo(cmd, wait=3):
        run(f'sudo {cmd}', 0.5)
        return run('cy123456', wait)

    # Step 1: chown
    print("1. chown...")
    sudo('chown -R cy:cy /opt/bet365cn')

    # Step 2: git fetch + reset (force)
    print("2. git fetch origin...")
    out = run('cd /opt/bet365cn && git fetch origin 2>&1', 5)
    print(f"   fetch: {out[-200:]}")
    
    print("3. git reset --hard origin/main...")
    out = run('cd /opt/bet365cn && git reset --hard origin/main 2>&1', 5)
    print(f"   reset: {out[-200:]}")
    
    print("4. git log...")
    out = run('cd /opt/bet365cn && git log --oneline -3', 2)
    print(f"   log: {out[-300:]}")
    
    print("5. verify auth.py...")
    out = run('head -10 /opt/bet365cn/backend/auth.py', 2)
    print(f"   auth.py: {out[-200:]}")

    # Step 3: PG migration
    print("6. PG migration...")
    sudo('-u postgres psql -d bet365cn -c "ALTER TABLE admin_accounts ADD COLUMN IF NOT EXISTS coin_balance INTEGER DEFAULT 0"')
    sudo('-u postgres psql -d bet365cn -c "ALTER TABLE admin_accounts ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT \'active\'"')
    sudo('-u postgres psql -d bet365cn -c "ALTER TABLE admin_accounts ADD COLUMN IF NOT EXISTS last_login_at TIMESTAMP"')
    sudo('-u postgres psql -d bet365cn -c "ALTER TABLE admin_accounts ADD COLUMN IF NOT EXISTS last_login_ip VARCHAR(45)"')
    sudo('-u postgres psql -d bet365cn -c "ALTER TABLE user_accounts ADD COLUMN IF NOT EXISTS created_by_admin_id INTEGER"')
    sudo('-u postgres psql -d bet365cn -c "ALTER TABLE user_accounts ADD COLUMN IF NOT EXISTS last_login_at TIMESTAMP"')
    sudo('-u postgres psql -d bet365cn -c "CREATE INDEX IF NOT EXISTS ix_user_nickname ON user_accounts(nickname)"')
    sudo('-u postgres psql -d bet365cn -c "ALTER TABLE coin_transactions ADD COLUMN IF NOT EXISTS balance_before INTEGER"')
    sudo('-u postgres psql -d bet365cn -c "ALTER TABLE coin_transactions ADD COLUMN IF NOT EXISTS balance_after INTEGER"')
    sudo('-u postgres psql -d bet365cn -c "ALTER TABLE operation_logs ADD COLUMN IF NOT EXISTS ip_address VARCHAR(45)"')
    sudo("-u postgres psql -d bet365cn -c \"UPDATE admin_accounts SET role='super_admin', status='active', coin_balance=0 WHERE username='superadmin'\"")

    # Step 4: Build frontend
    print("7. npm build...")
    out = run('cd /opt/bet365cn/frontend && npm run build 2>&1', 40)
    print(f"   build: {out[-300:]}")

    # Step 5: Copy
    print("8. copy to nginx...")
    sudo('cp -r /opt/bet365cn/frontend/dist/* /var/www/bet365cn/')
    sudo('cp -r /opt/bet365cn/frontend/public/team-logos /var/www/bet365cn/')

    # Step 6: Restore + restart
    print("9. restore + restart...")
    sudo('chown -R www-data:www-data /opt/bet365cn')
    sudo('systemctl restart bet365cn')
    sudo('systemctl restart nginx')

    time.sleep(4)
    
    # Step 7: Verify
    print("10. verify...")
    out = run('curl -s http://localhost:888/api/health', 2)
    print(f"   health: {out[-100:]}")
    out = run("curl -s -X POST http://localhost:888/api/admin/auth/login -H 'Content-Type: application/json' -d '{\"username\":\"superadmin\",\"password\":\"admin123\"}'", 3)
    print(f"   login: {out[-300:]}")

    chan.close()
    client.close()
    print("\n===== 完成 =====")

if __name__ == '__main__':
    deploy()
