import sqlite3
from contextlib import contextmanager
import threading
from typing import Optional, List, Dict, Any
import logging
import os
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

class DatabaseManager:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, db_path: str = "data/database/database.db"):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, db_path: str = "data/database/database.db"):
        if self._initialized:
            return
            
        self._db_path = db_path
        self._connection_pool = []
        self._max_connections = 5
        self._lock = threading.Lock()
        self._current_transaction_connection = threading.local() # Biến cục bộ cho luồng hiện tại
        self._current_transaction_connection.conn = None

        # Thiết lập logging trước
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('DatabaseManager')
        
        # Tạo thư mục nếu chưa tồn tại
        db_dir = os.path.dirname(self._db_path)
        if db_dir:  # Chỉ tạo thư mục nếu đường dẫn không rỗng
            os.makedirs(db_dir, exist_ok=True)
        
        # Khởi tạo database
        self._init_database()
        self._initialized = True
    
    def _init_database(self):
        """Khởi tạo cơ sở dữ liệu và tạo các bảng nếu chưa tồn tại"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Tạo bảng reminders
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    due_date TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    priority TEXT DEFAULT 'medium'
                )
            ''')
            
            # Tạo các index cho bảng reminders
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_reminders_due_date ON reminders(due_date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_reminders_status ON reminders(status)')
            
            # Tạo bảng cache cho API calls
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS api_cache (
                    key TEXT PRIMARY KEY,
                    value BLOB,
                    expires_at TEXT,
                    created_at TEXT
                )
            ''')
            
            # Tạo bảng để lưu trữ thời gian khởi chạy ứng dụng
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS app_launches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    launch_time TEXT NOT NULL
                )
            ''')
            # Tạo bảng weather_data
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS weather_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    temperature REAL,
                    feels_like REAL,
                    humidity INTEGER,
                    pressure INTEGER,
                    description TEXT,
                    icon TEXT,
                    wind_speed REAL,
                    clouds INTEGER,
                    timestamp REAL
                )
            ''')
            
            # Tạo bảng user_interactions_log để lưu trữ các tương tác của người dùng và các facts liên quan
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_interactions_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    action_type TEXT NOT NULL,
                    facts TEXT
                )
            ''')
            
            conn.commit()
    
    @contextmanager
    def _get_connection(self):
        """Lấy connection từ pool hoặc tạo mới nếu cần. Ưu tiên connection từ transaction."""
        if self._current_transaction_connection.conn:
            yield self._current_transaction_connection.conn
            return

        conn = None
        try:
            with self._lock:
                if self._connection_pool:
                    conn = self._connection_pool.pop()
                else:
                    conn = sqlite3.connect(
                        self._db_path,
                        check_same_thread=False,
                        timeout=30
                    )
                    conn.row_factory = sqlite3.Row
            yield conn
        except Exception as e:
            self.logger.error(f"Database error: {str(e)}")
            raise
        finally:
            if conn and not self._current_transaction_connection.conn:
                with self._lock:
                    if len(self._connection_pool) < self._max_connections:
                        self._connection_pool.append(conn)
                    else:
                        conn.close()
    
    @contextmanager
    def transaction(self):
        """Context manager để thực hiện các thao tác database trong một giao dịch nguyên tử."""
        if self._current_transaction_connection.conn:
            # Đã có một transaction đang hoạt động trong luồng này, tiếp tục sử dụng nó
            yield self._current_transaction_connection.conn
            return

        conn = None
        try:
            conn = sqlite3.connect(self._db_path, check_same_thread=False, timeout=30)
            conn.row_factory = sqlite3.Row
            conn.autocommit = False # Bắt đầu transaction
            self._current_transaction_connection.conn = conn
            yield conn
            conn.commit()
        except Exception as e:
            self.logger.error(f"Transaction error: {str(e)}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
            self._current_transaction_connection.conn = None # Reset connection cho luồng hiện tại

    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Thực thi query và trả về kết quả dạng list of dicts. 
           Commit/rollback được quản lý bởi context manager transaction nếu có."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(query, params)
                if query.strip().upper().startswith('SELECT'):
                    return [dict(row) for row in cursor.fetchall()]
                # Không còn commit/rollback ở đây nữa, do transaction() sẽ xử lý
                return []
            except Exception as e:
                self.logger.error(f"Query execution error: {str(e)}")
                # Không rollback ở đây nữa, do transaction() sẽ xử lý
                raise
    
    def add_reminder(self, title: str, description: str, due_date: str, priority: str = "medium") -> int:
        """Thêm reminder mới và trả về ID"""
        try:
            # Xác thực định dạng due_date
            if not isinstance(due_date, str):
                raise ValueError("due_date phải là một chuỗi.")
            datetime.fromisoformat(due_date.replace('Z', '+00:00'))
        except ValueError as e:
            self.logger.error(f"Lỗi: Định dạng ngày hết hạn không hợp lệ cho reminder: {due_date}. Cần định dạng ISO 8601.")
            raise ValueError("Định dạng ngày hết hạn không hợp lệ. Vui lòng sử dụng định dạng ISO 8601 (ví dụ: YYYY-MM-DD HH:MM:SS).")

        with self.transaction(): # Bắt đầu một giao dịch
            query = '''
                INSERT INTO reminders (title, description, due_date, created_at, priority)
                VALUES (?, ?, ?, datetime('now'), ?)
            '''
            self.execute_query(query, (title, description, due_date, priority))
            # last_insert_rowid() an toàn trong cùng một transaction
            return self.execute_query('SELECT last_insert_rowid()')[0]['last_insert_rowid()']
    
    def get_reminders(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lấy danh sách reminders với optional filter theo status"""
        query = 'SELECT * FROM reminders'
        params = []
        if status:
            query += ' WHERE status = ?'
            params.append(status)
        query += ' ORDER BY due_date'
        return self.execute_query(query, tuple(params))
    
    def update_reminder_status(self, reminder_id: int, status: str) -> None:
        """Cập nhật trạng thái của reminder"""
        query = 'UPDATE reminders SET status = ? WHERE id = ?'
        self.execute_query(query, (status, reminder_id))
    
    def update_reminder(self, reminder_id: int, title: str, description: str, due_date: str, priority: str) -> None:
        """Cập nhật thông tin reminder"""
        query = '''
            UPDATE reminders 
            SET title = ?, description = ?, due_date = ?, priority = ?
            WHERE id = ?
        '''
        self.execute_query(query, (title, description, due_date, priority, reminder_id))
    
    def delete_reminder(self, reminder_id: int) -> None:
        """Xóa reminder theo ID"""
        query = 'DELETE FROM reminders WHERE id = ?'
        self.execute_query(query, (reminder_id,))
    
    def cache_api_response(self, key: str, value: Any, expires_in_seconds: int) -> None:
        """Cache API response với thời gian hết hạn (value có thể là str hoặc bytes)"""
        query = '''
            INSERT OR REPLACE INTO api_cache (key, value, expires_at, created_at)
            VALUES (?, ?, datetime('now', '+' || ? || ' seconds'), datetime('now'))
        '''
        # SQLite sẽ tự động xử lý bytes thành BLOB
        self.execute_query(query, (key, value, expires_in_seconds))
    
    def get_cached_response(self, key: str) -> Optional[Any]: # Thay đổi kiểu trả về thành Any
        """Lấy cached response nếu còn hạn"""
        query = '''
            SELECT value FROM api_cache 
            WHERE key = ? AND expires_at > datetime('now')
        '''
        result = self.execute_query(query, (key,))
        # Dữ liệu BLOB sẽ được trả về dưới dạng bytes
        return result[0]['value'] if result else None
    
    def log_app_launch(self) -> None:
        """Ghi lại thời gian ứng dụng được khởi chạy"""
        query = '''
            INSERT INTO app_launches (launch_time)
            VALUES (datetime('now'))
        '''
        try:
            self.execute_query(query)
            self.logger.info("App launch time logged.")
        except Exception as e:
            self.logger.error(f"Error logging app launch: {str(e)}")
    
    def save_weather_data(self, weather_data: Dict[str, Any]) -> None:
        """Lưu dữ liệu thời tiết vào bảng weather_data."""
        with self.transaction():
            # Xóa các bản ghi cũ hơn một tuần để tránh tích lũy quá nhiều dữ liệu
            seven_days_ago = (datetime.now() - timedelta(days=7)).timestamp()
            self.execute_query("DELETE FROM weather_data WHERE timestamp < ?", (seven_days_ago,))

            query = '''
                INSERT INTO weather_data (temperature, feels_like, humidity, pressure, description, icon, wind_speed, clouds, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''
            params = (
                weather_data.get('temperature'),
                weather_data.get('feels_like'),
                weather_data.get('humidity'),
                weather_data.get('pressure'),
                weather_data.get('description'),
                weather_data.get('icon'),
                weather_data.get('wind_speed'),
                weather_data.get('clouds'),
                weather_data.get('timestamp', datetime.now().timestamp())
            )
            self.execute_query(query, params)
        self.logger.info("Weather data saved successfully.")
    
    def log_user_interaction(self, action_type: str, facts: Dict[str, Any]):
        """Ghi lại tương tác của người dùng cùng với các facts hiện tại."""
        try:
            facts_json = json.dumps(facts)
            with self.transaction():
                query = "INSERT INTO user_interactions_log (timestamp, action_type, facts) VALUES (?, ?, ?)"
                self.execute_query(query, (datetime.now().isoformat(), action_type, facts_json))
                self.logger.info(f"Đã ghi lại tương tác người dùng: {action_type} với facts {facts_json}")
        except Exception as e:
            self.logger.error(f"Lỗi khi ghi lại tương tác người dùng: {e}")

    def get_weather_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Lấy lịch sử dữ liệu thời tiết gần đây nhất."""
        query = "SELECT * FROM weather_data ORDER BY timestamp DESC LIMIT ?"
        return self.execute_query(query, (limit,))

    def get_weather_stats(self) -> Dict[str, Any]:
        """Tính toán các thống kê cơ bản về dữ liệu thời tiết."""
        stats = {
            "avg_temp": None,
            "max_temp": None,
            "min_temp": None,
            "avg_humidity": None,
            "max_humidity": None,
            "min_humidity": None
        }
        query = "SELECT AVG(temperature), MAX(temperature), MIN(temperature), AVG(humidity), MAX(humidity), MIN(humidity) FROM weather_data"
        result = self.execute_query(query)
        if result:
            row = result[0]
            stats["avg_temp"] = row[0]
            stats["max_temp"] = row[1]
            stats["min_temp"] = row[2]
            stats["avg_humidity"] = row[3]
            stats["max_humidity"] = row[4]
            stats["min_humidity"] = row[5]
        return stats

    def close_all_connections(self):
        """Đóng tất cả các kết nối trong pool."""
        with self._lock:
            for conn in self._connection_pool:
                conn.close()
            self._connection_pool.clear()
            self.logger.info("All database connections closed.")

    def add_api_cache(self, key: str, data: dict, duration: int) -> None:
        """Adds or updates an API response in the cache with a specific duration in seconds."""
        expires_at = datetime.now() + timedelta(seconds=duration)
        query = '''
            INSERT OR REPLACE INTO api_cache (key, value, expires_at, created_at)
            VALUES (?, ?, ?, datetime('now'))
        '''
        with self.transaction():
            self.execute_query(query, (key, json.dumps(data), expires_at.isoformat()))
            self.logger.debug(f"Cached API response for key: {key}")

    def get_api_cache(self, key: str) -> Optional[dict]:
        """Retrieves an API response from the cache if it's not expired."""
        query = "SELECT value, expires_at FROM api_cache WHERE key = ?"
        result = self.execute_query(query, (key,))
        if result and result[0]['expires_at'] and datetime.fromisoformat(result[0]['expires_at']) > datetime.now():
            self.logger.debug(f"Cache hit for key: {key}")
            return json.loads(result[0]['value'])
        self.logger.debug(f"Cache miss or expired for key: {key}")
        return None