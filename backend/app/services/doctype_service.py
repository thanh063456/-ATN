import re
from dataclasses import dataclass, field
from rapidfuzz import fuzz

from app.core.doc_types_config import DOC_TYPES_CONFIG

@dataclass
class DocTypeResult:
    code: str
    name: str
    group: str
    subtype: str | None = None
    confidence: float = 0.0
    signals: list[str] = field(default_factory=list)
    subject: str | None = None
    issuing_unit: str | None = None
    document_number: str | None = None
    source: str = "rules"


def clean_text(text: str) -> str:
    """Loại bỏ dấu, lowercase để fuzzy match."""
    import unicodedata
    text = text.replace('Đ', 'D').replace('đ', 'd')
    text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('utf-8')
    return text.lower().strip()


class DocTypeService:
    def __init__(self):
        self.rules = DOC_TYPES_CONFIG.types
        self.types_by_code = {t.code: t for t in self.rules}
        
    def _extract_header_zone(self, text: str) -> list[str]:
        """Lấy ~30 dòng đầu tiên, loại bỏ khoảng trắng thừa."""
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        return lines[:30]

    def _extract_document_number(self, header_lines: list[str]) -> tuple[str | None, str | None]:
        """
        Tìm số hiệu văn bản. VD: "Số: 123/TB-ĐHĐL" hoặc "Số 123?TB-ĐHĐL"
        Returns (full_number, suffix)
        """
        for line in header_lines[:15]:
            # Chuẩn hóa các lỗi OCR thường gặp ở dòng số hiệu
            clean_l = line.replace('?', '-').replace('—', '-').replace('–', '-')
            match = re.search(r'(?:[sS][oốOỐôÔ0][: ]*)\s*([0-9lIoO]+(?:\.[0-9lIoO]+)?\s*[\/\-]\s*([A-Za-zĐđ]+(?:\-[A-Za-zĐđ]+)*))', clean_l)
            if match:
                full = match.group(1).replace(' ', '')
                suffix = match.group(2).replace(' ', '').upper()
                return full, suffix
        return None, None

    def _find_title_line(self, header_lines: list[str]) -> tuple[str | None, int]:
        """Tìm dòng tiêu đề viết hoa (standalone)."""
        for i, line in enumerate(header_lines):
            line_str = line.strip()
            # Title is usually UPPERCASE, 4 <= len <= 70, not starting with "Số:" / "SO:"
            is_up = line_str.isupper() or clean_text(line_str).upper() == line_str.upper()
            if is_up and 4 <= len(line_str) <= 70:
                if line_str.upper().startswith("SỐ:") or line_str.upper().startswith("SO:"):
                    continue
                cl = clean_text(line_str)
                # Ignore common header noise (kể cả TRUNG ĐẠI HỌC, UBND)
                if any(noise in cl for noise in ["cong hoa xa hoi", "doc lap tu do", "truong dai hoc", "trung dai hoc", "bo giao duc", "ubnd"]):
                    continue
                if cl.startswith("phong ") or cl.startswith("khoa ") or cl.startswith("ban ") or cl.startswith("trung tam ") or "ctsv" in cl:
                    continue
                return line_str, i
        return None, -1

    def _extract_subject(self, header_lines: list[str], title_idx: int) -> str | None:
        """Trích xuất trích yếu (V/v...)"""
        # Look for "V/v", "Về việc"
        for line in header_lines:
            match = re.search(r'(?i)(?:v/v|về việc)[:\s]*(.+)', line)
            if match:
                return match.group(1).strip()
                
        # If title is found, the subject might be the next 1-2 lines
        if title_idx != -1 and title_idx + 1 < len(header_lines):
            next_line = header_lines[title_idx + 1]
            if not next_line.isupper() and len(next_line) > 10 and not next_line.lower().startswith("kính gửi"):
                return next_line
        return None
        
    def _extract_issuing_unit(self, header_lines: list[str]) -> str | None:
        """Trích xuất đơn vị ban hành (thường ở top left)."""
        for line in header_lines[:5]:
            cl = clean_text(line)
            if "truong" in cl or "khoa" in cl or "phong" in cl or "trung tam" in cl or "ubnd" in cl:
                if "cong hoa" not in cl and "doc lap" not in cl:
                    return line
        return None

    def classify(self, first_page_text: str, page_count: int | None = None) -> DocTypeResult:
        if not first_page_text:
            return DocTypeResult(code="KHAC", name="Khác", group="KHAC", confidence=0.0, signals=["empty_text"])

        header_lines = self._extract_header_zone(first_page_text)
        signals = []
        confidence = 0.0
        predicted_code = "KHAC"
        
        # 1. Trích xuất metadata cơ bản
        doc_no, suffix = self._extract_document_number(header_lines)
        title_line, title_idx = self._find_title_line(header_lines)
        subject = self._extract_subject(header_lines, title_idx)
        issuing_unit = self._extract_issuing_unit(header_lines)
        
        header_text_clean = clean_text("\n".join(header_lines))
        
        if doc_no:
            signals.append(f"doc_no_suffix:{suffix}")
            
        if title_line:
            signals.append(f"title_line:{title_line}")

        # 2. Rules scoring
        scores = {t.code: 0.0 for t in self.rules}
        
        for t in self.rules:
            # Suffix match
            if suffix and t.so_hieu_patterns:
                for p in t.so_hieu_patterns:
                    clean_p = p.strip('-').upper()
                    if suffix == clean_p or suffix.startswith(clean_p) or suffix.endswith(clean_p):
                        scores[t.code] += 0.6
                        signals.append(f"matched_suffix:{t.code}")
                        break
            
            # Title match (substring + fuzzy)
            if title_line and t.title_patterns:
                cl_title = clean_text(title_line)
                title_words = set(cl_title.split())
                for p in t.title_patterns:
                    if " " not in p:
                        if p in title_words:
                            scores[t.code] += 0.8
                            signals.append(f"matched_title:{t.code}")
                            break
                    else:
                        if p in cl_title or fuzz.partial_ratio(p, cl_title) >= 85:
                            scores[t.code] += 0.8
                            signals.append(f"matched_title:{t.code}")
                            break
                        
            # Body hints (weak signals)
            if t.body_hints:
                for hint in t.body_hints:
                    if hint in header_text_clean:
                        scores[t.code] += 0.15
                        
        # 3. Special rule: CÔNG VĂN
        # If has "Kính gửi", "v/v", and NO strong uppercase title
        has_kinh_gui = "kinh gui" in header_text_clean
        has_vv = "v/v" in header_text_clean or "ve viec" in header_text_clean
        if has_kinh_gui and has_vv and not title_line:
            scores["CONG_VAN"] += 0.7
            signals.append("rule:cong_van_kinhgui_vv")
            
        # 4. Special rule: ĐƠN TỪ
        has_don = any(k in header_text_clean for k in ["don xin", "don de nghi", "giay de nghi", "don de dat"])
        has_identity = any(k in header_text_clean for k in ["em ten la", "ten em la", "ho va ten", "sinh vien:", "mssv"])
        if has_kinh_gui and has_don:
            scores["DON_TU"] += 0.8
            signals.append("rule:don_tu_structure")
        elif has_don and has_identity:
            scores["DON_TU"] += 0.75
            signals.append("rule:don_tu_identity")
            
        # 5. Special rule: DANH SÁCH
        if "danh sach" in header_text_clean and any(k in header_text_clean for k in ["stt", "mssv", "ma sinh vien", "ho va ten", "ho ten"]):
            scores["DANH_SACH"] += 0.8
            signals.append("rule:danh_sach_table")
                
        # Determine best
        best_code = max(scores, key=scores.get)
        best_score = scores[best_code]
        
        if best_score >= 0.55:
            predicted_code = best_code
            confidence = min(0.95, best_score)
        else:
            predicted_code = "KHAC"
            confidence = best_score
            signals.append("low_confidence_fallback")
            
        # Subtype matching for DON_TU
        subtype = None
        if predicted_code == "DON_TU":
            dt_rule = self.types_by_code["DON_TU"]
            if dt_rule.subtypes:
                for st in dt_rule.subtypes:
                    for kw in st.keywords:
                        if kw in header_text_clean:
                            subtype = st.code
                            signals.append(f"subtype_matched:{st.code}")
                            break
                    if subtype:
                        break
                        
        t_info = self.types_by_code[predicted_code]
        
        return DocTypeResult(
            code=predicted_code,
            name=t_info.name,
            group=t_info.group,
            subtype=subtype,
            confidence=round(confidence, 2),
            signals=signals,
            subject=subject,
            issuing_unit=issuing_unit,
            document_number=doc_no,
            source="rules"
        )

doctype_service = DocTypeService()
