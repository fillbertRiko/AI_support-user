import logging
import sqlite3
from datetime import datetime
from typing import Optional

class ErrorService:
    def __init__(self):
        self.db_path = "data/errors.db"
        self._init_db()
        
    def _init_db(self):
        """Khởi tạo cơ sở dữ liệu nếu chưa tồn tại"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Tạo bảng errors nếu chưa tồn tại
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS errors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    error_message TEXT NOT NULL,
                    error_type TEXT,
                    stack_trace TEXT,
                    context TEXT
                )
            ''')
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logging.error(f"Lỗi khi khởi tạo cơ sở dữ liệu: {str(e)}")
    
    def log_error(self, error_message: str, error_type: Optional[str] = None, 
                 stack_trace: Optional[str] = None, context: Optional[str] = None):
        """
        Ghi log lỗi vào cơ sở dữ liệu
        
        Args:
            error_message (str): Thông báo lỗi
            error_type (str, optional): Loại lỗi
            stack_trace (str, optional): Stack trace của lỗi
            context (str, optional): Ngữ cảnh xảy ra lỗi
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Ghi log lỗi vào cơ sở dữ liệu
            cursor.execute('''
                INSERT INTO errors (timestamp, error_message, error_type, stack_trace, context)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                error_message,
                error_type,
                stack_trace,
                context
            ))
            
            conn.commit()
            conn.close()
            
            # Ghi log vào file
            logging.error(f"Error: {error_message}")
            if error_type:
                logging.error(f"Type: {error_type}")
            if stack_trace:
                logging.error(f"Stack trace: {stack_trace}")
            if context:
                logging.error(f"Context: {context}")
                
        except Exception as e:
            logging.error(f"Lỗi khi ghi log: {str(e)}")
    
    def get_recent_errors(self, limit: int = 10) -> list:
        """
        Lấy danh sách các lỗi gần đây
        
        Args:
            limit (int): Số lượng lỗi cần lấy
            
        Returns:
            list: Danh sách các lỗi
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM errors
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (limit,))
            
            errors = cursor.fetchall()
            conn.close()
            
            return errors
            
        except Exception as e:
            logging.error(f"Lỗi khi lấy danh sách lỗi: {str(e)}")
            return [] 