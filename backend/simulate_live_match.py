#!/usr/bin/env python3 -u
"""bet365cn 滚球模拟 — 曼城vs利物浦 19:30开球 真实90分钟（服务器本地执行）"""
import requests, time, random, sys, json
from datetime import datetime

API = "http://localhost:888"
S = requests.Session()

def log(msg):
    t = datetime.utcnow().strftime('%H:%M:%S')
    print(f"[{t}] {msg}", flush=True)

def slogin():
    r = S.post(f"{API}/api/admin/auth/login",
               json={"username":"superadmin","password":"admin123"}, timeout=5)
    return r.json()["token"]["access_token"]

log("登录...")
TOKEN = slogin()
H = {"Authorization": f"Bearer {TOKEN}"}
log("✅")

def post(path, data):
    return S.post(f"{API}{path}", json=data, headers=H, timeout=5).json()

def put(path, data):
    return S.put(f"{API}{path}", json=data, headers=H, timeout=5).json()

# ========== 创建比赛 ==========
log("创建比赛...")
r = post("/api/admin/matches", {
    "home_team":"Manchester City","away_team":"Liverpool",
    "league_name":"England - Premier League",
    "match_time":"2026-06-07T11:30:00Z","status":"pending",
})
mid = r["match"]["id"]
log(f"比赛ID={mid}")

log("创建赔率...")
for mt, data in {
    "ML": {"home":1.85,"draw":3.60,"away":4.20},
    "Spread": {"hdp":-0.5,"home":1.90,"away":1.90},
    "Totals": {"hdp":2.5,"over":1.90,"under":1.90},
}.items():
    post("/api/admin/odds", {"match_id":mid,"market_type":mt,"data":data})
log("✅ 3种盘口")

# ========== 等待开球 ==========
def bj(): return datetime.utcnow().timestamp() + 8*3600

now = bj()
midnight = now - (now % 86400)
TARGET = 19*3600 + 30*60
left = TARGET - (now - midnight)

if left > 0:
    log(f"等待 {int(left//60)}分{int(left%60)}秒 到 19:30...")
    while True:
        now = bj()
        l = TARGET - (now - (now - (now % 86400)))
        if l <= 0: break
        if int(l) % 30 == 0:
            log(f"  距开球: {int(l//60)}分{int(l%60)}秒")
        time.sleep(min(15, l+1))

# ========== 开球 ==========
log("⚽ 开球！")
put(f"/api/admin/matches/{mid}", {
    "status":"live","scores_home":0,"scores_away":0,
    "match_minute":0,"match_period":"first_half",
})

def tick(minute, score_h, score_a, ml, spread_hdp, totals_hdp, totals, suspended=False):
    period = "first_half" if minute <= 45 else "second_half"
    put(f"/api/admin/matches/{mid}", {
        "scores_home":score_h,"scores_away":score_a,
        "match_minute":minute,"match_period":period,
    })
    s = "suspended" if suspended else "active"
    rnd = lambda: round(random.uniform(-0.03,0.03), 2)
    for mt, d in [
        ("ML", {"home":ml[0],"draw":ml[1],"away":ml[2]}),
        ("Spread", {"hdp":spread_hdp,"home":round(1.90+rnd(),2),"away":round(1.90+rnd(),2)}),
        ("Totals", {"hdp":totals_hdp,"over":totals[0],"under":totals[1]}),
    ]:
        put(f"/api/admin/odds/match/{mid}/{mt}", {"status":s,"data":d})

SCRIPT = [
    (0,   0,0, (1.85,3.60,4.20), -0.5, 2.5, (1.90,1.90), False, "开球！伊蒂哈德球场"),
    (3,   0,0, (1.83,3.55,4.30), -0.5, 2.5, (1.88,1.92), False, "曼城控球"),
    (6,   0,0, (1.80,3.50,4.50), -0.5, 2.5, (1.85,1.95), False, "利物浦防守"),
    (10,  0,0, (1.78,3.50,4.60), -0.5, 2.5, (1.83,1.97), False, "德布劳内远射"),
    (13,  0,0, (1.75,3.55,4.80), -0.5, 2.5, (1.80,2.00), False, "角球机会"),
    (15,  0,0, (1.73,3.55,5.00), -0.5, 2.5, (1.82,1.98), False, "节奏加快"),
    (18,  0,0, (1.70,3.55,5.20), -0.5, 2.5, (1.88,1.92), False, "阿诺德传中"),
    (20,  0,0, (1.68,3.60,5.50), -0.5, 2.5, (1.85,1.95), False, "萨拉赫单刀偏出！"),
    (23,  1,0, (1.38,4.50,9.50), -0.5, 2.5, (2.15,1.68), True,  "⚽ 曼城1-0！斯特林远射 → 封盘"),
    (25,  1,0, (1.36,4.60,10.0), -0.5, 2.5, (2.20,1.65), False, "开盘"),
    (28,  1,0, (1.34,4.80,10.5), -0.5, 2.5, (2.25,1.62), False, "曼城施压"),
    (31,  1,0, (1.32,5.00,11.0), -0.5, 2.5, (2.30,1.60), False, "利物浦调整"),
    (34,  1,0, (1.35,4.80,10.5), -0.5, 2.5, (2.22,1.64), False, "稳住阵脚"),
    (37,  1,0, (1.33,4.90,11.0), -0.5, 2.5, (2.18,1.66), False, "哈兰德冲顶"),
    (40,  1,0, (1.31,5.00,11.5), -0.5, 2.5, (2.20,1.65), False, "补时2分钟"),
    (42,  1,0, (1.30,5.00,12.0), -0.5, 2.5, (2.22,1.64), False, "萨拉赫任意球"),
    (45,  1,0, (1.28,5.50,13.0), -0.5, 2.5, (2.25,1.62), False, "半场 1-0"),
    (46,  1,0, (1.30,5.20,12.5), -0.5, 2.5, (2.15,1.68), False, "下半场"),
    (49,  1,0, (1.32,5.00,12.0), -0.5, 2.5, (2.10,1.70), False, "利物浦进攻"),
    (52,  1,0, (1.34,4.80,11.5), -0.5, 2.5, (2.05,1.75), False, "角球"),
    (55,  1,0, (1.36,4.60,11.0), -0.5, 2.5, (2.00,1.80), False, "萨拉赫射门"),
    (58,  1,0, (1.38,4.50,10.5), -0.5, 2.5, (1.95,1.85), False, "利物浦压上"),
    (61,  1,0, (1.40,4.30,10.0), -0.5, 2.5, (1.90,1.90), False, "曼城防守"),
    (64,  1,0, (1.42,4.20,9.50), -0.5, 2.5, (1.88,1.92), False, "德布劳内反击"),
    (67,  2,0, (1.06,9.00,35.0), -1.5, 3.5, (1.72,2.08), True,  "⚽ 曼城2-0！哈兰德 → 封盘"),
    (69,  2,0, (1.05,9.50,40.0), -1.5, 3.5, (1.68,2.15), False, "开盘"),
    (72,  2,0, (1.04,10.0,45.0), -1.5, 3.5, (1.70,2.10), False, "体能下降"),
    (75,  2,0, (1.03,12.0,55.0), -1.5, 3.5, (1.75,2.05), False, "控节奏"),
    (78,  2,0, (1.03,13.0,60.0), -1.5, 3.5, (1.78,2.02), False, "换人"),
    (81,  2,0, (1.02,14.0,65.0), -1.5, 3.5, (1.80,2.00), False, "格拉利什"),
    (84,  2,0, (1.02,15.0,70.0), -1.5, 3.5, (1.82,1.98), False, "最后几分钟"),
    (87,  2,0, (1.01,18.0,80.0), -1.5, 3.5, (1.85,1.95), False, "补时3分钟"),
    (89,  2,0, (1.01,20.0,90.0), -1.5, 3.5, (1.88,1.92), False, "最后进攻"),
    (90,  2,0, (1.00,25.0,100.), -1.5, 3.5, (1.90,1.90), False, "全场结束 曼城2-0！"),
]

match_start = bj()
log("开始模拟90分钟比赛...")
for minute, sh, sa, ml, hdp, thdp, tot, sus, evt in SCRIPT:
    target = match_start + minute * 60
    wait = target - bj()
    if wait > 0: time.sleep(wait)
    tick(minute, sh, sa, ml, hdp, thdp, tot, suspended=sus)
    sus_tag = "🚫" if sus else "  "
    log(f"  {minute:>3}' {sh}:{sa} ML{ml[0]:.2f}/{ml[1]:.2f}/{ml[2]:.2f} {sus_tag} {evt}")

# ========== 结算 ==========
log("结算...")
time.sleep(2)
put(f"/api/admin/matches/{mid}", {"status":"settled","scores_home":2,"scores_away":0})
time.sleep(2)
try:
    post(f"/api/admin/matches/{mid}/settle", {})
    log("✅ 结算完成")
except Exception as e:
    log(f"结算异常: {e}")

log(f"✅ 模拟完成！曼城2-0利物浦 | ID={mid}")
