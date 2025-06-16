import customtkinter as ctk
from tkinter import messagebox
import logging
import json

from models.knowledge_base import KnowledgeBase

logger = logging.getLogger(__name__)

class KnowledgeEditorFrame(ctk.CTkToplevel):
    def __init__(self, master, knowledge_base: KnowledgeBase):
        super().__init__(master)
        self.title("Quản lý Cơ sở Tri thức")
        self.geometry("900x700")
        self.knowledge_base = knowledge_base

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0) # For input section

        # --- Phần hiển thị quy tắc --- #
        self.rules_display_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.rules_display_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.rules_display_frame.grid_columnconfigure(0, weight=1)
        self.rules_display_frame.grid_rowconfigure(0, weight=1)

        self.rules_textbox = ctk.CTkTextbox(self.rules_display_frame, wrap="word", state="disabled", font=("Montserrat", 12))
        self.rules_textbox.grid(row=0, column=0, sticky="nsew")

        # --- Phần thêm quy tắc mới --- #
        self.add_rule_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.add_rule_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=10)
        self.add_rule_frame.grid_columnconfigure(0, weight=0)
        self.add_rule_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self.add_rule_frame, text="Tên quy tắc:", font=("Montserrat", 12, "bold")).grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.rule_name_entry = ctk.CTkEntry(self.add_rule_frame, width=200, font=("Montserrat", 12))
        self.rule_name_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=2)

        ctk.CTkLabel(self.add_rule_frame, text="Mô tả:", font=("Montserrat", 12, "bold")).grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.rule_description_entry = ctk.CTkEntry(self.add_rule_frame, font=("Montserrat", 12))
        self.rule_description_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=2)

        ctk.CTkLabel(self.add_rule_frame, text="Điều kiện (JSON):", font=("Montserrat", 12, "bold")).grid(row=2, column=0, sticky="nw", padx=5, pady=2)
        self.conditions_entry = ctk.CTkTextbox(self.add_rule_frame, height=80, font=("Montserrat", 12))
        self.conditions_entry.grid(row=2, column=1, sticky="ew", padx=5, pady=2)
        self.conditions_entry.insert("1.0", """
[
    {"fact": "example_fact", "operator": "==", "value": "example_value"}
]
""")

        ctk.CTkLabel(self.add_rule_frame, text="Hành động (JSON):", font=("Montserrat", 12, "bold")).grid(row=3, column=0, sticky="nw", padx=5, pady=2)
        self.actions_entry = ctk.CTkTextbox(self.add_rule_frame, height=80, font=("Montserrat", 12))
        self.actions_entry.grid(row=3, column=1, sticky="ew", padx=5, pady=2)
        self.actions_entry.insert("1.0", """
[
    {"type": "recommendation", "message": "This is a recommendation"},
    {"type": "action", "command": "do_something"}
]
""")

        self.add_rule_button = ctk.CTkButton(self.add_rule_frame, text="Thêm quy tắc", command=self._add_rule, font=("Montserrat", 14, "bold"))
        self.add_rule_button.grid(row=4, column=1, sticky="e", padx=5, pady=10)

        self._load_rules_to_display()

    def _load_rules_to_display(self):
        """Tải và hiển thị các quy tắc hiện có trong textbox."""
        self.rules_textbox.configure(state="normal")
        self.rules_textbox.delete("1.0", "end")
        
        rules = self.knowledge_base.get_rules()
        if not rules:
            self.rules_textbox.insert("end", "Chưa có quy tắc nào.")
            self.rules_textbox.configure(state="disabled")
            return

        for rule_name, rule_data in rules.items():
            self.rules_textbox.insert("end", f"Tên quy tắc: {rule_name}\n")
            self.rules_textbox.insert("end", f"  Mô tả: {rule_data.get('description', 'N/A')}\n")
            self.rules_textbox.insert("end", f"  Điều kiện: {json.dumps(rule_data.get('conditions', []), indent=2, ensure_ascii=False)}\n")
            self.rules_textbox.insert("end", f"  Hành động: {json.dumps(rule_data.get('actions', []), indent=2, ensure_ascii=False)}\n")
            self.rules_textbox.insert("end", "\n" + "-"*50 + "\n\n")
        
        self.rules_textbox.configure(state="disabled")
        logger.info("Displayed all current rules.")

    def _add_rule(self):
        """Xử lý việc thêm một quy tắc mới từ các trường nhập liệu."""
        rule_name = self.rule_name_entry.get().strip()
        description = self.rule_description_entry.get().strip()
        conditions_str = self.conditions_entry.get("1.0", "end").strip()
        actions_str = self.actions_entry.get("1.0", "end").strip()

        if not rule_name or not description or not conditions_str or not actions_str:
            messagebox.showwarning("Lỗi nhập liệu", "Vui lòng điền đầy đủ tất cả các trường.")
            return

        try:
            conditions = json.loads(conditions_str)
            actions = json.loads(actions_str)
        except json.JSONDecodeError as e:
            messagebox.showerror("Lỗi JSON", f"Định dạng JSON không hợp lệ: {e}")
            return

        rule_data = {
            "description": description,
            "conditions": conditions,
            "actions": actions
        }

        if self.knowledge_base.add_rule(rule_name, rule_data):
            messagebox.showinfo("Thành công", f"Đã thêm quy tắc '{rule_name}' vào cơ sở tri thức.")
            self._load_rules_to_display() # Cập nhật hiển thị
            # Xóa nội dung các trường nhập liệu sau khi thêm thành công
            self.rule_name_entry.delete(0, "end")
            self.rule_description_entry.delete(0, "end")
            self.conditions_entry.delete("1.0", "end")
            self.actions_entry.delete("1.0", "end")
        else:
            messagebox.showwarning("Thất bại", f"Quy tắc '{rule_name}' đã tồn tại hoặc có lỗi xảy ra.") 