"""检查 bet365cn 错误日志"""
import paramiko, time

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('125.65.79.20', port=22, username='cy', password='cy123456')
chan = client.invoke_shell()
time.sleep(1)
chan.recv(4096)

def run(cmd, wait=3):
    chan.send(cmd + '\n')
    time.sleep(wait)
    return chan.recv(65536).decode('utf-8', errors='replace')

def sudo(cmd, wait=3):
    run(f'sudo {cmd}', 0.5)
    return run('cy123456', wait)

print("=== Error Log ===")
out = sudo('tail -50 /var/log/bet365cn-error.log', 3)
print(out[-2000:])

print("\n=== WSGI check ===")
out = run('cd /opt/bet365cn/backend && /opt/bet365cn/backend/venv/bin/python -c "from app import create_app; app = create_app(); print(\'OK\')" 2>&1', 5)
print(out[-1000:])

print("\n=== Restart manual ===")
sudo('systemctl restart bet365cn', 3)
time.sleep(5)
out = run('curl -s http://localhost:8000/api/health', 3)
print(f"Direct gunicorn: {out[-200:]}")

chan.close()
client.close()
