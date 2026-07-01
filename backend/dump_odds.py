import requests, json, sys

api_key = "cbed45cdeb7ea196b7ba4335757cf3d4beaf6654ee2b73b30a29fd2c2b38e46b"
PROXY = {"http": "http://172.18.176.1:10808", "https": "http://172.18.176.1:10808"}

resp = requests.get("https://api.odds-api.io/v3/events",
    params={"sport": "football", "league": "international-world-cup", "apiKey": api_key},
    proxies=PROXY, timeout=30)
event_id = resp.json()[0]["id"]
match_name = f"{resp.json()[0]['home']} vs {resp.json()[0]['away']}"
match_date = resp.json()[0]["date"][:10]

resp = requests.get("https://api.odds-api.io/v3/odds",
    params={"eventId": event_id, "bookmakers": "Bet365", "apiKey": api_key},
    proxies=PROXY, timeout=30)
data = resp.json()
markets = data["bookmakers"]["Bet365"]

lines = []
lines.append(f"# {match_name} — odds-api.io 全部玩法明细")
lines.append(f"## 世界杯2026 · {match_date}")
lines.append("")

for mk in markets:
    name = mk["name"]
    odds_list = mk["odds"]
    updated = mk.get("updatedAt", "")[:16].replace("T", " ")
    n = len(odds_list)
    
    if n > 100 and name not in ("ML", "Spread", "Totals"):
        lines.append(f"### {name} ({n}项, 展示前20)")
        odds_list = odds_list[:20]
    else:
        lines.append(f"### {name} ({n}项)")
    lines.append(f"*{updated}*")
    lines.append("")
    lines.append("| 选项 | 赔率 |")
    lines.append("|------|------|")
    
    for o in odds_list:
        if "home" in o and "draw" in o and "away" in o:
            lines.append(f"| 主胜 | @{o['home']} |")
            lines.append(f"| 平局 | @{o['draw']} |")
            lines.append(f"| 客胜 | @{o['away']} |")
            break
        elif "yes" in o and "no" in o:
            lines.append(f"| Yes | @{o['yes']} |")
            lines.append(f"| No  | @{o['no']} |")
            break
        elif "over" in o and "under" in o and "hdp" in o:
            lines.append(f"| Over {o['hdp']} | @{o['over']} |")
            lines.append(f"| Under {o['hdp']} | @{o['under']} |")
        elif "over" in o and "under" in o and "label" in o:
            lines.append(f"| {o['label']} | @{o.get('under','-')} |")
        elif "home" in o and "away" in o and "hdp" in o:
            lines.append(f"| 主 {o['hdp']} | @{o['home']} |")
            lines.append(f"| 客 {o['hdp']} | @{o['away']} |")
        elif "home" in o and "away" in o and "label" in o:
            lines.append(f"| {o['label']} | 主{o.get('home','')} 客{o.get('away','')} |")
        elif "home" in o and "draw" in o and "away" in o and "hdp" in o:
            lines.append(f"| {o.get('label',o['hdp'])} 主/平/客 | @{o['home']}/@{o['draw']}/@{o['away']} |")
        elif "over" in o and "label" in o:
            over = o.get('over',''); under = o.get('under','')
            lines.append(f"| {o['label']} | {'@'+over if over else ''} {'@'+under if under else ''} |")
        elif "label" in o and "over" in o:
            lines.append(f"| {o['label']} | @{o['over']} |")
        elif "label" in o and "under" in o:
            lines.append(f"| {o['label']} | @{o['under']} |")
        elif "label" in o:
            val = o.get('over') or o.get('under') or o.get('price') or ''
            lines.append(f"| {o['label']} | @{val} |")
        else:
            lines.append(f"| {str(o)[:80]} |")
    lines.append("")

# Summary
lines.append("---")
lines.append("## 玩法汇总 (共{}种)".format(len(markets)))
lines.append("")
lines.append("| # | 玩法 | 选项数 | 分类 |")
lines.append("|---|------|:---:|------|")
for i, mk in enumerate(markets):
    name = mk["name"]; n = len(mk["odds"])
    if name == "ML": cat = "胜平负"
    elif "Spread" in name or "Handicap" in name: cat = "让球"
    elif "Totals" in name or "Goals" in name or "Goal Line" in name: cat = "大小球"
    elif "Corners" in name: cat = "角球"
    elif "Both Teams" in name: cat = "双方进球"
    elif any(w in name for w in ["Player","Anytime","Multi","Goalkeeper","Scorers"]): cat = "球员"
    elif any(w in name for w in ["Team","Match"]): cat = "球队统计"
    else: cat = "特殊"
    lines.append(f"| {i+1} | {name} | {n} | {cat} |")

path = "/mnt/c/Users/admin/Desktop/bet365cn_odds_reference.md"
with open(path, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print(f"Done: {path}, {len(markets)} markets, {len(lines)} lines")
