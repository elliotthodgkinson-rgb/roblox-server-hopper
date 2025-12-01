import requests
import json
import time

place_id = "109983668079237"
base = f"https://games.roblox.com/v1/games/{place_id}/servers/Public"
out_file = "servers.json"

MAX_PAGES = 3
PAGE_DELAY = 3
BACKOFF_TIME = 5

headers = {"User-Agent": "Mozilla/5.0"}

all_servers = []
error_pages = 0

print("Python server updater starting. Output:", out_file)

cursor = None

for page in range(1, MAX_PAGES + 1):
    params = {
        "limit": 100,
        "cursor": cursor
    }

    try:
        response = requests.get(base, headers=headers, params=params)

        # Handle rate limit
        if response.status_code == 429:
            print(f"[Page {page}] 429 rate limited, waiting {BACKOFF_TIME}s...")
            time.sleep(BACKOFF_TIME)
            error_pages += 1
            if error_pages >= 2:
                print("Too many page errors; stopping.")
                break
            continue

        response.raise_for_status()
        data = response.json()

    except Exception as e:
        print(f"[Page {page}] fetch error:", e)
        break

    cursor = data.get("nextPageCursor")
    servers = data.get("data", [])

    print(f"[Page {page}] received {len(servers)} servers")
    all_servers.extend(servers)

    if not cursor:
        break

    time.sleep(PAGE_DELAY)

# ----------------------------
# FILTER SERVERS (fixes Error 771)
# ----------------------------

cleaned = []

for s in all_servers:
    # Skip servers with missing fields
    if "id" not in s or "playing" not in s or "maxPlayers" not in s:
        continue

    # Skip full servers (fixes 90% of 771 errors)
    if s["playing"] >= s["maxPlayers"]:
        continue

    # Skip high-latency / dead servers
    ping = s.get("ping", 999)
    if ping is None or ping >= 600:
        continue

    cleaned.append({"id": s["id"]})

# Save safely
with open(out_file, "w") as f:
    json.dump(cleaned, f, indent=4)

print(f"Done! Saved {len(cleaned)} joinable servers.")
