import os
import logging

logger = logging.getLogger(__name__)

def get_weather_icon_path(weather_id: int) -> str:
    """Lấy đường dẫn đến biểu tượng thời tiết"""
    icon_dir = os.path.join('views', 'assets', 'weather_icons')
    if not os.path.exists(icon_dir):
        os.makedirs(icon_dir)
        logger.info(f"Created weather icons directory: {icon_dir}")

    # Chuyển đổi weather_id thành tên file
    if 200 <= weather_id < 300:  # Thunderstorm
        icon_name = "thunderstorm.png"
    elif 300 <= weather_id < 400:  # Drizzle
        icon_name = "drizzle.png"
    elif 500 <= weather_id < 600:  # Rain
        icon_name = "rain.png"
    elif 600 <= weather_id < 700:  # Snow
        icon_name = "snow.png"
    elif 700 <= weather_id < 800:  # Atmosphere
        icon_name = "atmosphere.png"
    elif weather_id == 800:  # Clear
        icon_name = "clear.png"
    elif 801 <= weather_id <= 804:  # Clouds
        icon_name = "clouds.png"
    else:
        icon_name = "default.png"

    return os.path.join(icon_dir, icon_name) 