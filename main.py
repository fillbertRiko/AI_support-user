import os
import customtkinter as ctk
from tkinter import messagebox, TclError
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
from services.error_correction_service import ErrorCorrectionService
from services.fact_collector import FactCollector

# Thiết lập logging
def setup_logging():
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        
    log_file = os.path.join(log_dir, "app.log")
    
    # Đóng tất cả handlers hiện tại
    for handler in logging.getLogger().handlers[:]:
        handler.close()
        logging.getLogger().removeHandler(handler)
    
    # Thiết lập logging mới với encoding UTF-8
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8', mode='a'),
            # Sử dụng StreamHandler với encoding UTF-8 cho console
            logging.StreamHandler(open(os.devnull, 'w', encoding='utf-8'))
        ]
    )

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

def get_time_of_day():
    """Xác định thời gian trong ngày dựa trên giờ hiện tại"""
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
    """Cập nhật màu nền của cửa sổ dựa trên thời gian"""
    time_category = get_time_of_day()
    bg_color = BACKGROUND_COLORS[time_category]
    text_color = TEXT_COLORS[time_category]
    
    # Cập nhật màu nền cho root window
    root.configure(fg_color=bg_color)
    
    # Cập nhật màu chữ cho tất cả các widget con
    for widget in root.winfo_children():
        if isinstance(widget, (ctk.CTkLabel, ctk.CTkButton)):
            widget.configure(text_color=text_color)

class MainWindow(ctk.CTkFrame):
    def __init__(self, root, loading_window=None, loading_label=None, progress_bar=None):
        super().__init__(root)
        self.root = root
        self.loading_window = loading_window
        self.loading_label = loading_label
        self.progress_bar = progress_bar
        self.logger = logging.getLogger(__name__)

        # Khởi tạo các biến cho các frame và controller để tránh AttributeError
        self.db = None
        self.weather_service = None
        self.error_correction_service = None
        self.gemini_service = None
        self.greeting_frame = None
        self.weather_frame = None
        self.schedule_frame = None
        self.vscode_frame = None
        self.schedule_controller = None
        self.vscode_controller = None
        self.knowledge_base = None
        self.inference_engine = None
        self.rule_suggester = None
        self.recommendation_label = None
        self.manage_knowledge_button = None
        self.suggest_rules_button = None
        self.fact_collector = None

        try:
            # Giai đoạn 1: Khởi tạo các dịch vụ thiết yếu cần thiết cho UI ngay lập tức
            self._update_loading("Đang khởi tạo cơ sở dữ liệu...", 0.1)
            self.db = DatabaseManager()

            self._update_loading("Đang khởi tạo Weather Service...", 0.2)
            self.weather_service = WeatherService(self.db)
            
            self._update_loading("Đang khởi tạo Fact Collector...", 0.25)
            self.fact_collector = FactCollector(self.db)

            # Giai đoạn 2: Khởi tạo cửa sổ chính và các thành phần UI (trì hoãn)
            self.after(100, self._update_loading, "Đang khởi tạo giao diện chính...", 0.3)
            self.after(200, self._initialize_main_window)
            
            self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

        except Exception as e:
            self.logger.error(f"Lỗi khởi tạo MainWindow: {str(e)}", exc_info=True)
            if self.loading_window and self.loading_window.winfo_exists():
                self.loading_window.destroy()
            raise

    def _on_closing(self):
        if self.db:
            self.db.close_all()
        self.destroy()

    def _update_loading(self, message, progress):
        if self.loading_label.winfo_exists(): # Check if widget still exists
            try:
                self.progress_bar.set(progress)
                self.loading_label.configure(text=message)
                self.update_idletasks()
            except TclError as e:
                self.logger.warning(f"TclError during _update_loading: {e} - widget might have been destroyed.")
            except Exception as e:
                self.logger.error(f"Error in _update_loading: {e}", exc_info=True)

    def _open_knowledge_editor(self):
        KnowledgeEditorFrame(self.scrollable_frame, self.db, self.knowledge_base, self.error_correction_service)

    def _open_knowledge_suggestion_editor(self):
        KnowledgeSuggestionFrame(self.scrollable_frame, self.db, self.rule_suggester)

    def _run_expert_system_inference(self):
        try:
            self.logger.info("Bắt đầu suy luận hệ chuyên gia...")
            facts = self.fact_collector.collect_facts()
            self.logger.info(f"Các sự kiện thu thập được: {facts}")

            recommendations = self.rule_suggester.infer_rules(facts)
            self.logger.info(f"Đề xuất: {recommendations}")

            if recommendations:
                self.recommendation_label.config(text="Đề xuất: " + ", ".join(recommendations))
            else:
                self.recommendation_label.config(text="Không có đề xuất nào vào lúc này.")
        except Exception as e:
            self.logger.error(f"Lỗi khi chạy suy luận hệ chuyên gia: {e}", exc_info=True)
            messagebox.showerror("Lỗi Suy Luận", f"Đã xảy ra lỗi khi chạy suy luận hệ chuyên gia: {e}")

    def _update_time(self):
        if self.greeting_frame.winfo_exists():
            try:
                self.greeting_frame.update_time()
                # Only log time if minute changes
                current_minute = datetime.now().minute
                if not hasattr(self, '_last_logged_minute') or self._last_logged_minute != current_minute:
                    self.logger.info(f"Cập nhật thời gian: {datetime.now().strftime('%H:%M:%S')}")
                    self._last_logged_minute = current_minute
                self.after(1000, self._update_time) # Update every second
            except TclError as e:
                self.logger.warning(f"TclError during _update_time: {e} - widget might have been destroyed.")
            except Exception as e:
                self.logger.error(f"Error in _update_time: {e}", exc_info=True)
        else:
            self.logger.warning("greeting_frame không tồn tại khi gọi _update_time.")

    def update_colors(self):
        if self.root.winfo_exists():
            try:
                # Update colors of all frames/widgets that need it
                self.main_frame.config(bg='#f0f0f0') # Example color
                self.scrollable_frame.config(bg='#f0f0f0') # Example color
                self.label_title.config(bg='#f0f0f0', fg='#333333')
                if self.recommendation_label.winfo_exists():
                    self.recommendation_label.config(bg='#f0f0f0', fg='#333333')

                # Update child frames if they have an update_colors method
                for frame in [self.greeting_frame, self.weather_frame, self.schedule_frame, self.vscode_frame]:
                    if frame and hasattr(frame, 'update_colors') and frame.winfo_exists():
                        frame.update_colors()

                self.logger.info("Màu sắc giao diện được cập nhật.")
                # Schedule next update if needed, e.g., for dynamic themes
                # self.after(60000, self.update_colors) # Example: update every minute

            except TclError as e:
                self.logger.warning(f"TclError during update_colors: {e} - widget might have been destroyed.")
            except Exception as e:
                self.logger.error(f"Error in update_colors: {e}", exc_info=True)
        else:
            self.logger.warning("root không tồn tại khi gọi update_colors.")

    def _initialize_main_window(self):
        try:
            self._update_loading("Thiết lập cửa sổ chính...", 0.4)
            self.root.title("My AI Assistant")
            self.root.geometry("800x600")
            self.root.resizable(False, False)

            self.main_frame = ctk.CTkFrame(self)
            self.main_frame.pack(fill="both", expand=True)

            self.scrollable_frame = ctk.CTkScrollableFrame(self.main_frame)
            self.scrollable_frame.pack(fill="both", expand=True)

            # Khởi tạo các thành phần UI
            self._initialize_ui_components()

            self._update_loading("Hoàn tất khởi tạo UI...", 0.7)
            
            # Giai đoạn 3: Khởi tạo các dịch vụ và bộ điều khiển còn lại (trì hoãn thêm)
            self.after(10, self._initialize_services_deferred)

        except Exception as e:
            self.logger.error(f"Lỗi trong _initialize_main_window: {e}", exc_info=True)
            if self.loading_window and self.loading_window.winfo_exists():
                self.loading_window.destroy()

    def _initialize_ui_components(self):
        self._update_loading("Đang tạo frame chào mừng...", 0.5)
        self.greeting_frame = GreetingFrame(self.scrollable_frame)
        self.greeting_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=5)

        self._update_loading("Đang tạo khung đề xuất...", 0.55)
        self.recommendation_label = ctk.CTkLabel(
            self.scrollable_frame,
            text="",
            font=("Montserrat", 14, "italic"),
            text_color="#FFD700",
            wraplength=700,
            justify="left",
            anchor="w"
        )
        self.recommendation_label.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        
        self._update_loading("Đang tạo frame thời tiết...", 0.6)
        self.weather_frame = WeatherFrame(self.scrollable_frame, self.weather_service)
        self.weather_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)
        
        self._update_loading("Đang tạo frame lịch trình...", 0.65)
        self.schedule_frame = ScheduleFrame(
            self.scrollable_frame,
            self.db,
            self.fact_collector
        )
        self.schedule_frame.grid(row=3, column=0, sticky="nsew", padx=10, pady=5)
        
        self._update_loading("Đang tạo frame VSCode...", 0.68)
        self.vscode_frame = VSCodeFrame(self.scrollable_frame, self.db, self.fact_collector)
        self.vscode_frame.grid(row=4, column=0, sticky="nsew", padx=10, pady=5)
        
        self._update_loading("Đang tạo các nút điều khiển...", 0.69)
        self.manage_knowledge_button = ctk.CTkButton(
            self.scrollable_frame,
            text="Quản lý Quy tắc Hệ chuyên gia",
            command=self._open_knowledge_editor,
            font=("Montserrat", 14, "bold"),
            fg_color="#5D3FD3",
            hover_color="#6A5ACD"
        )
        self.manage_knowledge_button.grid(row=5, column=0, sticky="ew", padx=10, pady=10)
        
        self._update_loading("Đang tạo nút đề xuất quy tắc...", 0.69)
        self.suggest_rules_button = ctk.CTkButton(
            self.scrollable_frame,
            text="Đề Xuất Quy Tắc AI",
            command=self._open_knowledge_suggestion_editor,
            font=("Montserrat", 14, "bold"),
            fg_color="#007BFF",
            hover_color="#0056B3"
        )
        self.suggest_rules_button.grid(row=6, column=0, sticky="ew", padx=10, pady=10)

    def _initialize_services_deferred(self):
        try:
            self._update_loading("Đang khởi tạo các dịch vụ còn lại...", 0.75)
            self.error_correction_service = ErrorCorrectionService()
            self.gemini_service = GeminiErrorCorrectionService()
            
            self._update_loading("Đang khởi tạo Schedule Controller...", 0.8)
            self.schedule_controller = ScheduleController(self.db, self.fact_collector)
            
            self._update_loading("Đang khởi tạo VSCode Controller...", 0.85)
            self.vscode_controller = VSCodeController(self.db, self.fact_collector)
            
            self._update_loading("Đang khởi tạo hệ chuyên gia...", 0.9)
            self.knowledge_base = KnowledgeBase()
            self.inference_engine = InferenceEngine(self.knowledge_base)
            self.rule_suggester = RuleSuggester(self.db, self.knowledge_base)
            
            self._update_loading("Hoàn tất khởi tạo dịch vụ...", 1.0)

            # Bây giờ mọi thứ đã được khởi tạo, hãy chạy suy luận và bắt đầu cập nhật định kỳ
            self._run_expert_system_inference()
            self._update_time()
            self.update_colors()

            # Đóng loading window nếu có
            if self.loading_window and self.loading_window.winfo_exists():
                self.loading_window.destroy()
                self.loading_window = None
                self.loading_label = None
                self.progress_bar = None

        except Exception as e:
            self.logger.error(f"Lỗi trong _initialize_services_deferred: {e}", exc_info=True)
            if self.loading_window and self.loading_window.winfo_exists():
                self.loading_window.destroy()

def check_internet_connection():
    """Kiểm tra kết nối internet"""
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except OSError:
        return False

def main():
    try:
        # Thiết lập logging
        setup_logging()
        logger = logging.getLogger(__name__)
        
        # Ghi log startup vào file riêng với encoding UTF-8
        with open("startup_log.txt", "a", encoding="utf-8") as f:
            f.write(f"{datetime.now()} - Starting MyAI application.\n")
        
        logger.info("Khởi động ứng dụng MyAI...")
        
        # Kiểm tra kết nối internet
        if not check_internet_connection():
            logger.warning("Không có kết nối internet!")
            messagebox.showwarning("Cảnh báo", "Không có kết nối internet! Một số tính năng có thể không hoạt động.")

        # Kiểm tra và tạo các thư mục cần thiết
        required_dirs = ['logs', 'data/database', 'data/excel', 'data/cache']
        for dir_path in required_dirs:
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
                logger.info(f"Đã tạo thư mục: {dir_path}")

        # Tạo cửa sổ chính
        logger.debug("Đang tạo cửa sổ chính...")
        root = ctk.CTk()
        
        # Thiết lập theme và màu sắc
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Tạo và hiển thị loading window
        loading_window = ctk.CTkToplevel(root)
        loading_window.title("Đang tải...")
        loading_window.geometry("400x200")
        loading_window.transient(root)
        loading_window.grab_set()
        
        # Căn giữa loading window
        loading_window.update_idletasks()
        width = loading_window.winfo_width()
        height = loading_window.winfo_height()
        x = (loading_window.winfo_screenwidth() // 2) - (width // 2)
        y = (loading_window.winfo_screenheight() // 2) - (height // 2)
        loading_window.geometry(f'{width}x{height}+{x}+{y}')
        
        # Thêm label loading
        loading_label = ctk.CTkLabel(
            loading_window,
            text="Đang khởi tạo ứng dụng...",
            font=("Montserrat", 14)
        )
        loading_label.pack(pady=20)
        
        # Thêm progress bar
        progress_bar = ctk.CTkProgressBar(loading_window)
        progress_bar.pack(pady=10, padx=20, fill="x")
        progress_bar.set(0)
        
        # Cập nhật UI
        loading_window.update()
        
        try:
            logger.debug("Đang khởi tạo MainWindow...")
            app = MainWindow(root, loading_window, loading_label, progress_bar)
            app.pack(fill="both", expand=True)
            
            # Chạy ứng dụng
            logger.info("Ứng dụng đã sẵn sàng!")
            root.mainloop()
            
        except Exception as e:
            logger.error(f"Lỗi khởi tạo MainWindow: {str(e)}", exc_info=True)
            if loading_window.winfo_exists():
                loading_window.destroy()
            messagebox.showerror("Lỗi", f"Không thể khởi tạo ứng dụng: {str(e)}")
            sys.exit(1)
        
    except Exception as e:
        logger.error(f"Lỗi trong hàm main: {str(e)}", exc_info=True)
        messagebox.showerror("Lỗi", f"Không thể khởi động ứng dụng: {str(e)}")
        sys.exit(1)
    finally:
        logger.info("Đóng ứng dụng MyAI...")

if __name__ == "__main__":
    main() 