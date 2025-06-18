# MyAI - Trợ lý thông minh

Ứng dụng desktop thông minh với giao diện hiện đại, tích hợp nhiều tính năng hữu ích như thời tiết, lịch trình, VSCode tracking và hệ thống suy luận thông minh.

## 🌟 Tính năng chính

- **🌤️ Thời tiết chi tiết**: Nhiệt độ, độ ẩm, áp suất, tầm nhìn, điểm sương
- **👋 Lời chào thông minh**: Thay đổi theo thời gian trong ngày
- **📅 Quản lý lịch trình**: Tạo và quản lý lịch trình hàng ngày
- **💻 VSCode Tracking**: Theo dõi trạng thái VSCode
- **🧠 Hệ thống suy luận**: Đưa ra đề xuất thông minh dựa trên context
- **📊 Cơ sở tri thức**: Quản lý và đề xuất quy tắc mới
- **🎨 Giao diện hiện đại**: Sử dụng CustomTkinter với theme tối
- **💾 Database SQLite**: Lưu trữ dữ liệu cục bộ an toàn

## 📋 Yêu cầu hệ thống

- **Python**: 3.8 hoặc cao hơn
- **Hệ điều hành**: Windows 10/11, macOS, Linux
- **RAM**: Tối thiểu 4GB
- **Dung lượng**: 100MB trống
- **Kết nối internet**: Để lấy dữ liệu thời tiết

## 🚀 Cài đặt

### Bước 1: Clone repository
```bash
git clone <repository-url>
cd my_ai
```

### Bước 2: Tạo môi trường ảo
```bash
# Windows
python -m venv .venv

# Linux/Mac
python3 -m venv .venv
```

### Bước 3: Kích hoạt môi trường ảo
```bash
# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

### Bước 4: Cài đặt dependencies
```bash
pip install -r requirements.txt
```

### Bước 5: Cấu hình API keys
Tạo file `.env` trong thư mục gốc:
```bash
# Windows
copy .env.example .env

# Linux/Mac
cp .env.example .env
```

Chỉnh sửa file `.env`:
```env
# OpenWeatherMap API Key (bắt buộc)
OPENWEATHER_API_KEY=your_openweather_api_key_here

# Gemini API Key (tùy chọn - cho tính năng AI)
GEMINI_API_KEY=your_gemini_api_key_here
```

### Bước 6: Lấy API keys

#### OpenWeatherMap API Key (Miễn phí):
1. Truy cập [OpenWeatherMap](https://openweathermap.org/)
2. Đăng ký tài khoản miễn phí
3. Vào "API keys" trong profile
4. Copy API key và paste vào file `.env`

#### Gemini API Key (Tùy chọn):
1. Truy cập [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Tạo API key mới
3. Copy và paste vào file `.env`

## 🎯 Sử dụng

### Khởi chạy ứng dụng
```bash
python main.py
```

### Giao diện chính

#### 1. **Frame Chào hỏi**
- Hiển thị lời chào theo thời gian (sáng/chiều/tối)
- Đồng hồ thời gian thực
- Tên người dùng tùy chỉnh

#### 2. **Frame Thời tiết**
- **Nhiệt độ hiện tại**: Hiển thị nhiệt độ và cảm giác
- **Mô tả thời tiết**: Trời nắng, mưa, mây, etc.
- **Chỉ số chi tiết**:
  - 💨 Tốc độ gió (km/h)
  - 💧 Độ ẩm (%)
  - 👁️ Tầm nhìn (km)
  - 📊 Áp suất (hPa)
  - 💧 Điểm sương (°C)
- **Dự báo**: Mô tả thời tiết trong ngày

#### 3. **Frame Lịch trình**
- Xem lịch trình theo ngày trong tuần
- Thêm/sửa/xóa lịch trình
- Tích hợp với hệ thống suy luận

#### 4. **Frame VSCode**
- Theo dõi trạng thái VSCode
- Lịch sử sử dụng
- Thống kê thời gian code

#### 5. **Hệ thống suy luận**
- Hiển thị đề xuất thông minh
- Dựa trên thời tiết, lịch trình, thời gian
- Cập nhật tự động

### Các nút chức năng

#### **Quản lý Cơ sở Tri thức**
- Xem và chỉnh sửa các quy tắc
- Thêm quy tắc mới
- Xóa quy tắc không cần thiết

#### **Đề Xuất Quy Tắc Mới**
- Hệ thống AI đề xuất quy tắc mới
- Dựa trên hành vi sử dụng
- Tối ưu hóa trải nghiệm

## 🏗️ Cấu trúc dự án

```
my_ai/
├── 📁 controllers/          # Bộ điều khiển logic
│   ├── inference_engine.py  # Hệ thống suy luận
│   ├── rule_suggester.py    # Đề xuất quy tắc
│   ├── schedule_controller.py # Điều khiển lịch trình
│   └── vscode_controller.py # Điều khiển VSCode
├── 📁 models/               # Mô hình dữ liệu
│   ├── database.py          # Quản lý database
│   ├── knowledge_base.py    # Cơ sở tri thức
│   └── schedule.py          # Mô hình lịch trình
├── 📁 services/             # Dịch vụ
│   ├── weather_service.py   # Dịch vụ thời tiết
│   ├── fact_collector.py    # Thu thập dữ liệu
│   └── error_correction_service.py # Sửa lỗi
├── 📁 views/                # Giao diện
│   └── components/          # Các component UI
│       ├── greeting_frame.py    # Frame chào hỏi
│       ├── weather_frame.py     # Frame thời tiết
│       ├── schedule_frame.py    # Frame lịch trình
│       └── vscode_frame.py      # Frame VSCode
├── 📁 data/                 # Dữ liệu
│   ├── database/            # Database SQLite
│   ├── cache/               # Cache dữ liệu
│   └── excel/               # File Excel
├── 📁 logs/                 # Log files
├── 📁 tests/                # Unit tests
├── 📄 main.py               # Entry point
├── 📄 requirements.txt      # Dependencies
└── 📄 README.md             # Hướng dẫn này
```

## ⚙️ Cấu hình

### Tùy chỉnh thành phố thời tiết
Chỉnh sửa trong `services/weather_service.py`:
```python
self.default_city = "Hanoi"  # Thay đổi thành phố mặc định
```

### Tùy chỉnh giao diện
- **Theme**: Mặc định là dark mode
- **Kích thước**: Có thể resize cửa sổ
- **Font**: Sử dụng Montserrat

### Cấu hình database
- **Vị trí**: `data/database/database.db`
- **Tự động backup**: Có
- **Schema**: Tự động cập nhật

## 🔧 Troubleshooting

### Lỗi thường gặp

#### 1. **"Không thể khởi tạo DatabaseManager"**
```bash
# Xóa database cũ và tạo lại
rm data/database/database.db
python main.py
```

#### 2. **"Không có kết nối internet"**
- Kiểm tra kết nối internet
- Ứng dụng vẫn hoạt động với dữ liệu cache

#### 3. **"API key không hợp lệ"**
- Kiểm tra file `.env`
- Đảm bảo API key đúng định dạng
- Kiểm tra quota API

#### 4. **Giao diện không hiển thị**
```bash
# Cài đặt lại dependencies
pip uninstall customtkinter
pip install customtkinter
```

### Log files
- **App log**: `logs/app.log`
- **Error log**: `logs/errors.json`
- **Startup log**: `startup_log.txt`

## 🚀 Tính năng nâng cao

### Hệ thống suy luận
Ứng dụng sử dụng hệ thống suy luận thông minh để đưa ra đề xuất:

1. **Thu thập dữ liệu**: Thời tiết, lịch trình, thời gian
2. **Phân tích context**: Đánh giá tình huống hiện tại
3. **Áp dụng quy tắc**: Chạy các quy tắc trong knowledge base
4. **Đưa ra đề xuất**: Hiển thị kết quả cho người dùng

### Caching thông minh
- **Weather cache**: 1 giờ
- **API cache**: Tối ưu hóa request
- **Database cache**: Tăng tốc truy vấn

### Error handling
- **Graceful degradation**: Ứng dụng vẫn hoạt động khi có lỗi
- **Auto-recovery**: Tự động khôi phục khi có thể
- **User-friendly errors**: Thông báo lỗi dễ hiểu

## 🤝 Đóng góp

1. Fork repository
2. Tạo feature branch
3. Commit changes
4. Push to branch
5. Tạo Pull Request

## 📄 License

MIT License - Xem file LICENSE để biết thêm chi tiết.

## 📞 Hỗ trợ

- **Issues**: Tạo issue trên GitHub
- **Email**: [your-email@example.com]
- **Documentation**: Xem thêm trong thư mục `docs/`

---

**MyAI** - Trợ lý thông minh cho cuộc sống hiện đại! 🚀 