"""Deploy backup script v2 + cron"""
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

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('125.65.79.20', port=22, username='cy', password='cy123456', timeout=15)

# Upload backup script
sftp = client.open_sftp()
sftp.put('/mnt/c/Users/admin/Desktop/bet365cn/backend/backup_db.sh', '/tmp/backup_db.sh')
sftp.close()

chan = client.invoke_shell()
time.sleep(1)
chan.recv(4096)

print("=== Setup dir + permissions ===", flush=True)
sudo_cmd(chan, 'sudo mkdir -p /opt/backups/bet365cn', 2)
sudo_cmd(chan, 'sudo chown -R postgres:postgres /opt/backups', 2)
sudo_cmd(chan, 'sudo mv /tmp/backup_db.sh /opt/backup_db.sh', 2)
sudo_cmd(chan, 'sudo chmod +x /opt/backup_db.sh', 2)

print("\n=== Test backup as postgres ===", flush=True)
sudo_cmd(chan, 'sudo -u postgres /opt/backup_db.sh 2>&1', 5)

print("\n=== Verify backup file ===", flush=True)
sudo_cmd(chan, 'sudo ls -lh /opt/backups/bet365cn/', 2)

print("\n=== Cron setup ===", flush=True)
cron_entry = '0 3 * * * /opt/backup_db.sh >> /opt/backups/bet365cn/backup.log 2>&1'
sudo_cmd(chan, f'(sudo crontab -u postgres -l 2>/dev/null | grep -v backup_db; echo "{cron_entry}") | sudo crontab -u postgres -', 3)

print("\n=== Verify cron ===", flush=True)
sudo_cmd(chan, 'sudo crontab -u postgres -l', 2)

chan.close()
client.close()
print("\n=== DONE ===", flush=True)
