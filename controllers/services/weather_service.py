import requests
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from PIL import Image # Import Image for error checking
from io import BytesIO # Import BytesIO for error checking
from src.utils.config import Config # Corrected import path
from src.core.database import DatabaseManager # Thêm import này

class WeatherService:
    def __init__(self, db_manager: DatabaseManager):
        self.config = Config()
        self.db = db_manager # Gán db_manager được truyền vào
        self.logger = logging.getLogger('WeatherService')
        self.weather_config = self.config.get_weather_config()
        self.api_key = self.weather_config.get('api_key')
        self.city = self.weather_config.get('city', 'Hanoi')
        self.country_code = self.weather_config.get('country_code', 'VN')
        self.base_url = "http://api.openweathermap.org/data/2.5/weather"
        self.cache_duration = 300 # Thời gian cache mặc định 5 phút (300 giây)
        
    def get_weather(self, city: str = None) -> Optional[Dict[str, Any]]:
        """
        Lấy thông tin thời tiết hiện tại từ cache hoặc API.
        
        Args:
            city (str, optional): Tên thành phố. Nếu không cung cấp, sẽ sử dụng city mặc định.
            
        Returns:
            Optional[Dict[str, Any]]: Dữ liệu thời tiết hoặc None nếu có lỗi
        """
        if city:
            self.city = city
            
        cache_key = f"weather_{self.city}_{self.country_code}"
        
        # 1. Thử lấy từ cache
        cached_data = self.db.get_cached_response(cache_key)
        if cached_data:
            try:
                # Dữ liệu BLOB được trả về dưới dạng bytes, cần decode và parse JSON
                data = json.loads(cached_data.decode('utf-8'))
                self.logger.info("Dữ liệu thời tiết được lấy từ cache.")
                return data
            except (json.JSONDecodeError, AttributeError) as e:
                self.logger.error(f"Lỗi khi giải mã dữ liệu cached: {e}. Xóa cache và thử lại.")
                self.db.execute_query("DELETE FROM api_cache WHERE key = ?", (cache_key,))

        try:
            # Kiểm tra API key
            if not self.api_key or self.api_key == "YOUR_API_KEY":
                logging.error("API key chưa được cấu hình. Vui lòng cập nhật API key trong config.json")
                return None
            
            # 2. Nếu không có trong cache hoặc đã hết hạn, gọi API
            self.logger.info("Không có dữ liệu thời tiết trong cache hoặc đã hết hạn. Đang gọi API...")
            params = {
                'q': f"{self.city},{self.country_code}",
                'appid': self.api_key,
                'units': 'metric',
                'lang': 'vi'
            }
            
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()  # Ném ra lỗi nếu status code không phải 200
            
            data = response.json()
            
            # 3. Lưu vào cache
            self.db.cache_api_response(cache_key, json.dumps(data).encode('utf-8'), self.cache_duration)
            self.logger.info("Dữ liệu thời tiết đã được lưu vào cache.")
            
            return data
            
        except requests.exceptions.RequestException as e:
            logging.error(f"Lỗi khi gọi API thời tiết: {str(e)}")
            if hasattr(e.response, 'text'):
                logging.error(f"Chi tiết lỗi: {e.response.text}")
            return None
        except Exception as e:
            logging.error(f"Lỗi không xác định khi lấy thời tiết: {str(e)}")
            return None

    def _cache_weather_data(self, city: str, data: dict, duration: int = None) -> None:
        """Lưu dữ liệu thời tiết vào cache"""
        if duration is None:
            duration = self.cache_duration
        cache_key = f"weather_{city}_{self.country_code}"
        self.db.cache_api_response(cache_key, json.dumps(data).encode('utf-8'), duration)

    def _get_cached_weather(self, city: str) -> Optional[dict]:
        """Lấy dữ liệu thời tiết từ cache"""
        cache_key = f"weather_{city}_{self.country_code}"
        cached_data = self.db.get_cached_response(cache_key)
        if cached_data:
            try:
                return json.loads(cached_data.decode('utf-8'))
            except (json.JSONDecodeError, AttributeError):
                return None
        return None
    
    def get_temperature(self) -> Optional[float]:
        """Lấy nhiệt độ hiện tại"""
        data = self.get_weather()
        if data and 'main' in data:
            return data['main'].get('temp')
        return None
    
    def get_weather_description(self) -> Optional[str]:
        """Lấy mô tả thời tiết"""
        data = self.get_weather()
        if data and 'weather' in data and len(data['weather']) > 0:
            return data['weather'][0].get('description')
        return None
    
    def get_weather_icon(self) -> Optional[str]:
        """Lấy mã biểu tượng thời tiết"""
        data = self.get_weather()
        if data and 'weather' in data and len(data['weather']) > 0:
            return data['weather'][0].get('icon')
        return None
    
    def get_weather_icon_bytes(self, icon_code: str) -> Optional[bytes]:
        """Lấy icon thời tiết trực tiếp từ API"""
        # Không sử dụng caching database nữa, luôn tải trực tiếp
        
        try:
            # Tải icon từ OpenWeatherMap
            url = f'https://openweathermap.org/img/wn/{icon_code}@2x.png'
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            # Kiểm tra Content-Type để đảm bảo đây là hình ảnh
            if 'image' not in response.headers.get('Content-Type', ''):
                self.logger.error(f"Expected image but got {response.headers.get('Content-Type')} for {icon_code}. Response: {response.text[:100]}...")
                return None
            
            # Thử mở hình ảnh để xác nhận nó là hình ảnh hợp lệ
            try:
                Image.open(BytesIO(response.content))
            except Exception as e:
                self.logger.error(f"Received invalid image data from API for {icon_code}: {e}. Content-Type: {response.headers.get('Content-Type')}")
                return None

            return response.content
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Weather icon error: {str(e)}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error: {str(e)}")
            return None 