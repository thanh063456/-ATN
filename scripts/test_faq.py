import urllib.request
import urllib.parse
import json

questions = [
    "Làm thế nào để xin nghỉ học tạm thời 1 năm?",
    "Học bổng tài trợ của doanh nghiệp cần điều kiện gì?",
    "Thời tiết hôm nay ở Đà Lạt thế nào có đi chơi được không?",
    "Bị điểm F môn thể dục có được xét học bổng không?",
    "Sinh viên nghèo có được miễn giảm học phí không?",
    "Bị mất thẻ sinh viên thì làm lại ở đâu?",
    "Làm sao để xin hoãn nghĩa vụ quân sự?",
    "Chào bạn, bạn là ai?",
]

for q in questions:
    url = "http://127.0.0.1:8000/api/v1/search/faq/ask?q=" + urllib.parse.quote(q)
    try:
        req = urllib.request.urlopen(url)
        data = json.loads(req.read().decode())
        print(f"=== Q: {q} ===")
        print(f"Matched: {data.get('matched_article')}")
        print(f"Answer: {data.get('summary_answer')}")
        print(f"Confidence: {data.get('confidence_score')}")
        print(f"Forms: {[f.get('form_code') for f in data.get('required_forms', [])]}\n")
    except Exception as e:
        print(f"Error for {q}: {e}")
