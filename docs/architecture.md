# bet365cn — 技术方案 v2.0

> 基于需求文档 v1.2
> 设计日期：2026-05-19
> 目标承载：**1000 并发用户**

---

## 一、技术选型

| 层级 | 技术 | 理由 |
|------|------|------|
| **前端** | Vue 3 + Vite + Vue Router + Pinia | 复用 KickBet 经验，响应式移动端 |
| **UI 组件** | 手写 CSS（Bet365 风格） | 不引入组件库，精确模仿 Bet365 |
| **后端框架** | Python Flask 3.x | 复用 KickBet 经验，轻量够用 |
| **WSGI 服务器** | **Gunicorn**（4-8 workers） | 多进程并行处理请求，替代 Flask 内置单线程 |
| **反向代理** | **Nginx** | 静态文件直出 + API 反向代理 + 负载均衡 |
| **数据库** | **PostgreSQL 15+** | 行级锁、并发写入、1000 人同时下注不锁死 |
| **缓存** | **Redis 7+** | 热点数据缓存（比赛列表/赔率），减少 API 和 DB 压力 |
| **定时任务** | APScheduler + Redis 分布式锁 | 多 worker 环境下任务不重复执行 |
| **API 客户端** | requests + WSL 代理 | 复用 KickBet 模式 |
| **部署** | 已有方案（用户确认） | |

### 为什么 SQLite 不行

| 场景 | SQLite | PostgreSQL |
|------|--------|------------|
| 1000 人同时浏览比赛 | ✅ 并发读没问题 | ✅ |
| 100 人同时下注 | ❌ 写锁排队，响应超时 | ✅ 行级锁，互不阻塞 |
| 超管结算 + 用户下注同时 | ❌ 一方被锁阻塞 | ✅ |
| 定时任务写入 + 用户请求 | ❌ 抢占写入锁 | ✅ |

### 为什么 Flask 内置服务器不行

```
Flask 内置:  并发请求 → [queue] → 单线程逐一处理 → 第100个请求等前面99个
Gunicorn:    并发请求 → Nginx分发 → [worker1] [worker2] ... [worker8] → 并行处理
```

---

## 二、部署架构

```
                    ┌──────────────────────────┐
 用户浏览器 ──────→  │         Nginx            │
                    │                          │
                    │  /          → 静态文件     │  ← Vue 打包产物
                    │  /api/*     → Gunicorn    │  ← 反向代理
                    │  /api/admin → Gunicorn    │
                    └──────────┬───────────────┘
                               │
                    ┌──────────┴───────────────┐
                    │     Gunicorn (8 workers)  │
                    │     Flask Application      │
                    └──────────┬───────────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
     ┌────────┴──────┐  ┌──────┴──────┐  ┌──────┴──────┐
     │  PostgreSQL    │  │    Redis    │  │  APScheduler│
     │  (数据存储)     │  │  (缓存)     │  │  (定时任务)  │
     └───────────────┘  └─────────────┘  └─────────────┘
```

---

## 三、并发场景下的关键设计

### 3.1 下注原子性（防止超扣/重复扣）

```
用户下注请求:
  BEGIN TRANSACTION
    1. SELECT coin_balance FROM user_accounts WHERE id=? FOR UPDATE  ← 行级锁
    2. 校验余额 ≥ 下注金额
    3. UPDATE user_accounts SET coin_balance = coin_balance - ? WHERE id=?
    4. INSERT INTO bets (...)
    5. INSERT INTO coin_transactions (type='bet_place', ...)
  COMMIT

> FOR UPDATE 保证同一用户的多个下注请求串行执行，不会出现超扣
> 只锁该用户的行，不影响其他用户下注
```

### 3.2 缓存策略

| 数据 | 缓存位置 | TTL | 说明 |
|------|----------|-----|------|
| 比赛列表 | Redis | 5 分钟 | 最高频访问，1000 人首页 |
| 单场赔率 | Redis | 3 分钟 | 定时任务刷新时更新缓存 |
| 用户余额 | Redis | 实时（下注后清除） | 避免每次查询DB |
| 球队名映射 | 内存 | 启动时加载 | 静态数据 |

```
请求流程:
  用户请求比赛列表
    → 查 Redis → 命中 → 直接返回（<1ms）
    → 未命中 → 查 PostgreSQL → 写入 Redis → 返回（~10ms）
```

### 3.3 定时任务防重复（多 Worker）

```
8 个 Gunicorn worker 各启动一个 APScheduler
  → 同一个定时任务会被执行 8 次！
  → 解决方案：Redis 分布式锁

scheduler_job():
    lock = redis.set("lock:fetch_odds", "1", nx=True, ex=600)
    if not lock:
        return  // 已有其他 worker 在执行，跳过
    try:
        fetch_odds()
    finally:
        redis.delete("lock:fetch_odds")
```

### 3.4 赔率实时性问题

```
V1.0 赛前下注容忍度:
  赔率每 10 分钟刷新 → 用户看到的是最多 10 分钟前的赔率
  → 可接受（赛前赔率变动慢）

下注时校验:
  后端取 odds 表最新一条 → 对比用户提交的 odds_value
  → 如果赔率已变化 > 5% → 提示用户"赔率已更新，请确认新赔率"
  → 如果赔率不变 → 直接确认
```

---

## 四、项目结构（更新）

---

## 四、项目结构

```
bet365cn/
├── backend/                    # Flask 后端
│   ├── app.py                  # 应用入口
│   ├── config.py               # 配置文件（PG/Redis/Gunicorn）
│   ├── models.py               # SQLAlchemy 数据模型
│   ├── auth.py                 # JWT 认证（用户+管理员双体系）
│   ├── cache.py                # Redis 缓存封装
│   ├── routes/
│   │   ├── user_auth.py        # 用户登录/改密
│   │   ├── matches.py          # 比赛列表/详情/赔率
│   │   ├── bets.py             # 下注/查询
│   │   └── user_center.py      # 金币历史/下注历史
│   ├── admin/
│   │   ├── admin_auth.py       # 管理员登录
│   │   ├── users.py            # 用户账号管理
│   │   ├── coins.py            # 金币操作
│   │   ├── settlements.py      # 结算管理
│   │   ├── admins.py           # 管理员管理（超管）
│   │   └── logs.py             # 操作日志（超管）
│   ├── services/
│   │   ├── odds_fetcher.py     # odds-api.io 数据采集
│   │   ├── settlement.py       # 结算计算引擎
│   │   └── team_names.py       # 球队名中英文映射
│   ├── scheduler.py            # APScheduler 定时任务
│   ├── wsgi.py                 # Gunicorn 入口
│   └── database/
│       └── init_db.py          # 数据库初始化
├── frontend/                   # Vue 3 前端
│   ├── src/
│   │   ├── views/              # 用户端页面
│   │   ├── admin/              # 管理端页面
│   │   ├── components/         # 通用组件
│   │   ├── stores/             # Pinia 状态管理
│   │   ├── router/             # 路由配置
│   │   └── api/                # API 请求封装
│   └── vite.config.js
├── nginx/
│   └── bet365cn.conf           # Nginx 配置
├── scripts/
│   └── deploy.sh               # 部署脚本
└── data/
    └── team_names.json         # 球队名映射表
```

---

## 五、数据库设计

### 3.1 表结构

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  admin_accounts  │     │  user_accounts   │     │    matches       │
│─────────────────│     │─────────────────│     │─────────────────│
│ id (PK)          │     │ id (PK)          │     │ id (PK)          │
│ username (UQ)    │     │ username (UQ)    │     │ event_id (UQ)    │
│ password_hash    │     │ password_hash    │     │ home_team        │
│ role             │     │ nickname         │     │ away_team        │
│  'super_admin'   │     │  "用户001"        │     │ league_name      │
│  'admin'         │     │ coin_balance     │     │ league_slug      │
│ created_at       │     │ created_at       │     │ match_date       │
│ created_by       │     │ status           │     │ status           │
└─────────────────┘     │  'active'        │     │  pending/live/   │
                         │  'disabled'      │     │  settled/cancelled│
                         └─────────────────┘     │ scores_home      │
                                                 │ scores_away      │
┌─────────────────┐                              │ updated_at       │
│      odds        │                              └─────────────────┘
│─────────────────│
│ id (PK)          │     ┌─────────────────┐     ┌─────────────────┐
│ match_id (FK)    │     │      bets        │     │ coin_transactions│
│ bookmaker        │     │─────────────────│     │─────────────────│
│ market_type      │     │ id (PK)          │     │ id (PK)          │
│  'ML'/'Spread'/  │     │ user_id (FK)     │     │ user_id (FK)     │
│  'Totals'/'CS'   │     │ match_id (FK)    │     │ amount           │
│ odds_data (JSON) │     │ market_type      │     │ 正数=加 / 负数=减 │
│ updated_at       │     │ selection        │     │ type             │
└─────────────────┘     │  'home'/'draw'/   │     │  'admin_add'     │
                         │  'away'/'over'/   │     │  'admin_deduct'  │
                         │  'under'/'2-1'..│     │  'bet_place'     │
                         │ odds_value        │     │  'bet_win'       │
                         │ bet_amount        │     │  'bet_refund'    │
                         │ potential_win     │     │ operator_id (FK) │
                         │ status            │     │ created_at       │
                         │  'pending'        │     └─────────────────┘
                         │  'won'/'lost'     │
                         │  'push'/'refunded'│     ┌─────────────────┐
                         │ placed_at         │     │ operation_logs   │
                         │ settled_at        │     │─────────────────│
                         └─────────────────┘     │ id (PK)          │
                                                 │ admin_id (FK)    │
┌─────────────────┐                              │ action           │
│   settlements    │                              │ target_type      │
│─────────────────│                              │ target_id        │
│ id (PK)          │                              │ detail (JSON)    │
│ match_id (FK)    │                              │ created_at       │
│ status           │                              └─────────────────┘
│  'pending'       │
│  'confirmed'     │
│ total_bets       │
│ total_users      │
│ total_payout     │
│ detail (JSON)    │
│ confirmed_by (FK)│
│ created_at       │
│ confirmed_at     │
└─────────────────┘
```

### 3.2 关键索引

| 表 | 索引 | 用途 |
|----|------|------|
| matches | event_id UNIQUE | API去重 |
| matches | (status, match_date) | 首页查询"今天 pending的比赛" |
| odds | (match_id, market_type, bookmaker) | 查询某场比赛的赔率 |
| bets | (user_id, status) | "我的下注"列表 |
| bets | (match_id, status) | 结算时查询本场所有下注 |
| coin_transactions | (user_id, created_at) | 用户金币明细 |
| operation_logs | (admin_id, created_at) | 操作日志查询 |

---

## 六、API 设计

### 4.1 用户端 API（前缀 `/api`）

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | /api/auth/login | 用户登录 | 无 |
| POST | /api/auth/change-password | 修改密码 | 用户 |
| GET | /api/matches?status=&date= | 比赛列表 | 用户 |
| GET | /api/matches/:id | 比赛详情（含四种赔率） | 用户 |
| POST | /api/bets | 下注 | 用户 |
| GET | /api/bets?status= | 我的下注历史 | 用户 |
| GET | /api/transactions | 我的金币变动 | 用户 |
| GET | /api/profile | 个人信息 | 用户 |

### 4.2 下注接口请求体

```json
{
  "match_id": 123,
  "market_type": "ML",
  "selection": "home",
  "bet_amount": 100
}
```

> 后端校验：余额≥bet_amount≥50，赔率有效，比赛状态为 pending

### 4.3 管理员端 API（前缀 `/api/admin`）

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | /admin/auth/login | 管理员登录 | 无 |
| POST | /admin/users | 创建用户 | 超管/普管 |
| DELETE | /admin/users/:id | 删除用户 | 超管/普管 |
| GET | /admin/users | 用户列表 | 超管/普管 |
| POST | /admin/users/:id/coins | 增减金币 | 超管/普管 |
| GET | /admin/settlements | 待结算列表 | 超管 |
| POST | /admin/settlements/:id/confirm | 确认结算 | 超管 |
| POST | /admin/matches/:id/cancel | 取消比赛 | 超管 |
| POST | /admin/admins | 创建管理员 | 超管 |
| DELETE | /admin/admins/:id | 删除管理员 | 超管 |
| GET | /admin/admins | 管理员列表 | 超管 |
| GET | /admin/logs | 操作日志 | 超管 |
| GET | /admin/stats | 金币统计 | 超管 |

---

## 七、定时任务

| 任务 | 频率 | 说明 |
|------|------|------|
| `fetch_matches` | 每 30 分钟 | 拉取五大联赛+世界杯 pending/live 比赛，更新/插入 matches 表 |
| `fetch_odds` | 每 10 分钟 | 遍历 pending 比赛，拉取 Bet365+Sbobet 赔率，更新 odds 表 |
| `check_settled` | 每 15 分钟 | 查询已结束的比赛，将 status=live/pending 且 API 返回 settled 的比赛状态更新，触发结算待确认 |
| `cleanup_old` | 每天凌晨 | 清理 7 天前的赔率数据（可选） |

### API 消耗预算（V1.0）

```
fetch_matches:   6 联赛 × 1 次 × 2 次/小时 = 12 次
fetch_odds:      ~30 场 × 1 次 × 6 次/小时 = 180 次 (合并 Bet365+Sbobet 到一次请求)
check_settled:   1 次 × 4 次/小时 = 4 次
───────────────────────────────────────────
总计: ~196 次/小时（接近 200 上限，需注意）
```

> ⚠️ 注意：fetch_odds 的单次请求可以用 `bookmakers=Bet365,Sbobet` 同时获取两家赔率，节省一半调用。算上缓存优化后约 100-120 次/小时。

---

## 八、结算计算引擎

### 判定逻辑

```
function settle(bet, final_score):
    home_goals = final_score.home
    away_goals = final_score.away
    total_goals = home_goals + away_goals
    
    switch bet.market_type:
        case 'ML':
            if bet.selection == 'home' and home_goals > away_goals: return WON
            if bet.selection == 'draw' and home_goals == away_goals: return WON
            if bet.selection == 'away' and away_goals > home_goals: return WON
            return LOST
            
        case 'Spread':
            hdp = bet.odds_data.hdp
            adjusted = home_goals - hdp  // hdp>0 主队让球
            if adjusted > away_goals: winner = 'home'
            elif adjusted < away_goals: winner = 'away'
            else: return PUSH  // 走水
            
            if bet.selection == winner: return WON
            return LOST
            
        case 'Totals':
            hdp = bet.odds_data.hdp
            if total_goals == hdp: return PUSH  // 走水
            if bet.selection == 'over' and total_goals > hdp: return WON
            if bet.selection == 'under' and total_goals < hdp: return WON
            return LOST
            
        case 'CS':
            expected = bet.selection  // "2-1"
            actual = f"{home_goals}-{away_goals}"
            if expected == actual: return WON
            return LOST
```

### 走水（Push）处理
- 状态标记为 `push`
- 退回本金，不赚不赔
- 在 coin_transactions 中记录 `type='bet_refund'`

---

## 九、前端路由

### 用户端

| 路由 | 页面 | 说明 |
|------|------|------|
| `/` | 首页 | 今日比赛列表（全部/即将开始/进行中/已结束） |
| `/match/:id` | 比赛详情 | 四种玩法 Tab 切换 + 下注 |
| `/my-bets` | 我的下注 | 下注历史列表 |
| `/my-coins` | 金币记录 | 金币变动明细 |
| `/login` | 登录 | |
| `/profile` | 个人中心 | 改密码 |

### 管理端

| 路由 | 页面 | 权限 |
|------|------|------|
| `/admin/login` | 管理员登录 | |
| `/admin` | 管理后台首页 | 超管/普管 |
| `/admin/users` | 用户管理（创建/删除） | 超管/普管 |
| `/admin/coins` | 金币操作 | 超管/普管 |
| `/admin/settlements` | 结算管理 | 超管 |
| `/admin/admins` | 管理员管理 | 超管 |
| `/admin/logs` | 操作日志 | 超管 |
| `/admin/stats` | 金币统计 | 超管 |

---

## 十、关键交互流程

### 8.1 用户下注流程

```
首页(比赛列表) → 点击比赛 → 比赛详情页
  ┌──────────────────────────────────┐
  │ 赛事信息（队名/时间/联赛）         │
  │ [胜平负] [让球盘] [大小球] [波胆] │ ← Tab 切换
  │                                  │
  │ 玩法选项（按钮组/比分网格）        │
  │ 金额输入 [___] 金币               │
  │ 预估奖励：XXX 金币                 │
  │ [确认下注]                        │
  └──────────────────────────────────┘
  → 确认弹窗 → 扣金币 → 跳转"我的下注"
```

### 8.2 超管结算流程

```
管理后台 → 结算管理 → 待结算列表
  ┌─────────────────────────────────────┐
  │ 曼城 3:1 伯恩茅斯  [待结算]          │
  │ 共 15 注 | 12 用户 | 总赔付 3,200 金 │
  │                                     │
  │ [展开查看明细]                       │
  │   用户001 胜平负-主胜 100金 → 赢165金 │
  │   用户003 大小球-大球 200金 → 输      │
  │   ...                               │
  │                                     │
  │ [确认结算]  [取消比赛]               │
  └─────────────────────────────────────┘
```

---

## 十一、球队名映射方案

### 文件：`data/team_names.json`

```json
{
  "England - Premier League": {
    "Manchester City": "曼城",
    "Arsenal": "阿森纳",
    "AFC Bournemouth": "伯恩茅斯",
    ...
  },
  "Spain - LaLiga": {
    "Real Madrid": "皇家马德里",
    "FC Barcelona": "巴塞罗那",
    ...
  }
}
```

### 映射逻辑

```
function translate_team(league_name, team_name):
    league_map = team_names[league_name]
    if league_map and team_name in league_map:
        return league_map[team_name]
    return team_name  // 降级：显示英文
```

> 优先覆盖五大联赛。世界杯球队动态补充。

---

## 十二、开发顺序建议

| 阶段 | 内容 | 预估 |
|------|------|------|
| **Phase 1** | 项目骨架 + 数据库模型 + 球队映射表 | 基础 |
| **Phase 2** | odds-api.io 数据采集 + 定时任务 | 数据 |
| **Phase 3** | 用户端 API（登录/比赛/下注/历史） | 后端 |
| **Phase 4** | 管理端 API（用户管理/金币/结算） | 后端 |
| **Phase 5** | 用户端前端（首页/详情/下注/个人中心） | 前端 |
| **Phase 6** | 管理端前端（用户管理/金币/结算/日志） | 前端 |
| **Phase 7** | Bet365 风格 UI 精细打磨 | 视觉 |
| **Phase 8** | 测试 + 部署 | 交付 |
