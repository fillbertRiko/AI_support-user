import logging
import google.generativeai as genai
from models.config import Config

logger = logging.getLogger(__name__)

class GeminiErrorCorrectionService:
    def __init__(self):
        self.config = Config()
        self.api_key = self.config.get_api_key('gemini')
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-pro')

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