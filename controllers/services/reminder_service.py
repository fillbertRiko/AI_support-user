import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from ..core.database import DatabaseManager

class ReminderService:
    def __init__(self):
        self.db = DatabaseManager()
        self.logger = logging.getLogger('ReminderService')
    
    def add_reminder(self, title: str, description: str, due_date: str, priority: int = 0) -> int:
        """Thêm reminder mới"""
        try:
            return self.db.add_reminder(title, description, due_date)
        except Exception as e:
            self.logger.error(f"Error adding reminder: {str(e)}")
            raise
    
    def get_reminders(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lấy danh sách reminders"""
        try:
            return self.db.get_reminders(status)
        except Exception as e:
            self.logger.error(f"Error getting reminders: {str(e)}")
            return []
    
    def update_reminder_status(self, reminder_id: int, status: str) -> None:
        """Cập nhật trạng thái reminder"""
        try:
            self.db.update_reminder_status(reminder_id, status)
        except Exception as e:
            self.logger.error(f"Error updating reminder status: {str(e)}")
            raise
    
    def get_due_reminders(self) -> List[Dict[str, Any]]:
        """Lấy danh sách reminders sắp đến hạn"""
        try:
            query = '''
                SELECT * FROM reminders 
                WHERE status = 'pending' 
                AND due_date <= datetime('now', '+1 day')
                ORDER BY due_date
            '''
            return self.db.execute_query(query)
        except Exception as e:
            self.logger.error(f"Error getting due reminders: {str(e)}")
            return []
    
    def delete_reminder(self, reminder_id: int) -> None:
        """Xóa reminder"""
        try:
            query = 'DELETE FROM reminders WHERE id = ?'
            self.db.execute_query(query, (reminder_id,))
        except Exception as e:
            self.logger.error(f"Error deleting reminder: {str(e)}")
            raise
    
    def get_reminder_by_id(self, reminder_id: int) -> Optional[Dict[str, Any]]:
        """Lấy thông tin chi tiết của một reminder"""
        try:
            query = 'SELECT * FROM reminders WHERE id = ?'
            result = self.db.execute_query(query, (reminder_id,))
            return result[0] if result else None
        except Exception as e:
            self.logger.error(f"Error getting reminder by id: {str(e)}")
            return None 