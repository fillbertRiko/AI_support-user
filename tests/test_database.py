import unittest
import os
import sqlite3
from datetime import datetime, timedelta
from src.core.database import DatabaseManager

class TestDatabaseManager(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Thiết lập test database"""
        cls.test_db_path = "test_database.db"
        cls.db = DatabaseManager(cls.test_db_path)
        
    def setUp(self):
        """Chuẩn bị dữ liệu test trước mỗi test case"""
        # Xóa dữ liệu cũ
        with self.db._get_connection() as conn:
            conn.execute("DELETE FROM reminders")
            conn.execute("DELETE FROM api_cache")
            conn.commit()
            
    def test_singleton_pattern(self):
        """Test singleton pattern của DatabaseManager"""
        db1 = DatabaseManager(self.test_db_path)
        db2 = DatabaseManager(self.test_db_path)
        self.assertIs(db1, db2)
        
    def test_add_reminder(self):
        """Test thêm reminder"""
        title = "Test Reminder"
        description = "Test Description"
        due_date = (datetime.now() + timedelta(days=1)).isoformat()
        priority = "high"
        reminder_id = self.db.add_reminder(title, description, due_date, priority)
        self.assertIsNotNone(reminder_id)
        
    def test_get_reminders(self):
        """Test lấy danh sách reminders"""
        self.db.add_reminder("Test 1", "Desc 1", (datetime.now() + timedelta(days=1)).isoformat(), "high")
        self.db.add_reminder("Test 2", "Desc 2", (datetime.now() + timedelta(days=2)).isoformat(), "medium")
        reminders = self.db.get_reminders()
        self.assertEqual(len(reminders), 2)
        
    def test_update_reminder(self):
        """Test cập nhật reminder"""
        reminder_id = self.db.add_reminder(
            "Original Title",
            "Original Description",
            (datetime.now() + timedelta(days=1)).isoformat(),
            "high"
        )
        self.db.update_reminder(reminder_id, "Updated Title", "Updated Description", (datetime.now() + timedelta(days=2)).isoformat(), "medium")
        reminders = self.db.get_reminders()
        self.assertEqual(reminders[0]["title"], "Updated Title")
        
    def test_delete_reminder(self):
        """Test xóa reminder"""
        reminder_id = self.db.add_reminder(
            "Test Title",
            "Test Description",
            (datetime.now() + timedelta(days=1)).isoformat(),
            "high"
        )
        self.db.delete_reminder(reminder_id)
        reminders = self.db.get_reminders()
        self.assertEqual(len(reminders), 0)
        
    def test_api_cache(self):
        """Test cache API"""
        cache_data = {"data": "test data"}
        self.db.add_api_cache("test_key", cache_data, 3600)
        cached_data = self.db.get_api_cache("test_key")
        self.assertEqual(cached_data["data"], cache_data["data"])
        
    @classmethod
    def tearDownClass(cls):
        """Clean up after tests"""
        cls.db.close_all_connections()
        try:
            os.remove(cls.test_db_path)
        except PermissionError:
            print(f"Không thể xóa file {cls.test_db_path} vì nó đang được sử dụng bởi một tiến trình khác.")

if __name__ == '__main__':
    unittest.main() 