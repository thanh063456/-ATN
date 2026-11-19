import asyncio
import unicodedata
import re
from sqlalchemy import select
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
    "kkht": ["hoc bong khuyen khich", "kkht", "hoc bong", "688"],
    "drl": ["diem ren luyen", "drl", "ren luyen"],
    "cpa": ["diem tich luy", "cpa", "canh bao hoc vu", "gpa", "hoc luc"],
    "gpa": ["diem tich luy", "gpa", "cpa"],
    "nvqs": ["nghia vu quan su", "nvqs", "tam hoan", "13/2013/ttlt", "di linh"],
    "bhyt": ["bao hiem y te", "bhyt", "bao hiem"],
    "ktx": ["ky tuc xa", "ktx", "noi tru"],
    "blht": ["bao luu", "tam dung", "nghi hoc tam thoi", "blht"],
    "htcpht": ["ho tro chi phi hoc tap", "htcpht", "chi phi hoc tap"],
    "ctxh": ["cong tac xa hoi", "ctxh"],
    "nckh": ["nghien cuu khoa hoc", "nckh"],
}

STOPWORDS = {
    "va", "cua", "cho", "ve", "cac", "tai", "theo", "duoc", "co", "trong", "da", "la",
    "sinh", "vien", "bo", "phong", "to", "chuc", "thong", "bao", "van", "ban",
    "can", "nhung", "gi", "o", "dau", "nhu", "the", "nao", "khi", "bi", "khong",
    "gap", "nhanh", "xin", "hoi", "xem", "biet", "em", "voi", "giup", "so", "nam", "truong", "dai", "hoc"
}

ADMIN_FORM_WORDS = {"don", "xin", "de", "nghi", "phieu", "giay", "to", "ban"}

def score_doc(query: str, doc_title: str, doc_content: str):
    q_ascii = strip_accents(query)
    title_ascii = strip_accents(doc_title)
    content_ascii = strip_accents(doc_content)
    
    words = [w for w in q_ascii.split() if w]
    
    # Check expansions
    expansions = []
    for w in words:
        if w in CTSV_ACRONYMS:
            expansions.extend(CTSV_ACRONYMS[w])
    if q_ascii in CTSV_ACRONYMS:
        expansions.extend(CTSV_ACRONYMS[q_ascii])
    expansions = list(set(expansions))
    
    # Core intent words (exclude generic stopwords)
    core_words = [w for w in words if w not in STOPWORDS]
    # Distinguish administrative form words vs topic words
    topic_words = [w for w in core_words if w not in ADMIN_FORM_WORDS]
    
    # Requirement: If topic words exist, at least one topic word (or its expansion) MUST appear in title or content!
    # Otherwise, it's irrelevant filler (e.g. searching 'tạm dừng' matching 'đơn xin xét học bổng' because of 'đơn xin')
    has_topic_match = False
    
    score = 0.0
    
    # 1. Exact phrase match in title
    if q_ascii in title_ascii:
        score += 100.0
        has_topic_match = True
    elif q_ascii in content_ascii:
        score += 40.0
        has_topic_match = True
        
    # 2. Expansions match
    for exp in expansions:
        if exp in title_ascii:
            score += 80.0
            has_topic_match = True
        elif exp in content_ascii:
            score += 35.0
            has_topic_match = True
            
    # 3. Topic words match
    if topic_words:
        matched_topics_title = [w for w in topic_words if re.search(r'(?:\b|^)' + re.escape(w) + r'(?:\b|$)', title_ascii)]
        matched_topics_content = [w for w in topic_words if re.search(r'(?:\b|^)' + re.escape(w) + r'(?:\b|$)', content_ascii)]
        if matched_topics_title:
            has_topic_match = True
            score += len(matched_topics_title) * 25.0
        if matched_topics_content:
            has_topic_match = True
            score += len(matched_topics_content) * 10.0
            
        # If user specified topic words but NONE matched in either title or content, and no expansion matched:
        if not has_topic_match:
            return 0.0 # Strict reject! No rambling!
    else:
        # User only searched admin form words, e.g. "don xin"
        matched_admin_title = [w for w in core_words if re.search(r'(?:\b|^)' + re.escape(w) + r'(?:\b|$)', title_ascii)]
        if matched_admin_title:
            score += len(matched_admin_title) * 15.0
            has_topic_match = True

    # 4. Bigram consecutive matches
    if len(words) >= 2:
        for i in range(len(words) - 1):
            bg = f"{words[i]} {words[i+1]}"
            if bg not in {"don xin", "de nghi", "sinh vien", "hoc tap"}:
                if bg in title_ascii:
                    score += 30.0
                elif bg in content_ascii:
                    score += 15.0

    return score if has_topic_match else 0.0

async def run_benchmark():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Document))
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
            # combine ocr text
            s = score_doc(q, d.title or "", "")
            if s > 0:
                ranked.append((s, d.title))
        ranked.sort(key=lambda x: x[0], reverse=True)
        print(f"\n==========================================")
        print(f"QUERY: '{q}' (Matched: {len(ranked)} / {len(docs)})")
        print(f"==========================================")
        for s, title in ranked:
            print(f"   [{s:5.1f}] {title}")

asyncio.run(run_benchmark())
