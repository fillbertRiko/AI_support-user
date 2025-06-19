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
    # Không tạo log file, chỉ log ra console hoặc tắt hoàn toàn
    for handler in logging.getLogger().handlers[:]:
        handler.close()
        logging.getLogger().removeHandler(handler)
    # Nếu muốn tắt hoàn toàn:
    logging.disable(logging.CRITICAL)
    # Nếu muốn giữ log ra console, bỏ dòng trên và dùng StreamHandler ra sys.stdout

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

class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        try:
            # Khởi tạo database
            self.db = DatabaseManager(os.path.join('data', 'database', 'database.db'))
            
            # Khởi tạo các dịch vụ cơ bản
            self.weather_service = WeatherService(self.db)
            self.fact_collector = FactCollector(self.db, self.weather_service)
            
            # Khởi tạo knowledge base
            self.knowledge_base = KnowledgeBase()
            
            # Khởi tạo giao diện chính
            self._initialize_main_window()
            
            # Khởi tạo các dịch vụ và bộ điều khiển
            self._initialize_services()
            
            # Bắt đầu suy luận hệ chuyên gia
            self._run_expert_system_inference()
            
        except Exception as e:
            self.logger.error(f"Lỗi khởi tạo MainWindow: {str(e)}", exc_info=True)
            raise

    def _on_closing(self):
        """Xử lý khi đóng ứng dụng"""
        try:
            self.logger.info("Đang đóng ứng dụng...")
            
            # Dừng tất cả các timer và cập nhật
            try:
                self.after_cancel("all")
            except:
                pass
                
            # Đóng các kết nối database
            if hasattr(self, 'db') and self.db:
                try:
                    self.db.close()
                except Exception as e:
                    self.logger.warning(f"Lỗi khi đóng database: {e}")
            
            # Đóng các service
            if hasattr(self, 'weather_service') and self.weather_service:
                try:
                    self.weather_service.close()
                except Exception as e:
                    self.logger.warning(f"Lỗi khi đóng weather service: {e}")
            
            # Force quit nếu cần
            try:
                self.quit()
                self.destroy()
            except Exception as e:
                self.logger.error(f"Lỗi khi đóng window: {e}")
                # Force quit nếu destroy không hoạt động
                import sys
                sys.exit(0)
                
        except Exception as e:
            self.logger.error(f"Lỗi trong _on_closing: {e}")
            # Force quit nếu có lỗi
            import sys
            sys.exit(0)

    def _open_knowledge_editor(self):
        KnowledgeEditorFrame(self.scrollable_frame, self.db, self.knowledge_base, self.error_correction_service)

    def _open_knowledge_suggestion(self):
        KnowledgeSuggestionFrame(self.scrollable_frame, self.db, self.rule_suggester)

    def _run_expert_system_inference(self):
        """Chạy suy luận hệ chuyên gia"""
        try:
            self.logger.info("Bắt đầu suy luận hệ chuyên gia...")
            
            # Thu thập facts
            facts = self.fact_collector.collect_facts()
            self.logger.info(f"Các sự kiện thu thập được: {facts}")
            
            # Kiểm tra xem rule_suggester đã được khởi tạo chưa
            if self.rule_suggester is None:
                self.logger.warning("RuleSuggester chưa được khởi tạo, bỏ qua suy luận")
                return
                
            # Chạy suy luận
            recommendations = self.rule_suggester.infer_rules(facts)
            self.logger.info(f"Đề xuất: {recommendations}")
            
            # Cập nhật giao diện
            if recommendations:
                self.recommendation_label.configure(text="Đề xuất: " + ", ".join(recommendations))
            else:
                self.recommendation_label.configure(text="Không có đề xuất nào vào lúc này.")
                
        except Exception as e:
            self.logger.error(f"Lỗi khi chạy suy luận hệ chuyên gia: {e}", exc_info=True)
            self.recommendation_label.configure(text="Lỗi khi tạo đề xuất.")

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
        if self.winfo_exists():
            try:
                # Sử dụng màu sắc phù hợp với customtkinter theme
                # Không cần configure màu nền cho các frame chính vì đã có theme
                
                # Chỉ cập nhật màu chữ nếu cần
                if hasattr(self, 'recommendation_label') and self.recommendation_label.winfo_exists():
                    self.recommendation_label.configure(text_color=("gray10", "gray90"))

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
            self.logger.warning("MainWindow không tồn tại khi gọi update_colors.")

    def _initialize_main_window(self):
        """Khởi tạo cửa sổ chính và các thành phần UI"""
        try:
            # Thiết lập cửa sổ chính
            self.title("MyAI - Trợ lý thông minh")
            self.geometry("1400x900")
            self.minsize(1200, 700)
            
            # Cấu hình grid
            self.grid_columnconfigure(0, weight=1)
            self.grid_rowconfigure(0, weight=1)
            
            # Frame chính
            self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
            self.main_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
            self.main_frame.grid_columnconfigure(0, weight=1)
            self.main_frame.grid_rowconfigure(1, weight=1)
            
            # Tiêu đề
            self.label_title = ctk.CTkLabel(
                self.main_frame,
                text="MyAI - Trợ lý thông minh",
                font=("Montserrat", 24, "bold")
            )
            self.label_title.grid(row=0, column=0, pady=(0, 20), sticky="ew")
            
            # Frame có thể cuộn
            self.scrollable_frame = ctk.CTkScrollableFrame(
                self.main_frame,
                fg_color="transparent",
                width=1300,
                height=800
            )
            self.scrollable_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
            self.scrollable_frame.grid_columnconfigure(0, weight=1)
            
            # Khởi tạo các frame con
            self._initialize_frames()
            
            # Thiết lập protocol đóng
            self.protocol("WM_DELETE_WINDOW", self._on_closing)
            
        except Exception as e:
            self.logger.error(f"Lỗi khởi tạo giao diện chính: {e}", exc_info=True)
            raise

    def _initialize_frames(self):
        """Khởi tạo các frame con"""
        try:
            # Kiểm tra xem các frame đã được khởi tạo chưa
            if hasattr(self, 'greeting_frame') and self.greeting_frame is not None:
                self.logger.warning("GreetingFrame đã được khởi tạo, bỏ qua")
                return
            
            # Label đề xuất
            self.recommendation_label = ctk.CTkLabel(
                self.scrollable_frame,
                text="Đang tải đề xuất...",
                font=("Montserrat", 14, "italic"),
                text_color=("gray10", "gray90"),
                wraplength=1000,
                justify="left",
                anchor="w"
            )
            self.recommendation_label.grid(row=1, column=0, pady=(0, 20), sticky="ew")
                
            # Frame chào mừng
            self.greeting_frame = GreetingFrame(self.scrollable_frame)
            self.greeting_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)

            # Frame thời tiết
            self.weather_frame = WeatherFrame(self.scrollable_frame, self.weather_service)
            self.weather_frame.grid(row=4, column=0, sticky="nsew", padx=10, pady=5)
            
            # Frame lịch trình
            self.schedule_frame = ScheduleFrame(
                self.scrollable_frame, 
                self.db, 
                self.fact_collector
            )
            self.schedule_frame.grid(row=5, column=0, sticky="nsew", padx=10, pady=5)
            
            # Frame VSCode
            self.vscode_frame = VSCodeFrame(self.scrollable_frame, self.db, self.fact_collector)
            self.vscode_frame.grid(row=6, column=0, sticky="nsew", padx=10, pady=5)
            
            # Nút quản lý cơ sở tri thức
            self.manage_knowledge_button = ctk.CTkButton(
                self.scrollable_frame,
                text="Quản lý Cơ sở Tri thức",
                command=self._open_knowledge_editor,
                font=("Montserrat", 14, "bold"),
                fg_color="#6A5ACD",
                hover_color="#6A5ACD"
            )
            self.manage_knowledge_button.grid(row=7, column=0, sticky="ew", padx=10, pady=10)
            
            # Nút đề xuất quy tắc
            self.suggest_rules_button = ctk.CTkButton(
                self.scrollable_frame,
                text="Đề Xuất Quy Tắc Mới",
                command=self._open_knowledge_suggestion,
                font=("Montserrat", 14, "bold"),
                fg_color="#007ACC",
                hover_color="#0056B3"
            )
            self.suggest_rules_button.grid(row=8, column=0, sticky="ew", padx=10, pady=10)
            
        except Exception as e:
            self.logger.error(f"Lỗi khởi tạo các frame: {e}", exc_info=True)
            raise

    def _initialize_services(self):
        """Khởi tạo các dịch vụ và bộ điều khiển"""
        try:
            self.logger.info("Đang khởi tạo các dịch vụ và bộ điều khiển...")
            
            # Khởi tạo Error Correction Service
            self.error_correction_service = ErrorCorrectionService()
            
            # Khởi tạo Gemini Service
            self.gemini_service = GeminiErrorCorrectionService()
            
            # Khởi tạo Inference Engine
            self.inference_engine = InferenceEngine(self.knowledge_base)
            
            # Khởi tạo Rule Suggester
            self.rule_suggester = RuleSuggester(self.db, self.knowledge_base)
            
            # Khởi tạo Schedule Controller
            self.schedule_controller = ScheduleController(self.db, self.fact_collector)
            
            # Khởi tạo VSCode Controller
            self.vscode_controller = VSCodeController(self.db, self.fact_collector)
            
            self.logger.info("Đã khởi tạo tất cả các dịch vụ và bộ điều khiển")
            
        except Exception as e:
            self.logger.error(f"Lỗi khởi tạo services: {e}", exc_info=True)
            # Không raise exception để tránh crash ứng dụng

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
        # Không ghi log startup vào file nữa
        # logger.info("Khởi động ứng dụng MyAI...")
        
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

        # Thiết lập theme và màu sắc
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        try:
            logger.debug("Đang khởi tạo MainWindow...")
            app = MainWindow()
            
            # Thiết lập protocol để xử lý khi đóng cửa sổ
            app.protocol("WM_DELETE_WINDOW", app._on_closing)
            
            # Cập nhật màu sắc
            app.update_colors()
            
            # Bắt đầu cập nhật thời gian
            app._update_time()
            
            logger.info("Ứng dụng đã sẵn sàng!")
            
            # Chạy ứng dụng
            app.mainloop()

        except Exception as e:
            logger.error(f"Lỗi khởi tạo MainWindow: {str(e)}", exc_info=True)
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