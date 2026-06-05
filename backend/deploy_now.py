"""bet365cn deploy script - proper sudo handling"""
import paramiko, time

def sudo_cmd(chan, cmd, wait=3):
    """Send a sudo command and handle the password prompt."""
    chan.send(cmd + '\n')
    time.sleep(1)
    # Wait for sudo prompt
    out = ''
    for _ in range(5):
        if chan.recv_ready():
            chunk = chan.recv(4096).decode(errors='replace')
            out += chunk
            if 'password' in out.lower() or '[sudo]' in out:
                break
        time.sleep(0.5)
    
    # Send password
    if 'password' in out.lower() or '[sudo]' in out:
        chan.send('cy123456\n')
    
    # Wait for command to complete
    time.sleep(wait)
    if chan.recv_ready():
        out += chan.recv(8192).decode(errors='replace')
    print(out[-500:], flush=True)
    return out

def plain_cmd(chan, cmd, wait=3):
    """Send a non-sudo command."""
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
chan.recv(4096)  # Clear banner

# Step 1: git pull
print("=== Step 1: git pull ===", flush=True)
sudo_cmd(chan, 'cd /opt/bet365cn && sudo -u www-data git pull origin main', 5)

# Step 2: Build frontend
print("=== Step 2: npm build ===", flush=True)
sudo_cmd(chan, 'sudo chown -R cy:cy /opt/bet365cn/frontend', 2)
plain_cmd(chan, 'cd /opt/bet365cn/frontend && npm run build', 30)

# Step 3: Copy dist to nginx
print("=== Step 3: Copy to nginx ===", flush=True)
sudo_cmd(chan, 'sudo cp -r /opt/bet365cn/frontend/dist/* /var/www/bet365cn/', 2)
sudo_cmd(chan, 'sudo cp -r /opt/bet365cn/frontend/public/team-logos /var/www/bet365cn/ 2>&1; echo COPY_OK', 2)

# Step 4: Fix ownership
print("=== Step 4: Fix permissions ===", flush=True)
sudo_cmd(chan, 'sudo chown -R www-data:www-data /opt/bet365cn/frontend', 2)

# Step 5: Restart services
print("=== Step 5: Restart ===", flush=True)
sudo_cmd(chan, 'sudo systemctl restart bet365cn && sudo systemctl restart nginx && echo RESTART_OK', 5)

# Step 6: Health check
print("=== Step 6: Health check ===", flush=True)
time.sleep(3)
plain_cmd(chan, 'curl -s http://localhost:888/api/health', 2)

# Step 7: Verify new API endpoints
print("=== Step 7: Verify APIs ===", flush=True)
plain_cmd(chan, """curl -s -X POST http://localhost:888/api/admin/auth/login -H 'Content-Type: application/json' -d '{"username":"superadmin","password":"admin123"}' | python3 -c "import sys,json; d=json.load(sys.stdin); print('token_ok' if 'token' in d else 'FAIL:'+str(d))" 2>&1""", 3)

chan.close()
client.close()
print("\n=== Deploy DONE ===", flush=True)
