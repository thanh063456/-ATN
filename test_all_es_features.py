import urllib.request, urllib.parse, json, time

BASE_URL = "http://127.0.0.1:8000/api/v1/search"

def run_test(name, url, method="GET", body=None, is_ndjson=False):
    t0 = time.perf_counter()
    try:
        data_bytes = json.dumps(body).encode("utf-8") if body else None
        headers = {"Content-Type": "application/json"} if body else {}
        req = urllib.request.Request(url, data=data_bytes, headers=headers, method=method)
        with urllib.request.urlopen(req, timeout=10) as resp:
            http_code = resp.status
            resp_body = resp.read().decode("utf-8")
            elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
            if is_ndjson:
                lines = [json.loads(line) for line in resp_body.strip().split("\n") if line.strip()]
                return {"name": name, "status": "PASS", "code": http_code, "ms": elapsed_ms, "data": lines, "error": None}
            data = json.loads(resp_body)
            return {"name": name, "status": "PASS", "code": http_code, "ms": elapsed_ms, "data": data, "error": None}
    except urllib.error.HTTPError as e:
        elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
        err_msg = e.read().decode("utf-8")
        return {"name": name, "status": "FAIL", "code": e.code, "ms": elapsed_ms, "data": None, "error": err_msg}
    except Exception as e:
        elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
        return {"name": name, "status": "FAIL", "code": 0, "ms": elapsed_ms, "data": None, "error": str(e)}

# 1. Fulltext search
r1 = run_test("1. Fulltext Search (BM25, OCR, Đa trường)", f"{BASE_URL}?q=mghp&page_size=5")

# Find a valid document_id and student_id from results
doc_id = None
st_id = "20210678"
if r1["data"] and r1["data"].get("results"):
    first_hit = r1["data"]["results"][0]
    doc_id = first_hit.get("document_id")
    if first_hit.get("student_id"):
        st_id = first_hit.get("student_id")

# 2. Hybrid RRF Search
r2 = run_test("2. Hybrid Search RRF (BM25 + kNN Vector)", f"{BASE_URL}/hybrid-rrf", method="POST", body={"query": "mghp", "limit": 5, "rank_constant_k": 20})

# 3. FAQ NLP Ask
r3 = run_test("3. FAQ Tra cứu Quy chế CTSV (RAG)", f"{BASE_URL}/faq/ask?q=dieu+kien+mien+giam+hoc+phi")

# 4. Real-time Autocomplete / Suggest
r4 = run_test("4. Real-time Autocomplete / Suggest", f"{BASE_URL}/suggest?q=mien+giam")

# 5. Trending Keywords
r5 = run_test("5. Trending Search Keywords", f"{BASE_URL}/trending")

# 6. Cluster Stats & Health
r6 = run_test("6. Cluster Health & Index Stats", f"{BASE_URL}/stats")

# 7. Similar Documents (More Like This)
r7 = run_test("7. More Like This / Similar Docs", f"{BASE_URL}/documents/{doc_id}/similar?limit=3") if doc_id else {"name": "7. More Like This", "status": "SKIP", "code": 0, "ms": 0, "error": "No doc ID"}

# 8. Document Validity Tracker
r8 = run_test("8. Document Validity Tracker", f"{BASE_URL}/documents/{doc_id}/validity") if doc_id else {"name": "8. Document Validity", "status": "SKIP", "code": 0, "ms": 0, "error": "No doc ID"}

# 9. Duplicate Check
r9 = run_test("9. Duplicate / SimHash Check", f"{BASE_URL}/documents/{doc_id}/duplicate-check") if doc_id else {"name": "9. Duplicate Check", "status": "SKIP", "code": 0, "ms": 0, "error": "No doc ID"}

# 10. Policy Compliance Audit
r10 = run_test("10. Policy Compliance Eligibility Audit", f"{BASE_URL}/documents/{doc_id}/policy-audit") if doc_id else {"name": "10. Policy Audit", "status": "SKIP", "code": 0, "ms": 0, "error": "No doc ID"}

# 11. Student Profile 360
r11 = run_test("11. Student Profile 360 & Timeline", f"{BASE_URL}/student-profile/{st_id}")

# 12. Trending Topics (Significant Terms)
r12 = run_test("12. Trending Topics (Significant Terms)", f"{BASE_URL}/analytics/trending-topics")

# 13. Staff Performance Analytics
r13 = run_test("13. Staff Performance & KPI Analytics", f"{BASE_URL}/analytics/staff-performance")

# 14. Watcher Alert Rule Creation
r14 = run_test("14. Watcher Alert Rule Creation", f"{BASE_URL}/watchers", method="POST", body={"name": "Giám sát mồ côi khẩn cấp", "query_text": "mồ côi", "category_code": "DON_XIN"})

# 15. Watcher Triggered Events
watcher_id = r14["data"].get("watcher_id") if r14["data"] else "wtch_01"
r15 = run_test("15. Watcher Triggered Events Monitoring", f"{BASE_URL}/watchers/{watcher_id}/triggered-events")

# 16. ES|QL Pipe Query
r16 = run_test("16. ES|QL Pipe Query Engine (ES 8.11+)", f"{BASE_URL}/esql/query", method="POST", body={"query": "FROM ctsv_documents | LIMIT 5"})

# 17. ELSER Sparse Vector Search
r17 = run_test("17. ELSER v2 Sparse Vector Search", f"{BASE_URL}/elser", method="POST", body={"query": "miễn giảm học phí", "limit": 5})

# 18. OCR-Tolerant Search
r18 = run_test("18. OCR-Tolerant Fuzzy Search", f"{BASE_URL}/ocr-tolerant", method="POST", body={"query": "miên giam hoc phi", "limit": 5})

# 19. Kibana Dashboard NDJSON Export
r19 = run_test("19. Kibana Saved Objects NDJSON Export", f"{BASE_URL}/kibana/export-dashboard", is_ndjson=True)

# 20. Kibana Canvas Preview
r20 = run_test("20. Kibana Canvas Workpad Preview", f"{BASE_URL}/kibana/canvas-preview")

# 21. Sync Status (CDC Pipeline)
r21 = run_test("21. CDC Sync Pipeline (Drift Status)", f"{BASE_URL}/sync/status")

# 22. ILM Lifecycle Status
r22 = run_test("22. ILM Policy (Hot-Warm-Cold)", f"{BASE_URL}/ilm/status")

# 23. Security FLS & PII Masking Preview
r23 = run_test("23. Security FLS & PII Masking Preview", f"{BASE_URL}/security/fls-preview", method="POST")

all_tests = [
    r1, r2, r3, r4, r5, r6, r7, r8, r9, r10,
    r11, r12, r13, r14, r15, r16, r17, r18, r19, r20,
    r21, r22, r23
]

print("=" * 115)
print(f"{'STT':<4} | {'CHỨC NĂNG ELASTICSEARCH ĐO KIỂM':<45} | {'TRẠNG THÁI':<12} | {'HTTP':<6} | {'LATENCY':<10}")
print("=" * 115)

pass_count = 0
for idx, t in enumerate(all_tests, 1):
    st = t["status"]
    if st == "PASS":
        pass_count += 1
    print(f"{idx:<4} | {t['name']:<45} | {st:<12} | {t['code']:<6} | {t['ms']} ms")
    if st != "PASS":
        print(f"     => LỖI: {t.get('error')}")

print("=" * 115)
print(f"KẾT QUẢ TỔNG QUAN: {pass_count}/{len(all_tests)} CHỨC NĂNG HOẠT ĐỘNG HOÀN HẢO ({round(pass_count/len(all_tests)*100, 1)}%)")
