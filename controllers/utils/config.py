import os
import json
from typing import Any, Dict

class Config:
    def __init__(self):
        self.config_file = "config.json"
        self.default_config = {
            "weather": {
                "city": "Hanoi",
                "country_code": "VN",
                "api_key": "YOUR_API_KEY",  # Thay thế bằng API key thực
                "update_interval": 300  # 5 phút
            },
            "app": {
                "window_size": "800x600",
                "theme": "light",
                "language": "vi"
            },
            "logging": {
                "level": "INFO",
                "file": "app.log",
                "max_size": 1024 * 1024,  # 1MB
                "backup_count": 5
            },
            "database": {
                "path": "data/app.db",
                "backup_path": "data/backups"
            }
        }
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Tải cấu hình từ file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # Tạo file cấu hình mặc định nếu chưa tồn tại
                self.save_config(self.default_config)
                return self.default_config
        except Exception as e:
            print(f"Lỗi khi tải cấu hình: {str(e)}")
            return self.default_config
    
    def save_config(self, config: Dict[str, Any]) -> None:
        """Lưu cấu hình vào file"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Lỗi khi lưu cấu hình: {str(e)}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Lấy giá trị cấu hình theo key"""
        try:
            keys = key.split('.')
            value = self.config
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any) -> None:
        """Cập nhật giá trị cấu hình"""
        try:
            keys = key.split('.')
            config = self.config
            for k in keys[:-1]:
                config = config[k]
            config[keys[-1]] = value
            self.save_config(self.config)
        except Exception as e:
            print(f"Lỗi khi cập nhật cấu hình: {str(e)}")
    
    def get_weather_config(self) -> Dict[str, Any]:
        """Lấy cấu hình thời tiết"""
        return self.get('weather', {})
    
    def get_app_config(self) -> Dict[str, Any]:
        """Lấy cấu hình ứng dụng"""
        return self.get('app', {})
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Lấy cấu hình logging"""
        return self.get('logging', {})
    
    def get_database_config(self) -> Dict[str, Any]:
        """Lấy cấu hình database"""
        return self.get('database', {})

    def get_news_config(self) -> Dict[str, Any]:
        """Lấy cấu hình tin tức"""
        return self.get('news', {})

    def get_cache_duration(self, service_name: str, default_duration: int = 300) -> int:
        """Lấy thời gian cache cho một dịch vụ cụ thể"""
        return self.get(f'{service_name}.update_interval', default_duration) 