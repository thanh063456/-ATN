import asyncio, sys
sys.path.insert(0, 'E:/Download/-ATN-main/-ATN-main/backend')
from app.core.database import AsyncSessionLocal
from app.models.documents import Document
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.routers.search import _strip_accents

async def check():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Document).options(selectinload(Document.ocr_results)).where(Document.title.contains("Lê Văn Bình")))
        doc = res.scalar_one_or_none()
        if doc:
            print("Title:", doc.title)
            for ocr in doc.ocr_results:
                txt = ocr.corrected_text or ocr.raw_text or ""
                print("OCR snippet:", txt[:400])
                for term in ["nghia vu quan su", "nvqs", "tam hoan nvqs", "13/2013/ttlt", "di linh", "quan su"]:
                    if term in _strip_accents(txt):
                        print(f"MATCHED TERM: '{term}' in OCR text!")

asyncio.run(check())
