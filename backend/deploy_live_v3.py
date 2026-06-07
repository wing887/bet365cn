"""bet365cn deploy — 滚球 v3 到服务器"""
import paramiko, time

def sudo_cmd(chan, cmd, wait=4):
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
    print(out[-500:], flush=True)
    return out

def plain_cmd(chan, cmd, wait=3):
    chan.send(cmd + '\n')
    time.sleep(wait)
    out = ''
    if chan.recv_ready():
        out = chan.recv(8192).decode(errors='replace')
    print(out[-300:] if out else '(no output)', flush=True)
    return out

HOST = '125.65.79.20'
PORT = 22
USER = 'cy'
PASSWORD = 'cy123456'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=PORT, username=USER, password=PASSWORD, timeout=15)
chan = client.invoke_shell()
time.sleep(1)
chan.recv(4096)

print("=== 1: git checkout feature/live-betting-v3 ===", flush=True)
sudo_cmd(chan, 'cd /opt/bet365cn && sudo -u www-data git fetch origin', 8)
sudo_cmd(chan, 'cd /opt/bet365cn && sudo -u www-data git checkout feature/live-betting-v3', 5)
sudo_cmd(chan, 'cd /opt/bet365cn && sudo -u www-data git pull origin feature/live-betting-v3', 5)

print("=== 2: PostgreSQL migration ===", flush=True)
sudo_cmd(chan, "sudo -u postgres psql -d bet365cn -c \"ALTER TABLE matches ADD COLUMN IF NOT EXISTS match_minute INTEGER;\"", 4)
sudo_cmd(chan, "sudo -u postgres psql -d bet365cn -c \"ALTER TABLE matches ADD COLUMN IF NOT EXISTS match_period VARCHAR(20);\"", 4)
sudo_cmd(chan, "sudo -u postgres psql -d bet365cn -c \"ALTER TABLE bet_limits ADD COLUMN IF NOT EXISTS live_max_bet_amount INTEGER NOT NULL DEFAULT 3000;\"", 4)
sudo_cmd(chan, "sudo -u postgres psql -d bet365cn -c \"UPDATE bet_limits SET live_max_bet_amount = 500 WHERE market_type = 'CS' AND live_max_bet_amount = 3000;\"", 4)

print("=== 3: Frontend build ===", flush=True)
sudo_cmd(chan, 'sudo chown -R cy:cy /opt/bet365cn/frontend', 3)
plain_cmd(chan, 'cd /opt/bet365cn/frontend && npm run build 2>&1', 40)

print("=== 4: Copy to nginx ===", flush=True)
sudo_cmd(chan, 'sudo cp -r /opt/bet365cn/frontend/dist/* /var/www/bet365cn/', 3)
sudo_cmd(chan, 'sudo cp -r /opt/bet365cn/frontend/public/team-logos /var/www/bet365cn/ 2>&1; echo OK', 3)

print("=== 5: Fix permissions ===", flush=True)
sudo_cmd(chan, 'sudo chown -R www-data:www-data /opt/bet365cn/frontend', 3)

print("=== 6: Restart services ===", flush=True)
sudo_cmd(chan, 'sudo systemctl restart bet365cn && echo BET365CN_OK', 5)
sudo_cmd(chan, 'sudo systemctl restart nginx && echo NGINX_OK', 5)

print("=== 7: Verify ===", flush=True)
time.sleep(2)
plain_cmd(chan, 'curl -s http://localhost:888/api/health', 3)
plain_cmd(chan, 'curl -s -H "Authorization: Bearer test" http://localhost:888/api/bets/limits 2>&1 | head -c 200', 3)
plain_cmd(chan, 'sudo systemctl status bet365cn --no-pager | head -5', 3)

chan.close()
client.close()
print("\n=== DEPLOY DONE ===", flush=True)
