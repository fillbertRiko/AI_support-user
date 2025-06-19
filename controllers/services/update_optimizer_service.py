import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import sqlite3
from collections import defaultdict
import numpy as np
from models.database import DatabaseManager

class UpdateOptimizerService:
    def __init__(self):
        self.db = DatabaseManager()
        self.logger = logging.getLogger('UpdateOptimizerService')
        
        # Khởi tạo database cho việc theo dõi cập nhật
        self._init_database()
        
        # Các tham số cho thuật toán học
        self.min_update_interval = 300  # 5 phút
        self.max_update_interval = 3600  # 1 giờ
        self.learning_rate = 0.1  # Tốc độ học
        self.decay_factor = 0.95  # Hệ số suy giảm cho dữ liệu cũ
        
    def _init_database(self):
        """Khởi tạo các bảng cần thiết cho việc theo dõi cập nhật"""
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            
            # Bảng lưu lịch sử cập nhật
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS update_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    service_type TEXT NOT NULL,
                    update_time TEXT NOT NULL,
                    data_changed BOOLEAN NOT NULL,
                    user_interaction BOOLEAN NOT NULL,
                    response_time REAL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Bảng lưu thời gian cập nhật tối ưu
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS optimal_update_intervals (
                    service_type TEXT PRIMARY KEY,
                    interval INTEGER NOT NULL,
                    last_updated TEXT NOT NULL,
                    confidence REAL DEFAULT 0.0
                )
            ''')
            
            conn.commit()
    
    def log_update(self, service_type: str, data_changed: bool, user_interaction: bool, response_time: float):
        """Ghi lại thông tin về một lần cập nhật"""
        query = '''
            INSERT INTO update_history 
            (service_type, update_time, data_changed, user_interaction, response_time)
            VALUES (?, ?, ?, ?, ?)
        '''
        try:
            self.db.execute_query(query, (
                service_type,
                datetime.now().isoformat(),
                data_changed,
                user_interaction,
                response_time
            ))
            self.logger.debug(f"Logged update for {service_type}")
        except Exception as e:
            self.logger.error(f"Error logging update: {str(e)}")
    
    def get_update_history(self, service_type: str, days: int = 7) -> list:
        """Lấy lịch sử cập nhật của một service"""
        query = '''
            SELECT * FROM update_history
            WHERE service_type = ? 
            AND update_time >= datetime('now', ?)
            ORDER BY update_time DESC
        '''
        try:
            return self.db.execute_query(query, (service_type, f'-{days} days'))
        except Exception as e:
            self.logger.error(f"Error getting update history: {str(e)}")
            return []
    
    def analyze_update_patterns(self, service_type: str) -> Dict[str, Any]:
        """Phân tích mẫu cập nhật để tìm thời gian tối ưu"""
        history = self.get_update_history(service_type)
        if not history:
            return {
                'interval': self.max_update_interval,
                'confidence': 0.0
            }
        
        # Tính toán các chỉ số
        data_change_rate = sum(1 for h in history if h['data_changed']) / len(history)
        user_interaction_rate = sum(1 for h in history if h['user_interaction']) / len(history)
        
        # Tính toán thời gian giữa các lần cập nhật
        update_times = [datetime.fromisoformat(h['update_time']) for h in history]
        update_intervals = [(update_times[i] - update_times[i+1]).total_seconds() 
                          for i in range(len(update_times)-1)]
        
        if not update_intervals:
            return {
                'interval': self.max_update_interval,
                'confidence': 0.0
            }
        
        # Tính toán thời gian cập nhật tối ưu dựa trên các yếu tố
        base_interval = np.median(update_intervals)
        
        # Điều chỉnh dựa trên tỷ lệ thay đổi dữ liệu
        if data_change_rate > 0.5:  # Nếu dữ liệu thay đổi thường xuyên
            base_interval *= 0.8
        elif data_change_rate < 0.2:  # Nếu dữ liệu ít thay đổi
            base_interval *= 1.2
            
        # Điều chỉnh dựa trên tương tác người dùng
        if user_interaction_rate > 0.7:  # Nếu người dùng tương tác nhiều
            base_interval *= 0.9
        elif user_interaction_rate < 0.3:  # Nếu người dùng ít tương tác
            base_interval *= 1.1
            
        # Giới hạn trong khoảng cho phép
        optimal_interval = max(min(int(base_interval), self.max_update_interval), 
                             self.min_update_interval)
        
        # Tính độ tin cậy dựa trên số lượng dữ liệu và độ ổn định
        confidence = min(len(history) / 100, 1.0)  # Tăng độ tin cậy theo số lượng dữ liệu
        if update_intervals:
            std_dev = np.std(update_intervals)
            confidence *= (1 - min(std_dev / self.max_update_interval, 0.5))
        
        return {
            'interval': optimal_interval,
            'confidence': confidence
        }
    
    def update_optimal_interval(self, service_type: str):
        """Cập nhật thời gian tối ưu cho một service"""
        analysis = self.analyze_update_patterns(service_type)
        
        query = '''
            INSERT OR REPLACE INTO optimal_update_intervals
            (service_type, interval, last_updated, confidence)
            VALUES (?, ?, ?, ?)
        '''
        try:
            self.db.execute_query(query, (
                service_type,
                analysis['interval'],
                datetime.now().isoformat(),
                analysis['confidence']
            ))
            self.logger.info(f"Updated optimal interval for {service_type}: {analysis['interval']}s")
        except Exception as e:
            self.logger.error(f"Error updating optimal interval: {str(e)}")
    
    def get_optimal_interval(self, service_type: str) -> int:
        """Lấy thời gian cập nhật tối ưu cho một service"""
        query = '''
            SELECT interval, confidence, last_updated
            FROM optimal_update_intervals
            WHERE service_type = ?
        '''
        try:
            result = self.db.execute_query(query, (service_type,))
            if result:
                # Kiểm tra xem dữ liệu có quá cũ không (hơn 1 ngày)
                last_updated = datetime.fromisoformat(result[0]['last_updated'])
                if (datetime.now() - last_updated).days > 1:
                    # Cập nhật lại nếu dữ liệu quá cũ
                    self.update_optimal_interval(service_type)
                    return self.get_optimal_interval(service_type)
                return result[0]['interval']
            
            # Nếu chưa có dữ liệu, phân tích và lưu
            self.update_optimal_interval(service_type)
            return self.get_optimal_interval(service_type)
            
        except Exception as e:
            self.logger.error(f"Error getting optimal interval: {str(e)}")
            return self.max_update_interval  # Trả về giá trị mặc định nếu có lỗi 