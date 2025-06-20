import logging
from datetime import datetime, timedelta
from collections import Counter
import os
import sys
import win32com.client # Import for Task Scheduler interaction
from typing import Optional

from models.database import DatabaseManager

class SchedulerService:
    def __init__(self):
        self.db = DatabaseManager()
        self.logger = logging.getLogger('SchedulerService')

    def get_app_launch_history(self, days: int = 30) -> list:
        """Lấy lịch sử khởi chạy ứng dụng từ database trong N ngày gần đây nhất"""
        query = """
            SELECT launch_time
            FROM app_launches
            WHERE launch_time >= datetime('now', ?)
            ORDER BY launch_time DESC
        """
        params = (f'-{days} days',)
        try:
            results = self.db.execute_query(query, params)
            return [row['launch_time'] for row in results]
        except Exception as e:
            self.logger.error(f"Error getting app launch history: {str(e)}")
            return []

    def analyze_launch_times(self, history: list) -> dict:
        """Phân tích lịch sử khởi chạy để tìm ra các thời điểm phổ biến"""
        if not history:
            return {}

        hourly_counts = Counter()
        daily_counts = Counter()

        for launch_time_str in history:
            try:
                # Cần xử lý múi giờ nếu database lưu múi giờ
                # Hiện tại giả định là giờ cục bộ
                launch_dt = datetime.fromisoformat(launch_time_str)
                hourly_counts[launch_dt.hour] += 1
                daily_counts[launch_dt.weekday()] += 1 # Thứ 2 là 0, Chủ Nhật là 6
            except ValueError as e:
                self.logger.warning(f"Invalid datetime format in database: {launch_time_str} - {e}")
                continue

        # Tìm giờ phổ biến nhất
        most_common_hour = None
        if hourly_counts:
            most_common_hour = hourly_counts.most_common(1)[0][0]
        
        # Tìm ngày trong tuần phổ biến nhất (nếu cần)
        most_common_day = None
        if daily_counts:
            most_common_day = daily_counts.most_common(1)[0][0]

        return {
            "hourly_counts": hourly_counts,
            "daily_counts": daily_counts,
            "most_common_hour": most_common_hour,
            "most_common_day": most_common_day
        }

    def suggest_optimal_launch_time(self) -> Optional[datetime]:
        """Gợi ý thời gian khởi chạy tối ưu dựa trên phân tích"""
        history = self.get_app_launch_history()
        analysis = self.analyze_launch_times(history)

        if analysis.get("most_common_hour") is not None:
            # Giả định chúng ta chỉ quan tâm đến giờ phổ biến nhất hiện tại
            now = datetime.now()
            suggested_time = now.replace(
                hour=analysis["most_common_hour"],
                minute=0,
                second=0,
                microsecond=0
            )
            # Nếu giờ gợi ý đã qua trong ngày, đề xuất cho ngày mai
            if suggested_time <= now:
                suggested_time += timedelta(days=1)
            return suggested_time
        return None

    def schedule_app_launch(self, launch_time: datetime, task_name: str = "GreetingAppAutoLaunch") -> bool:
        """Tạo hoặc cập nhật tác vụ trong Windows Task Scheduler"""
        if sys.platform != "win32":
            self.logger.warning("Task scheduling is only supported on Windows.")
            return False

        try:
            scheduler = win32com.client.Dispatch("Schedule.Service")
            scheduler.Connect()

            root_folder = scheduler.GetFolder("\\")
            task_definition = scheduler.NewTask(0) # 0 = TASK_FLAG_FORCE_IMMEDIATE_START

            # Cấu hình cài đặt tác vụ
            task_definition.Settings.Enabled = True
            task_definition.Settings.StopIfGoingOnBatteries = False
            task_definition.Settings.DisallowStartIfOnBatteries = False
            task_definition.Settings.RunOnlyIfNetworkAvailable = False
            task_definition.Settings.WakeToRun = True # Đánh thức máy tính để chạy tác vụ

            # Tạo trigger (Lặp lại hàng ngày vào một thời gian cụ thể)
            # TASK_TRIGGER_DAILY = 2, TASK_TRIGGER_TIME = 1
            trigger = task_definition.Triggers.Create(1) # TASK_TRIGGER_TIME for specific time
            trigger.StartBoundary = launch_time.isoformat()
            trigger.Enabled = True
            trigger.Id = "DailyLaunch"
            trigger.Repetition.Interval = "PT1D" # Lặp lại mỗi 1 ngày (P1D for daily, PT1H for hourly)
            trigger.Repetition.Duration = "P1Y" # Lặp lại trong 1 năm

            # Tạo action (chạy file .bat)
            action = task_definition.Actions.Create(0) # TASK_ACTION_EXEC
            # Lấy đường dẫn tuyệt đối đến run_on_startup.bat
            script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'run_on_startup.bat'))
            action.Path = script_path
            action.WorkingDirectory = os.path.dirname(script_path)

            # Đăng ký tác vụ
            # TASK_CREATE_OR_UPDATE = 6
            # TASK_LOGON_NONE = 0, TASK_LOGON_S4U = 1, TASK_LOGON_PASSWORD = 2, TASK_LOGON_INTERACTIVE_TOKEN = 3
            # TASK_LOGON_SERVICE_ACCOUNT = 4, TASK_LOGON_GROUP = 5, TASK_LOGON_INTERACTIVE_TOKEN_OR_PASSWORD = 6
            root_folder.RegisterTaskDefinition(
                task_name, 
                task_definition, 
                6, # TASK_CREATE_OR_UPDATE
                "", # User (empty for current user)
                "", # Password (empty for current user)
                3 # TASK_LOGON_INTERACTIVE_TOKEN - Chạy khi người dùng đăng nhập
            )
            self.logger.info(f"Task '{task_name}' scheduled to launch at {launch_time.strftime("%H:%M")}")
            return True
        except Exception as e:
            self.logger.error(f"Error scheduling task: {str(e)}")
            self.logger.error("Please ensure you run the application with administrator privileges to schedule tasks.")
            return False

    # def schedule_app_launch(self, launch_time: datetime, task_name: str = "GreetingAppAutoLaunch"):
    #     """Tạo hoặc cập nhật tác vụ trong Windows Task Scheduler"""
    #     # Logic để tương tác với Task Scheduler sẽ ở đây
    #     # Điều này yêu cầu thư viện như win32com.client hoặc pywin32
    #     pass # Placeholder 