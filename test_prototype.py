import sys, asyncio, re
sys.path.insert(0, 'E:/Download/-ATN-main/-ATN-main/backend')
from app.core.database import AsyncSessionLocal
from app.models.documents import Document
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.routers.search import _strip_accents
from app.services.ctsv_faq_service import resolve_acronyms_and_slang
from app.services.embedding_service import embedding_service

# Define domains and required terms
DOMAIN_MAP = {
    "NVQS": {
        "intents": ["nvqs", "nghia vu quan su", "tam hoan nvqs", "di linh", "quan su"],
        "terms": ["nghia vu quan su", "nvqs", "tam hoan nvqs", "13/2013", "di linh", "quan su", "ban chi huy quan su"],
    },
    "MGHP": {
        "intents": ["mghp", "mien giam hoc phi", "81/2021", "nghi dinh 81"],
        "terms": ["mien giam hoc phi", "mghp", "nghi dinh 81", "81/2021", "giam hoc phi", "mien hoc phi", "hoc phi"],
    },
    "KKHT": {
        "intents": ["kkht", "hoc bong khuyen khich", "688", "quyet dinh 688"],
        "terms": ["hoc bong khuyen khich", "kkht", "khuyen khich hoc tap", "quyet dinh 688", "688/qd", "hoc bong k1", "1413/tb"],
    },
    "DRL": {
        "intents": ["drl", "diem ren luyen", "88/hd", "huong dan 88", "ren luyen"],
        "terms": ["diem ren luyen", "drl", "ren luyen", "88/hd", "huong dan 88"],
    },
    "KTX": {
        "intents": ["ktx", "ky tuc xa", "noi tru"],
        "terms": ["ky tuc xa", "ktx", "noi tru", "cho o", "315/qd"],
    },
    "BHYT": {
        "intents": ["bhyt", "bao hiem y te", "55/tb"],
        "terms": ["bao hiem y te", "bhyt", "bao hiem than the", "55/tb", "thong bao 55"],
    },
    "BLHT": {
        "intents": ["blht", "tam dung", "bao luu", "nghi hoc", "nghi hoc tam thoi", "nghi hoc co thoi han"],
        "terms": ["bao luu", "tam dung", "nghi hoc co thoi han", "nghi hoc tam thoi", "blht", "tam hoan va bao luu"],
    },
    "HTCPHT": {
        "intents": ["htcpht", "ho tro chi phi hoc tap", "ho tro chi phi"],
        "terms": ["ho tro chi phi hoc tap", "htcpht", "chi phi hoc tap"],
    },
    "VAY_VON": {
        "intents": ["vay von", "ngan hang chinh sach", "205/hd"],
        "terms": ["vay von", "ngan hang chinh sach", "205/hd", "giay xac nhan"],
    },
    "CPA": {
        "intents": ["cpa", "gpa", "tich luy", "canh bao hoc vu"],
        "terms": ["gpa", "cpa", "diem tich luy", "canh bao hoc vu", "hoc luc"],
    },
    "NCKH": {
        "intents": ["nckh", "nghien cuu khoa hoc", "890/qd", "890"],
        "terms": ["nghien cuu khoa hoc", "nckh", "890/qd", "890"],
    }
}

def detect_domain(q_ascii: str) -> str | None:
    # First priority: check NVQS if military words exist
    if any(k in q_ascii for k in ["nvqs", "nghia vu quan su", "di linh", "hoan nvqs", "quan su"]):
        return "NVQS"
    for dom, data in DOMAIN_MAP.items():
        if dom == "NVQS":
            continue
        if any(k in q_ascii for k in data["intents"]):
            return dom
    return None

async def test():
    test_queries = [
        "mghp", "kkht", "nvqs", "drl", "cpa", "ktx", "bhyt", "blht", "htcpht",
        "mien giam hoc phi", "hoc bong khuyen khich", "diem ren luyen", "tam hoan nghia vu quan su",
        "ky tuc xa", "bao hiem y te", "don xin tam dung hoc tap", "vay von",
        "xin mghp", "xet kkht", "hoan nvqs", "cham drl", "o ktx", "mua bhyt", "xin blht"
    ]

    async with AsyncSessionLocal() as db:
        res = await db.execute(
            select(Document)
            .options(
                selectinload(Document.category),
                selectinload(Document.metadata_),
                selectinload(Document.ocr_results),
            )
            .where(Document.is_deleted == False)
        )
        docs = res.scalars().all()

        print(f"{'QUERY':<25} | {'DOMAIN':<8} | {'TOP RESULT':<50}")
        print("-" * 90)
        for q in test_queries:
            q_res, _ = resolve_acronyms_and_slang(q)
            q_ascii = _strip_accents(q)
            dom = detect_domain(q_ascii)
            
            scored = []
            for d in docs:
                ocr_body = ""
                if d.ocr_results:
                    for ocr in d.ocr_results:
                        if getattr(ocr, "is_latest", False):
                            ocr_body = ocr.corrected_text or ocr.raw_text or ""
                            break
                    if not ocr_body and d.ocr_results:
                        ocr_body = d.ocr_results[0].corrected_text or d.ocr_results[0].raw_text or ""
                
                title_ascii = _strip_accents(d.title or "")
                ocr_ascii = _strip_accents(ocr_body)
                
                score = 0.0
                if dom:
                    dom_terms = DOMAIN_MAP[dom]["terms"]
                    has_dom_title = any(t in title_ascii for t in dom_terms)
                    has_dom_ocr = any(t in ocr_ascii for t in dom_terms)
                    if not (has_dom_title or has_dom_ocr):
                        continue # Strict domain filtering!
                    if has_dom_title:
                        score += 200.0
                    if has_dom_ocr:
                        score += 100.0
                
                # phrase check
                if q_ascii in title_ascii:
                    score += 150.0
                elif q_ascii in ocr_ascii:
                    score += 80.0
                
                if score > 0:
                    scored.append((score, d))
            
            scored.sort(key=lambda x: x[0], reverse=True)
            top_title = scored[0][1].title[:48] if scored else "NO MATCH"
            print(f"{q:<25} | {str(dom):<8} | {top_title:<50}")

asyncio.run(test())
