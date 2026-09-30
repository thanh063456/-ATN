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
        self.timeout = httpx.Timeout(settings.ai_timeout_seconds, connect=2.0)

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

    async def refine_ocr_text(self, raw_text: str) -> dict[str, Any]:
        """
        Dùng AI hậu xử lý, sửa các lỗi chính tả OCR tiếng Việt nhưng giữ nguyên cấu trúc văn bản hành chính.
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
        prompt = (
            "Bạn là chuyên gia ngôn ngữ học tiếng Việt và hiệu đính văn bản hành chính công tác sinh viên Đại học Đà Lạt.\n"
            "Dưới đây là văn bản trích xuất từ mô hình OCR quét tài liệu (có thể có lỗi nhận dạng dấu tiếng Việt, nhầm lẫn chữ O/0, l/1, hoặc lỗi gõ phím).\n"
            "Nhiệm vụ của bạn:\n"
            "1. Sửa các lỗi chính tả, phục hồi đúng dấu câu tiếng Việt chuẩn xác.\n"
            "2. Giữ nguyên 100% các dữ liệu thực tế quan trọng: Mã số sinh viên, số tiền, ngày tháng năm, tên riêng người và trường.\n"
            "3. Giữ nguyên bố cục văn bản hành chính (Tiêu ngữ, Tên đơn, Kính gửi, Thân bài, Ký tên).\n"
            "4. CHỈ TRẢ VỀ DUY NHẤT VĂN BẢN ĐÃ ĐƯỢC HIỆU ĐÍNH, KHÔNG GIẢI THÍCH, KHÔNG THÊM LỜI DẪN.\n\n"
            f"--- VĂN BẢN OCR GỐC ---\n{raw_text}\n--- HẾT ---"
        )

        try:
            if provider == "gemini" and settings.gemini_api_key:
                refined = await self._call_gemini(prompt)
                if refined:
                    return {
                        "original_text": raw_text,
                        "refined_text": refined,
                        "provider": "gemini",
                        "model": settings.gemini_model,
                        "success": True,
                    }
            elif provider == "openai" and settings.openai_api_key:
                refined = await self._call_openai(prompt)
                if refined:
                    return {
                        "original_text": raw_text,
                        "refined_text": refined,
                        "provider": "openai",
                        "model": settings.openai_model,
                        "success": True,
                    }
            elif provider == "ollama":
                refined = await self._call_ollama(prompt)
                if refined:
                    return {
                        "original_text": raw_text,
                        "refined_text": refined,
                        "provider": "ollama",
                        "model": settings.ollama_model,
                        "success": True,
                    }
        except Exception as exc:
            logger.warning(f"AI text refinement with provider '{provider}' unavailable ({exc}). Using Admin Dictionary fallback.")

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
            logger.warning(f"AI entity extraction failed with {provider}: {exc}. Falling back to regex.")

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

        return {
            "student_name": fallback_data.get("student_name"),
            "student_id": fallback_data.get("student_id"),
            "class_name": fallback_data.get("class_name") or extra.get("class_name"),
            "faculty": fallback_data.get("faculty") or extra.get("faculty"),
            "document_type": fallback_data.get("document_type") or extra.get("document_type"),
            "reason": fallback_data.get("reason") or extra.get("reason"),
            "amount": None,
            "document_date": doc_date_str,
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

    async def _call_ollama(self, prompt: str) -> str:
        """Gọi Local Ollama API (http://localhost:11434/api/generate)."""
        url = f"{settings.ollama_base_url.rstrip('/')}/api/generate"
        payload = {
            "model": settings.ollama_model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "num_predict": 2048,
            }
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data.get("response", "").strip()

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
