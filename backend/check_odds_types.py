import requests, json

api_key = "cbed45cdeb7ea196b7ba4335757cf3d4beaf6654ee2b73b30a29fd2c2b38e46b"
PROXY = {"http": "http://172.18.176.1:10808", "https": "http://172.18.176.1:10808"}

resp = requests.get("https://api.odds-api.io/v3/events",
    params={"sport": "football", "league": "international-world-cup", "apiKey": api_key},
    proxies=PROXY, timeout=30)
event_id = resp.json()[0]["id"]

resp2 = requests.get("https://api.odds-api.io/v3/odds",
    params={"eventId": event_id, "bookmakers": "Bet365", "apiKey": api_key},
    proxies=PROXY, timeout=30)
data = resp2.json()

# Print raw structure first
print("=== RAW STRUCTURE ===")
print(f"bookmakerIds: {data.get('bookmakerIds')}")
print(f"bookmakers type: {type(data.get('bookmakers')).__name__}")
print(f"bookmakers: {data.get('bookmakers')}")

# The odds might be nested differently
print("\n=== All top-level keys ===")
for k, v in data.items():
    if k not in ("home", "away", "urls", "sport", "league"):
        if isinstance(v, (list, dict)):
            print(f"  {k}: {type(v).__name__}, len={len(v) if isinstance(v,(list,dict)) else '?'}")
            if isinstance(v, dict):
                print(f"    sub-keys: {list(v.keys())[:10]}")
            elif isinstance(v, list) and len(v) > 0:
                print(f"    first item: {type(v[0]).__name__} = {str(v[0])[:200]}")
        else:
            print(f"  {k}: {v}")

# Check if there's a nested structure
for k in ["data", "odds", "markets", "sites"]:
    if k in data:
        print(f"\n=== data.{k} ===")
        print(json.dumps(data[k], indent=2, ensure_ascii=False)[:1000])
