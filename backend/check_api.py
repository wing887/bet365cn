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
    print(out[-800:], flush=True)
    return out

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('125.65.79.20', port=22, username='cy', password='cy123456', timeout=15)
chan = client.invoke_shell()
time.sleep(1)
chan.recv(4096)

# Check .env for keys
print("=== .env ODDS_API_KEYS ===")
sudo_cmd(chan, 'sudo cat /opt/bet365cn/backend/.env | grep ODDS', 2)

# Direct API test
print("\n=== 直接测试 API ===")
sudo_cmd(chan, 'curl -s "https://api.odds-api.io/v3/odds/?sport=football&league=international-world-cup&regions=uk&markets=h2h&apiKey=cbed45cdeb7ea196b7ba4335757cf3d4beaf6654ee2b73b30a29fd2c2b38e46b" --proxy http://172.18.176.1:10808 2>&1 | head -c 300', 5)

# Check log for sync errors
print("\n=== 同步日志 ===")
sudo_cmd(chan, 'sudo journalctl -u bet365cn --no-pager -n 50 2>&1 | grep -i -E "sync|odds|error|fail|key|api"', 5)

chan.close()
client.close()
