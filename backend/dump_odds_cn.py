import requests, json
from collections import defaultdict

PROXY = {"http": "http://172.18.176.1:10808", "https": "http://172.18.176.1:10808"}
api_keys = [
    "cbed45cdeb7ea196b7ba4335757cf3d4beaf6654ee2b73b30a29fd2c2b38e46b",
    "a26c35648273b834d344da959c383d9700e75e5279d574b81a61887f16b6ea9b",
    "5642057727ebd5163744ae40ef81b330df1f88df061463a5941cfcd25a4112c5",
]

# Try each key
data = None
for key in api_keys:
    try:
        resp = requests.get("https://api.odds-api.io/v3/events",
            params={"sport":"football","league":"international-world-cup","apiKey":key},
            proxies=PROXY, timeout=15)
        if resp.status_code == 200 and isinstance(resp.json(), list):
            evt = resp.json()[0]
            event_id = evt["id"]
            print(f"Events OK with key {key[:8]}...")
            
            resp2 = requests.get("https://api.odds-api.io/v3/odds",
                params={"eventId":event_id,"bookmakers":"Bet365","apiKey":key},
                proxies=PROXY, timeout=15)
            if resp2.status_code == 200 and "bookmakers" in resp2.json():
                data = resp2.json()
                print(f"Odds OK, {len(data['bookmakers']['Bet365'])} markets")
                break
        print(f"  key {key[:8]}... failed (status={resp.status_code})")
    except Exception as e:
        print(f"  key {key[:8]}... error: {e}")

if not data:
    print("All keys failed, reading from local cache")
    exit(1)

evt = data
home = evt.get("home","?"); away = evt.get("away","?")
date = evt.get("date","")[:16].replace("T"," ")
markets = evt["bookmakers"]["Bet365"]

NAME_CN = {
    "ML": "胜平负（独赢）",
    "Draw No Bet": "平局退款",
    "Double Chance": "双重机会",
    "Spread": "让球盘（亚盘）",
    "Spread HT": "半场让球",
    "European Handicap": "欧洲让球（多档）",
    "Alternative Asian Handicap": "替代亚盘（多档）",
    "1st Half Handicap": "上半场让球",
    "Half Time Result": "半场胜平负",
    "Totals": "大小球（亚盘）",
    "Goals Over/Under": "总进球（欧盘）",
    "Alternative Total Goals": "替代总进球",
    "Alternative Goal Line": "替代进球线（亚盘）",
    "Number of Goals In Match": "进球数区间",
    "Exact Total Goals": "精确总进球",
    "Team Total Goals Home": "主队总进球",
    "Team Total Goals Away": "客队总进球",
    "Correct Score": "波胆（精确比分）",
    "Both Teams To Score": "双方进球",
    "Both Teams To Score HT": "半场双方进球",
    "Both Teams To Score 2H": "下半场双方进球",
    "Corners Spread": "角球让球",
    "Corners Totals": "角球大小",
    "Corners Totals HT": "半场角球大小",
    "Corners": "角球总数",
    "Total Corners": "角球分布",
    "Alternative Corners": "替代角球",
    "Corners Race": "角球竞速",
    "Corners 2-Way": "角球双向",
    "Corner Handicap": "角球让球（多档）",
    "Team Corners Home": "主队角球",
    "Team Corners Away": "客队角球",
    "Anytime Goalscorer": "任意时间进球",
    "Team Goalscorer": "球队进球球员",
    "Multi Scorers": "多球进球",
    "Player To Score or Assist": "进球或助攻",
    "Player Shots": "球员射门",
    "Player Shots on Target": "球员射正",
    "Player Shots on Target Outside Box": "禁区外射正",
    "Player Headed Shots on Target": "头球射正",
    "Player Cards": "球员吃牌",
    "Player to be Booked": "球员被罚牌",
    "Player Fouls Committed": "球员犯规",
    "Player To Be Fouled": "球员被侵犯",
    "Player Tackles": "球员抢断",
    "Player Passes": "球员传球",
    "Goalkeeper Saves": "门将扑救",
    "Match Shots": "全场射门",
    "Match Shots on Target": "全场射正",
    "Match Tackles": "全场抢断",
    "Match Offsides": "全场越位",
    "Team Shots Home": "主队射门",
    "Team Shots Away": "客队射门",
    "Team Shots on Target Home": "主队射正",
    "Team Shots on Target Away": "客队射正",
    "Team Tackles Home": "主队抢断",
    "Team Tackles Away": "客队抢断",
    "Team Offsides Home": "主队越位",
    "Team Offsides Away": "客队越位",
    "Specials": "逆转取胜",
    "Goal Method": "进球方式",
    "First 10 Minutes (00:00 - 09:59)": "前10分钟",
}
NAME_CN = {k: v for k, v in NAME_CN.items() if v}  # clean
for mk in markets:
    if mk["name"] not in NAME_CN:
        NAME_CN[mk["name"]] = mk["name"]

def cn(n): return NAME_CN.get(n, n)

# Categorize
cats = defaultdict(list)
for mk in markets:
    n = mk["name"]
    if n == "ML": cats["胜平负"].append(mk)
    elif "Correct Score" == n: cats["波胆"].append(mk)
    elif "Both Teams" in n: cats["双方进球"].append(mk)
    elif any(w in n for w in ["Corners","Corner"]): cats["角球"].append(mk)
    elif any(w in n for w in ["Player","Anytime","Multi","Goalkeeper","Scorers","Booked","Cards","Fouls","Fouled","Tackles","Passes","Saves"]):
        if "Match" not in n and "Team" not in n: cats["球员"].append(mk)
        else: cats["球队数据"].append(mk)
    elif any(w in n for w in ["Team","Match"]): cats["球队数据"].append(mk)
    elif any(w in n for w in ["Totals","Goals","Goal Line"]): cats["大小球"].append(mk)
    elif any(w in n for w in ["Spread","Handicap","Result"]): cats["让球"].append(mk)
    else: cats["特殊"].append(mk)

# Category order
CAT_ORDER = ["胜平负","让球","大小球","波胆","双方进球","角球","球员","球队数据","特殊"]

# Build markdown
L = []
L.append(f"# {home} vs {away}")
L.append(f"## 世界杯2026 · {date}")
L.append(f"**Bet365 · odds-api.io v3**")
L.append("")

def od(o):
    """Format one outcome"""
    if "home" in o and "draw" in o and "away" in o:
        hdp = o.get("hdp",""); hdp_s = f"（让{hdp}球）" if hdp else ""
        return f"主{o['home']} / 平{o['draw']} / 客{o['away']} {hdp_s}"
    # European Handicap: {hdp, draw, away} without home
    if "draw" in o and "away" in o and "hdp" in o:
        hdp = o["hdp"]
        return f"让{hdp}球 平{o['draw']} / 客{o['away']}"
    if "home" in o and "away" in o:
        hdp = o.get("hdp",""); label = o.get("label","")
        hdp_s = f"（{hdp}球）" if hdp else ""
        if label: return f"主{o.get('home','-')} / 客{o.get('away','-')} [{label}]"
        return f"主{o['home']} / 客{o['away']} {hdp_s}"
    if "over" in o and "under" in o:
        hdp = o.get("hdp",""); hdp_s = f"（{hdp}球）" if hdp else ""
        return f"大{o['over']} / 小{o['under']} {hdp_s}"
    if "yes" in o and "no" in o:
        return f"是 {o['yes']} / 否 {o['no']}"
    if "label" in o:
        label = o['label']
        # Translate common labels
        label = label.replace("Draw","平局").replace("Home","主").replace("Away","客")
        label = label.replace("Mexico","墨西哥").replace("South Africa","南非")
        label = label.replace(" or ","或").replace(" (1)","(主)").replace(" (2)","(客)")
        label = label.replace(" Goals","球").replace(" Goal","球").replace(" Over","球以上")
        label = label.replace("Under ","小于").replace("Tie","平手")
        v = o.get("over") or o.get("under") or o.get("price") or o.get("home") or ""
        v2 = o.get("away","")
        if v2: v = f"{v} / {v2}"
        return f"{label} @{v}"
    return str(o)[:80]

for cat_name in CAT_ORDER:
    cms = cats.get(cat_name, [])
    if not cms: continue
    L.append(f"## {cat_name}")
    L.append("")
    
    for mk in cms:
        n = mk["name"]; odds = mk["odds"]
        count = len(odds); u = mk.get("updatedAt","")[:16].replace("T"," ")
        L.append(f"### {cn(n)}（{count}项）")
        L.append(f"*更新 {u}*")
        L.append("")
        L.append("| 选项 | 赔率 |")
        L.append("|------|------|")
        
        show = odds if count <= 30 else odds[:20]
        if count > 30:
            L.append(f"| ⚠️ 仅显示前20项，共{count}项 |")
        
        for o in show:
            L.append(f"| | {od(o)} |")
        L.append("")

L.append("---")
L.append(f"**共 {len(markets)} 种玩法** · odds-api.io v3 免费Key · Bet365")
L.append(f"**比赛**: {home} vs {away} · 世界杯2026 · {date}")

path = "/mnt/c/Users/admin/Desktop/bet365cn_odds_reference.md"
with open(path, "w", encoding="utf-8") as f:
    f.write("\n".join(L))
print(f"Done: {path}, {len(markets)} markets, {len(L)} lines")
for c in CAT_ORDER:
    if c in cats:
        print(f"  {c}: {len(cats[c])} 种")
