import logging
import requests
from datetime import datetime
from models.database import DatabaseManager
from models.config import Config

logger = logging.getLogger(__name__)

class WeatherService:
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.config = Config()
        self.api_key = self.config.get_api_key('openweathermap')
        print(f"DEBUG: OpenWeatherMap API Key in WeatherService: {self.api_key}")
        self.base_url = "http://api.openweathermap.org/data/2.5/weather"
        self.city = "Hanoi"
        self.country_code = "VN"

    def get_weather(self):
        """Lấy thông tin thời tiết"""
        try:
            if not self.api_key:
                logger.error("OpenWeatherMap API Key is not set. Please set it in your .env file.")
                return None
            
            params = {
                'q': f"{self.city},{self.country_code}",
                'appid': self.api_key,
                'units': 'metric',
                'lang': 'vi'
            }
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            weather_data = {
                'temperature': data['main']['temp'],
                'feels_like': data['main']['feels_like'],
                'humidity': data['main']['humidity'],
                'pressure': data['main']['pressure'],
                'description': data['weather'][0]['description'],
                'icon': data['weather'][0]['icon'],
                'wind_speed': data['wind']['speed'],
                'clouds': data['clouds']['all'],
                'timestamp': datetime.now().timestamp()
            }
            
            # Lưu vào database
            self.db.save_weather_data(weather_data)
            
            return weather_data
            
        except Exception as e:
            logger.error(f"Error getting weather data: {str(e)}")
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