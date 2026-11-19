import urllib.request, json, urllib.parse

base = 'http://127.0.0.1:8000/api/v1/search'
queries = ['mghp', 'kkht', 'nvqs', 'don xin tam dung hoc tap', 'mien giam hoc phi']

for q in queries:
    # Full-text
    url = f"{base}?q={urllib.parse.quote(q)}&page_size=3"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            print(f"=== FULLTEXT: {q} ===")
            print(f"Total: {data.get('total_hits')}, Resolved: {data.get('resolved_query')}, Intent: {data.get('detected_intent')}")
            for r in data.get('results', [])[:2]:
                print(f"  - {r.get('title')} (Score: {r.get('score')})")
    except Exception as e:
        print(f"Fulltext error for {q}: {e}")

    # Hybrid-rrf
    try:
        req = urllib.request.Request(f"{base}/hybrid-rrf", 
            data=json.dumps({"query": q, "limit": 3, "rank_constant_k": 20}).encode(),
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req) as resp:
            hdata = json.loads(resp.read().decode())
            print(f"--- HYBRID-RRF: {q} ---")
            print(f"Total: {hdata.get('total_results')}")
            for r in hdata.get('results', [])[:2]:
                print(f"  - {r.get('title')} (RRF: {r.get('rrf_score')}, BM25: {r.get('bm25_score')}, kNN: {r.get('knn_score')})")
    except Exception as e:
        print(f"Hybrid error for {q}: {e}")
    print()
