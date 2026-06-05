import paramiko, time

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('125.65.79.20', port=22, username='cy', password='cy123456', timeout=15)
chan = client.invoke_shell()
time.sleep(1)
chan.recv(4096)

def send(cmd, wait=4):
    chan.send(cmd + '\n')
    time.sleep(wait)
    out = b''
    while chan.recv_ready():
        out += chan.recv(65536)
    decoded = out.decode(errors='replace')
    if decoded:
        print(decoded[-800:], flush=True)

def sudo(cmd, wait=4):
    chan.send(cmd + '\n')
    time.sleep(1.5)
    chan.send('cy123456\n')
    time.sleep(wait)
    out = b''
    while chan.recv_ready():
        out += chan.recv(65536)
    decoded = out.decode(errors='replace')
    if decoded:
        print(decoded[-800:], flush=True)

print("=== bet_limits table ===", flush=True)
sudo("""sudo -u postgres psql -d bet365cn -c "
CREATE TABLE IF NOT EXISTS bet_limits (
    id SERIAL PRIMARY KEY,
    market_type VARCHAR(20) UNIQUE NOT NULL,
    max_bet_amount INTEGER NOT NULL DEFAULT 5000,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by INTEGER REFERENCES admin_accounts(id)
);
INSERT INTO bet_limits (market_type, max_bet_amount) 
VALUES ('ML', 5000), ('Spread', 5000), ('Totals', 5000), ('CS', 1000) 
ON CONFLICT (market_type) DO NOTHING;
SELECT * FROM bet_limits;
" """, 6)

print("=== odds.status column ===", flush=True)
sudo("""sudo -u postgres psql -d bet365cn -c "
ALTER TABLE odds ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'active';
UPDATE odds SET status = 'active' WHERE status IS NULL;
SELECT status, COUNT(*) FROM odds GROUP BY status;
" """, 6)

print("=== Restart ===", flush=True)
sudo("sudo systemctl restart bet365cn && echo OK", 6)

chan.close()
client.close()
print("DONE", flush=True)
