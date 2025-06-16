import os
import requests
from pathlib import Path

# Danh sách các biểu tượng thời tiết cần tải
WEATHER_ICONS = {
    'clear': 'https://cdn-icons-mp4.flaticon.com/512/3222/3222800.mp4',
    'clouds': 'https://cdn-icons-mp4.flaticon.com/512/1146/1146869.mp4',
    'rain': 'https://cdn-icons-mp4.flaticon.com/512/1779/1779940.mp4',
    'drizzle': 'https://cdn-icons-mp4.flaticon.com/512/1779/1779940.mp4',
    'thunderstorm': 'https://cdn-icons-mp4.flaticon.com/512/1779/1779940.mp4',
    'snow': 'https://cdn-icons-mp4.flaticon.com/512/1779/1779940.mp4',
    'fog': 'https://cdn-icons-mp4.flaticon.com/512/1146/1146869.mp4',
    'default': 'https://cdn-icons-mp4.flaticon.com/512/3222/3222800.mp4'
}

def download_weather_icons():
    """Tải các biểu tượng thời tiết động"""
    # Tạo thư mục nếu chưa tồn tại
    icons_dir = Path(__file__).parent.parent / 'src' / 'assets' / 'weather_icons'
    icons_dir.mkdir(parents=True, exist_ok=True)
    
    # Tải từng biểu tượng
    for icon_name, url in WEATHER_ICONS.items():
        try:
            print(f"Đang tải biểu tượng {icon_name}...")
            response = requests.get(url)
            response.raise_for_status()
            
            # Lưu file
            icon_path = icons_dir / f"{icon_name}.gif"
            with open(icon_path, 'wb') as f:
                f.write(response.content)
            print(f"Đã tải xong biểu tượng {icon_name}")
            
        except Exception as e:
            print(f"Lỗi khi tải biểu tượng {icon_name}: {str(e)}")

if __name__ == "__main__":
    download_weather_icons() 