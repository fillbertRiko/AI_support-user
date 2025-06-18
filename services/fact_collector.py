import logging
from datetime import datetime

class FactCollector:
    def __init__(self, db, weather_service=None):
        self.db = db
        self.weather_service = weather_service
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
                # Kiểm tra xem có hoạt động Gym không
                gym_activities = [s for s in schedule if 'gym' in s.get('activity', '').lower() or 'tập' in s.get('activity', '').lower()]
                if gym_activities:
                    facts['schedule_activity'] = 'Gym'
                else:
                    facts['schedule_activity'] = 'Other'
            else:
                facts['has_schedule'] = False
                facts['schedule_count'] = 0
                facts['schedule_activity'] = 'None'
            
            # Xác định schedule_empty_or_flexible
            if facts['schedule_count'] == 0:
                facts['schedule_empty_or_flexible'] = True
            else:
                facts['schedule_empty_or_flexible'] = False
                
            # Kiểm tra các ứng dụng đã chạy
            recent_apps = self.db.get_recent_applications(limit=5)
            if recent_apps:
                # Kiểm tra cấu trúc dữ liệu trước khi truy cập
                app_names = []
                for app in recent_apps:
                    if isinstance(app, dict):
                        # Nếu là dict, tìm key phù hợp
                        if 'name' in app:
                            app_names.append(app['name'])
                        elif 'launch_time' in app:
                            app_names.append(f"App_{app['launch_time']}")
                        else:
                            app_names.append(str(app))
                    else:
                        app_names.append(str(app))
                facts['recent_apps'] = app_names
                
                # Kiểm tra VSCode status
                vscode_running = any('vscode' in app.lower() or 'code' in app.lower() for app in app_names)
                facts['vscode_status'] = 'open' if vscode_running else 'closed'
            else:
                facts['recent_apps'] = []
                facts['vscode_status'] = 'closed'
                
        except Exception as e:
            self.logger.error(f"Lỗi khi thu thập dữ liệu từ cơ sở dữ liệu: {e}", exc_info=True)
            # Đặt giá trị mặc định nếu có lỗi
            facts['has_schedule'] = False
            facts['schedule_count'] = 0
            facts['schedule_activity'] = 'None'
            facts['schedule_empty_or_flexible'] = True
            facts['recent_apps'] = []
            facts['vscode_status'] = 'closed'
        
        # Thu thập thông tin thời tiết (nếu có weather service)
        try:
            if hasattr(self, 'weather_service') and self.weather_service:
                weather_data = self.weather_service.get_weather()
                if weather_data and 'description' in weather_data:
                    description = weather_data['description'].lower()
                    if 'mưa' in description:
                        facts['weather_condition'] = 'mưa'
                    elif 'nắng' in description or 'trời quang' in description:
                        facts['weather_condition'] = 'nắng'
                    else:
                        facts['weather_condition'] = description
                else:
                    facts['weather_condition'] = 'unknown'
            else:
                facts['weather_condition'] = 'unknown'
        except Exception as e:
            self.logger.error(f"Lỗi khi thu thập thông tin thời tiết: {e}", exc_info=True)
            facts['weather_condition'] = 'unknown'
            
        return facts 