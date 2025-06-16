import os

def get_weather_icon_path(icon_name: str) -> str:
    """
    Lấy đường dẫn đầy đủ đến file biểu tượng thời tiết
    
    Args:
        icon_name (str): Tên của biểu tượng (ví dụ: 'clear', 'rain', 'clouds')
        
    Returns:
        str: Đường dẫn đầy đủ đến file biểu tượng
    """
    # Đường dẫn đến thư mục chứa biểu tượng
    icons_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'weather_icons')
    
    # Tạo đường dẫn đầy đủ đến file biểu tượng
    icon_path = os.path.join(icons_dir, f"{icon_name}.gif")
    
    return icon_path 