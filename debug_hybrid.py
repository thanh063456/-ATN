import urllib.request, json

req = urllib.request.Request('http://127.0.0.1:8000/api/v1/search/hybrid-rrf', 
    data=json.dumps({'query': 'tam hoan nghia vu quan su', 'limit': 3, 'rank_constant_k': 20}).encode(),
    headers={'Content-Type': 'application/json'})
with urllib.request.urlopen(req) as resp:
    hdata = json.loads(resp.read().decode())
    for r in hdata.get('results', []):
        print(f"{r.get('title')}\nRRF: {r.get('rrf_score')} | BM25: #{r.get('bm25_rank')} (score {r.get('bm25_score')}) | kNN: #{r.get('knn_rank')} (score {r.get('knn_score')})\n")
