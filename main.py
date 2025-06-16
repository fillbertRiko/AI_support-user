import os
import customtkinter as ctk
from tkinter import messagebox
import sys
import logging
import socket
import time
from datetime import datetime
import pandas as pd
from models.config import Config
from models.database import DatabaseManager
from models.knowledge_base import KnowledgeBase
from views.components.schedule_frame import ScheduleFrame
from views.components.vscode_frame import VSCodeFrame
from views.components.greeting_frame import GreetingFrame
from views.components.weather_frame import WeatherFrame
from views.components.knowledge_editor_frame import KnowledgeEditorFrame
from views.components.knowledge_suggestion_frame import KnowledgeSuggestionFrame
from controllers.schedule_controller import ScheduleController
from controllers.vscode_controller import VSCodeController
from controllers.inference_engine import InferenceEngine
from controllers.rule_suggester import RuleSuggester
from services.scheduler_service import SchedulerService
from services.weather_service import WeatherService
from services.gemini_error_correction_service import GeminiErrorCorrectionService

# Thiết lập theme cho CustomTkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Định nghĩa màu nền theo thời gian
BACKGROUND_COLORS = {
    "morning": "#FFE4B5",  # Màu cam nhạt cho buổi sáng
    "afternoon": "#87CEEB",  # Màu xanh nhạt cho buổi chiều
    "evening": "#483D8B",  # Màu tím nhạt cho buổi tối
    "night": "#191970"  # Màu xanh đậm cho đêm
}

# Định nghĩa màu chữ theo thời gian
TEXT_COLORS = {
    "morning": "#333333",  # Màu xám đậm cho nền sáng
    "afternoon": "#333333", # Màu xám đậm cho nền sáng
    "evening": "#ffffff",  # Màu trắng cho nền tối
    "night": "#ffffff"   # Màu trắng cho nền tối
}

# Thiết lập logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def manage_log_file():
    """Manages the application log file by archiving it daily."""
    log_file_path = 'app.log'
    if os.path.exists(log_file_path):
        last_modified_timestamp = os.path.getmtime(log_file_path)
        last_modified_date = datetime.fromtimestamp(last_modified_timestamp).date()
        current_date = datetime.now().date()

        if last_modified_date < current_date:
            # Archive the old log file
            archive_name = last_modified_date.strftime('app_%Y-%m-%d.log')
            os.rename(log_file_path, archive_name)
            logger.info(f"Archived old log file to: {archive_name}")

            # Create a new, empty log file for today
            open(log_file_path, 'a', encoding='utf-8').close()
            logger.info(f"Created new log file: {log_file_path}")

def check_internet_connection():
    """Kiểm tra kết nối internet"""
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except OSError:
        return False

def get_time_of_day():
    """Xác định thời gian trong ngày"""
    hour = datetime.now().hour
    if 5 <= hour < 12:
        return "morning"
    elif 12 <= hour < 17:
        return "afternoon"
    elif 17 <= hour < 22:
        return "evening"
    else:
        return "night"

def update_background_color(root):
    """Cập nhật màu nền và màu chữ dựa trên thời gian"""
    time_of_day = get_time_of_day()
    bg_color = BACKGROUND_COLORS[time_of_day]
    text_color = TEXT_COLORS[time_of_day]
    
    # Cập nhật màu nền cho root window
    root.configure(fg_color=bg_color)
    
    # Hàm đệ quy để cập nhật màu nền và màu chữ cho tất cả các widget con
    def apply_colors_recursively(widget, current_bg_color, current_text_color):
        try:
            if hasattr(widget, 'configure'):
                if 'fg_color' in widget.configure().keys():
                    widget.configure(fg_color=current_bg_color)
                if 'text_color' in widget.configure().keys():
                    widget.configure(text_color=current_text_color)
        except Exception:
            # Bỏ qua các widget không có thuộc tính fg_color hoặc text_color
            pass
        
        for child in widget.winfo_children():
            apply_colors_recursively(child, current_bg_color, current_text_color)

    apply_colors_recursively(root, bg_color, text_color)

class MainWindow(ctk.CTkFrame):
    def __init__(self, parent, initial_focus: str = None):
        super().__init__(parent)
        try:
            logger.debug("Bắt đầu khởi tạo MainWindow...")
            self.parent = parent
            
            # Lấy màu nền và màu chữ ban đầu
            initial_bg_color = BACKGROUND_COLORS[get_time_of_day()]
            initial_text_color = TEXT_COLORS[get_time_of_day()]

            # Cập nhật màu nền ban đầu cho root window
            self.parent.configure(fg_color=initial_bg_color)

            # Đảm bảo cửa sổ luôn hiển thị trên cùng
            self.parent.attributes('-topmost', True)
            self.parent.lift()
            self.parent.focus_force()
            
            self.config = Config()
            self.db = DatabaseManager()
            self.db.log_app_launch()

            # Khởi tạo các service và controller
            logger.debug("Khởi tạo các service và controller...")
            self.scheduler = SchedulerService()
            self.weather_service = WeatherService(self.db)
            self.gemini_service = GeminiErrorCorrectionService()
            self.schedule_controller = ScheduleController(self.db, self._collect_facts)
            self.vscode_controller = VSCodeController(self.db, self._collect_facts)

            # Khởi tạo các thành phần hệ chuyên gia
            self.knowledge_base = KnowledgeBase()
            self.inference_engine = InferenceEngine(self.knowledge_base)
            self.rule_suggester = RuleSuggester(self.db, self.knowledge_base)

            # Thiết lập cửa sổ chính
            logger.debug("Thiết lập cửa sổ chính...")
            self.parent.title("My AI Assistant")
            self.parent.geometry("800x600")
            self.parent.resizable(False, False)

            # Tạo main frame để chứa các frame con
            logger.debug("Tạo main frame...")
            self.main_frame = ctk.CTkFrame(
                self,
                fg_color=initial_bg_color
            )
            self.main_frame.pack(fill="both", expand=True, padx=0, pady=0)

            # Cấu hình grid cho main_frame
            self.main_frame.grid_columnconfigure(0, weight=1)
            # Cấu hình tất cả các hàng với weight để chúng có thể mở rộng
            for i in range(4): # 4 hàng cho greeting, weather, schedule, vscode
                self.main_frame.grid_rowconfigure(i, weight=1)

            # Tạo một scrollable frame để chứa các frame con
            self.scrollable_frame = ctk.CTkScrollableFrame(self.main_frame)
            self.scrollable_frame.pack(fill="both", expand=True, padx=0, pady=0)

            # Cấu hình grid cho scrollable_frame
            self.scrollable_frame.grid_columnconfigure(0, weight=1)
            for i in range(7): # 7 hàng cho greeting, recommendation, weather, schedule, vscode, 2 nút
                self.scrollable_frame.grid_rowconfigure(i, weight=1)

            # Tạo các frame con
            self.create_frames()

            # Cập nhật màu nền định kỳ
            self.update_colors()

            # Chạy suy luận ngay khi khởi động
            logger.info("Khởi chạy hệ chuyên gia...")
            self._run_expert_system_inference()

        except Exception as e:
            logger.error(f"Lỗi khởi tạo MainWindow: {str(e)}")
            messagebox.showerror("Lỗi", f"Không thể khởi tạo ứng dụng: {str(e)}")

    def create_frames(self):
        """Tạo các frame con"""
        # Frame chào mừng
        self.greeting_frame = GreetingFrame(self.scrollable_frame)
        self.greeting_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=5)

        # Label hiển thị lời khuyên từ AI
        self.recommendation_label = ctk.CTkLabel(
            self.scrollable_frame,
            text="",
            font=("Montserrat", 14, "italic"),
            text_color="#FFD700", # Màu vàng sáng cho lời khuyên
            wraplength=700,
            justify="left",
            anchor="w" # Căn trái
        )
        self.recommendation_label.grid(row=1, column=0, sticky="ew", padx=10, pady=5)

        # Frame thời tiết
        self.weather_frame = WeatherFrame(self.scrollable_frame, self.weather_service)
        self.weather_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)

        # Frame thời khóa biểu
        self.schedule_frame = ScheduleFrame(self.scrollable_frame)
        self.schedule_frame.grid(row=3, column=0, sticky="nsew", padx=10, pady=5)

        # Frame VSCode
        self.vscode_frame = VSCodeFrame(self.scrollable_frame, self.db, self._collect_facts)
        self.vscode_frame.grid(row=4, column=0, sticky="nsew", padx=10, pady=5)

        # Nút để mở trình chỉnh sửa tri thức
        self.manage_knowledge_button = ctk.CTkButton(
            self.scrollable_frame,
            text="Quản lý Quy tắc Hệ chuyên gia",
            command=self._open_knowledge_editor,
            font=("Montserrat", 14, "bold"),
            fg_color="#5D3FD3", # Màu tím đậm
            hover_color="#6A5ACD" # Màu tím nhạt hơn khi hover
        )
        self.manage_knowledge_button.grid(row=5, column=0, sticky="ew", padx=10, pady=10)

        # Nút để mở khung đề xuất quy tắc
        self.suggest_rules_button = ctk.CTkButton(
            self.scrollable_frame,
            text="Đề Xuất Quy Tắc AI",
            command=self._open_knowledge_suggestion_editor,
            font=("Montserrat", 14, "bold"),
            fg_color="#007BFF", # Màu xanh dương
            hover_color="#0056B3"
        )
        self.suggest_rules_button.grid(row=6, column=0, sticky="ew", padx=10, pady=10)

    def _open_knowledge_editor(self):
        """Mở cửa sổ chỉnh sửa cơ sở tri thức."""
        KnowledgeEditorFrame(self.parent, self.knowledge_base)

    def _open_knowledge_suggestion_editor(self):
        """Mở cửa sổ đề xuất quy tắc."""
        KnowledgeSuggestionFrame(self.parent, self.rule_suggester, self.knowledge_base, self._run_expert_system_inference)

    def _run_expert_system_inference(self):
        """Thu thập dữ kiện, chạy suy luận và xử lý kết quả."""
        logger.debug("Bắt đầu chạy suy luận hệ chuyên gia...")
        
        facts = self._collect_facts()
        logger.debug(f"Facts thu thập được: {facts}")
        
        activated_actions = self.inference_engine.run_inference(facts)
        logger.debug(f"Các hành động được kích hoạt: {activated_actions}")

        if activated_actions:
            # Hiển thị lời khuyên trên giao diện
            recommendation_messages = []
            for action in activated_actions:
                if action["type"] == "recommendation":
                    recommendation_messages.append(f"{action['message']} (Quy tắc: {action['rule_description']})")
                elif action["type"] == "action":
                    if action["command"] == "open_vscode":
                        self.vscode_controller.open_vscode()
                    # Thêm các hành động khác nếu cần
            
            recommendation_text = "\n".join(recommendation_messages)
            logger.debug(f"Đang cập nhật recommendation_label với text: {recommendation_text}")
            
            # Đảm bảo label được cấu hình đúng
            self.recommendation_label.configure(
                text=recommendation_text,
                font=("Montserrat", 14, "italic"),
                text_color="#FFD700",
                wraplength=700,
                justify="left"
            )
            logger.debug("Đã cập nhật recommendation_label")
        else:
            logger.debug("Không có hành động nào được kích hoạt, xóa text cũ")
            self.recommendation_label.configure(text="")

        # Lên lịch chạy lại sau 1 phút
        self.parent.after(60000, self._run_expert_system_inference)

    def _collect_facts(self) -> dict:
        """Thu thập các dữ kiện hiện tại của hệ thống."""
        facts = {}
        logger.debug("Bắt đầu thu thập facts...")
        
        # Thu thập dữ kiện thời gian
        now = datetime.now()
        hour = now.hour
        day_of_week = now.strftime("%A") # Ví dụ: Monday, Tuesday
        logger.debug(f"Thời gian hiện tại: {now}, Giờ: {hour}, Ngày: {day_of_week}")
        
        if 5 <= hour < 12:
            facts["time_category"] = "morning"
        elif 12 <= hour < 17:
            facts["time_category"] = "afternoon"
        elif 17 <= hour < 22:
            facts["time_category"] = "evening"
        else:
            facts["time_category"] = "night"
        logger.debug(f"Phân loại thời gian: {facts['time_category']}")
        
        # Thêm ngày trong tuần vào facts
        facts["day_of_week"] = day_of_week
        logger.debug(f"Ngày trong tuần: {day_of_week}")

        # Thu thập dữ kiện thời tiết
        weather_data = self.weather_service.get_weather()
        if weather_data:
            facts["weather_condition"] = weather_data.get('description', '').lower()
            logger.debug(f"Dữ liệu thời tiết: {weather_data}")
            logger.debug(f"Điều kiện thời tiết: {facts['weather_condition']}")
        else:
            logger.warning("Không lấy được dữ liệu thời tiết")

        # Thu thập dữ kiện lịch trình
        schedule_data = self.schedule_controller.get_schedule_data()
        if schedule_data is not None and not schedule_data.empty:
            logger.debug(f"Dữ liệu lịch trình: {schedule_data}")
            today_schedule = schedule_data.get(day_of_week, pd.Series()).astype(str).str.lower()
            logger.debug(f"Lịch trình hôm nay ({day_of_week}): {today_schedule}")
            
            if "gym" in " ".join(today_schedule.tolist()):
                facts["schedule_activity"] = "Gym"
                logger.debug("Phát hiện hoạt động Gym trong lịch trình")
            
            is_empty_or_flexible = True
            for item in today_schedule:
                if item.strip() != "" and "nghỉ" not in item and "linh hoạt" not in item:
                    is_empty_or_flexible = False
                    break
            facts["schedule_empty_or_flexible"] = is_empty_or_flexible
            logger.debug(f"Lịch trình trống/linh hoạt: {is_empty_or_flexible}")
        else:
            logger.warning("Không lấy được dữ liệu lịch trình")

        # Thu thập dữ kiện trạng thái VSCode
        facts["vscode_status"] = "closed" # Placeholder
        logger.debug(f"Trạng thái VSCode: {facts['vscode_status']}")

        logger.debug(f"Tổng hợp tất cả facts: {facts}")
        return facts

    def update_colors(self):
        """Cập nhật màu nền định kỳ"""
        update_background_color(self.parent)
        self.parent.after(60000, self.update_colors)  # Cập nhật mỗi phút

def main():
    try:
        # Kiểm tra kết nối internet
        if not check_internet_connection():
            messagebox.showwarning("Cảnh báo", "Không có kết nối internet!")
            return

        # Quản lý file log
        manage_log_file()

        # Tạo cửa sổ chính
        root = ctk.CTk()
        app = MainWindow(root)
        app.pack(fill="both", expand=True)
        root.mainloop()

    except Exception as e:
        logger.error(f"Lỗi trong hàm main: {str(e)}")
        messagebox.showerror("Lỗi", f"Đã xảy ra lỗi: {str(e)}")

if __name__ == "__main__":
    main() 