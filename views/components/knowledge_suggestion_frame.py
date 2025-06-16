import customtkinter as ctk
import logging
from models.knowledge_base import KnowledgeBase
from tkinter import messagebox # Import messagebox
from datetime import datetime

logger = logging.getLogger(__name__)

class KnowledgeSuggestionFrame(ctk.CTkFrame):
    def __init__(self, parent, rule_suggester, knowledge_base, refresh_callback):
        super().__init__(parent)
        self.rule_suggester = rule_suggester
        self.knowledge_base = knowledge_base
        self.refresh_callback = refresh_callback
        self.suggested_rules = []

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure((0,1,2), weight=0) # Cho tiêu đề và nút
        self.grid_rowconfigure(3, weight=1) # Cho khu vực hiển thị quy tắc

        self.title_label = ctk.CTkLabel(self, text="Quy Tắc Đề Xuất", font=("Montserrat", 16, "bold"))
        self.title_label.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        self.suggest_button = ctk.CTkButton(
            self,
            text="Đề Xuất Quy Tắc Mới",
            command=self._suggest_rules,
            font=("Montserrat", 14, "bold"),
            fg_color="#28A745", # Màu xanh lá cây
            hover_color="#218838"
        )
        self.suggest_button.grid(row=1, column=0, padx=10, pady=5, sticky="ew")

        self.suggested_rules_frame = ctk.CTkScrollableFrame(self)
        self.suggested_rules_frame.grid(row=3, column=0, padx=10, pady=5, sticky="nsew")
        self.suggested_rules_frame.grid_columnconfigure(0, weight=1)

        self._display_suggested_rules()

    def _suggest_rules(self):
        """Gọi RuleSuggester để đề xuất quy tắc và cập nhật giao diện."""
        self.suggested_rules = self.rule_suggester.suggest_rules()
        self._display_suggested_rules()
        logger.info(f"Đã tìm thấy {len(self.suggested_rules)} quy tắc được đề xuất.")

    def _display_suggested_rules(self):
        """Hiển thị các quy tắc được đề xuất trong khung."""
        # Xóa các widget cũ
        for widget in self.suggested_rules_frame.winfo_children():
            widget.destroy()

        if not self.suggested_rules:
            no_rules_label = ctk.CTkLabel(self.suggested_rules_frame, text="Không có quy tắc nào được đề xuất hiện tại.", font=("Montserrat", 12, "italic"))
            no_rules_label.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
            return

        for i, rule in enumerate(self.suggested_rules):
            rule_frame = ctk.CTkFrame(self.suggested_rules_frame, border_width=1, border_color="#cccccc")
            rule_frame.grid(row=i, column=0, padx=5, pady=5, sticky="ew")
            rule_frame.grid_columnconfigure(0, weight=1) # Cho mô tả
            rule_frame.grid_columnconfigure(1, weight=0) # Cho nút chấp nhận

            description_label = ctk.CTkLabel(
                rule_frame,
                text=f"Đề xuất: {rule['description']}",
                font=("Montserrat", 12),
                wraplength=400,
                justify="left"
            )
            description_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")

            accept_button = ctk.CTkButton(
                rule_frame,
                text="Chấp Nhận",
                command=lambda r=rule: self._accept_rule(r),
                font=("Montserrat", 12, "bold"),
                fg_color="#17A2B8", # Màu xanh
                hover_color="#138496"
            )
            accept_button.grid(row=0, column=1, padx=10, pady=5, sticky="e")

    def _accept_rule(self, rule_data):
        """Chấp nhận quy tắc được đề xuất và thêm vào cơ sở tri thức."""
        # Sử dụng một cách tạo tên quy tắc duy nhất hơn
        rule_name = f"suggested_rule_{datetime.now().strftime("%Y%m%d%H%M%S%f")}" 
        if self.knowledge_base.add_rule(rule_name, rule_data):
            logger.info(f"Đã thêm quy tắc mới: {rule_name}")
            messagebox.showinfo("Thành công", f"Đã thêm quy tắc '{rule_data['description']}' vào cơ sở tri thức.")
            # Xóa quy tắc đã chấp nhận khỏi danh sách đề xuất
            self.suggested_rules = [r for r in self.suggested_rules if r != rule_data]
            self._display_suggested_rules() # Cập nhật lại hiển thị
            if self.refresh_callback: # Cập nhật giao diện chính sau khi thêm quy tắc
                self.refresh_callback()
        else:
            logger.warning(f"Không thể thêm quy tắc {rule_name}. Có thể đã tồn tại.")
            messagebox.showerror("Lỗi", f"Không thể thêm quy tắc. Có thể đã tồn tại hoặc có lỗi.") 