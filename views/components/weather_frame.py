import customtkinter as ctk
import logging
from datetime import datetime
from PIL import Image, ImageTk
import os
import requests # Thêm import requests
import io       # Thêm import io
from services.weather_service import WeatherService
from services.error_correction_service import ErrorCorrectionService
from services.update_optimizer_service import UpdateOptimizerService
from typing import Any # Import Any

logger = logging.getLogger(__name__)

class WeatherFrame(ctk.CTkFrame):
    def __init__(self, parent, weather_service: WeatherService):
        super().__init__(parent, fg_color="transparent") # Frame chính trong suốt
        self.weather_service = weather_service
        self.error_correction_service = ErrorCorrectionService()
        self.update_optimizer = UpdateOptimizerService()
        self.last_weather_data = None
        self.user_interaction = False

        # Khởi tạo metric_values ngay từ đầu
        self.metric_values = {}

        # Đảm bảo thư mục lưu trữ icon tồn tại
        self.icon_cache_dir = "views/assets/weather_icons"
        os.makedirs(self.icon_cache_dir, exist_ok=True)

        self.grid_columnconfigure(0, weight=1)
        # Sử dụng ít hàng hơn vì bố cục sẽ gọn hơn
        self.grid_rowconfigure((0, 1, 2, 3), weight=1)

        # Tạo các widget
        self.create_widgets()
        
        # Schedule updates
        self.schedule_weather_updates()

    def create_widgets(self):
        """Tạo các widget cho frame"""
        # Header Frame: Địa điểm và nút "Thấy thời tiết khác nhau?"
        self.header_frame = ctk.CTkFrame(self, fg_color="#3b5998", corner_radius=10) # Màu xanh dương
        self.header_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=5)
        self.header_frame.grid_columnconfigure((0, 1), weight=1)
        self.header_frame.grid_rowconfigure(0, weight=1)

        # Location and dropdown icon
        self.location_and_dropdown_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.location_and_dropdown_frame.grid(row=0, column=0, sticky="w", padx=15, pady=10)
        self.location_and_dropdown_frame.grid_columnconfigure(0, weight=1)

        self.location_label = ctk.CTkLabel(
            self.location_and_dropdown_frame,
            text="1509 Hải Đăng 8, Đa Tốn, Hà Nội",
            font=("Montserrat", 16, "bold"),
            text_color="#ffffff"
        )
        self.location_label.grid(row=0, column=0, sticky="w")
        
        # Dropdown icon (using unicode character for simplicity)
        self.dropdown_icon = ctk.CTkLabel(
            self.location_and_dropdown_frame,
            text=" ˅", # Unicode for dropdown arrow
            font=("Montserrat", 16, "bold"),
            text_color="#ffffff"
        )
        self.dropdown_icon.grid(row=0, column=1, sticky="w", padx=(0,0))

        # "Thấy thời tiết khác nhau?" button
        self.feedback_button = ctk.CTkButton(
            self.header_frame,
            text="Thấy thời tiết khác nhau?",
            font=("Montserrat", 14),
            fg_color="#5f7ac4", # Màu xanh nhạt hơn
            hover_color="#4f6bc9",
            text_color="#ffffff",
            corner_radius=8
        )
        self.feedback_button.grid(row=0, column=1, sticky="e", padx=15, pady=10)

        # Main Weather Info Frame
        self.main_weather_info_frame = ctk.CTkFrame(self, fg_color="#3b5998", corner_radius=10) # Cùng màu với header
        self.main_weather_info_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        self.main_weather_info_frame.grid_columnconfigure((0, 1), weight=1)
        self.main_weather_info_frame.grid_rowconfigure((0, 1, 2), weight=1)

        # Current weather time
        self.current_weather_time_label = ctk.CTkLabel(
            self.main_weather_info_frame,
            text="Thời tiết hiện tại\n21:17", # Thời gian sẽ được cập nhật động
            font=("Montserrat", 14, "bold"),
            text_color="#ffffff",
            justify="left"
        )
        self.current_weather_time_label.grid(row=0, column=0, sticky="nw", padx=15, pady=(10, 5))

        # Weather Icon and Temperature
        self.icon_and_temp_frame = ctk.CTkFrame(self.main_weather_info_frame, fg_color="transparent")
        self.icon_and_temp_frame.grid(row=1, column=0, columnspan=2, sticky="w", padx=15, pady=5)
        self.icon_and_temp_frame.grid_columnconfigure((0, 1), weight=0) # Không mở rộng

        self.icon_label = ctk.CTkLabel(
            self.icon_and_temp_frame,
            text="" # Image will be set dynamically
        )
        self.icon_label.grid(row=0, column=0, sticky="w")
        
        self.temp_label = ctk.CTkLabel(
            self.icon_and_temp_frame,
            text="29°C",
            font=("Montserrat", 48, "bold"),
            text_color="#ffffff"
        )
        self.temp_label.grid(row=0, column=1, sticky="w", padx=(10, 0))

        # Description and Feels Like
        self.description_frame = ctk.CTkFrame(self.main_weather_info_frame, fg_color="transparent")
        self.description_frame.grid(row=1, column=1, sticky="w", padx=(0,0), pady=5)
        self.description_frame.grid_columnconfigure(0, weight=1)

        self.description_label = ctk.CTkLabel(
            self.description_frame,
            text="Mưa nhỏ",
            font=("Montserrat", 18, "bold"),
            text_color="#ffffff",
            justify="left"
        )
        self.description_label.grid(row=0, column=0, sticky="w")

        self.feels_like_label = ctk.CTkLabel(
            self.description_frame,
            text="Cảm thấy như 30°",
            font=("Montserrat", 14),
            text_color="#ffffff",
            justify="left"
        )
        self.feels_like_label.grid(row=1, column=0, sticky="w")

        # Daily Forecast Description
        self.daily_forecast_description_label = ctk.CTkLabel(
            self,
            text="Dự báo có mưa nhỏ. Nhiệt độ thấp là 28°.",
            font=("Montserrat", 14),
            text_color="#ffffff",
            wraplength=600, # Adjust wraplength as needed
            justify="left"
        )
        self.daily_forecast_description_label.grid(row=2, column=0, sticky="ew", padx=10, pady=5)

        # Metrics Grid (Giờ, Độ ẩm, Tầm nhìn, Áp suất, Điểm sương)
        self.metrics_frame = ctk.CTkFrame(self, fg_color="#3b5998", corner_radius=10)
        self.metrics_frame.grid(row=3, column=0, sticky="nsew", padx=10, pady=5)
        self.metrics_frame.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)
        self.metrics_frame.grid_rowconfigure((0, 1), weight=1)

        metrics_data = {
            "Gió": {"value": "9 km/giờ", "unit": "", "font_size": 16},
            "Độ ẩm": {"value": "70%", "unit": "", "font_size": 16},
            "Tầm nhìn": {"value": "10 km", "unit": "", "font_size": 16},
            "Áp suất": {"value": "1005 mb", "unit": "", "font_size": 16},
            "Điểm sương": {"value": "23°", "unit": "", "font_size": 16}
        }

        for i, (label_text, data) in enumerate(metrics_data.items()):
            # Tiêu đề chỉ số + icon (i)
            metric_header_frame = ctk.CTkFrame(self.metrics_frame, fg_color="transparent")
            metric_header_frame.grid(row=0, column=i, padx=5, pady=2, sticky="s")
            metric_header_frame.grid_columnconfigure((0, 1), weight=1)
            
            ctk.CTkLabel(
                metric_header_frame,
                text=label_text,
                font=("Montserrat", 12),
                text_color="#ffffff"
            ).grid(row=0, column=0, sticky="e")

            ctk.CTkLabel(
                metric_header_frame,
                text=" ⓘ", # Unicode for info icon
                font=("Montserrat", 10),
                text_color="#ffffff"
            ).grid(row=0, column=1, sticky="w")

            # Giá trị chỉ số
            value_label = ctk.CTkLabel(
                self.metrics_frame,
                text=data["value"],
                font=("Montserrat", data["font_size"], "bold"),
                text_color="#ffffff"
            )
            value_label.grid(row=1, column=i, padx=5, pady=2, sticky="n")
            self.metric_values[label_text.lower().replace(" ", "_")] = value_label # Store reference

        # Moved the initial weather update call here
        self.update_weather()

    def get_or_download_weather_icon(self, icon_code: str) -> ctk.CTkImage | None:
        """Lấy biểu tượng thời tiết từ cache hoặc tải xuống nếu chưa có."""
        try:
            icon_path = os.path.join(self.icon_cache_dir, f"{icon_code}.png")

            if os.path.exists(icon_path):
                try:
                    image = Image.open(icon_path)
                    return ctk.CTkImage(image, size=(50, 50))
                except Exception as e:
                    logger.error(f"Lỗi khi tải biểu tượng cục bộ {icon_path}: {e}")
                    # Xóa file bị lỗi để thử tải lại
                    try:
                        os.remove(icon_path)
                    except:
                        pass

            # Nếu không có hoặc lỗi, tải xuống từ API
            try:
                icon_url = f"https://openweathermap.org/img/wn/{icon_code}@2x.png"
                response = requests.get(icon_url, timeout=10)
                response.raise_for_status() # Nâng ngoại lệ cho mã trạng thái lỗi

                image_data = response.content
                image = Image.open(io.BytesIO(image_data))
                
                # Lưu icon vào cache
                try:
                    image.save(icon_path)
                    logger.info(f"Đã tải và lưu biểu tượng {icon_code}.png vào {icon_path}")
                except Exception as e:
                    logger.warning(f"Không thể lưu icon {icon_code}: {e}")
                
                return ctk.CTkImage(image, size=(50, 50))

            except requests.exceptions.RequestException as e:
                logger.error(f"Lỗi khi tải biểu tượng thời tiết {icon_code} từ API: {e}")
            except Exception as e:
                logger.error(f"Lỗi xử lý hình ảnh biểu tượng {icon_code}: {e}")
                
        except Exception as e:
            logger.error(f"Lỗi tổng quát khi xử lý icon {icon_code}: {e}")
            
        return None

    def update_weather_icon(self, icon_code: str):
        """Cập nhật biểu tượng thời tiết trên giao diện."""
        try:
            # Kiểm tra xem icon_label có tồn tại và được khởi tạo đúng không
            if not hasattr(self, 'icon_label'):
                logger.warning("icon_label chưa được khởi tạo, bỏ qua cập nhật icon")
                return
                
            if not self.icon_label.winfo_exists():
                logger.warning("icon_label không tồn tại, bỏ qua cập nhật icon")
                return
                
            # Sử dụng phương thức mới để lấy hoặc tải icon
            icon_image = self.get_or_download_weather_icon(icon_code)

            if icon_image:
                # Kiểm tra lại một lần nữa trước khi configure
                if self.icon_label.winfo_exists():
                    try:
                        self.icon_label.configure(image=icon_image, text="")
                        logger.debug(f"Đã cập nhật icon thời tiết thành công: {icon_code}")
                    except Exception as e:
                        logger.error(f"Lỗi khi configure icon_label: {e}")
                else:
                    logger.warning("icon_label đã bị destroy, bỏ qua cập nhật")
            else:
                if self.icon_label.winfo_exists():
                    try:
                        self.icon_label.configure(text="N/A", image=None)
                        logger.warning(f"Không tìm thấy hoặc không thể tải biểu tượng thời tiết cho mã: {icon_code}")
                    except Exception as e:
                        logger.error(f"Lỗi khi configure icon_label với text: {e}")
        except Exception as e:
            logger.error(f"Lỗi khi cập nhật icon thời tiết: {e}")
            # Không làm gì nếu có lỗi, tránh crash ứng dụng

    def update_top_info(self, temp: Any, description: str, icon: str):
        """Cập nhật nhiệt độ, mô tả và biểu tượng chính."""
        self.temp_label.configure(text=f"{int(temp)}°C" if isinstance(temp, (int, float)) else str(temp))
        self.description_label.configure(text=description.capitalize())
        self.update_weather_icon(icon)

    def update_main_labels(self, feels_like: Any, humidity: Any, pressure: Any, wind_speed: Any):
        """Cập nhật các nhãn chính khác như 'feels like', độ ẩm, áp suất, tốc độ gió."""
        self.feels_like_label.configure(text=f"Cảm thấy như {int(feels_like)}°" if isinstance(feels_like, (int, float)) else f"Cảm thấy như {feels_like}")
        self.metric_values["gió"].configure(text=f"{wind_speed} km/giờ" if isinstance(wind_speed, (int, float)) else str(wind_speed))
        self.metric_values["độ_ẩm"].configure(text=f"{humidity}%" if isinstance(humidity, (int, float)) else str(humidity))
        self.metric_values["áp_suất"].configure(text=f"{pressure} mb" if isinstance(pressure, (int, float)) else str(pressure))
        # Tầm nhìn và điểm sương sẽ được xử lý ở update_metrics

    def update_metrics(self, clouds: Any, visibility: Any, dew_point: Any):
        """Cập nhật các giá trị metrics khác."""
        self.metric_values["tầm_nhìn"].configure(text=f"{visibility} km" if isinstance(visibility, (int, float)) else str(visibility))
        self.metric_values["điểm_sương"].configure(text=f"{dew_point}°" if isinstance(dew_point, (int, float)) else str(dew_point))

    def update_daily_forecast_description(self, description: str, min_temp: Any = "N/A"):
        """Cập nhật mô tả dự báo hàng ngày."""
        self.daily_forecast_description_label.configure(text=f"Dự báo có {description}. Nhiệt độ thấp là {min_temp}°.")

    def update_weather(self):
        """Cập nhật thông tin thời tiết từ service và hiển thị lên UI."""
        try:
            weather_data = self.weather_service.get_weather()
            logger.debug(f"Dữ liệu thời tiết từ WeatherService: {weather_data}")

            if weather_data:
                logger.debug(f"Dữ liệu thời tiết nhận được: {weather_data}")

                # Cập nhật thời gian hiện tại
                current_time_str = datetime.now().strftime("%H:%M")
                self.current_weather_time_label.configure(text=f"Thời tiết hiện tại\n{current_time_str}")

                # Cập nhật thông tin hàng đầu
                self.update_top_info(
                    temp=weather_data.get('temperature', 'N/A'),
                    description=weather_data.get('description', 'N/A'),
                    icon=weather_data.get('icon', '04d')
                )
                logger.debug("Cập nhật thông tin hàng đầu thành công.")

                # Cập nhật labels chính
                feels_like = weather_data.get('feels_like', 'N/A')
                humidity = weather_data.get('humidity', 'N/A')
                pressure = weather_data.get('pressure', 'N/A')
                wind_speed = weather_data.get('wind_speed', 'N/A')
                
                # Cập nhật chỉ số gió
                # Lưu ý: OpenWeatherMap trả về tốc độ gió theo m/s. Cần chuyển đổi sang km/giờ.
                wind_speed_kmh = round(float(wind_speed) * 3.6, 1) if isinstance(wind_speed, (int, float)) else 'N/A'

                self.update_main_labels(
                    feels_like=feels_like,
                    humidity=humidity,
                    pressure=pressure,
                    wind_speed=wind_speed_kmh # Sử dụng giá trị đã chuyển đổi
                )
                logger.debug("Cập nhật labels chính thành công.")

                # Cập nhật metrics
                visibility = weather_data.get('visibility', 'N/A') # Thêm tầm nhìn
                dew_point = weather_data.get('dew_point', 'N/A') # Thêm điểm sương

                # Chuyển đổi tầm nhìn từ mét sang km
                visibility_km = round(float(visibility) / 1000, 1) if isinstance(visibility, (int, float)) else 'N/A'

                self.update_metrics(
                    clouds='N/A', # Không sử dụng clouds cho tầm nhìn
                    visibility=visibility_km,
                    dew_point=dew_point
                )
                logger.debug("Cập nhật metrics thành công.")

                # Cập nhật mô tả dự báo hàng ngày
                min_temp = weather_data.get('temp_min', 'N/A') # Giả sử có temp_min trong data
                self.update_daily_forecast_description(
                    description=weather_data.get('description', 'N/A'),
                    min_temp=min_temp
                )
                logger.debug("Cập nhật mô tả dự báo hàng ngày thành công.")

            else:
                self.location_label.configure(text="N/A")
                self.current_weather_time_label.configure(text="Thời tiết hiện tại\nN/A")
                self.temp_label.configure(text="N/A")
                self.description_label.configure(text="N/A")
                self.feels_like_label.configure(text="Cảm thấy như N/A")
                self.daily_forecast_description_label.configure(text="Dự báo có N/A. Nhiệt độ thấp là N/A°.")
                for key in self.metric_values:
                    self.metric_values[key].configure(text="N/A")
                self.icon_label.configure(image=None, text="N/A")

        except Exception as e:
            logger.error(f"Lỗi khi cập nhật thời tiết: {str(e)}")
            self.error_correction_service.log_error(
                service='weather',
                error_type='RUNTIME_ERROR',
                error_message=str(e),
                context="An unexpected error occurred during weather update."
            )
            # Reset UI to N/A on error
            self.location_label.configure(text="N/A")
            self.current_weather_time_label.configure(text="Thời tiết hiện tại\nN/A")
            self.temp_label.configure(text="N/A")
            self.description_label.configure(text="N/A")
            self.feels_like_label.configure(text="Cảm thấy như N/A")
            self.daily_forecast_description_label.configure(text="Dự báo có N/A. Nhiệt độ thấp là N/A°.")
            for key in self.metric_values:
                self.metric_values[key].configure(text="N/A")
            self.icon_label.configure(image=None, text="N/A")

    def schedule_weather_updates(self):
        """Lên lịch cập nhật thời tiết định kỳ"""
        # Lấy thời gian cập nhật tối ưu
        optimal_interval = self.update_optimizer.get_optimal_interval('weather')
        self.after(optimal_interval * 1000, self.update_weather)