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

        # Phần đánh giá code Gemini
        self.code_review_label = ctk.CTkLabel(
            self,
            text="Đánh Giá Mã với Gemini",
            font=("Montserrat", 16, "bold")
        )
        self.code_review_label.pack(pady=10)

        self.code_input_textbox = ctk.CTkTextbox(
            self,
            height=150,
            font=("Montserrat", 12)
        )
        self.code_input_textbox.pack(fill="x", padx=10, pady=5)
        self.code_input_textbox.insert("0.0", "Dán mã của bạn vào đây để được Gemini đánh giá...")

        self.review_button = ctk.CTkButton(
            self,
            text="Đánh Giá Mã",
            command=self.review_code,
            font=("Montserrat", 14, "bold"),
            fg_color="#28A745", # Màu xanh lá cây
            hover_color="#218838"
        )
        self.review_button.pack(pady=5)

        self.review_output_textbox = ctk.CTkTextbox(
            self,
            height=200,
            font=("Montserrat", 12),
            state="disabled" # Make it read-only initially
        )
        self.review_output_textbox.pack(fill="x", padx=10, pady=5)

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

    def review_code(self):
        """Gửi mã đi để được đánh giá bởi Gemini"""
        code_to_review = self.code_input_textbox.get("1.0", "end-1c")
        if not code_to_review or code_to_review.strip() == "Dán mã của bạn vào đây để được Gemini đánh giá...":
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập mã để đánh giá.")
            return
        
        self.review_output_textbox.configure(state="normal")
        self.review_output_textbox.delete("1.0", "end")
        self.review_output_textbox.insert("1.0", "Đang gửi mã đến Gemini để đánh giá... Vui lòng chờ.")
        self.review_output_textbox.configure(state="disabled")
        
        # Run the review in a separate thread to prevent UI freezing
        # For simplicity, directly call here. In a real app, use threading/async.
        try:
            review_result = self.controller.review_code_with_gemini(code_to_review)
            self.review_output_textbox.configure(state="normal")
            self.review_output_textbox.delete("1.0", "end")
            self.review_output_textbox.insert("1.0", review_result)
            self.review_output_textbox.configure(state="disabled")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Có lỗi xảy ra khi đánh giá mã: {str(e)}")
            self.review_output_textbox.configure(state="normal")
            self.review_output_textbox.delete("1.0", "end")
            self.review_output_textbox.insert("1.0", "Không thể đánh giá mã. Vui lòng thử lại.")
            self.review_output_textbox.configure(state="disabled") 