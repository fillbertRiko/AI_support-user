import customtkinter as ctk
import logging
import pandas as pd
from controllers.schedule_controller import ScheduleController
from tkinter import messagebox

logger = logging.getLogger(__name__)

class ScheduleFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.parent = parent
        self.controller = ScheduleController()
        self.grid_columnconfigure(0, weight=1) # Cấu hình cột chính để mở rộng
        self.grid_rowconfigure(0, weight=1)    # Cấu hình hàng chính để mở rộng
        
        # Tạo các widget
        self.create_widgets()
        
    def create_widgets(self):
        """Tạo các widget cho frame"""
        # Label tiêu đề
        self.title_label = ctk.CTkLabel(
            self,
            text="Thời Khóa Biểu",
            font=("Montserrat", 20, "bold")
        )
        self.title_label.grid(row=0, column=0, columnspan=8, pady=10, sticky="ew") # Căn giữa tiêu đề
        
        # Nút mở file (Tạm thời bỏ qua vì dữ liệu hardcode)
        # self.open_button = ctk.CTkButton(
        #     self,
        #     text="Mở File Thời Khóa Biểu",
        #     command=self.open_schedule
        # )
        # self.open_button.pack(pady=5)
        
        # Frame chứa bảng thời khóa biểu
        self.table_frame = ctk.CTkFrame(self, fg_color="#2b2b2b") # Màu nền tối cho bảng
        self.table_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        
        # Cấu hình grid cho table_frame
        for i in range(8): # 8 cột: Thời gian + 7 ngày
            self.table_frame.grid_columnconfigure(i, weight=1)
        for i in range(6): # 6 hàng: Tiêu đề + 5 khung thời gian
            self.table_frame.grid_rowconfigure(i, weight=1)

        # Hiển thị dữ liệu
        self.display_schedule()
        
    def open_schedule(self):
        """Mở file thời khóa biểu - Không sử dụng khi hardcode data"""
        messagebox.showinfo("Thông báo", "Tính năng mở file đang tạm thời vô hiệu hóa (dữ liệu hardcode).")
            
    def display_schedule(self):
        """Hiển thị dữ liệu thời khóa biểu"""
        schedule_data = self.controller.get_schedule_data()
        if schedule_data is not None and not schedule_data.empty:
            # Xóa các widget cũ trong table_frame
            for widget in self.table_frame.winfo_children():
                widget.destroy()
                
            # Tiêu đề cột
            headers = ['Thời gian'] + list(schedule_data.columns[1:])
            for j, col_name in enumerate(headers):
                header_label = ctk.CTkLabel(
                    self.table_frame,
                    text=col_name,
                    font=("Montserrat", 14, "bold"),
                    fg_color="#333333", # Màu nền cho tiêu đề
                    text_color="#ffffff",
                    corner_radius=5
                )
                header_label.grid(row=0, column=j, padx=1, pady=1, sticky="nsew")
                
            # Dữ liệu bảng
            for i, (index, row_data) in enumerate(schedule_data.iterrows()):
                # Cột Thời gian (index)
                time_label = ctk.CTkLabel(
                    self.table_frame,
                    text=row_data['Thời gian'],
                    font=("Montserrat", 12, "bold"),
                    fg_color="#333333", # Màu nền cho cột thời gian
                    text_color="#ffffff",
                    corner_radius=5
                )
                time_label.grid(row=i+1, column=0, padx=1, pady=1, sticky="nsew")
                
                # Các cột dữ liệu còn lại (Thứ 2 đến Chủ Nhật)
                for j, col_name in enumerate(schedule_data.columns[1:]):
                    value = str(row_data[col_name])
                    
                    # Xác định màu nền và font cho từng ô
                    bg_color = "#444444" # Màu nền mặc định cho ô dữ liệu
                    text_color = "#ffffff" # Màu chữ mặc định
                    font_weight = "normal"

                    if "Gym" in value or "Đang đi làm" in value or "Dự án nhỏ" in value or "Ôn tập" in value or "Buffer" in value:
                        bg_color = "#556B2F" # Màu xanh olive đậm cho các hoạt động đặc biệt
                        font_weight = "bold"
                    
                    cell_label = ctk.CTkLabel(
                        self.table_frame,
                        text=value,
                        font=("Montserrat", 12, font_weight),
                        fg_color=bg_color,
                        text_color=text_color,
                        wraplength=120, # Giới hạn chiều rộng cho nội dung ô
                        justify="center",
                        corner_radius=5
                    )
                    cell_label.grid(row=i+1, column=j+1, padx=1, pady=1, sticky="nsew")
        else:
            # Hiển thị thông báo nếu không có dữ liệu
            no_data_label = ctk.CTkLabel(
                self.table_frame,
                text="Không có dữ liệu thời khóa biểu để hiển thị.",
                font=("Montserrat", 16)
            )
            no_data_label.pack(expand=True, fill="both") 