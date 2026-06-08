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
    print(out, flush=True)
    return out

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('125.65.79.20', port=22, username='cy', password='cy123456', timeout=15)
chan = client.invoke_shell()
time.sleep(1)
chan.recv(4096)

# Check gunicorn log directly
print("=== 服务日志 (最近100行) ===")
sudo_cmd(chan, 'sudo tail -100 /var/log/syslog 2>/dev/null | grep -i bet365cn || sudo journalctl -u bet365cn --no-pager -n 50 2>&1 | tail -50', 8)

chan.close()
client.close()
