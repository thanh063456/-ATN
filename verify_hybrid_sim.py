import sys, asyncio, re
sys.path.insert(0, 'E:/Download/-ATN-main/-ATN-main/backend')
from app.core.database import AsyncSessionLocal
from app.models.documents import Document
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.routers.search import _strip_accents
from app.services.ctsv_faq_service import resolve_acronyms_and_slang
from app.services.embedding_service import embedding_service

DOMAIN_MAP = {
    "NVQS": {
        "intents": ["nvqs", "nghia vu quan su", "tam hoan nvqs", "di linh", "quan su", "hoan nvqs"],
        "terms": ["nghia vu quan su", "nvqs", "tam hoan nvqs", "13/2013", "di linh", "quan su", "ban chi huy quan su"],
    },
    "MGHP": {
        "intents": ["mghp", "mien giam hoc phi", "81/2021", "nghi dinh 81", "xin mghp"],
        "terms": ["mien giam hoc phi", "mghp", "nghi dinh 81", "81/2021", "giam hoc phi", "mien hoc phi", "chinh sach"],
    },
    "KKHT": {
        "intents": ["kkht", "hoc bong khuyen khich", "688", "quyet dinh 688", "xet kkht"],
        "terms": ["hoc bong khuyen khich", "kkht", "khuyen khich hoc tap", "quyet dinh 688", "688/qd", "hoc bong k1", "1413/tb"],
    },
    "DRL": {
        "intents": ["drl", "diem ren luyen", "88/hd", "huong dan 88", "cham drl", "ren luyen"],
        "terms": ["diem ren luyen", "drl", "ren luyen", "88/hd", "huong dan 88"],
    },
    "KTX": {
        "intents": ["ktx", "ky tuc xa", "noi tru", "o ktx"],
        "terms": ["ky tuc xa", "ktx", "noi tru", "cho o", "315/qd"],
    },
    "BHYT": {
        "intents": ["bhyt", "bao hiem y te", "55/tb", "mua bhyt"],
        "terms": ["bao hiem y te", "bhyt", "bao hiem than the", "55/tb", "thong bao 55"],
    },
    "BLHT": {
        "intents": ["blht", "tam dung", "bao luu", "nghi hoc", "xin blht", "nghi hoc tam thoi", "nghi hoc co thoi han"],
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
    if any(k in q_ascii for k in ["nvqs", "nghia vu quan su", "di linh", "hoan nvqs", "quan su"]):
        return "NVQS"
    for dom, data in DOMAIN_MAP.items():
        if dom == "NVQS":
            continue
        if any(k in q_ascii for k in data["intents"]):
            return dom
    return None

async def verify_hybrid_simulation():
    k_const = 20
    queries = [
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
        all_docs = res.scalars().all()

        print(f"{'QUERY':<25} | {'DOMAIN':<7} | {'BM25 TOP MATCH':<40} | {'RRF TOP MATCH':<40}")
        print("=" * 120)

        for q in queries:
            resolved_q, _ = resolve_acronyms_and_slang(q)
            q_ascii = _strip_accents(q)
            dom = detect_domain(q_ascii)
            q_vec = await embedding_service.get_embedding(resolved_q)

            bm25_scored = []
            knn_scored = []

            for d in all_docs:
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
                st_info = f"{d.metadata_.student_name or ''} {d.metadata_.student_id or ''}" if d.metadata_ else ""
                d_text = f"{title_ascii} {ocr_ascii} {_strip_accents(st_info)}"

                lex_score = 0.0

                if dom:
                    dom_terms = DOMAIN_MAP[dom]["terms"]
                    has_dom_title = any(t in title_ascii for t in dom_terms)
                    has_dom_ocr = any(t in ocr_ascii for t in dom_terms)
                    if not (has_dom_title or has_dom_ocr):
                        continue
                    if has_dom_title:
                        lex_score += 150.0
                    if has_dom_ocr:
                        lex_score += 80.0

                if q_ascii in title_ascii:
                    lex_score += 100.0
                elif q_ascii in ocr_ascii:
                    lex_score += 50.0

                if lex_score > 0:
                    bm25_scored.append((lex_score, d))

                d_vec = embedding_service._generate_local_vector((d.title or "") + " " + ocr_body[:300])
                dot_product = sum(a * b for a, b in zip(q_vec, d_vec))
                
                # Strict vector filtering: if domain is detected, document MUST belong to that domain!
                if dom:
                    if lex_score > 0 and dot_product > 0.0:
                        knn_scored.append((dot_product, d))
                else:
                    if dot_product > 0.30:
                        knn_scored.append((dot_product, d))

            bm25_sorted = sorted(bm25_scored, key=lambda x: x[0], reverse=True)
            knn_sorted = sorted(knn_scored, key=lambda x: x[0], reverse=True)

            bm25_ranks = {doc.id: (rank, score) for rank, (score, doc) in enumerate(bm25_sorted, 1)}
            knn_ranks = {doc.id: (rank, score) for rank, (score, doc) in enumerate(knn_sorted, 1)}

            all_matched_ids = set(bm25_ranks.keys()).union(set(knn_ranks.keys()))
            if not all_matched_ids:
                print(f"{q:<25} | {str(dom):<7} | {'NO MATCH':<40} | {'NO MATCH':<40}")
                continue

            doc_map = {d.id: d for d in all_docs}
            rrf_scored = []
            for did in all_matched_ids:
                score_rrf = 0.0
                if did in bm25_ranks:
                    r_bm, _ = bm25_ranks[did]
                    score_rrf += 1.0 / (k_const + r_bm)
                if did in knn_ranks:
                    r_knn, _ = knn_ranks[did]
                    score_rrf += 1.0 / (k_const + r_knn)
                rrf_scored.append((score_rrf, did))

            rrf_sorted = sorted(rrf_scored, key=lambda x: x[0], reverse=True)
            top_bm25_doc = bm25_sorted[0][1].title[:38] if bm25_sorted else "NONE"
            top_rrf_doc = doc_map[rrf_sorted[0][1]].title[:38] if rrf_sorted else "NONE"
            print(f"{q:<25} | {str(dom):<7} | {top_bm25_doc:<40} | {top_rrf_doc:<40}")

asyncio.run(verify_hybrid_simulation())
