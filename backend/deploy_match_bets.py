"""bet365cn deploy script - feature/live-betting-v3"""
import paramiko, time

def sudo_cmd(chan, cmd, wait=3):
    chan.send(cmd + '\n')
    time.sleep(1)
    out = ''
    for _ in range(5):
        if chan.recv_ready():
            chunk = chan.recv(4096).decode(errors='replace')
            out += chunk
            if 'password' in out.lower() or '[sudo]' in out:
                break
        time.sleep(0.5)
    if 'password' in out.lower() or '[sudo]' in out:
        chan.send('cy123456\n')
    time.sleep(wait)
    if chan.recv_ready():
        out += chan.recv(8192).decode(errors='replace')
    print(out[-600:], flush=True)
    return out

def plain_cmd(chan, cmd, wait=3):
    chan.send(cmd + '\n')
    time.sleep(wait)
    out = ''
    if chan.recv_ready():
        out = chan.recv(8192).decode(errors='replace')
    print(out[-400:] if out else '(no output)', flush=True)
    return out

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('125.65.79.20', port=22, username='cy', password='cy123456', timeout=15)
chan = client.invoke_shell()
time.sleep(1)
chan.recv(4096)

# Step 1: git pull
print("=== Step 1: git pull ===", flush=True)
sudo_cmd(chan, 'cd /opt/bet365cn && sudo -u www-data git stash', 2)
sudo_cmd(chan, 'cd /opt/bet365cn && sudo -u www-data git fetch origin', 3)
sudo_cmd(chan, 'cd /opt/bet365cn && sudo -u www-data git checkout feature/live-betting-v3', 3)
sudo_cmd(chan, 'cd /opt/bet365cn && sudo -u www-data git pull origin feature/live-betting-v3', 5)

# Step 2: Build frontend
print("=== Step 2: npm build ===", flush=True)
sudo_cmd(chan, 'sudo chown -R cy:cy /opt/bet365cn/frontend', 2)
plain_cmd(chan, 'cd /opt/bet365cn/frontend && npm run build', 30)

# Step 3: Copy to nginx
print("=== Step 3: Copy to nginx ===", flush=True)
sudo_cmd(chan, 'sudo cp -r /opt/bet365cn/frontend/dist/* /var/www/bet365cn/', 2)
sudo_cmd(chan, 'sudo cp -r /opt/bet365cn/frontend/public/team-logos /var/www/bet365cn/ 2>/dev/null; echo COPY_DONE', 2)

# Step 4: Fix ownership
print("=== Step 4: Fix permissions ===", flush=True)
sudo_cmd(chan, 'sudo chown -R www-data:www-data /opt/bet365cn/frontend', 2)

# Step 5: Restart
print("=== Step 5: Restart bet365cn ===", flush=True)
sudo_cmd(chan, 'sudo systemctl restart bet365cn && echo RESTART_OK', 5)

# Step 6: Health check
print("=== Step 6: Health check ===", flush=True)
time.sleep(3)
plain_cmd(chan, 'curl -s http://localhost:888/api/health', 3)

# Step 7: Verify new API
print("=== Step 7: Verify new API ===", flush=True)
verify_cmd = (
    'TOKEN=$(curl -s -X POST http://localhost:888/api/admin/auth/login '
    "-H 'Content-Type: application/json' "
    "-d '{\"username\":\"superadmin\",\"password\":\"admin123\"}' "
    "| python3 -c \"import sys,json; print(json.load(sys.stdin)['token']['access_token'])\"); "
    'echo "Token: ${TOKEN:0:30}..."; '
    'curl -s "http://localhost:888/api/admin/users/8/match-bets?period_start=2026-01-01&period_end=2026-12-31" '
    '-H "Authorization: Bearer $TOKEN"'
)
plain_cmd(chan, verify_cmd, 5)

chan.close()
client.close()
print("\n=== Deploy DONE ===", flush=True)
