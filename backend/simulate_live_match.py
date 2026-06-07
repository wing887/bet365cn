#!/usr/bin/env python3
"""
bet365cn 滚球真实时模拟
曼城 vs 利物浦，19:30 开球，真实90分钟
"""
import requests, time, random, json
from datetime import datetime

API = "https://bet365cn.top"
S = requests.Session()

def slogin():
    r = S.post(f"{API}/api/admin/auth/login", json={"username":"superadmin","password":"admin123"})
    return r.json()["token"]["access_token"]

TOKEN = slogin()
H = {"Authorization": f"Bearer {TOKEN}"}

def post(path, data):
    return S.post(f"{API}{path}", json=data, headers=H).json()

def put(path, data):
    return S.put(f"{API}{path}", json=data, headers=H).json()

# ==================== 创建比赛 ====================
print("🎬 创建 曼城 vs 利物浦")
BEIJING_NOW = datetime.utcnow().timestamp() + 8*3600
print(f"   北京时间: {datetime.fromtimestamp(BEIJING_NOW).strftime('%H:%M:%S')}")

r = post("/api/admin/matches", {
    "home_team": "Manchester City",
    "away_team": "Liverpool",
    "league_name": "England - Premier League",
    "match_time": "2026-06-07T11:30:00Z",  # 19:30 北京
    "status": "pending",
})
mid = r["match"]["id"]
print(f"   比赛ID: {mid} (pending)")

# 创建初始赔率
for mt, data in {
    "ML": {"home":1.85,"draw":3.60,"away":4.20},
    "Spread": {"hdp":-0.5,"home":1.90,"away":1.90},
    "Totals": {"hdp":2.5,"over":1.90,"under":1.90},
}.items():
    post("/api/admin/odds", {"match_id":mid,"market_type":mt,"data":data})
print("   赔率已就绪")
print(f"\n⏰ 等待 19:30 开球...\n")

# ==================== 等待开球 ====================
def beijing_now():
    return datetime.utcnow().timestamp() + 8*3600

target = 19*3600 + 30*60  # 19:30 in seconds since midnight
while True:
    now = beijing_now()
    midnight = now - (now % 86400)
    elapsed = now - midnight
    remaining = target - elapsed
    if remaining <= 0:
        break
    mins = int(remaining // 60)
    secs = int(remaining % 60)
    print(f"   距开球: {mins}分{secs}秒", end="\r")
    time.sleep(min(30, remaining))

print(f"\n\n⚽ 开球！19:30\n")

# ==================== 比赛开始 ====================
put(f"/api/admin/matches/{mid}", {
    "status": "live", "scores_home":0, "scores_away":0,
    "match_minute":0, "match_period":"first_half",
})

def tick(minute, score_h, score_a, ml, spread_hdp, totals_hdp, totals, suspended=False):
    """更新比赛状态+赔率"""
    period = "first_half" if minute <= 45 else ("half_time" if minute == 45 else "second_half")
    put(f"/api/admin/matches/{mid}", {
        "scores_home": score_h, "scores_away": score_a,
        "match_minute": minute, "match_period": period,
    })
    s = "suspended" if suspended else "active"
    for mt, d in [
        ("ML", {"home":ml[0],"draw":ml[1],"away":ml[2]}),
        ("Spread", {"hdp":spread_hdp,"home":1.90+random.uniform(-0.05,0.05),"away":1.90+random.uniform(-0.05,0.05)}),
        ("Totals", {"hdp":totals_hdp,"over":totals[0],"under":totals[1]}),
    ]:
        put(f"/api/admin/odds/match/{mid}/{mt}", {"status":s, "data":d})

# ==================== 90分钟剧本 ====================
SCRIPT = [
    # (比赛分钟, 比分(h,a), ML(h,d,a), Spread_hdp, Totals_hdp, Totals(ov,un), 封盘, 事件)
    # === 上半场 ===
    (0,   0,0, (1.85,3.60,4.20), -0.5, 2.5, (1.90,1.90), False, "开球！伊蒂哈德球场座无虚席"),
    (3,   0,0, (1.83,3.55,4.30), -0.5, 2.5, (1.88,1.92), False, "曼城开场控球"),
    (6,   0,0, (1.80,3.50,4.50), -0.5, 2.5, (1.85,1.95), False, "利物浦严密防守"),
    (10,  0,0, (1.78,3.50,4.60), -0.5, 2.5, (1.83,1.97), False, "德布劳内远射被扑"),
    (13,  0,0, (1.75,3.55,4.80), -0.5, 2.5, (1.80,2.00), False, "曼城角球机会"),
    (15,  0,0, (1.73,3.55,5.00), -0.5, 2.5, (1.82,1.98), False, "比赛节奏加快"),
    (18,  0,0, (1.70,3.55,5.20), -0.5, 2.5, (1.88,1.92), False, "阿诺德传中被解围"),
    (20,  0,0, (1.68,3.60,5.50), -0.5, 2.5, (1.85,1.95), False, "萨拉赫单刀偏出！利物浦最佳机会"),
    (23,  1,0, (1.38,4.50,9.50), -0.5, 2.5, (2.15,1.68), True,  "⚽⚽ 进球！！曼城1-0！斯特林禁区外远射破门 → 全盘封盘"),
    (25,  1,0, (1.36,4.60,10.0), -0.5, 2.5, (2.20,1.65), False, "开盘恢复，曼城气势大涨"),
    (28,  1,0, (1.34,4.80,10.5), -0.5, 2.5, (2.25,1.62), False, "曼城持续施压"),
    (31,  1,0, (1.32,5.00,11.0), -0.5, 2.5, (2.30,1.60), False, "利物浦调整阵型"),
    (34,  1,0, (1.35,4.80,10.5), -0.5, 2.5, (2.22,1.64), False, "利物浦稳住阵脚"),
    (37,  1,0, (1.33,4.90,11.0), -0.5, 2.5, (2.18,1.66), False, "哈兰德头球高出"),
    (40,  1,0, (1.31,5.00,11.5), -0.5, 2.5, (2.20,1.65), False, "补时2分钟"),
    (42,  1,0, (1.30,5.00,12.0), -0.5, 2.5, (2.22,1.64), False, "萨拉赫任意球..."),
    (45,  1,0, (1.28,5.50,13.0), -0.5, 2.5, (2.25,1.62), False, "半场结束 曼城1-0利物浦"),

    # === 下半场 ===
    (46,  1,0, (1.30,5.20,12.5), -0.5, 2.5, (2.15,1.68), False, "下半场开始！"),
    (49,  1,0, (1.32,5.00,12.0), -0.5, 2.5, (2.10,1.70), False, "利物浦进攻"),
    (52,  1,0, (1.34,4.80,11.5), -0.5, 2.5, (2.05,1.75), False, "利物浦获得角球"),
    (55,  1,0, (1.36,4.60,11.0), -0.5, 2.5, (2.00,1.80), False, "萨拉赫射门被埃德森抱住"),
    (58,  1,0, (1.38,4.50,10.5), -0.5, 2.5, (1.95,1.85), False, "利物浦持续压上"),
    (61,  1,0, (1.40,4.30,10.0), -0.5, 2.5, (1.90,1.90), False, "曼城收缩防守"),
    (64,  1,0, (1.42,4.20,9.50), -0.5, 2.5, (1.88,1.92), False, "德布劳内反击推进"),
    (67,  2,0, (1.06,9.00,35.0), -1.5, 3.5, (1.72,2.08), True,  "⚽⚽ 进球！！曼城2-0！哈兰德禁区内转身抽射 → 封盘"),
    (69,  2,0, (1.05,9.50,40.0), -1.5, 3.5, (1.68,2.15), False, "开盘恢复，曼城稳操胜券"),
    (72,  2,0, (1.04,10.0,45.0), -1.5, 3.5, (1.70,2.10), False, "利物浦体能下降"),
    (75,  2,0, (1.03,12.0,55.0), -1.5, 3.5, (1.75,2.05), False, "曼城控制节奏"),
    (78,  2,0, (1.03,13.0,60.0), -1.5, 3.5, (1.78,2.02), False, "利物浦换人调整"),
    (81,  2,0, (1.02,14.0,65.0), -1.5, 3.5, (1.80,2.00), False, "格拉利什替补上场"),
    (84,  2,0, (1.02,15.0,70.0), -1.5, 3.5, (1.82,1.98), False, "最后几分钟"),
    (87,  2,0, (1.01,18.0,80.0), -1.5, 3.5, (1.85,1.95), False, "补时3分钟"),
    (89,  2,0, (1.01,20.0,90.0), -1.5, 3.5, (1.88,1.92), False, "利物浦最后一次进攻"),
    (90,  2,0, (1.00,25.0,100.), -1.5, 3.5, (1.90,1.90), False, "全场结束！曼城2-0利物浦"),
]

# ==================== 执行 ====================
match_start = beijing_now()
last_update_minute = -1

for minute, sh, sa, ml, hdp, thdp, tot, sus, evt in SCRIPT:
    # 等待到达该分钟
    target_time = match_start + minute * 60
    while beijing_now() < target_time:
        time.sleep(0.5)
    
    # 更新
    tick(minute, sh, sa, ml, hdp, thdp, tot, suspended=sus)
    
    real_min = int((beijing_now() - match_start) / 60)
    sus_tag = "🚫封盘" if sus else "  "
    t = datetime.fromtimestamp(beijing_now()).strftime('%H:%M:%S')
    print(f"  [{t}] {minute:>3}' {sh}:{sa} | ML {ml[0]:.2f}/{ml[1]:.2f}/{ml[2]:.2f} | {sus_tag} {evt}")

# ==================== 结算 ====================
print(f"\n⏹ 比赛结束，结算中...")
time.sleep(2)
put(f"/api/admin/matches/{mid}", {"status":"settled","scores_home":2,"scores_away":0})
time.sleep(1)
r = post(f"/api/admin/matches/{mid}/settle", {})
print(f"   结算结果: {json.dumps(r, indent=2, ensure_ascii=False)[:500]}")
print(f"\n✅ 真实时模拟完成！曼城 2-0 利物浦")
