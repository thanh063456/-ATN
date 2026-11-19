import urllib.request, json, urllib.parse

base = 'http://127.0.0.1:8000/api/v1/search'
test_cases = [
    "mghp", "kkht", "nvqs", "drl", "cpa", "ktx", "bhyt", "blht", "htcpht",
    "mien giam hoc phi", "hoc bong khuyen khich", "diem ren luyen", "tam hoan nghia vu quan su",
    "ky tuc xa", "bao hiem y te", "don xin tam dung hoc tap", "vay von",
    "xin mghp", "xet kkht", "hoan nvqs", "cham drl", "o ktx", "mua bhyt", "xin blht"
]

print(f"{'QUERY':<25} | {'FT COUNT':<8} | {'FT TOP MATCH':<45} | {'HYBRID TOP MATCH':<45}")
print("-" * 130)

for q in test_cases:
    # Fulltext
    ft_top = "NONE"
    ft_cnt = 0
    try:
        url = f"{base}?q={urllib.parse.quote(q)}&page_size=3"
        with urllib.request.urlopen(urllib.request.Request(url)) as resp:
            data = json.loads(resp.read().decode())
            ft_cnt = data.get("total_hits", 0)
            if data.get("results"):
                ft_top = data["results"][0].get("title", "")[:42]
    except Exception as e:
        ft_top = f"ERR: {e}"

    # Hybrid
    hy_top = "NONE"
    try:
        req = urllib.request.Request(f"{base}/hybrid-rrf", 
            data=json.dumps({"query": q, "limit": 3, "rank_constant_k": 20}).encode(),
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req) as resp:
            hdata = json.loads(resp.read().decode())
            if hdata.get("results"):
                hy_top = hdata["results"][0].get("title", "")[:42]
    except Exception as e:
        hy_top = f"ERR: {e}"

    print(f"{q:<25} | {ft_cnt:<8} | {ft_top:<45} | {hy_top:<45}")
