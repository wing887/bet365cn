#!/usr/bin/env python3
"""
bet365cn 滚球模拟脚本 — 曼城 vs 利物浦 完整比赛剧本
比赛从 16:15 开始，模拟90分钟内的赔率变化、进球、封盘。

用法: python3 simulate_live_match.py
"""
import requests
import time
import random
import json
from datetime import datetime, timedelta

API = "https://bet365cn.top"
SUPERADMIN = {"username": "superadmin", "password": "admin123"}
USER = {"username": "live_test", "password": "test123"}

SESSION = requests.Session()

def login(email_password):
    r = SESSION.post(f"{API}/api/admin/auth/login", json=email_password)
    return r.json()["token"]["access_token"]

def api(method, path, **kwargs):
    return SESSION.request(method, f"{API}{path}", **kwargs)

TOKEN = login(SUPERADMIN)

# ============ 赔率变化剧本 ============
# 每个阶段定义 [ML主胜, ML平, ML客胜, Spread大盘, 大球, 小球]
# 以及事件描述

SCRIPT = [
    # (比赛分钟, 比分(home,away), ML赔率(h,d,a), Spread hdp, Totals hdp, Totals(over,under), 事件)
    (0,   (0,0), (1.85, 3.60, 4.20), -0.5,  2.5,  (1.90, 1.90), "开球！曼城vs利物浦"),
    (5,   (0,0), (1.80, 3.50, 4.50), -0.5,  2.5,  (1.85, 1.95), "曼城控球占优，赔率微调"),
    (12,  (0,0), (1.72, 3.60, 5.00), -0.5,  2.5,  (1.82, 1.98), "利物浦反击，客胜赔率上升"),
    (18,  (0,0), (1.70, 3.50, 5.50), -0.5,  2.5,  (1.88, 1.92), "比赛胶着"),
    (23,  (1,0), (1.40, 4.50, 9.00), -0.5,  2.5,  (2.10, 1.70), "⚽ 进球！曼城 1-0！斯特林破门 → 全盘封盘30秒"),
    (24,  (1,0), (1.38, 4.50, 9.50), -0.5,  2.5,  (2.15, 1.68), "开盘恢复"),
    (30,  (1,0), (1.35, 4.80, 10.0), -1.0,  2.5,  (2.20, 1.65), "曼城围攻"),
    (38,  (1,0), (1.33, 5.00, 11.0), -1.0,  3.0,  (1.95, 1.85), "萨拉赫远射偏出"),
    (45,  (1,0), (1.30, 5.50, 12.0), -1.0,  3.0,  (1.90, 1.90), "上半场结束 1-0"),
    (50,  (1,0), (1.32, 5.00, 11.5), -1.0,  2.5,  (1.92, 1.88), "下半场开始"),
    (58,  (1,0), (1.38, 4.80, 10.0), -0.5,  2.5,  (1.85, 1.95), "利物浦压上"),
    (67,  (2,0), (1.08, 8.00, 30.0), -1.5,  3.5,  (1.75, 2.05), "⚽ 进球！曼城 2-0！哈兰德头球 → 封盘"),
    (68,  (2,0), (1.07, 8.50, 35.0), -1.5,  3.5,  (1.72, 2.10), "开盘"),
    (75,  (2,0), (1.05, 10.0, 50.0), -1.5,  3.5,  (1.80, 2.00), "曼城稳守"),
    (82,  (2,0), (1.03, 15.0, 80.0), -1.5,  3.5,  (1.85, 1.95), "比赛尾声"),
    (90,  (2,0), (1.02, 20.0, 100.), -1.5,  3.5,  (1.90, 1.90), "⏹ 全场结束 曼城 2-0 利物浦"),
]

def create_match():
    """创建比赛（pending状态，等4:15开球）"""
    r = api("POST", "/api/admin/matches", json={
        "home_team": "Manchester City",
        "away_team": "Liverpool",
        "league_name": "England - Premier League",
        "match_time": "2026-06-07T08:15:00Z",
        "status": "live",
        "scores_home": 0,
        "scores_away": 0,
    }, headers={"Authorization": f"Bearer {TOKEN}"})
    d = r.json()
    if d.get("success"):
        return d["match"]["id"]
    else:
        raise Exception(f"创建失败: {d}")

def add_odds(match_id):
    """初始化4种盘口赔率"""
    markets = {
        "ML": {"home": 1.85, "draw": 3.60, "away": 4.20},
        "Spread": {"hdp": -0.5, "home": 1.90, "away": 1.90},
        "Totals": {"hdp": 2.5, "over": 1.90, "under": 1.90},
        "CS": [
            {"label": "1-0", "odds": 7.00},
            {"label": "2-0", "odds": 8.50},
            {"label": "2-1", "odds": 9.00},
            {"label": "1-1", "odds": 6.50},
            {"label": "0-0", "odds": 11.0},
            {"label": "0-1", "odds": 15.0},
            {"label": "3-0", "odds": 17.0},
            {"label": "3-1", "odds": 21.0},
        ]
    }
    for mt, data in markets.items():
        api("POST", "/api/admin/odds", json={
            "match_id": match_id,
            "market_type": mt,
            "data": data,
        }, headers={"Authorization": f"Bearer {TOKEN}"})

def update_odds(match_id, minute, score, ml, spread_hdp, totals_hdp, totals_odds):
    """更新赔率：直接调admin API更新"""
    # ML
    body = {"status": "active"}
    r = api("PUT", f"/api/admin/odds/match/{match_id}/ML",
            json=body, headers={"Authorization": f"Bearer {TOKEN}"})
    # Spread
    r = api("PUT", f"/api/admin/odds/match/{match_id}/Spread",
            json=body, headers={"Authorization": f"Bearer {TOKEN}"})
    # Totals
    r = api("PUT", f"/api/admin/odds/match/{match_id}/Totals",
            json=body, headers={"Authorization": f"Bearer {TOKEN}"})
    # Update match score/minute
    api("PUT", f"/api/admin/matches/{match_id}", json={
        "scores_home": score[0],
        "scores_away": score[1],
        "match_minute": minute,
        "match_period": "first_half" if minute <= 45 else "second_half",
    }, headers={"Authorization": f"Bearer {TOKEN}"})

def suspend_all(match_id):
    """封盘所有盘口"""
    for mt in ["ML", "Spread", "Totals", "CS"]:
        api("PUT", f"/api/admin/odds/match/{match_id}/{mt}", json={
            "status": "suspended"
        }, headers={"Authorization": f"Bearer {TOKEN}"})

def unsuspend_all(match_id):
    """开盘所有盘口"""
    for mt in ["ML", "Spread", "Totals", "CS"]:
        api("PUT", f"/api/admin/odds/match/{match_id}/{mt}", json={
            "status": "active"
        }, headers={"Authorization": f"Bearer {TOKEN}"})

def settle(match_id):
    """结算比赛"""
    api("PUT", f"/api/admin/matches/{match_id}", json={
        "status": "settled",
        "scores_home": 2,
        "scores_away": 0,
    }, headers={"Authorization": f"Bearer {TOKEN}"})
    r = api("POST", f"/api/admin/matches/{match_id}/settle",
            headers={"Authorization": f"Bearer {TOKEN}"})
    print("结算完成")

# ============ 主流程 ============

print("🎬 创建曼城 vs 利物浦 滚球比赛...")
match_id = create_match()
print(f"   比赛ID: {match_id}")
add_odds(match_id)
print("   赔率已添加 (ML/Spread/Totals/CS)")

print("\n⏰ 等待开球时间 16:15...")
# 立即开始（不等真实时间）
print("   跳过等待，直接开始模拟")

# 加速时间线：每个阶段间隔2-5秒
start = datetime.utcnow()
for i, (minute, score, ml, spread_hdp, totals_hdp, totals_odds, event) in enumerate(SCRIPT):
    # 检查是否需要封盘（进球事件）
    if "进球" in event:
        print(f"\n   🚫 封盘中...")
        suspend_all(match_id)
        time.sleep(3)
        print(f"   ✅ 开盘恢复")
        unsuspend_all(match_id)
        time.sleep(1)
    
    update_odds(match_id, minute, score, ml, spread_hdp, totals_hdp, totals_odds)
    
    home_score, away_score = score
    print(f"   [{minute:>3}'] {score[0]}:{score[1]} | ML {ml[0]:.2f}/{ml[1]:.2f}/{ml[2]:.2f} | {event}")
    
    # 间隔（加速：1-3秒/阶段）
    if "结束" in event:
        break
    time.sleep(random.uniform(1.5, 3))

print(f"\n⏹ 比赛结束，结算中...")
settle(match_id)

elapsed = (datetime.utcnow() - start).total_seconds()
print(f"\n✅ 模拟完成！比赛ID={match_id}，耗时{elapsed:.0f}秒")
print(f"   打开 https://bet365cn.top 查看")
