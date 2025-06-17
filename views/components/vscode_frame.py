import customtkinter as ctk
from tkinter import messagebox
import pandas as pd
from controllers.vscode_controller import VSCodeController

class VSCodeFrame(ctk.CTkFrame):
    def __init__(self, parent, db, fact_collector):
        super().__init__(parent, fg_color="transparent")
        self.parent = parent
        self.controller = VSCodeController(db, fact_collector)
        
        # Tạo các widget
        self.create_widgets()
        
    def create_widgets(self):
        """Tạo các widget cho frame"""
        # Label tiêu đề
        self.title_label = ctk.CTkLabel(
            self,
            text="Cài Đặt VSCode",
            font=("Montserrat", 20, "bold")
        )
        self.title_label.pack(pady=10)
        
        # Nút mở VSCode
        self.open_button = ctk.CTkButton(
            self,
            text="Mở VSCode",
            command=self.open_vscode,
            font=("Montserrat", 14, "bold")
        )
        self.open_button.pack(pady=5)
        
        # Frame chứa bảng cài đặt
        self.table_frame = ctk.CTkFrame(self)
        self.table_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Hiển thị dữ liệu
        self.display_settings()

    def open_vscode(self):
        """Mở VSCode"""
        if not self.controller.open_vscode():
            messagebox.showerror("Lỗi", "Không thể mở VSCode")
            
    def display_settings(self):
        """Hiển thị cài đặt VSCode"""
        settings_data = self.controller.get_settings()
        if settings_data is not None:
            # Xóa các widget cũ trong table_frame
            for widget in self.table_frame.winfo_children():
                widget.destroy()
                
            # Tạo bảng mới
            for i, col in enumerate(settings_data.columns):
                label = ctk.CTkLabel(
                    self.table_frame,
                    text=col,
                    font=("Montserrat", 12, "bold")
                )
                label.grid(row=0, column=i, padx=5, pady=5)
                
            for i, row in settings_data.iterrows():
                for j, value in enumerate(row):
                    label = ctk.CTkLabel(
                        self.table_frame,
                        text=str(value),
                        font=("Montserrat", 12)
                    )
                    label.grid(row=i+1, column=j, padx=5, pady=5)