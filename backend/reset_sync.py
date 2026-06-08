"""清空服务器比赛数据 + 重新同步 v2 — 修复 FK 顺序"""
import paramiko, time, requests

HOST = '125.65.79.20'

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
    print(out[-500:], flush=True)
    return out

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=22, username='cy', password='cy123456', timeout=15)
chan = client.invoke_shell()
time.sleep(1)
chan.recv(4096)

# Delete in correct FK order
print("=== 删除数据（按FK顺序） ===", flush=True)
sqls = [
    ("coin tx", "DELETE FROM coin_transactions;"),
    ("bets", "DELETE FROM bets;"),
    ("odds", "DELETE FROM odds;"),
    ("settlements", "DELETE FROM settlements;"),
    ("operation logs", "DELETE FROM operation_logs;"),
    ("matches", "DELETE FROM matches;"),
]
for label, sql in sqls:
    sudo_cmd(chan, f'sudo -u postgres psql -d bet365cn -c "{sql}"', 2)

# Verify
print("\n=== 验证 ===", flush=True)
sudo_cmd(chan, 'sudo -u postgres psql -d bet365cn -c "SELECT count(*) as matches FROM matches;"', 2)
sudo_cmd(chan, 'sudo -u postgres psql -d bet365cn -c "SELECT count(*) as bets FROM bets;"', 2)
sudo_cmd(chan, 'sudo -u postgres psql -d bet365cn -c "SELECT count(*) as odds FROM odds;"', 2)

# Restart to clear any cached state
print("\n=== 重启服务 ===", flush=True)
sudo_cmd(chan, 'sudo systemctl restart bet365cn && echo OK', 5)

chan.close()
client.close()

# Wait for restart
time.sleep(3)

# Trigger sync
print("\n=== 触发 sync_matches ===", flush=True)
resp = requests.get(f'http://{HOST}:888/api/sync/matches', timeout=10)
print(resp.json())

print("等待 90 秒...", flush=True)
time.sleep(90)

resp = requests.get(f'http://{HOST}:888/api/sync/status', timeout=10)
print(f"比赛: {resp.json()}")

print("\n=== 触发 sync_odds ===", flush=True)
resp = requests.get(f'http://{HOST}:888/api/sync/odds', timeout=10)
print(resp.json())

print("等待 90 秒...", flush=True)
time.sleep(90)

resp = requests.get(f'http://{HOST}:888/api/sync/status', timeout=10)
d = resp.json()
print(f"最终: 比赛={d['matches_count']}, 赔率={d['odds_count']}")

# Show matches via API
headers = {'Authorization': f'Bearer {requests.post(f"http://{HOST}:888/api/admin/auth/login", json={"username":"superadmin","password":"admin123"}, timeout=10).json()["token"]["access_token"]}'}
resp = requests.get(f'http://{HOST}:888/api/matches?status=all', headers=headers, timeout=10)
matches = resp.json().get('matches', [])
print(f"\n共 {len(matches)} 场比赛:")
for m in matches[:8]:
    print(f"  {m['home_team']} vs {m['away_team']} [{m['status']}]")

print("\n=== DONE ===", flush=True)
