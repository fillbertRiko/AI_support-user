import logging
import sqlite3
from datetime import datetime
import json
from sentence_transformers import SentenceTransformer
import numpy as np

class ErrorCorrectionService:
    def __init__(self, db_path='data/app_data.db', model_name='all-MiniLM-L6-v2'):
        self.db_path = db_path
        self.logger = logging.getLogger(self.__class__.__name__)
        try:
            self.model = SentenceTransformer(model_name)
            self.logger.info(f"Đã tải mô hình SentenceTransformer: {model_name}")
        except Exception as e:
            self.logger.error(f"Không thể tải mô hình SentenceTransformer {model_name}: {e}")
            self.model = None # Set to None if model loading fails
        self._init_database()

    def _init_database(self):
        """Khởi tạo bảng error_log trong cơ sở dữ liệu."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            # Xóa bảng cũ nếu tồn tại để đảm bảo schema mới nhất
            cursor.execute('DROP TABLE IF EXISTS error_log')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS error_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    service TEXT NOT NULL,
                    error_type TEXT,
                    error_message TEXT,
                    context TEXT,
                    error_message_embedding TEXT,
                    context_embedding TEXT
                )
            ''')
            conn.commit()
            self.logger.info("Bảng 'error_log' đã được khởi tạo hoặc đã tồn tại.")
        except sqlite3.Error as e:
            self.logger.error(f"Lỗi khi khởi tạo cơ sở dữ liệu cho error_log: {e}")
        finally:
            if conn:
                conn.close()

    def _get_embedding(self, text: str):
        """Tạo vector embedding cho một chuỗi văn bản."""
        if self.model is None:
            self.logger.warning("Mô hình embedding chưa được tải. Không thể tạo embedding.")
            return None
        try:
            embedding = self.model.encode(text, convert_to_numpy=True)
            return json.dumps(embedding.tolist()) # Lưu dưới dạng chuỗi JSON
        except Exception as e:
            self.logger.error(f"Lỗi khi tạo embedding: {e}")
            return None

    def log_error(self, service: str, error_type: str, error_message: str, context: str = None):
        """Ghi lại một lỗi vào cơ sở dữ liệu."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            timestamp = datetime.now().isoformat()

            error_msg_embedding = self._get_embedding(error_message)
            context_embedding = self._get_embedding(context) if context else None

            cursor.execute("INSERT INTO error_log (timestamp, service, error_type, error_message, context, error_message_embedding, context_embedding) VALUES (?, ?, ?, ?, ?, ?, ?)",
                           (timestamp, service, error_type, error_message, context, error_msg_embedding, context_embedding))
            conn.commit()
            self.logger.info(f"Đã ghi log lỗi cho dịch vụ '{service}': {error_message}")
        except sqlite3.Error as e:
            self.logger.error(f"Lỗi khi ghi log lỗi: {e}")
        finally:
            if conn:
                conn.close()

    def get_error_history(self, service: str = None, limit: int = 100):
        """Lấy lịch sử lỗi. Nếu service được chỉ định, sẽ lọc theo service đó."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            if service:
                cursor.execute("SELECT * FROM error_log WHERE service = ? ORDER BY timestamp DESC LIMIT ?", (service, limit))
            else:
                cursor.execute("SELECT * FROM error_log ORDER BY timestamp DESC LIMIT ?", (limit,))
            return cursor.fetchall()
        except sqlite3.Error as e:
            self.logger.error(f"Lỗi khi lấy lịch sử lỗi: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def analyze_errors(self, service: str = None):
        """Phân tích đơn giản các loại lỗi."""
        error_history = self.get_error_history(service=service)
        error_counts = {}
        for error in error_history:
            error_type = error[3] # error_type là cột thứ 4 (index 3)
            if error_type in error_counts:
                error_counts[error_type] += 1
            else:
                error_counts[error_type] = 1
        return error_counts

    def find_similar_errors(self, new_error_message: str, service: str = None, top_k: int = 5):
        """Tìm kiếm các lỗi tương tự dựa trên embedding."""
        if self.model is None:
            self.logger.warning("Mô hình embedding chưa được tải. Không thể tìm kiếm lỗi tương tự.")
            return []

        new_embedding_str = self._get_embedding(new_error_message)
        if not new_embedding_str:
            return []
        new_embedding = json.loads(new_embedding_str)

        all_errors = self.get_error_history(service=service)
        similarities = []

        for error in all_errors:
            # error_message_embedding là cột thứ 7 (index 6)
            existing_embedding_str = error[6]
            if existing_embedding_str:
                existing_embedding = json.loads(existing_embedding_str)
                # Tính toán độ tương đồng (ví dụ: cosine similarity)
                sim = np.dot(new_embedding, existing_embedding) / (np.linalg.norm(new_embedding) * np.linalg.norm(existing_embedding))
                similarities.append((sim, error))
        
        similarities.sort(key=lambda x: x[0], reverse=True)
        return [error for sim, error in similarities[:top_k]] 