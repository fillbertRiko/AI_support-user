import os
import logging
import google.generativeai as genai
from typing import Optional

# Thư viện Google GenAI, bạn cần cài đặt: pip install google-generativeai
try:
    import google.generativeai as genai
except ImportError:
    logging.error("Thư viện google-generativeai chưa được cài đặt. Vui lòng chạy: pip install google-generativeai")
    genai = None

logger = logging.getLogger(__name__)

class GeminiErrorCorrectionService:
    def __init__(self):
        """Khởi tạo service"""
        self.api_key = os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY chưa được cấu hình. Vui lòng cấu hình biến môi trường GEMINI_API_KEY.")
        self.model = genai.GenerativeModel('gemini-pro')
        self.chat = self.model.start_chat(history=[])
        
    def _validate_api_key(self) -> bool:
        """Kiểm tra API key"""
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY chưa được cấu hình. Vui lòng cấu hình biến môi trường GEMINI_API_KEY.")
        return True

    def _handle_api_error(self, error):
        """Xử lý lỗi khi gọi Gemini API"""
        if '404' in str(error):
            logging.error("Lỗi khi gọi Gemini API: Model không được tìm thấy hoặc không được hỗ trợ.")
        else:
            logging.error(f"Lỗi khi gọi Gemini API: {error}")
        return None
        
    def _format_error_message(self, error_message: str, error_context: str) -> str:
        """Định dạng thông báo lỗi cho Gemini"""
        return f"""
Hãy phân tích lỗi sau và đưa ra gợi ý sửa lỗi:

Lỗi: {error_message}
Ngữ cảnh: {error_context}

Hãy cung cấp:
1. Phân tích nguyên nhân lỗi
2. Các bước để sửa lỗi
3. Code mẫu nếu cần thiết
"""
        
    def get_fix_suggestion(self, error_message: str, error_context: str) -> str:
        """Lấy gợi ý sửa lỗi từ Gemini"""
        try:
            if not self._validate_api_key():
                return "GEMINI_API_KEY chưa được cấu hình. Vui lòng kiểm tra lại."
                
            prompt = self._format_error_message(error_message, error_context)
            response = self.model.generate_content(prompt)
            
            if response and response.text:
                return response.text
            else:
                return "Không nhận được phản hồi từ Gemini. Vui lòng thử lại sau."
                
        except Exception as e:
            logger.error(f"Lỗi khi gọi Gemini API: {str(e)}")
            return f"Không thể kết nối đến Gemini API: {str(e)}" 