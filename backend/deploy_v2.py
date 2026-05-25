"""快速重新部署后端"""
import paramiko, time

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('125.65.79.20', port=22, username='cy', password='cy123456')
chan = client.invoke_shell()
time.sleep(1)
chan.recv(4096)

def run(cmd, wait=3):
    chan.send(cmd + '\n')
    time.sleep(wait)
    return chan.recv(65536).decode('utf-8', errors='replace')

def sudo(cmd, wait=3):
    run(f'sudo {cmd}', 0.5)
    return run('cy123456', wait)

# 1. chown + pull
print("1. chown + pull...")
sudo('chown -R cy:cy /opt/bet365cn')
out = run('cd /opt/bet365cn && git fetch origin && git reset --hard origin/main', 5)
print(f"   git: {out[-300:]}")

# 2. Verify the fix
out = run('cd /opt/bet365cn/backend && /opt/bet365cn/backend/venv/bin/python -c "from auth import ROLE_AGENT; print(\'ROLE_AGENT:\', ROLE_AGENT)"', 3)
print(f"   import test: {out[-200:]}")

# 3. Build frontend
print("2. npm build...")
out = run('cd /opt/bet365cn/frontend && npm run build 2>&1', 30)
print(f"   build: {out[-200:]}")

# 4. Copy to nginx
print("3. copy...")
sudo('cp -r /opt/bet365cn/frontend/dist/* /var/www/bet365cn/')

# 5. Restore + restart
print("4. restart...")
sudo('chown -R www-data:www-data /opt/bet365cn')
sudo('systemctl restart bet365cn')

time.sleep(4)

# 6. Verify
print("5. verify...")
out = run('curl -s http://localhost:8000/api/health', 3)
print(f"   health: {out[-200:]}")
out = run("curl -s -X POST http://localhost:8000/api/admin/auth/login -H 'Content-Type: application/json' -d '{\"username\":\"superadmin\",\"password\":\"admin123\"}'", 3)
print(f"   login: {out[-300:]}")
out = run('curl -s http://localhost:888/api/health', 3)
print(f"   nginx: {out[-200:]}")

chan.close()
client.close()
print("\n===== 完成 =====")
