import asyncio
import unicodedata
import re
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.core.database import AsyncSessionLocal
from app.models.documents import Document

def strip_accents(text: str) -> str:
    if not text:
        return ""
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return text.replace("đ", "d").replace("Đ", "D").lower().strip()

CTSV_ACRONYMS = {
    "mghp": ["mien giam hoc phi", "mghp", "nghi dinh 81"],
    "kkht": ["hoc bong khuyen khich", "kkht", "khuyen khich hoc tap", "quyet dinh 688", "688"],
    "drl": ["diem ren luyen", "drl", "ren luyen", "88/hd"],
    "cpa": ["gpa", "cpa", "diem tich luy", "canh bao hoc vu", "hoc luc"],
    "gpa": ["gpa", "cpa", "diem tich luy"],
    "nvqs": ["nghia vu quan su", "nvqs", "tam hoan nvqs", "13/2013/ttlt", "di linh", "quan su"],
    "bhyt": ["bao hiem y te", "bhyt", "bao hiem than the", "55/tb"],
    "ktx": ["ky tuc xa", "ktx", "noi tru"],
    "blht": ["bao luu", "tam dung", "nghi hoc tam thoi", "blht", "nghi hoc co thoi han"],
    "htcpht": ["ho tro chi phi hoc tap", "htcpht", "chi phi hoc tap"],
    "ctxh": ["cong tac xa hoi", "ctxh"],
    "nckh": ["nghien cuu khoa hoc", "nckh", "890/qd"],
}

# Administrative form prefixes that should NOT alone trigger a match
ADMIN_FORM_PREFIXES = {
    "don", "xin", "de", "nghi", "phieu", "giay", "to", "ban", "so", "thong", "bao", "quyet", "dinh", "bao", "cao", "ke", "hoach", "huong", "dan", "danh", "sach", "quy", "dinh", "quy", "che"
}

GENERIC_FILLERS = {
    "va", "cua", "cho", "ve", "cac", "tai", "theo", "duoc", "co", "trong", "da", "la",
    "sinh", "vien", "bo", "phong", "to", "chuc", "truong", "dai", "hoc", "nam", "thang", "ngay",
    "can", "nhung", "gi", "o", "dau", "nhu", "the", "nao", "khi", "bi", "khong",
    "gap", "nhanh", "hoi", "xem", "biet", "em", "voi", "giup", "tap"
}

# Domain semantic aliases (concept mapping)
CONCEPT_MAP = {
    "tam dung": ["tam hoan", "bao luu", "nghi hoc co thoi han", "nghi hoc tam thoi"],
    "bao luu": ["tam hoan", "tam dung", "nghi hoc"],
    "nghi hoc": ["tam dung", "bao luu", "nghi hoc co thoi han"],
    "ky tuc xa": ["ktx", "cho o gia re", "noi tru"],
    "ho tro chi phi": ["ho tro chi phi hoc tap", "htcpht"],
    "hoc bong khuyen khich": ["kkht", "hoc bong k1", "hoc bong ky 1"],
    "vay von": ["ngan hang chinh sach", "giay xac nhan"],
    "nghia vu quan su": ["nvqs", "hoan di linh", "tam hoan"],
}

def precise_score(query: str, title: str, content: str):
    q_ascii = strip_accents(query)
    title_ascii = strip_accents(title)
    content_ascii = strip_accents(content)
    full_text_ascii = f"{title_ascii} {content_ascii}"

    tokens = [w for w in q_ascii.split() if w]
    
    # 1. Check exact phrase match in title (Highest priority!)
    if q_ascii in title_ascii:
        return 200.0 + (len(q_ascii) * 2.0)

    # 2. Extract acronym expansions
    expansions = []
    for t in tokens:
        if t in CTSV_ACRONYMS:
            expansions.extend(CTSV_ACRONYMS[t])
    if q_ascii in CTSV_ACRONYMS:
        expansions.extend(CTSV_ACRONYMS[q_ascii])
        
    for k, synonyms in CONCEPT_MAP.items():
        if k in q_ascii:
            expansions.extend(synonyms)
            
    expansions = list(set(expansions))

    # Match expansions against title and content
    expansion_score = 0.0
    for exp in expansions:
        if exp in title_ascii:
            expansion_score = max(expansion_score, 150.0)
        elif exp in content_ascii:
            expansion_score = max(expansion_score, 70.0)

    # 3. Identify content-bearing topic tokens
    topic_tokens = [t for t in tokens if t not in GENERIC_FILLERS and t not in ADMIN_FORM_PREFIXES]
    
    # Check multi-word concept phrases (e.g., "tam dung", "hoc phi", "ky tuc", "ren luyen", "quan su")
    bigrams = [f"{tokens[i]} {tokens[i+1]}" for i in range(len(tokens)-1)] if len(tokens) >= 2 else []
    content_bigrams = [bg for bg in bigrams if not all(w in GENERIC_FILLERS or w in ADMIN_FORM_PREFIXES for w in bg.split())]

    # Calculate token match
    matched_topics_title = [t for t in topic_tokens if re.search(r'(?:\b|^)' + re.escape(t) + r'(?:\b|$)', title_ascii)]
    matched_topics_content = [t for t in topic_tokens if re.search(r'(?:\b|^)' + re.escape(t) + r'(?:\b|$)', content_ascii)]
    matched_bigrams_title = [bg for bg in content_bigrams if bg in title_ascii]
    matched_bigrams_content = [bg for bg in content_bigrams if bg in content_ascii]

    # Strict Relevance Filter:
    # If the user query has topic tokens or bigrams:
    # A document is ONLY relevant if it matches the expansion, OR a content bigram, OR all/majority topic tokens!
    if expansion_score > 0:
        return expansion_score + (len(matched_topics_title) * 15.0)

    if content_bigrams:
        if matched_bigrams_title:
            return 120.0 + (len(matched_bigrams_title) * 30.0)
        if matched_bigrams_content:
            return 60.0 + (len(matched_bigrams_content) * 20.0)

    if topic_tokens:
        if len(topic_tokens) == 1:
            if matched_topics_title:
                return 90.0
            if matched_topics_content:
                return 40.0
            return 0.0 # Strict reject!
        else:
            # Multi-word topic: Must match at least 2 topic words or all topic words
            if len(matched_topics_title) >= len(topic_tokens):
                return 110.0 + (len(matched_topics_title) * 10.0)
            if len(matched_topics_title) >= 1 and len(matched_topics_content) >= len(topic_tokens) - 1:
                return 70.0
            if len(matched_topics_content) >= len(topic_tokens):
                return 50.0
            return 0.0 # Reject rambling partial matches!

    # Only administrative form words searched (e.g. "don xin", "thong bao")
    form_tokens = [t for t in tokens if t in ADMIN_FORM_PREFIXES]
    if form_tokens:
        matched_form = [t for t in form_tokens if re.search(r'(?:\b|^)' + re.escape(t) + r'(?:\b|$)', title_ascii)]
        if matched_form:
            return 30.0 + (len(matched_form) * 5.0)

    return 0.0

async def verify():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Document).options(selectinload(Document.ocr_results)))
        docs = res.scalars().all()

    test_queries = [
        "mghp",
        "kkht",
        "nvqs",
        "drl",
        "cpa",
        "don xin tam dung hoc tap",
        "mien giam hoc phi",
        "tam hoan nvqs",
        "ho so ho tro chi phi hoc tap",
        "ky tuc xa"
    ]

    for q in test_queries:
        ranked = []
        for d in docs:
            txt = ""
            for o in d.ocr_results:
                txt += (o.corrected_text or o.raw_text or "") + " "
            s = precise_score(q, d.title or "", txt)
            if s > 0:
                ranked.append((s, d.title))
        ranked.sort(key=lambda x: x[0], reverse=True)
        print(f"\nQUERY: '{q}' -> {len(ranked)} kết quả:")
        for s, title in ranked:
            print(f"   [{s:5.1f}] {title}")

asyncio.run(verify())
