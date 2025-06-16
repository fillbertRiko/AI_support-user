import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from src.services.weather_service import WeatherService
from src.core.database import DatabaseManager
import os

class TestWeatherService(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Thiết lập test environment"""
        cls.test_db_path = "test_weather.db"
        cls.db = DatabaseManager(cls.test_db_path)
        cls.db._init_database()  # Đảm bảo cơ sở dữ liệu được khởi tạo
        cls.weather_service = WeatherService(cls.db)
        
    def setUp(self):
        """Chuẩn bị dữ liệu test trước mỗi test case"""
        # Xóa cache cũ
        with self.db._get_connection() as conn:
            conn.execute("DELETE FROM api_cache")
            conn.commit()
            
    @patch('src.services.weather_service.requests.get')
    def test_get_weather_success(self, mock_get):
        """Test lấy thông tin thời tiết thành công"""
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "main": {
                "temp": 25.5,
                "humidity": 70
            },
            "weather": [{
                "main": "Clear",
                "description": "clear sky",
                "icon": "01d"
            }],
            "wind": {
                "speed": 5.0
            }
        }
        mock_get.return_value = mock_response
        
        # Test
        weather_data = self.weather_service.get_weather("Hanoi")
        
        # Kiểm tra kết quả
        self.assertIsNotNone(weather_data)
        self.assertEqual(weather_data["main"]["temp"], 25.5)
        self.assertEqual(weather_data["main"]["humidity"], 70)
        self.assertEqual(weather_data["weather"][0]["description"], "clear sky")
        self.assertEqual(weather_data["weather"][0]["icon"], "01d")
        self.assertEqual(weather_data["wind"]["speed"], 5.0)
        
    @patch('src.services.weather_service.requests.get')
    def test_get_weather_api_error(self, mock_get):
        """Test lỗi API"""
        # Mock response với lỗi
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        # Test
        weather_data = self.weather_service.get_weather("InvalidCity")
        
        # Kiểm tra kết quả
        self.assertIsNone(weather_data)
        
    def test_weather_cache(self):
        """Test cache thời tiết"""
        # Test data
        test_data = {
            "temperature": 25.5,
            "humidity": 70,
            "description": "clear sky",
            "icon": "01d",
            "wind_speed": 5.0
        }
        
        # Thêm cache
        self.weather_service._cache_weather_data("Hanoi", test_data)
        
        # Lấy từ cache
        cached_data = self.weather_service._get_cached_weather("Hanoi")
        
        # Kiểm tra kết quả
        self.assertIsNotNone(cached_data)
        self.assertEqual(cached_data["temperature"], test_data["temperature"])
        self.assertEqual(cached_data["humidity"], test_data["humidity"])
        
    def test_weather_cache_expiration(self):
        """Test hết hạn cache"""
        # Test data
        test_data = {
            "temperature": 25.5,
            "humidity": 70,
            "description": "clear sky",
            "icon": "01d",
            "wind_speed": 5.0
        }
        
        # Thêm cache với thời gian hết hạn ngắn
        self.weather_service._cache_weather_data("Hanoi", test_data, 1)  # 1 giây
        
        # Đợi cache hết hạn
        import time
        time.sleep(2)
        
        # Lấy từ cache
        cached_data = self.weather_service._get_cached_weather("Hanoi")
        
        # Kiểm tra kết quả
        self.assertIsNone(cached_data)
        
    @classmethod
    def tearDownClass(cls):
        """Dọn dẹp sau khi test xong"""
        if os.path.exists(cls.test_db_path):
            os.remove(cls.test_db_path)

if __name__ == '__main__':
    unittest.main() 