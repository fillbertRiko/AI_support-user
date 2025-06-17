import logging
from datetime import datetime

class FactCollector:
    def __init__(self, db):
        self.db = db
        self.logger = logging.getLogger(__name__)

    def collect_facts(self):
        """Thu thập tất cả các sự kiện từ các dịch vụ khác nhau."""
        facts = {}
        
        # Thu thập thông tin thời gian
        now = datetime.now()
        current_hour = now.hour
        day_of_week = now.strftime("%A")
        
        if 5 <= current_hour < 12:
            time_category = "morning"
        elif 12 <= current_hour < 18:
            time_category = "afternoon"
        else:
            time_category = "night"
            
        facts['time_category'] = time_category
        facts['day_of_week'] = day_of_week
        facts['current_hour'] = current_hour
        
        # Thu thập thông tin từ cơ sở dữ liệu
        try:
            # Kiểm tra lịch trình trong ngày
            schedule = self.db.get_schedule_for_day(day_of_week)
            if schedule:
                facts['has_schedule'] = True
                facts['schedule_count'] = len(schedule)
            else:
                facts['has_schedule'] = False
                facts['schedule_count'] = 0
                
            # Kiểm tra các ứng dụng đã chạy
            recent_apps = self.db.get_recent_applications(limit=5)
            if recent_apps:
                facts['recent_apps'] = [app['name'] for app in recent_apps]
                
        except Exception as e:
            self.logger.error(f"Lỗi khi thu thập dữ liệu từ cơ sở dữ liệu: {e}", exc_info=True)
            
        return facts 