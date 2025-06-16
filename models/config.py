import os
import json
from typing import Any, Dict
import logging
from dotenv import load_dotenv

class Config:
    _instance = None
    _config_file = 'data/config.json'
    _default_config = {
        'api_keys': {
            # API keys sẽ được tải từ .env
            'openweathermap': '',
            'newsapi': ''
        },
        'app_settings': {
            'window_width': 620,
            'window_height': 620,
            'update_interval': {
                'weather': 1800,  # 30 phút
                'news': 3600,     # 1 giờ
                #'reminders': 300  # 5 phút
            },
            'cache_duration': {
                'weather': 1800,
                'news': 3600
            }
        },
        'database': {
            'path': 'data/database/greeting.db',
            'max_connections': 5
        },
        'logging': {
            'level': 'INFO',
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        }
    }
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._initialized = True
        load_dotenv() # Load environment variables from .env
        self._config = self._load_config()
        self._setup_logging()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load config từ file hoặc tạo mới nếu chưa tồn tại"""
        if os.path.exists(self._config_file):
            try:
                with open(self._config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                # Merge default config with loaded config to ensure all keys are present
                merged_config = self._default_config.copy()
                self._deep_merge(merged_config, loaded_config)
                return merged_config
            except Exception as e:
                logging.error(f"Error loading config: {str(e)}")
                return self._default_config
        else:
            # Tạo thư mục nếu chưa tồn tại
            os.makedirs(os.path.dirname(self._config_file), exist_ok=True)
            # Lưu config mặc định
            self._save_config(self._default_config)
            return self._default_config
    
    def _save_config(self, config: Dict[str, Any]) -> None:
        """Lưu config vào file"""
        try:
            with open(self._config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logging.error(f"Error saving config: {str(e)}")
    
    def _setup_logging(self) -> None:
        """Thiết lập logging dựa trên config"""
        logging.basicConfig(
            level=getattr(logging, self._config['logging']['level']),
            format=self._config['logging']['format']
        )

    def _deep_merge(self, dict1, dict2):
        for k, v in dict2.items():
            if isinstance(v, dict) and k in dict1 and isinstance(dict1[k], dict):
                self._deep_merge(dict1[k], v)
            else:
                dict1[k] = v

    def get(self, key: str, default: Any = None) -> Any:
        """Lấy giá trị config theo key"""
        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
            if value is None:
                return default
        return value
    
    def set(self, key: str, value: Any) -> None:
        """Cập nhật giá trị config"""
        keys = key.split('.')
        config = self._config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
        self._save_config(self._config)
    
    def get_api_key(self, service: str) -> str:
        """Lấy API key cho service cụ thể"""
        # Lấy API key từ biến môi trường
        if service == 'openweathermap':
            return os.getenv('OPENWEATHER_API_KEY', '')
        elif service == 'newsapi':
            return os.getenv('NEWS_API_KEY', '')
        elif service == 'gemini':
            return os.getenv('GEMINI_API_KEY', '')
        return ''
    
    def get_update_interval(self, service: str) -> int:
        """Lấy thời gian cập nhật cho service"""
        return self.get(f'app_settings.update_interval.{service}', 3600)
    
    def get_cache_duration(self, service: str) -> int:
        """Lấy thời gian cache cho service"""
        return self.get(f'app_settings.cache_duration.{service}', 3600)
    
    def get_window_size(self) -> tuple:
        """Lấy kích thước cửa sổ"""
        return (
            self.get('app_settings.window_width', 620),
            self.get('app_settings.window_height', 620)
        ) 