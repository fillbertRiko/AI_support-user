import sqlite3
from contextlib import contextmanager
import threading
from typing import Optional, List, Dict, Any
import logging
import os
from datetime import datetime, timedelta
import json
import time
from utils.error_handler import DatabaseError

logger = logging.getLogger(__name__)

class DatabaseManager:
    _instance = None
    _initialized = False
    _db_path = None
    
    def __new__(cls, db_path=None):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._db_path = db_path
        elif db_path is not None and db_path != cls._db_path:
            # Nếu truyền db_path mới, cập nhật lại
            cls._db_path = db_path
        return cls._instance
    
    def __init__(self, db_path=None):
        if not self._initialized:
            try:
                logger.info("Khởi tạo DatabaseManager...")
                if db_path is not None:
                    self.db_path = db_path
                elif self._db_path is not None:
                    self.db_path = self._db_path
                else:
                    self.db_path = os.path.join('data', 'database', 'myai.db')
                
                # Đảm bảo thư mục tồn tại
                os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
                
                # Tạo kết nối ban đầu
                logger.debug("Tạo kết nối ban đầu...")
                self.conn = sqlite3.connect(self.db_path)
                self.conn.row_factory = sqlite3.Row
                
                # Thiết lập các tùy chọn SQLite
                logger.debug("Thiết lập các tùy chọn SQLite...")
                self.conn.execute("PRAGMA journal_mode=WAL")
                self.conn.execute("PRAGMA synchronous=NORMAL")
                self.conn.execute("PRAGMA temp_store=MEMORY")
                self.conn.execute("PRAGMA mmap_size=30000000000")
                self.conn.execute("PRAGMA page_size=4096")
                self.conn.execute("PRAGMA cache_size=10000")
                self.conn.execute("PRAGMA locking_mode=NORMAL")
                self.conn.execute("PRAGMA busy_timeout=5000")
                
                # Tạo các bảng cần thiết
                logger.debug("Tạo các bảng...")
                self._create_tables()
                
                # Khởi tạo connection pool
                logger.debug("Khởi tạo connection pool...")
                self.pool = []
                self.max_connections = 5
                self.timeout = 30
                
                # Khởi tạo cache
                logger.debug("Khởi tạo cache...")
                self.cache = {}
                self.cache_timeout = 300  # 5 phút
                
                self._initialized = True
                logger.info("DatabaseManager đã được khởi tạo thành công")
                
            except Exception as e:
                logger.error(f"Lỗi khởi tạo DatabaseManager: {str(e)}", exc_info=True)
                raise DatabaseError(f"Không thể khởi tạo DatabaseManager: {str(e)}")
    
    def _create_tables(self):
        """Tạo các bảng cần thiết nếu chưa tồn tại"""
        try:
            logger.debug("Bắt đầu tạo các bảng...")
            
            # Bảng reminders
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    due_date TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Bảng weather_data
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS weather_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    city TEXT NOT NULL,
                    temperature REAL,
                    description TEXT,
                    humidity INTEGER,
                    wind_speed REAL,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Bảng user_interactions_log
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS user_interactions_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    interaction_type TEXT NOT NULL,
                    details TEXT,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Bảng api_cache
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS api_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    endpoint TEXT NOT NULL,
                    response TEXT NOT NULL,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Bảng app_launches
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS app_launches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    launch_time TEXT DEFAULT CURRENT_TIMESTAMP,
                    version TEXT,
                    status TEXT DEFAULT 'success'
                )
            ''')
            
            # Bảng schedule
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS schedule (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    day_of_week TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    location TEXT
                )
            ''')
            
            # Cập nhật schema cho tất cả các bảng nếu cần
            self._update_all_table_schemas()
            
            # Tạo các index
            logger.debug("Tạo các index...")
            self._create_indexes_safely()
            
            # Commit các thay đổi
            self.conn.commit()
            logger.info("Đã tạo các bảng và index thành công")
            
        except Exception as e:
            logger.error(f"Lỗi tạo bảng: {str(e)}", exc_info=True)
            raise DatabaseError(f"Không thể tạo các bảng: {str(e)}")
    
    def _update_all_table_schemas(self):
        """Cập nhật schema cho tất cả các bảng nếu cần thiết"""
        try:
            # Định nghĩa schema mong muốn cho từng bảng
            expected_schemas = {
                'weather_data': {
                    'city': 'TEXT DEFAULT "Unknown"',
                    'temperature': 'REAL',
                    'description': 'TEXT',
                    'humidity': 'INTEGER',
                    'wind_speed': 'REAL',
                    'pressure': 'REAL',
                    'visibility': 'INTEGER',
                    'dew_point': 'REAL',
                    'feels_like': 'REAL',
                    'temp_min': 'REAL',
                    'temp_max': 'REAL',
                    'timestamp': 'TEXT DEFAULT CURRENT_TIMESTAMP'
                },
                'api_cache': {
                    'endpoint': 'TEXT NOT NULL',
                    'response': 'TEXT NOT NULL',
                    'timestamp': 'TEXT DEFAULT CURRENT_TIMESTAMP'
                },
                'user_interactions_log': {
                    'interaction_type': 'TEXT NOT NULL',
                    'details': 'TEXT',
                    'timestamp': 'TEXT DEFAULT CURRENT_TIMESTAMP'
                }
            }
            
            for table_name, expected_columns in expected_schemas.items():
                self._update_table_schema(table_name, expected_columns)
                
        except Exception as e:
            logger.warning(f"Không thể cập nhật schema cho tất cả bảng: {str(e)}")
    
    def _update_table_schema(self, table_name, expected_columns):
        """Cập nhật schema cho một bảng cụ thể"""
        try:
            # Kiểm tra xem bảng có tồn tại không
            cursor = self.conn.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
            if cursor.fetchone():
                # Bảng đã tồn tại, kiểm tra các cột
                cursor = self.conn.execute(f"PRAGMA table_info({table_name})")
                existing_columns = {column[1]: column[2] for column in cursor.fetchall()}
                
                # Thêm các cột thiếu
                for column_name, column_def in expected_columns.items():
                    if column_name not in existing_columns:
                        logger.info(f"Cập nhật schema bảng {table_name}: thêm cột {column_name}")
                        try:
                            self.conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_def}")
                        except Exception as e:
                            logger.warning(f"Không thể thêm cột {column_name} vào bảng {table_name}: {str(e)}")
                
                self.conn.commit()
                logger.info(f"Đã cập nhật schema cho bảng {table_name}")
        except Exception as e:
            logger.warning(f"Không thể cập nhật schema cho bảng {table_name}: {str(e)}")
    
    def _create_indexes_safely(self):
        """Tạo các index một cách an toàn, bỏ qua nếu có lỗi"""
        try:
            self.conn.execute('CREATE INDEX IF NOT EXISTS idx_reminders_due_date ON reminders(due_date)')
        except Exception as e:
            logger.warning(f"Không thể tạo index idx_reminders_due_date: {str(e)}")
        
        try:
            self.conn.execute('CREATE INDEX IF NOT EXISTS idx_reminders_status ON reminders(status)')
        except Exception as e:
            logger.warning(f"Không thể tạo index idx_reminders_status: {str(e)}")
        
        try:
            self.conn.execute('CREATE INDEX IF NOT EXISTS idx_weather_city ON weather_data(city)')
        except Exception as e:
            logger.warning(f"Không thể tạo index idx_weather_city: {str(e)}")
        
        try:
            self.conn.execute('CREATE INDEX IF NOT EXISTS idx_weather_timestamp ON weather_data(timestamp)')
        except Exception as e:
            logger.warning(f"Không thể tạo index idx_weather_timestamp: {str(e)}")
        
        try:
            self.conn.execute('CREATE INDEX IF NOT EXISTS idx_api_cache_endpoint ON api_cache(endpoint)')
        except Exception as e:
            logger.warning(f"Không thể tạo index idx_api_cache_endpoint: {str(e)}")
        
        try:
            self.conn.execute('CREATE INDEX IF NOT EXISTS idx_api_cache_timestamp ON api_cache(timestamp)')
        except Exception as e:
            logger.warning(f"Không thể tạo index idx_api_cache_timestamp: {str(e)}")
    
    def _update_weather_data_schema(self):
        """Cập nhật schema của bảng weather_data nếu cần thiết"""
        try:
            # Kiểm tra xem bảng weather_data có tồn tại không
            cursor = self.conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='weather_data'")
            if cursor.fetchone():
                # Bảng đã tồn tại, kiểm tra xem có cột city không
                cursor = self.conn.execute("PRAGMA table_info(weather_data)")
                columns = [column[1] for column in cursor.fetchall()]
                
                if 'city' not in columns:
                    logger.info("Cập nhật schema bảng weather_data: thêm cột city")
                    # Thêm cột city vào bảng hiện tại
                    self.conn.execute("ALTER TABLE weather_data ADD COLUMN city TEXT DEFAULT 'Unknown'")
                    self.conn.commit()
                    logger.info("Đã thêm cột city vào bảng weather_data")
        except Exception as e:
            logger.warning(f"Không thể cập nhật schema weather_data: {str(e)}")
            # Không raise exception vì đây không phải lỗi nghiêm trọng
    
    def get_connection(self):
        """Lấy một kết nối từ pool"""
        try:
            if len(self.pool) < self.max_connections:
                conn = self._create_connection()
                self.pool.append(conn)
                return conn
            else:
                # Đợi cho đến khi có kết nối khả dụng
                start_time = time.time()
                while time.time() - start_time < self.timeout:
                    for conn in self.pool:
                        if not conn.in_transaction:
                            return conn
                    time.sleep(0.1)
                raise DatabaseError("Timeout khi chờ kết nối")
        except Exception as e:
            logger.error(f"Lỗi lấy kết nối: {str(e)}", exc_info=True)
            raise DatabaseError(f"Không thể lấy kết nối: {str(e)}")
    
    def _create_connection(self):
        """Tạo một kết nối mới với các tùy chọn tối ưu"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            # Thiết lập các tùy chọn SQLite
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA temp_store=MEMORY")
            conn.execute("PRAGMA mmap_size=30000000000")
            conn.execute("PRAGMA page_size=4096")
            conn.execute("PRAGMA cache_size=10000")
            conn.execute("PRAGMA locking_mode=NORMAL")
            conn.execute("PRAGMA busy_timeout=5000")
            
            return conn
        except Exception as e:
            logger.error(f"Lỗi tạo kết nối mới: {str(e)}", exc_info=True)
            raise DatabaseError(f"Không thể tạo kết nối mới: {str(e)}")
    
    def release_connection(self, conn):
        """Trả kết nối về pool"""
        try:
            if conn in self.pool:
                if conn.in_transaction:
                    conn.rollback()
                self.pool.remove(conn)
                conn.close()
        except Exception as e:
            logger.error(f"Lỗi trả kết nối: {str(e)}", exc_info=True)
    
    def execute_query(self, query, params=None, use_cache=True):
        """Thực thi một truy vấn với caching"""
        try:
            # Tạo cache key
            cache_key = f"{query}:{str(params)}"
            
            # Kiểm tra cache
            if use_cache and cache_key in self.cache:
                cache_time, result = self.cache[cache_key]
                if time.time() - cache_time < self.cache_timeout:
                    return result
            
            # Thực thi truy vấn
            conn = self.get_connection()
            try:
                cursor = conn.execute(query, params or ())
                result = cursor.fetchall()
                
                # Cập nhật cache
                if use_cache:
                    self.cache[cache_key] = (time.time(), result)
                
                return result
            finally:
                self.release_connection(conn)
        except Exception as e:
            logger.error(f"Lỗi thực thi truy vấn: {str(e)}", exc_info=True)
            raise DatabaseError(f"Lỗi thực thi truy vấn: {str(e)}")
    
    def execute_transaction(self, queries):
        """Thực thi nhiều truy vấn trong một transaction"""
        conn = self.get_connection()
        try:
            conn.execute("BEGIN TRANSACTION")
            for query, params in queries:
                conn.execute(query, params or ())
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Lỗi thực thi transaction: {str(e)}", exc_info=True)
            raise DatabaseError(f"Lỗi thực thi transaction: {str(e)}")
        finally:
            self.release_connection(conn)
    
    def clear_cache(self):
        """Xóa toàn bộ cache"""
        self.cache.clear()
    
    def close(self):
        """Đóng kết nối database an toàn"""
        try:
            if hasattr(self, 'conn') and self.conn:
                self.conn.close()
                logger.info("Đã đóng kết nối database")
        except Exception as e:
            logger.error(f"Lỗi khi đóng database: {e}")
            
    def close_all(self):
        """Đóng tất cả kết nối (alias cho close)"""
        self.close()

    def add_reminder(self, title: str, description: str, due_date: str, priority: str = "medium") -> int:
        """Thêm reminder mới"""
        try:
            with self.transaction() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO reminders (title, description, due_date, created_at, priority)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (title, description, due_date, datetime.now().isoformat(), priority)
                )
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Lỗi thêm reminder: {str(e)}")
            raise DatabaseError("Không thể thêm reminder", "DB_ADD_ERROR", {"details": str(e)})

    def get_reminders(self, status: str = "pending") -> List[Dict[str, Any]]:
        """Lấy danh sách reminders"""
        try:
            with self.transaction() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT * FROM reminders 
                    WHERE status = ? 
                    ORDER BY due_date ASC
                    """,
                    (status,)
                )
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Lỗi lấy reminders: {str(e)}")
            raise DatabaseError("Không thể lấy danh sách reminders", "DB_GET_ERROR", {"details": str(e)})

    def update_reminder_status(self, reminder_id: int, new_status: str) -> bool:
        """Cập nhật trạng thái reminder"""
        try:
            with self.transaction() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE reminders 
                    SET status = ? 
                    WHERE id = ?
                    """,
                    (new_status, reminder_id)
                )
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Lỗi cập nhật trạng thái reminder: {str(e)}")
            raise DatabaseError("Không thể cập nhật trạng thái reminder", "DB_UPDATE_ERROR", {"details": str(e)})

    def delete_reminder(self, reminder_id: int) -> bool:
        """Xóa reminder"""
        try:
            with self.transaction() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    DELETE FROM reminders 
                    WHERE id = ?
                    """,
                    (reminder_id,)
                )
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Lỗi xóa reminder: {str(e)}")
            raise DatabaseError("Không thể xóa reminder", "DB_DELETE_ERROR", {"details": str(e)})

    def get_weather_data(self) -> Optional[Dict[str, Any]]:
        """Lấy dữ liệu thời tiết mới nhất"""
        try:
            with self.transaction() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT * FROM weather_data 
                    ORDER BY timestamp DESC 
                    LIMIT 1
                    """
                )
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Lỗi lấy dữ liệu thời tiết: {str(e)}")
            raise DatabaseError("Không thể lấy dữ liệu thời tiết", "DB_GET_ERROR", {"details": str(e)})

    def save_weather_data(self, data: Dict[str, Any]) -> None:
        """Lưu dữ liệu thời tiết mới"""
        try:
            with self.transaction() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO weather_data 
                    (temperature, feels_like, humidity, pressure, description, 
                     icon, wind_speed, clouds, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        data.get("temperature"),
                        data.get("feels_like"),
                        data.get("humidity"),
                        data.get("pressure"),
                        data.get("description"),
                        data.get("icon"),
                        data.get("wind_speed"),
                        data.get("clouds"),
                        data.get("timestamp")
                    )
                )
        except Exception as e:
            logger.error(f"Lỗi lưu dữ liệu thời tiết: {str(e)}")
            raise DatabaseError("Không thể lưu dữ liệu thời tiết", "DB_SAVE_ERROR", {"details": str(e)})

    def log_user_interaction(self, action_type: str, facts: Optional[str] = None) -> None:
        """Ghi log tương tác người dùng"""
        try:
            with self.transaction() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO user_interactions_log 
                    (timestamp, action_type, facts)
                    VALUES (?, ?, ?)
                    """,
                    (datetime.now().isoformat(), action_type, facts)
                )
        except Exception as e:
            logger.error(f"Lỗi ghi log tương tác: {str(e)}")
            raise DatabaseError("Không thể ghi log tương tác", "DB_LOG_ERROR", {"details": str(e)})

    def get_recent_interactions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Lấy danh sách tương tác gần đây"""
        try:
            with self.transaction() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT * FROM user_interactions_log 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                    """,
                    (limit,)
                )
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Lỗi lấy lịch sử tương tác: {str(e)}")
            raise DatabaseError("Không thể lấy lịch sử tương tác", "DB_GET_ERROR", {"details": str(e)})

    def get_cache(self, key: str) -> Optional[Any]:
        """Lấy dữ liệu từ cache"""
        try:
            with self.transaction() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT value, expires_at 
                    FROM api_cache 
                    WHERE key = ? AND expires_at > ?
                    """,
                    (key, datetime.now().isoformat())
                )
                row = cursor.fetchone()
                if row:
                    return json.loads(row["value"])
                return None
        except Exception as e:
            logger.error(f"Lỗi lấy cache: {str(e)}")
            raise DatabaseError("Không thể lấy dữ liệu từ cache", "DB_CACHE_ERROR", {"details": str(e)})

    def set_cache(self, key: str, value: Any, expires_in: int = 3600) -> None:
        """Lưu dữ liệu vào cache"""
        try:
            expires_at = datetime.now() + timedelta(seconds=expires_in)
            with self.transaction() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO api_cache 
                    (key, value, expires_at, created_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (key, json.dumps(value), expires_at.isoformat(), datetime.now().isoformat())
                )
        except Exception as e:
            logger.error(f"Lỗi lưu cache: {str(e)}")
            raise DatabaseError("Không thể lưu dữ liệu vào cache", "DB_CACHE_ERROR", {"details": str(e)})

    def clear_expired_cache(self) -> None:
        """Xóa cache hết hạn"""
        try:
            with self.transaction() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    DELETE FROM api_cache 
                    WHERE expires_at <= ?
                    """,
                    (datetime.now().isoformat(),)
                )
        except Exception as e:
            logger.error(f"Lỗi xóa cache hết hạn: {str(e)}")
            raise DatabaseError("Không thể xóa cache hết hạn", "DB_CACHE_ERROR", {"details": str(e)})

    def log_app_launch(self) -> None:
        """Ghi log thời gian khởi chạy ứng dụng"""
        try:
            with self.transaction() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO app_launches (launch_time)
                    VALUES (?)
                    """,
                    (datetime.now().isoformat(),)
                )
        except Exception as e:
            logger.error(f"Lỗi ghi log khởi chạy: {str(e)}")
            raise DatabaseError("Không thể ghi log khởi chạy", "DB_LOG_ERROR", {"details": str(e)})

    def get_launch_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Lấy lịch sử khởi chạy ứng dụng"""
        try:
            with self.transaction() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT * FROM app_launches 
                    ORDER BY launch_time DESC 
                    LIMIT ?
                    """,
                    (limit,)
                )
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Lỗi lấy lịch sử khởi chạy: {str(e)}")
            raise DatabaseError("Không thể lấy lịch sử khởi chạy", "DB_GET_ERROR", {"details": str(e)})

    def get_schedule_for_day(self, day_of_week: str):
        """Lấy lịch trình cho một ngày trong tuần (ví dụ: 'Monday', 'Tuesday', ...)."""
        try:
            with self.transaction() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM schedule WHERE day_of_week = ? ORDER BY start_time
                ''', (day_of_week,))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Lỗi lấy lịch trình cho ngày {day_of_week}: {str(e)}")
            return []

    def get_recent_applications(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Lấy danh sách ứng dụng gần đây"""
        try:
            with self.transaction() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM app_launches 
                    ORDER BY launch_time DESC 
                    LIMIT ?
                ''', (limit,))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Lỗi lấy danh sách ứng dụng gần đây: {str(e)}")
            return []

    @contextmanager
    def transaction(self):
        """Context manager để thực hiện các thao tác database trong một giao dịch nguyên tử."""
        conn = self.get_connection()
        try:
            conn.autocommit = False # Bắt đầu transaction
            yield conn
            conn.commit()
        except Exception as e:
            logger.error(f"Transaction error: {str(e)}")
            conn.rollback()
            raise
        finally:
            self.release_connection(conn)