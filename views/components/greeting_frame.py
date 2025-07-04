import customtkinter as ctk
from datetime import datetime
import logging
import time
from services.update_optimizer_service import UpdateOptimizerService
from services.error_correction_service import ErrorCorrectionService

logger = logging.getLogger(__name__)

class GreetingFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.parent = parent
        self.logger = logging.getLogger(__name__)
        self.logger.debug("Khởi tạo GreetingFrame...")
        self.update_optimizer = UpdateOptimizerService()
        self.error_correction_service = ErrorCorrectionService()
        self.last_greeting = None
        self.last_update_time = None
        self.user_interaction = False
        
        # Tạo frame chính với hiệu ứng gradient
        self.main_frame = ctk.CTkFrame(
            self,
            fg_color=("gray90", "gray13"),  # Màu sáng/tối tùy theme
            corner_radius=15
        )
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Tạo frame cho lời chào với hiệu ứng shadow
        self.greeting_container = ctk.CTkFrame(
            self.main_frame,
            fg_color=("gray85", "gray15"),
            corner_radius=10
        )
        self.greeting_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Tạo đường kẻ trên với gradient
        self.top_line = ctk.CTkFrame(
            self.greeting_container,
            height=2,
            fg_color=("gray70", "gray30")
        )
        self.top_line.pack(fill="x", padx=20, pady=(10, 5))
        
        # Label cho lời chào với font đẹp hơn
        self.greeting_label = ctk.CTkLabel(
            self.greeting_container,
            text="",
            font=("Montserrat", 24, "bold"),
            text_color=("gray20", "gray90"),
            anchor="center",
            wraplength=600
        )
        self.greeting_label.pack(fill="x", padx=20, pady=5)
        
        # Label cho thời gian với hiệu ứng số lớn
        self.time_label = ctk.CTkLabel(
            self.greeting_container,
            text="",
            font=("Montserrat", 48, "bold"),
            text_color=("gray20", "gray90"),
            anchor="center"
        )
        self.time_label.pack(fill="x", padx=20, pady=5)
        
        # Tạo đường kẻ dưới với gradient
        self.bottom_line = ctk.CTkFrame(
            self.greeting_container,
            height=2,
            fg_color=("gray70", "gray30")
        )
        self.bottom_line.pack(fill="x", padx=20, pady=(5, 10))
        
        # Thêm hiệu ứng hover cho frame
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        
        logger.debug("Cập nhật lời chào và thời gian lần đầu...")
        self.update_greeting()
        self.update_time()
        self.schedule_updates()
        logger.debug("Khởi tạo GreetingFrame hoàn tất.")

    def _on_enter(self, event):
        """Hiệu ứng khi hover vào frame"""
        self.main_frame.configure(fg_color=("gray85", "gray15"))
        
    def _on_leave(self, event):
        """Hiệu ứng khi rời khỏi frame"""
        self.main_frame.configure(fg_color=("gray90", "gray13"))

    def get_greeting(self):
        """Lấy lời chào dựa trên thời gian trong ngày"""
        hour = datetime.now().hour
        
        if 5 <= hour < 12:
            return "Chào buổi sáng Dương Huy!"
        elif 12 <= hour < 18:
            return "Chào buổi chiều Dương Huy!"
        else:
            return "Chào buổi tối Dương Huy!"
            
    def update_greeting(self):
        """Cập nhật lời chào"""
        try:
            start_time = time.time()
            
            greeting = self.get_greeting()
            
            # Kiểm tra xem dữ liệu có thay đổi không
            data_changed = self.last_greeting != greeting
            
            # Tính thời gian phản hồi
            response_time = time.time() - start_time
            
            # Ghi lại thông tin cập nhật
            self.update_optimizer.log_update(
                service_type='greeting',
                data_changed=data_changed,
                user_interaction=self.user_interaction,
                response_time=response_time
            )
            
            # Reset user interaction flag
            self.user_interaction = False
            
            # Cập nhật giao diện
            self.greeting_label.configure(text=greeting)
            self.logger.debug(f"Cập nhật greeting_label với text: {greeting}")
            
            # Lưu dữ liệu hiện tại
            self.last_greeting = greeting
            self.last_update_time = time.time()
            
        except Exception as e:
            self.greeting_label.configure(text="Lỗi:")
            print(f"Error updating greeting: {str(e)}")
            # Ghi log lỗi
            self.error_correction_service.log_error(
                service='greeting',
                error_type='RUNTIME_ERROR',
                error_message=str(e),
                context="An unexpected error occurred during greeting update."
            )

        # Lấy thời gian cập nhật tối ưu
        optimal_interval = self.update_optimizer.get_optimal_interval('greeting')
        
        # Cập nhật sau khoảng thời gian tối ưu
        self.after(optimal_interval * 1000, self.update_greeting)

    def update_time(self):
        """Cập nhật thời gian"""
        current_time = datetime.now().strftime("%H:%M:%S")
        self.time_label.configure(text=current_time)
        # Chỉ log khi thời gian thay đổi phút
        if current_time.endswith(":00"):
            self.logger.debug(f"Cập nhật time_label với text: {current_time}")
        # Lên lịch cập nhật thời gian mỗi giây
        self.after(1000, self.update_time)

    def schedule_updates(self):
        """Lên lịch cập nhật lời chào"""
        self.update_greeting()
        # Lên lịch cập nhật lời chào mỗi giờ
        self.after(3600000, self.schedule_updates)