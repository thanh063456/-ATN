import urllib.request, json, urllib.parse

base = 'http://127.0.0.1:8000/api/v1/search'
url = f"{base}?q={urllib.parse.quote('tam hoan nghia vu quan su')}&page_size=5"
with urllib.request.urlopen(urllib.request.Request(url)) as resp:
    data = json.loads(resp.read().decode())
    print("Resolved query:", data.get("resolved_query"))
    print("Total hits:", data.get("total_hits"))
    for r in data.get("results", []):
        print(f"Doc: {r.get('title')} | Score: {r.get('score')}")
