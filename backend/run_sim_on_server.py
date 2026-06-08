import paramiko, time

HOST='125.65.79.20'; USER='cy'; PASS='cy123456'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=22, username=USER, password=PASS, timeout=15)

# SFTP upload
sftp = client.open_sftp()
sftp.put('/mnt/c/Users/admin/Desktop/bet365cn/backend/simulate_live_match.py',
         '/tmp/simulate_live_match.py')
sftp.close()
print("✅ 上传完成")

# Run via invoke_shell
chan = client.invoke_shell()
time.sleep(1); chan.recv(4096)

# Check requests
chan.send('python3 -c "import requests; print(\"OK\")\"\n')
time.sleep(2)
out = ''
if chan.recv_ready(): out += chan.recv(4096).decode(errors='replace')
print(f"requests: {'OK' if 'OK' in out else 'NEED INSTALL'}")

# Kill old simulation if any
chan.send('pkill -f simulate_live_match.py 2>/dev/null; sleep 1\n')
time.sleep(2)
chan.recv(4096)

# Start simulation in background
chan.send('nohup python3 -u /tmp/simulate_live_match.py > /tmp/simulate_live.log 2>&1 &\necho "PID=$!"\n')
time.sleep(3)
out = ''
if chan.recv_ready(): out += chan.recv(8192).decode(errors='replace')
print(f"启动输出:\n{out[-300:]}")

# Wait and check log
time.sleep(8)
chan.send('cat /tmp/simulate_live.log\n')
time.sleep(3)
out = ''
if chan.recv_ready(): out += chan.recv(8192).decode(errors='replace')
print(f"日志:\n{out[-600:]}")

chan.close(); client.close()
print("\n✅ 完成")
