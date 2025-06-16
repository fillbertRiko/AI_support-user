import unittest
from unittest.mock import patch, MagicMock
import os
from src.services.gemini_error_correction_service import GeminiErrorCorrectionService

class TestGeminiErrorCorrectionService(unittest.TestCase):
    def setUp(self):
        """Chuẩn bị test environment"""
        self.service = GeminiErrorCorrectionService()
        
    @patch('src.services.gemini_error_correction_service.genai')
    def test_get_fix_suggestion_success(self, mock_genai):
        """Test lấy gợi ý sửa lỗi thành công"""
        # Mock Gemini response
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Gợi ý sửa lỗi: Kiểm tra lại API key"
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model
        
        # Test
        error_message = "API key not found"
        error_context = "Error in weather service"
        suggestion = self.service.get_fix_suggestion(error_message, error_context)
        
        # Kiểm tra kết quả
        self.assertIsNotNone(suggestion)
        # Không kiểm tra nội dung cụ thể
        
    @patch('src.services.gemini_error_correction_service.genai')
    def test_get_fix_suggestion_api_error(self, mock_genai):
        """Test lỗi khi gọi Gemini API"""
        # Mock lỗi
        mock_genai.GenerativeModel.side_effect = Exception("API Error")
        
        # Test
        error_message = "API key not found"
        error_context = "Error in weather service"
        suggestion = self.service.get_fix_suggestion(error_message, error_context)
        
        # Kiểm tra kết quả
        self.assertIsNotNone(suggestion)
        
    def test_validate_api_key(self):
        """Test kiểm tra API key"""
        os.environ['GEMINI_API_KEY'] = ''
        with self.assertRaises(ValueError):
            GeminiErrorCorrectionService()
        
    def test_format_error_message(self):
        """Test định dạng thông báo lỗi"""
        error_message = "API key not found"
        error_context = "Error in weather service"
        
        formatted_message = self.service._format_error_message(error_message, error_context)
        
        self.assertIn(error_message, formatted_message)
        self.assertIn(error_context, formatted_message)
        self.assertIn("Hãy phân tích lỗi", formatted_message)

if __name__ == '__main__':
    unittest.main() 