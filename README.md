# Ứng dụng Chào hỏi

Ứng dụng desktop hiển thị thông tin thời tiết, tin tức và nhắc nhở.

## Cài đặt

1. Tạo môi trường ảo:
```bash
python -m venv .venv
```

2. Kích hoạt môi trường ảo:
- Windows:
```bash
.venv\Scripts\activate
```
- Linux/Mac:
```bash
source .venv/bin/activate
```

3. Cài đặt dependencies:
```bash
pip install -r requirements.txt
```

4. Tạo file .env và cấu hình:
```bash
cp .env.example .env
```
Sau đó chỉnh sửa file .env với API keys của bạn.

## Chạy ứng dụng

```bash
python main.py
```

## Cấu trúc thư mục

```
my_ai/
├── src/
│   ├── core/           # Core functionality
│   │   ├── __init__.py
│   │   ├── config.py
│   │   └── database.py
│   ├── services/       # Business logic
│   │   ├── __init__.py
│   │   ├── weather_service.py
│   │   ├── news_service.py
│   │   └── reminder_service.py
│   ├── ui/            # UI components
│   │   ├── __init__.py
│   │   └── components/
│   │       ├── __init__.py
│   │       ├── greeting_frame.py
│   │       ├── weather_frame.py
│   │       ├── news_frame.py
│   │       └── reminder_frame.py
│   └── utils/         # Utility functions
│       └── __init__.py
├── data/              # Data storage
│   ├── database/
│   └── cache/
├── tests/             # Unit tests
├── .env              # Environment variables
├── .env.example      # Example environment variables
├── requirements.txt  # Dependencies
└── main.py          # Main entry point
```

## Tính năng

- Hiển thị lời chào theo thời gian trong ngày
- Hiển thị thời tiết hiện tại
- Hiển thị tin tức mới nhất
- Quản lý nhắc nhở
- Thanh cuộn cho nội dung dài
- Caching để tối ưu hiệu suất
- Xử lý lỗi và logging

## Yêu cầu

- Python 3.8+
- API key từ OpenWeatherMap
- API key từ NewsAPI 