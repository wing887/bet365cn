# bet365cn 部署文档 v1.0

> 目标：将 bet365cn 部署到外网服务器供测试
> 适用：Ubuntu 22.04/24.04 + OpenClaw 自动部署
> 更新时间：2026-05-19

---

## 一、服务器要求

| 项目 | 最低配置 |
|------|----------|
| OS | Ubuntu 22.04+ |
| CPU | 2 核 |
| 内存 | 2 GB |
| 磁盘 | 20 GB |
| 端口 | 80 (HTTP), 22 (SSH) |
| 域名 | 需要（或直接用 IP） |

---

## 二、部署架构

```
用户浏览器 (外网)
     │
     ▼
  Nginx (:80)
     ├── /          → Vue 静态文件 (/opt/bet365cn/frontend/dist/)
     └── /api/*     → Gunicorn (:8000)
                         │
                         ▼
                    Flask 应用
                         │
                    ┌────┴────┐
                    │         │
               PostgreSQL   Redis
```

---

## 三、环境安装

```bash
# 1. 更新系统
sudo apt update && sudo apt upgrade -y

# 2. 安装依赖
sudo apt install -y \
  python3 python3-pip python3-venv \
  nginx postgresql postgresql-client \
  redis-server curl git

# 3. 启动服务
sudo systemctl enable --now postgresql redis-server nginx

# 4. 创建项目目录
sudo mkdir -p /opt/bet365cn
sudo chown $USER:$USER /opt/bet365cn
```

---

## 四、PostgreSQL 配置

```bash
# 1. 创建数据库和用户
sudo -u postgres psql <<SQL
CREATE USER bet365cn WITH PASSWORD 'bet365cn_pass_2026';
CREATE DATABASE bet365cn OWNER bet365cn;
GRANT ALL PRIVILEGES ON DATABASE bet365cn TO bet365cn;
\c bet365cn
GRANT ALL ON SCHEMA public TO bet365cn;
SQL

# 2. 验证连接
PGPASSWORD=bet365cn_pass_2026 psql -h 127.0.0.1 -U bet365cn -d bet365cn -c "SELECT 1"
```

---

## 五、Redis 配置（缓存）

```bash
# 1. 确认 Redis 运行
redis-cli ping
# 应返回 PONG

# 2. 设置最大内存（可选）
sudo sed -i 's/^# maxmemory .*/maxmemory 256mb/' /etc/redis/redis.conf
sudo systemctl restart redis
```

---

## 六、项目部署

### 6.1 拉取代码

```bash
cd /opt/bet365cn
git clone https://github.com/wing887/bet365cn.git .

# 或者指定分支
git clone -b main https://github.com/wing887/bet365cn.git .
```

### 6.2 创建环境配置文件

```bash
# 创建 .env 文件（绝对不要提交到 Git）
cat > /opt/bet365cn/backend/.env <<'EOF'
FLASK_ENV=production
SECRET_KEY=CHANGE_ME_random_string_32_bytes_minimum
JWT_SECRET_KEY=CHANGE_ME_another_random_string_32_bytes
DATABASE_URL=postgresql://bet365cn:bet365cn_pass_2026@127.0.0.1:5432/bet365cn
REDIS_URL=redis://127.0.0.1:6379/0
ODDS_API_KEY=cbed45cdeb7ea196b7ba4335757cf3d4beaf6654ee2b73b30a29fd2c2b38e46b
ODDS_API_PROXY=
EOF
```

> ⚠️ 务必修改 SECRET_KEY 和 JWT_SECRET_KEY 为随机字符串。
> 如果服务器在海外，`ODDS_API_PROXY` 留空；国内需配代理。

### 6.3 后端部署

```bash
cd /opt/bet365cn/backend

# 1. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 2. 安装依赖
pip install -r requirements.txt
pip install gunicorn

# 3. 初始化数据库
PYTHONPATH=. python database/init_db.py
# 预期输出：✓ 数据库表已创建  ✓ 默认超管已创建  ✓ 球队名映射已导入

# 4. 验证
PYTHONPATH=. python -c "
from app import create_app
from models import db
app = create_app()
with app.app_context():
    print('DB OK:', db.session.execute(db.text('SELECT 1')).scalar())
"
```

### 6.4 前端构建

```bash
cd /opt/bet365cn/frontend

# 1. 安装依赖并构建
npm install
npm run build

# 2. 部署到 Nginx 目录
sudo cp -r dist/* /var/www/bet365cn/
```

> 需要先安装 Node.js（如没有）：
> ```bash
> curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
> sudo apt install -y nodejs
> ```

---

## 七、Nginx 配置

### 7.1 创建站点配置

```bash
sudo tee /etc/nginx/sites-available/bet365cn <<'NGINX'
server {
    listen 80;
    server_name _;  # 替换为你的域名，或用 _ 匹配所有

    # 前端静态文件
    root /var/www/bet365cn;
    index index.html;

    # SPA 路由支持（Vue Router hash 模式不需要，但如果用 history 模式则需）
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API 反向代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
    }

    # 安全头
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
}
NGINX

# 2. 启用站点
sudo ln -sf /etc/nginx/sites-available/bet365cn /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# 3. 验证并重载
sudo nginx -t && sudo systemctl reload nginx
```

### 7.2 创建静态文件目录

```bash
sudo mkdir -p /var/www/bet365cn
sudo cp -r /opt/bet365cn/frontend/dist/* /var/www/bet365cn/
sudo chown -R www-data:www-data /var/www/bet365cn
```

---

## 八、Systemd 服务（Gunicorn）

### 8.1 创建服务文件

```bash
sudo tee /etc/systemd/system/bet365cn.service <<'SYSTEMD'
[Unit]
Description=bet365cn Flask Application
After=network.target postgresql.service redis-server.service
Wants=postgresql.service redis-server.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/opt/bet365cn/backend
Environment="PATH=/opt/bet365cn/backend/venv/bin:/usr/local/bin:/usr/bin:/bin"
Environment="PYTHONPATH=/opt/bet365cn/backend"
EnvironmentFile=-/opt/bet365cn/backend/.env
ExecStart=/opt/bet365cn/backend/venv/bin/gunicorn \
    --workers 4 \
    --bind 127.0.0.1:8000 \
    --timeout 120 \
    --access-logfile /var/log/bet365cn-access.log \
    --error-logfile /var/log/bet365cn-error.log \
    --log-level info \
    wsgi:app
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SYSTEMD

# 2. 设置权限
sudo chown -R www-data:www-data /opt/bet365cn/backend
sudo mkdir -p /var/log
sudo touch /var/log/bet365cn-access.log /var/log/bet365cn-error.log
sudo chown www-data:www-data /var/log/bet365cn-*.log

# 3. 启动
sudo systemctl daemon-reload
sudo systemctl enable --now bet365cn
```

### 8.2 验证服务

```bash
# 检查状态
sudo systemctl status bet365cn

# 检查日志
sudo journalctl -u bet365cn -f --no-pager

# 测试 API
curl http://127.0.0.1:8000/api/health
```

---

## 九、防火墙配置

```bash
# UFW（如果启用）
sudo ufw allow 80/tcp
sudo ufw allow 22/tcp

# 云服务商安全组：放行 TCP 80 端口
```

---

## 十、首次运行验证

### 10.1 健康检查

```bash
# 1. API 健康检查
curl http://YOUR_SERVER_IP/api/health
# 预期: {"status":"healthy"}

# 2. 前端页面
curl http://YOUR_SERVER_IP/
# 预期: HTML 页面内容
```

### 10.2 功能测试

```bash
# 1. 管理员登录
curl -X POST http://YOUR_SERVER_IP/api/admin/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"superadmin","password":"admin123"}'

# 2. 创建测试用户
TOKEN=$(上一步获取的 token)
curl -X POST http://YOUR_SERVER_IP/api/admin/users \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"username":"test01","password":"test123"}'

# 3. 给用户充值
curl -X POST http://YOUR_SERVER_IP/api/admin/users/2/coins \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"amount":10000}'

# 4. 手动触发数据同步
curl http://YOUR_SERVER_IP/api/sync/matches
curl http://YOUR_SERVER_IP/api/sync/odds
```

### 10.3 前端访问

浏览器打开 `http://YOUR_SERVER_IP`：
- 用户登录：`test01 / test123`
- 管理员登录：`superadmin / admin123`

---

## 十一、维护命令

```bash
# 重启服务
sudo systemctl restart bet365cn
sudo systemctl reload nginx

# 查看后端日志
sudo journalctl -u bet365cn --since "10 min ago" --no-pager

# 查看 Nginx 日志
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# 更新代码
cd /opt/bet365cn
git pull
cd frontend && npm install && npm run build
sudo cp -r dist/* /var/www/bet365cn/
cd ../backend
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart bet365cn
```

---

## 十二、安全建议

- [ ] 修改 SECRET_KEY 和 JWT_SECRET_KEY（生成方法：`python3 -c "import secrets;print(secrets.token_hex(32))"`）
- [ ] 修改默认超管密码
- [ ] 配置 HTTPS（Let's Encrypt + Certbot）
- [ ] 限制 API 访问频率（Nginx limit_req）
- [ ] 定期备份数据库：`pg_dump -U bet365cn bet365cn > backup.sql`

---

## 十三、使用 OpenClaw 自动部署

如果让 OpenClaw 执行部署，将本文档的第三至第十节内容作为 prompt，OpenClaw 会按顺序执行命令。

**OpenClaw 部署 prompt**：
```
请按照以下步骤部署 bet365cn 到这台服务器：
[粘贴本文档第三节到第十节的内容]
在每一步执行后验证结果，遇到错误立即停止并报告。
```

**注意事项**：
- OpenClaw 部署时需要服务器的 SSH 访问权限
- 确保 OpenClaw 配置了正确的代理（国内服务器需要）
- 首次部署预计耗时 10-15 分钟
