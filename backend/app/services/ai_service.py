"""
backend/app/services/ai_service.py — AI Enhancement & Smart Entity Extraction Service

Hỗ trợ xử lý thông minh kết hợp:
1. Sửa lỗi chính tả ngữ cảnh & chuẩn hóa văn bản OCR (AI Spellcheck & Refinement)
2. Bóc tách thực thể nâng cao (Smart Fields Extraction: MSSV, Họ tên, Lớp, Khoa, Lý do, Số tiền, Loại đơn, Tóm tắt AI)
3. Hỗ trợ đa nền tảng:
   - Google Gemini API (gemini-1.5-flash / gemini-2.0-flash)
   - OpenAI API (gpt-4o-mini / gpt-4o)
   - Ollama (Local offline models: qwen2.5, llama3.2, phocto)
   - Fallback Rule-based / Regex khi offline hoặc không cấu hình API Key.
"""
import json
import re
from datetime import datetime
from typing import Any

import httpx
from loguru import logger

from app.core.config import settings
from app.services.extraction_service import extraction_service
from app.services.text_postprocessing import post_process_vietnamese


class AIService:
    """Service tích hợp AI hỗ trợ nhận diện và bóc tách dữ liệu thông minh."""

    def __init__(self) -> None:
        self.timeout = httpx.Timeout(settings.ai_timeout_seconds, connect=10.0)

    def _determine_provider(self) -> str:
        """Xác định provider khả dụng dựa trên cấu hình."""
        cfg_provider = settings.ai_provider.lower()
        if cfg_provider != "auto":
            return cfg_provider

        if settings.gemini_api_key:
            return "gemini"
        if settings.openai_api_key:
            return "openai"
        return "ollama"

    async def _refine_single_chunk(self, chunk: str, provider: str) -> str | None:
        """Hiệu đính 1 đoạn hoặc 1 trang văn bản qua LLM provider, bảo vệ cấu trúc header 2 cột."""
        if not chunk.strip():
            return chunk

        # Tách Header 2 cột hành chính (nếu có) để AI không làm xáo trộn bố cục 2 cột Nghị định 30
        header_prefix = ""
        body_to_refine = chunk
        
        # Nhận diện nếu chunk chứa tiêu đề chính: KẾ HOẠCH, QUYẾT ĐỊNH, THÔNG BÁO, TỜ TRÌNH, ĐƠN XIN...
        title_m = re.search(r'(?m)^\s*(KẾ\s+HOẠCH|QUYẾT\s+ĐỊNH|THÔNG\s+BÁO|TỜ\s+TRÌNH|CÔNG\s+VĂN|HƯỚNG\s+DẪN|BIÊN\s+BẢN|BÁO\s+CÁO|ĐƠN\s+XIN)\b', chunk, re.IGNORECASE)
        if title_m and title_m.start() > 0:
            header_prefix = chunk[:title_m.start()]
            body_to_refine = chunk[title_m.start():]
        elif any(kw in chunk.upper() for kw in ["CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM", "BỘ GIÁO DỤC VÀ ĐÀO TẠO", "TRƯỜNG ĐẠI HỌC ĐÀ LẠT"]):
            lines = chunk.splitlines(keepends=True)
            h_lines = []
            b_lines = []
            in_header = True
            for l in lines:
                if in_header and (any(kw in l.upper() for kw in ["CỘNG HÒA", "ĐỘC LẬP", "BỘ GIÁO DỤC", "ĐẠI HỌC ĐÀ LẠT", "SỐ:", "NGÀY"]) or not l.strip()):
                    h_lines.append(l)
                else:
                    in_header = False
                    b_lines.append(l)
            if h_lines:
                header_prefix = "".join(h_lines)
                body_to_refine = "".join(b_lines)

        prompt = (
            "Bạn là trợ lý ngôn ngữ tiếng Việt chuyên nghiệp hiệu đính văn bản hành chính công tác sinh viên Đại học Đà Lạt.\n"
            "Dưới đây là phần nội dung văn bản trích xuất từ mô hình OCR quét tài liệu (có thể có lỗi nhận dạng dấu hoặc chữ cái, nhầm số/ký tự).\n"
            "Nhiệm vụ của bạn:\n"
            "1. Sửa triệt để các lỗi chính tả, phục hồi đúng dấu câu tiếng Việt chuẩn xác.\n"
            "   - Sửa các lỗi OCR phổ biến: '6 ất công dân' hoặc 'công dân?' sửa thành 'công dân - HSSV'; 'L MỤC ĐÍCH' sửa thành 'I. MỤC ĐÍCH'.\n"
            "   - Chuẩn hóa tên chương trình: 'Tuần sinh hoạt công dân - HSSV' đầu khóa dành cho Tân sinh viên khóa 49, năm học 2025-2026.\n"
            "2. Giữ nguyên 100% các dữ liệu thực tế quan trọng: Mã số sinh viên, số tiền, ngày tháng năm, tên riêng người và trường.\n"
            "3. Giữ nguyên cấu trúc các đề mục (KẾ HOẠCH, I., II., 1.1., a., b., c.).\n"
            "4. CHỈ TRẢ VỀ DUY NHẤT VĂN BẢN ĐÃ ĐƯỢC HIỆU ĐÍNH, KHÔNG KÈM LỜI DẪN, KHÔNG GIẢI THÍCH.\n\n"
            f"--- NỘI DUNG OCR ---\n{body_to_refine}\n--- HẾT ---"
        )

        refined = None
        if provider == "gemini" and settings.gemini_api_key:
            refined = await self._call_gemini(prompt)
        elif provider == "openai" and settings.openai_api_key:
            refined = await self._call_openai(prompt)
        elif provider == "ollama":
            refined = await self._call_ollama(prompt)

        if refined and len(refined) > len(body_to_refine) * 0.3:
            final_text = header_prefix + refined
            return post_process_vietnamese(final_text)

        return None

    async def refine_ocr_text(self, raw_text: str) -> dict[str, Any]:
        """
        Dùng AI hậu xử lý, sửa các lỗi chính tả OCR tiếng Việt nhưng giữ nguyên cấu trúc văn bản hành chính.
        Nếu văn bản nhiều trang, tự động chia theo từng trang để tránh nghẽn/timeout LLM.
        """
        if not raw_text or not raw_text.strip():
            return {
                "original_text": raw_text,
                "refined_text": raw_text,
                "provider": "none",
                "model": "none",
                "success": False,
                "message": "Văn bản rỗng",
            }

        provider = self._determine_provider()
        used_model = getattr(settings, f"{provider}_model", provider)

        # Xử lý theo từng trang nếu có đánh dấu "--- Trang X ---"
        page_splits = re.split(r'(\n*---\s*Trang\s+\d+[^-\n]*---\n*)', raw_text)
        if len(page_splits) > 2:
            refined_parts = []
            any_llm_success = False
            for part in page_splits:
                if re.match(r'^\n*---\s*Trang\s+\d+[^-\n]*---\n*$', part):
                    refined_parts.append(part)
                elif part.strip():
                    try:
                        p_res = await self._refine_single_chunk(part, provider)
                        if p_res and len(p_res) > len(part) * 0.3:
                            refined_parts.append(p_res)
                            any_llm_success = True
                        else:
                            refined_parts.append(post_process_vietnamese(part))
                    except Exception as pe:
                        logger.warning("Trang con refinement lỗi ({err}), fallback từ điển", err=str(pe))
                        refined_parts.append(post_process_vietnamese(part))
                else:
                    refined_parts.append(part)

            if any_llm_success:
                return {
                    "original_text": raw_text,
                    "refined_text": "".join(refined_parts),
                    "provider": provider,
                    "model": used_model,
                    "success": True,
                }

        # Văn bản đơn trang hoặc không có dấu trang
        try:
            refined = await self._refine_single_chunk(raw_text, provider)
            if refined and len(refined) > len(raw_text) * 0.3:
                return {
                    "original_text": raw_text,
                    "refined_text": refined,
                    "provider": provider,
                    "model": used_model,
                    "success": True,
                }
        except Exception as exc:
            err_detail = f"{type(exc).__name__}: {str(exc) or repr(exc)}"
            logger.warning(f"AI text refinement with provider '{provider}' unavailable ({err_detail}). Using Admin Dictionary fallback.")

        # Fallback khi không gọi được LLM: Sử dụng pipeline hậu xử lý tiếng Việt & từ điển hành chính
        fallback_refined = post_process_vietnamese(raw_text)
        return {
            "original_text": raw_text,
            "refined_text": fallback_refined,
            "provider": "admin_dictionary_normalizer",
            "model": "rule_based_engine",
            "success": True,
            "message": "Đã chuẩn hóa chính tả và thể thức bằng Engine Từ điển Hành chính Tiếng Việt.",
        }

    async def extract_smart_fields(self, text: str) -> dict[str, Any]:
        """
        Dùng AI trích xuất thực thể thông minh (Entity Extraction) thành JSON chuẩn.
        Nếu AI không khả dụng, tự động fallback sang Regex Extraction.
        """
        if not text or not text.strip():
            return {
                "student_name": None,
                "student_id": None,
                "class_name": None,
                "faculty": None,
                "document_type": None,
                "reason": None,
                "amount": None,
                "document_date": None,
                "summary": None,
                "suggested_action": None,
                "provider": "none",
                "model": "none",
                "confidence_score": 0.0,
            }

        provider = self._determine_provider()
        json_schema_prompt = (
            "Bạn là trợ lý AI chuyên bóc tách dữ liệu hồ sơ văn bản Phòng Công tác Sinh viên (CTSV).\n"
            "Hãy đọc văn bản dưới đây và trích xuất các trường thông tin theo định dạng JSON hợp lệ:\n"
            "{\n"
            '  "student_name": "Họ và tên đầy đủ của sinh viên (viết hoa chữ cái đầu, ví dụ: Nguyễn Văn A)",\n'
            '  "student_id": "Mã số sinh viên (MSSV, chuỗi số từ 6-10 ký tự, ví dụ: 2412461)",\n'
            '  "class_name": "Lớp học (ví dụ: CTK44, DHKTPM18, hoặc null nếu không có)",\n'
            '  "faculty": "Khoa / Viện quản lý (ví dụ: Khoa Công nghệ Thông tin, hoặc null)",\n'
            '  "document_type": "Loại đơn/văn bản (ví dụ: Đơn xin miễn giảm học phí, Đơn xin bảo lưu, Đơn xin cấp học bổng, Đơn xin xác nhận)",\n'
            '  "reason": "Lý do ngắn gọn làm đơn / mục đích đơn",\n'
            '  "amount": "Số tiền đề xuất/được nhận nếu có (ví dụ: 5.000.000 VNĐ, hoặc null)",\n'
            '  "document_date": "Ngày tháng năm lập văn bản định dạng YYYY-MM-DD (nếu không rõ năm, suy luận hợp lý hoặc null)",\n'
            '  "summary": "Tóm tắt ngắn gọn nội dung và nguyện vọng của sinh viên trong 1-2 câu",\n'
            '  "suggested_action": "Gợi ý hành động cho cán bộ CTSV (ví dụ: Kiểm tra điều kiện hoàn cảnh và đối chiếu sổ hộ nghèo)"\n'
            "}\n"
            "LƯU Ý QUAN TRỌNG: CHỈ TRẢ VỀ DUY NHẤT 1 ĐỐI TƯỢNG JSON HỢP LỆ, KHÔNG BAO GỒM BẤT KỲ VĂN BẢN NÀO KHÁC NGOÀI JSON.\n\n"
            f"--- NỘI DUNG VĂN BẢN ---\n{text}\n--- HẾT ---"
        )

        ai_res = None
        used_provider = provider
        used_model = "unknown"

        try:
            raw_response = ""
            if provider == "gemini" and settings.gemini_api_key:
                used_model = settings.gemini_model
                raw_response = await self._call_gemini(json_schema_prompt)
            elif provider == "openai" and settings.openai_api_key:
                used_model = settings.openai_model
                raw_response = await self._call_openai(json_schema_prompt)
            elif provider == "ollama":
                used_model = settings.ollama_model
                raw_response = await self._call_ollama(json_schema_prompt)

            if raw_response:
                ai_res = self._clean_and_parse_json(raw_response)
        except Exception as exc:
            err_detail = f"{type(exc).__name__}: {str(exc) or repr(exc)}"
            logger.warning(f"AI entity extraction failed with {provider}: {err_detail}. Falling back to regex.")

        # Nếu AI trả về kết quả hợp lệ
        if ai_res and isinstance(ai_res, dict):
            # Parse document_date nếu có
            doc_date = ai_res.get("document_date")
            if doc_date and isinstance(doc_date, str):
                try:
                    # chuẩn hóa ISO format
                    dt = datetime.strptime(doc_date.strip()[:10], "%Y-%m-%d")
                    ai_res["document_date"] = dt.isoformat()
                except Exception:
                    pass

            # Bóc tách số hiệu thực tế từ văn bản gốc (nếu có)
            regex_meta = extraction_service.extract_metadata(text)
            ai_res["document_number"] = regex_meta.get("document_number")

            from app.services.tag_service import tag_service
            auto_tags = tag_service.generate_auto_tags(
                text=text,
                metadata=ai_res,
                confidence_score=0.95,
            )
            ai_res["tags"] = auto_tags
            ai_res["priority_score"] = tag_service.calculate_priority_score(auto_tags)
            ai_res["provider"] = used_provider
            ai_res["model"] = used_model
            ai_res["confidence_score"] = 0.95
            return ai_res

        # Fallback: Dùng ExtractionService Regex
        logger.info("Using regex fallback for smart fields extraction")
        fallback_data = extraction_service.extract_metadata(text)
        extra = fallback_data.get("extra", {}) or {}
        
        doc_date_val = fallback_data.get("document_date")
        if isinstance(doc_date_val, datetime):
            doc_date_str = doc_date_val.strftime("%Y-%m-%d")
        else:
            doc_date_str = None

        from app.services.tag_service import tag_service
        auto_tags = tag_service.generate_auto_tags(
            text=text,
            metadata=fallback_data,
            confidence_score=0.82,
        )

        return {
            "student_name": fallback_data.get("student_name"),
            "student_id": fallback_data.get("student_id"),
            "class_name": fallback_data.get("class_name") or extra.get("class_name"),
            "faculty": fallback_data.get("faculty") or extra.get("faculty"),
            "document_type": fallback_data.get("document_type") or extra.get("document_type"),
            "document_number": fallback_data.get("document_number"),
            "reason": fallback_data.get("reason") or extra.get("reason"),
            "amount": None,
            "document_date": doc_date_str,
            "tags": auto_tags,
            "priority_score": tag_service.calculate_priority_score(auto_tags),
            "summary": f"Đơn của sinh viên {fallback_data.get('student_name') or 'chưa rõ'} (MSSV: {fallback_data.get('student_id') or 'chưa rõ'})",
            "suggested_action": "Cán bộ kiểm tra đối chiếu thông tin với hồ sơ sinh viên gốc.",
            "provider": "rule_based",
            "model": "regex_pattern_matcher",
            "confidence_score": 0.82,
        }

    async def _call_gemini(self, prompt: str) -> str:
        """Gọi Google Gemini REST API v1beta."""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.gemini_model}:generateContent?key={settings.gemini_api_key}"
        payload = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 2048,
            }
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", "").strip()
        return ""

    async def _call_openai(self, prompt: str) -> str:
        """Gọi OpenAI Chat Completions API."""
        url = f"{settings.openai_base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": settings.openai_model,
            "messages": [
                {"role": "system", "content": "You are a professional assistant for university student affairs document OCR processing."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1,
            "max_tokens": 2048,
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            choices = data.get("choices", [])
            if choices:
                return choices[0].get("message", {}).get("content", "").strip()
        return ""

    async def _resolve_ollama_model(self, base_url: str) -> str:
        """Kiểm tra và tự động chọn model Ollama tối ưu VRAM GPU nếu có sẵn."""
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                r = await client.get(f"{base_url}/api/tags")
                if r.status_code == 200:
                    installed = [m.get("name", "") for m in r.json().get("models", [])]
                    for preferred in ("qwen2.5:3b", "qwen2.5:1.5b"):
                        for inst in installed:
                            if inst == preferred or inst.startswith(preferred + ":"):
                                return inst
        except Exception:
            pass
        return settings.ollama_model

    async def _call_ollama(self, prompt: str) -> str:
        """Gọi Local Ollama API (http://127.0.0.1:11434/api/generate)."""
        base_url = settings.ollama_base_url.rstrip("/")
        if "://localhost" in base_url:
            base_url = base_url.replace("://localhost", "://127.0.0.1")
        url = f"{base_url}/api/generate"

        model_name = await self._resolve_ollama_model(base_url)

        # Tính toán budget token dự đoán theo độ dài prompt để tăng tốc và tránh timeout
        words = len(prompt.split())
        num_predict = min(2048, max(256, int(words * 1.5)))

        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.2,
                "top_p": 0.9,
                "repeat_penalty": 1.2,
                "num_ctx": 2048,
                "num_predict": num_predict,
            }
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            res_text = data.get("response", "").strip()

            # Chống lặp dòng vô tận (hallucination repetition loop) của LLM
            lines = res_text.splitlines()
            dedup_lines = []
            prev_line = None
            rep_count = 0
            for l in lines:
                l_s = l.strip()
                if l_s and l_s == prev_line:
                    rep_count += 1
                    if rep_count >= 2:
                        continue
                else:
                    prev_line = l_s
                    rep_count = 1
                dedup_lines.append(l)
            return "\n".join(dedup_lines).strip()

    def _clean_and_parse_json(self, raw_text: str) -> dict[str, Any] | None:
        """Trích xuất và parse chuỗi JSON từ phản hồi LLM."""
        if not raw_text:
            return None
        text = raw_text.strip()
        # Loại bỏ markdown code block ```json ... ```
        if "```json" in text:
            m = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
            if m:
                text = m.group(1).strip()
        elif "```" in text:
            m = re.search(r"```\s*(.*?)\s*```", text, re.DOTALL)
            if m:
                text = m.group(1).strip()

        # Tìm chuỗi { ... }
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            text = text[start : end + 1]

        try:
            return json.loads(text)
        except Exception as exc:
            logger.debug(f"JSON decode error from AI response: {exc}. Content: {text[:200]}")
            return None


ai_service = AIService()
