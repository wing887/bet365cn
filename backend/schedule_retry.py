"""Wait 1h for rate limit reset, then retry sync_odds twice (spaced by 5 min)"""
import paramiko, time

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('125.65.79.20', port=22, username='cy', password='cy123456', timeout=15)

# Schedule retry via at command
# After 65 min (to be safe), trigger sync_odds
cmd = 'echo "curl -s http://localhost:888/api/sync/odds; sleep 300; curl -s http://localhost:888/api/sync/odds" | at now + 65 minutes 2>&1'
stdin, stdout, stderr = client.exec_command(cmd)
out = stdout.read().decode()
err = stderr.read().decode()
print(f"at schedule: {out}{err}")

# Also schedule a status check
cmd2 = 'echo "curl -s http://localhost:888/api/sync/status > /tmp/sync_result.txt" | at now + 80 minutes 2>&1'
stdin, stdout, stderr = client.exec_command(cmd2)
out = stdout.read().decode()
err = stderr.read().decode()
print(f"at check: {out}{err}")

client.close()
print("\n已调度: 65分钟后触发赔率同步(两次), 80分钟后检查结果")
print("当前状态: 104场比赛 / 0条赔率")
