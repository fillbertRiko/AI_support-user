import logging
import requests
from datetime import datetime
from models.database import DatabaseManager
from models.config import Config
import os
import json
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class WeatherService:
    def __init__(self, db):
        self.db = db
        self.logger = logging.getLogger(__name__)
        # Load biến môi trường từ file .env
        load_dotenv()
        self.api_key = self._load_api_key()
        self.base_url = "http://api.openweathermap.org/data/2.5/weather"
        self.default_city = "Hanoi"

    def _load_api_key(self):
        """Load API key from .env file"""
        try:
            # Lấy API key từ biến môi trường
            api_key = os.getenv('OPENWEATHER_API_KEY')
            if not api_key:
                self.logger.warning("Không tìm thấy OPENWEATHER_API_KEY trong file .env")
                return None
            return api_key
            
        except Exception as e:
            self.logger.error(f"Lỗi khi tải API key: {str(e)}", exc_info=True)
            return None

    def get_weather(self, city=None):
        """Lấy thông tin thời tiết cho thành phố"""
        try:
            if not self.api_key:
                self.logger.error("Không có API key")
                return None
                
            # Sử dụng thành phố mặc định nếu không có city được chỉ định
            city = city or self.default_city
                
            # Kiểm tra cache trước
            cached_data = self._get_cached_weather(city)
            if cached_data:
                return cached_data
                
            # Gọi API nếu không có trong cache
            url = f"{self.base_url}?q={city}&appid={self.api_key}&units=metric&lang=vi"
            response = requests.get(url)
            
            if response.status_code == 200:
                data = response.json()
                weather_data = {
                    'city': city,
                    'temperature': data['main']['temp'],
                    'description': data['weather'][0]['description'],
                    'humidity': data['main']['humidity'],
                    'wind_speed': data['wind']['speed'],
                    'pressure': data['main'].get('pressure', None),
                    'visibility': data.get('visibility', None),
                    'dew_point': data['main'].get('temp_min', None),  # Sử dụng temp_min làm dew_point tạm thời
                    'feels_like': data['main'].get('feels_like', None),
                    'temp_min': data['main'].get('temp_min', None),
                    'temp_max': data['main'].get('temp_max', None)
                }
                
                # Lưu vào cache
                self._cache_weather(city, weather_data)
                
                # Lưu vào database
                self._save_to_database(weather_data)
                
                return weather_data
            else:
                self.logger.error(f"Lỗi API: {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"Lỗi khi lấy thông tin thời tiết: {str(e)}", exc_info=True)
            return None

    def get_weather_history(self, limit: int = 10):
        """Lấy lịch sử thời tiết"""
        try:
            return self.db.get_weather_history(limit)
        except Exception as e:
            logger.error(f"Error getting weather history: {str(e)}")
            return []

    def get_weather_stats(self):
        """Lấy thống kê thời tiết"""
        try:
            return self.db.get_weather_stats()
        except Exception as e:
            logger.error(f"Error getting weather stats: {str(e)}")
            return {}

    def _get_cached_weather(self, city):
        """Lấy thông tin thời tiết từ cache"""
        try:
            cache_key = f"weather_{city}"
            result = self.db.execute_query(
                "SELECT * FROM api_cache WHERE endpoint = ? AND timestamp > datetime('now', '-1 hour')",
                (cache_key,)
            )
            if result:
                return json.loads(result[0]['response'])
            return None
        except Exception as e:
            self.logger.error(f"Lỗi khi đọc cache: {str(e)}", exc_info=True)
            return None
            
    def _cache_weather(self, city, data):
        """Lưu thông tin thời tiết vào cache"""
        try:
            cache_key = f"weather_{city}"
            self.db.execute_query(
                "INSERT OR REPLACE INTO api_cache (endpoint, response) VALUES (?, ?)",
                (cache_key, json.dumps(data))
            )
        except Exception as e:
            self.logger.error(f"Lỗi khi lưu cache: {str(e)}", exc_info=True)
            
    def _save_to_database(self, weather_data):
        """Lưu thông tin thời tiết vào database"""
        try:
            self.db.execute_query(
                """
                INSERT INTO weather_data (city, temperature, description, humidity, wind_speed, pressure, visibility, dew_point, feels_like, temp_min, temp_max)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    weather_data['city'],
                    weather_data['temperature'],
                    weather_data['description'],
                    weather_data['humidity'],
                    weather_data['wind_speed'],
                    weather_data.get('pressure'),
                    weather_data.get('visibility'),
                    weather_data.get('dew_point'),
                    weather_data.get('feels_like'),
                    weather_data.get('temp_min'),
                    weather_data.get('temp_max')
                )
            )
        except Exception as e:
            self.logger.error(f"Lỗi khi lưu vào database: {str(e)}", exc_info=True)

    def close(self):
        """Đóng service an toàn"""
        try:
            # Đóng các kết nối nếu có
            if hasattr(self, 'session') and self.session:
                self.session.close()
        except Exception as e:
            logger.error(f"Lỗi khi đóng WeatherService: {e}") 