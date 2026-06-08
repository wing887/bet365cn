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
    print(out[-400:], flush=True)
    return out

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('125.65.79.20', port=22, username='cy', password='cy123456', timeout=15)
chan = client.invoke_shell()
time.sleep(1)
chan.recv(4096)

print("=== git pull ===")
sudo_cmd(chan, 'cd /opt/bet365cn && sudo -u www-data git pull origin feature/live-betting-v3', 5)

print("\n=== restart ===")
sudo_cmd(chan, 'sudo systemctl restart bet365cn && echo RESTART_OK', 5)

print("\n=== health check ===")
time.sleep(2)
sudo_cmd(chan, 'curl -s http://localhost:888/api/health', 3)

chan.close()
client.close()
print("\nDONE")
