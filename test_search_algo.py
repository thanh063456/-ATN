import re
import unicodedata

def strip_accents(text: str) -> str:
    if not text:
        return ""
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return text.replace("đ", "d").replace("Đ", "D").lower().strip()

CTSV_ACRONYMS = {
    "mghp": ["mien giam hoc phi", "mghp", "nghi dinh 81"],
    "kkht": ["hoc bong khuyen khich", "kkht", "hoc bong", "688"],
    "drl": ["diem ren luyen", "drl"],
    "cpa": ["diem tich luy", "cpa", "canh bao hoc vu", "gpa"],
    "gpa": ["diem tich luy", "gpa", "cpa"],
    "nvqs": ["nghia vu quan su", "nvqs", "tam hoan nvqs", "13/2013/ttlt", "di linh"],
    "bhyt": ["bao hiem y te", "bhyt"],
    "ktx": ["ky tuc xa", "ktx", "noi tru"],
    "blht": ["bao luu", "tam dung", "nghi hoc tam thoi", "blht"],
    "htcpht": ["ho tro chi phi hoc tap", "htcpht", "chi phi hoc tap"],
    "ctxh": ["cong tac xa hoi", "ctxh"],
    "nckh": ["nghien cuu khoa hoc", "nckh"],
}

ADMIN_PREFIXES = {
    "don", "xin", "don xin", "de nghi", "don de nghi", "phieu", "phieu de nghi",
    "giay", "giay xac nhan", "giay chung nhan", "quyet dinh", "thong bao",
    "bao cao", "ke hoach", "huong dan", "bien ban", "danh sach", "quy dinh", "quy che"
}

STOPWORDS = {
    "va", "cua", "cho", "ve", "cac", "tai", "theo", "duoc", "co", "trong", "da", "la",
    "sinh", "vien", "bo", "phong", "to", "chuc", "thong", "bao", "van", "ban", "ve",
    "can", "nhung", "gi", "o", "dau", "la", "nhu", "the", "nao", "khi", "bi", "khong",
    "gap", "nhanh", "xin", "hoi", "xem", "biet", "em", "voi", "giup", "so"
}

def analyze_query(query: str):
    q_clean = query.strip().lower()
    q_ascii = strip_accents(q_clean)
    words = [w for w in q_ascii.split() if w]
    
    # 1. Expand acronyms
    expanded_terms = []
    detected_topic = None
    for w in words:
        if w in CTSV_ACRONYMS:
            expanded_terms.extend(CTSV_ACRONYMS[w])
            detected_topic = w
    if q_ascii in CTSV_ACRONYMS:
        expanded_terms.extend(CTSV_ACRONYMS[q_ascii])
        detected_topic = q_ascii
        
    # 2. Extract core topic words (exclude stopwords and standalone admin prefixes if more specific words exist)
    topic_words = [w for w in words if w not in STOPWORDS]
    
    # Identify non-prefix words if possible
    content_words = [w for w in topic_words if w not in {"don", "xin", "de", "nghi", "phieu", "giay"}]
    if content_words:
        must_match_words = content_words
    else:
        must_match_words = topic_words
        
    return {
        "raw": query,
        "ascii": q_ascii,
        "words": words,
        "expanded_terms": list(set(expanded_terms)),
        "must_match_words": must_match_words,
        "detected_topic": detected_topic
    }

print("Query analysis prototype loaded.")
