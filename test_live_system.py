import urllib.request
import json

print("=== KIEM TRA TRANG THAI HOAT DONG HE THONG LIVE ===")

# 1. Test Frontend 3000
try:
    with urllib.request.urlopen("http://127.0.0.1:3000/") as resp:
        content = resp.read()
        print(f"[1] FRONTEND (http://127.0.0.1:3000): HOAT DONG TOT (Status {resp.status}, Body {len(content)} bytes)")
except Exception as e:
    print(f"[1] FRONTEND ERROR: {e}")

# 2. Test Backend 8000
test_cases = [
    ("mghp", "Tu viet tat hoc vu"),
    ("kkht", "Hoc bong khuyen khich"),
    ("tam hoan nvqs", "Khong dau & Nghia vu quan su"),
    ("don xin tam dung hoc tap", "Tam hoan & Bao luu hoc tap"),
    ("drl", "Diem ren luyen"),
]

print("\n=== KIEM TRA THUC TE 5 TRUY VAN SEARCH TREN BACKEND (http://127.0.0.1:8000) ===")
for q, desc in test_cases:
    url = f"http://127.0.0.1:8000/api/v1/search?q={urllib.parse.quote(q)}"
    try:
        with urllib.request.urlopen(url) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            print(f"\nTruy van: '{q}' ({desc})")
            print(f"  + Phan giai viet tat: '{data.get('resolved_query')}'")
            print(f"  + Nhan dien y dinh:   {data.get('detected_intent')}")
            print(f"  + So ket qua khop:   {data.get('total_hits')} tai lieu (Do tre: {data.get('took_ms')} ms)")
            for i, r in enumerate(data.get("results", [])[:3]):
                print(f"    [{i+1}] {r.get('title')} (Diem: {r.get('score')})")
    except Exception as e:
        print(f"Error for '{q}': {e}")
