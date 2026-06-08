"""Quick deploy — backend only: git pull + restart bet365cn"""
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

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('125.65.79.20', port=22, username='cy', password='cy123456', timeout=15)
chan = client.invoke_shell()
time.sleep(1)
chan.recv(4096)

print("=== git pull ===", flush=True)
sudo_cmd(chan, 'cd /opt/bet365cn && sudo -u www-data git stash', 2)
sudo_cmd(chan, 'cd /opt/bet365cn && sudo -u www-data git pull origin feature/live-betting-v3', 5)

print("=== restart bet365cn ===", flush=True)
sudo_cmd(chan, 'sudo systemctl restart bet365cn && echo RESTART_OK', 5)

print("=== health check ===", flush=True)
time.sleep(2)
plain_cmd(chan, 'curl -s http://localhost:888/api/health', 2)

print("=== test search ===", flush=True)
plain_cmd(chan, (
    'TOKEN=$(curl -s -X POST http://localhost:888/api/admin/auth/login '
    "-H 'Content-Type: application/json' "
    "-d '{\"username\":\"superadmin\",\"password\":\"admin123\"}' "
    "| python3 -c \"import sys,json; print(json.load(sys.stdin)['token']['access_token'])\"); "
    'echo "Token_ok=$([ -n \"$TOKEN\" ] && echo yes || echo no)"; '
    'curl -s "http://localhost:888/api/admin/users?q=SUPER" -H "Authorization: Bearer $TOKEN" '
    '| python3 -c "import sys,json; d=json.load(sys.stdin); print(\"admin_search_ok=\"+str(len(d.get(\"admins\",d.get(\"users\",[])))))" 2>/dev/null || echo "API_FALLBACK"; '
    'curl -s "http://localhost:888/api/admin/users?q=test" -H "Authorization: Bearer $TOKEN" '
    '| python3 -c "import sys,json; d=json.load(sys.stdin); print(\"users_count=\"+str(len(d.get(\"users\",[]))))"'
), 5)

chan.close()
client.close()
print("\n=== DONE ===", flush=True)
