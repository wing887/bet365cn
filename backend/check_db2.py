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
    print(out, flush=True)
    return out

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('125.65.79.20', port=22, username='cy', password='cy123456', timeout=15)
chan = client.invoke_shell()
time.sleep(1)
chan.recv(4096)

print("=== 比赛概况 ===")
sudo_cmd(chan, "sudo -u postgres psql -d bet365cn -c \"SELECT status, league_slug, count(*) FROM matches GROUP BY status, league_slug ORDER BY count(*) DESC;\"", 3)

print("\n=== 前5场 ===")
sudo_cmd(chan, "sudo -u postgres psql -d bet365cn -c \"SELECT id, status, league_slug, home_team, away_team, to_char(match_date,'YYYY-MM-DD') FROM matches ORDER BY id LIMIT 5;\"", 3)

chan.close()
client.close()
