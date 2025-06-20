import logging
import google.generativeai as genai
from models.config import Config
import os

logger = logging.getLogger(__name__)

class GeminiErrorCorrectionService:
    def __init__(self):
        self.config = Config()
        self.api_key = os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY chưa được cấu hình. Vui lòng cấu hình biến môi trường GEMINI_API_KEY.")
        self.model = genai.GenerativeModel('models/gemini-1.5-flash')
        self.chat = self.model.start_chat(history=[])

    def get_fix_suggestion(self, error_message: str, error_context: str) -> str:
        """Lấy gợi ý sửa lỗi từ Gemini"""
        try:
            prompt = f"""
            Error Message: {error_message}
            Context: {error_context}
            
            Please analyze the error and provide a detailed suggestion to fix it.
            Include:
            1. What caused the error
            2. How to fix it
            3. Best practices to prevent similar errors
            """
            
            response = self.model.generate_content(prompt)
            return response.text
            
        except Exception as e:
            logger.error(f"Error getting fix suggestion from Gemini: {str(e)}")
            return "Không thể lấy gợi ý sửa lỗi từ Gemini. Vui lòng kiểm tra lại kết nối và API key."

    def get_code_review(self, code: str) -> str:
        """Lấy đánh giá code từ Gemini"""
        try:
            prompt = f"""
            Code to review:
            {code}
            
            Please review the code and provide:
            1. Code quality assessment
            2. Potential issues or bugs
            3. Suggestions for improvement
            4. Best practices to follow
            """
            
            response = self.model.generate_content(prompt)
            return response.text
            
        except Exception as e:
            logger.error(f"Error getting code review from Gemini: {str(e)}")
            return "Không thể lấy đánh giá code từ Gemini. Vui lòng kiểm tra lại kết nối và API key."

    def get_suggestion_from_facts(self, facts: dict) -> str:
        """Tạo prompt từ facts và lấy đề xuất từ Gemini"""
        try:
            prompt = self._build_prompt_from_facts(facts)
            response = self.model.generate_content(prompt)
            return response.text if hasattr(response, 'text') else str(response)
        except Exception as e:
            logger.error(f"Error getting suggestion from facts: {str(e)}")
            return "Không thể lấy đề xuất từ Gemini. Vui lòng kiểm tra lại kết nối và API key."

    def _build_prompt_from_facts(self, facts: dict) -> str:
        """Tạo prompt tự động từ facts tổng hợp"""
        prompt = (
            "Dựa trên các thông tin sau:\n"
            f"- Thời tiết: {facts.get('weather_condition', 'không rõ')}\n"
            f"- Lịch trình hôm nay: {facts.get('schedule_activity', 'không rõ')}\n"
            f"- Số lượng lịch trình: {facts.get('schedule_count', 'không rõ')}\n"
            f"- VSCode: {facts.get('vscode_status', 'không rõ')}\n"
            "Hãy đề xuất hoạt động hoặc lời khuyên phù hợp cho người dùng."
        )
        return prompt

    def list_models(self):
        """Liệt kê các model khả dụng"""
        try:
            genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
            for m in genai.list_models():
                print(m.name, m.supported_generation_methods)
        except Exception as e:
            logger.error(f"Error listing models: {str(e)}")
            return "Không thể liệt kê các model khả dụng. Vui lòng kiểm tra lại kết nối và API key." 