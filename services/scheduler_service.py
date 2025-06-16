import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class SchedulerService:
    def __init__(self):
        self.schedule_logs = {}

    def suggest_optimal_launch_time(self):
        """Đề xuất thời gian khởi động tối ưu"""
        current_time = datetime.now()
        
        # Nếu là buổi sáng (5-12h)
        if 5 <= current_time.hour < 12:
            return current_time.replace(hour=8, minute=0, second=0, microsecond=0)
        
        # Nếu là buổi chiều (12-18h)
        elif 12 <= current_time.hour < 18:
            return current_time.replace(hour=14, minute=0, second=0, microsecond=0)
        
        # Nếu là buổi tối (18-22h)
        elif 18 <= current_time.hour < 22:
            return current_time.replace(hour=20, minute=0, second=0, microsecond=0)
        
        # Nếu là đêm (22-5h)
        else:
            return (current_time + timedelta(days=1)).replace(hour=8, minute=0, second=0, microsecond=0)

    def log_schedule(self, task: str, scheduled_time: datetime, actual_time: datetime):
        """Ghi lại thông tin lên lịch"""
        if task not in self.schedule_logs:
            self.schedule_logs[task] = []

        self.schedule_logs[task].append({
            'scheduled_time': scheduled_time,
            'actual_time': actual_time,
            'delay': (actual_time - scheduled_time).total_seconds()
        })

        # Giới hạn số lượng log
        if len(self.schedule_logs[task]) > 100:
            self.schedule_logs[task] = self.schedule_logs[task][-100:]

        logger.debug(f"Scheduled task {task}: planned={scheduled_time}, actual={actual_time}")

    def get_schedule_stats(self, task: str = None):
        """Lấy thống kê lên lịch"""
        if task:
            if task not in self.schedule_logs:
                return {}
            return {
                'total_tasks': len(self.schedule_logs[task]),
                'avg_delay': self._calculate_avg_delay(self.schedule_logs[task])
            }
        else:
            stats = {}
            for task_name, logs in self.schedule_logs.items():
                stats[task_name] = {
                    'total_tasks': len(logs),
                    'avg_delay': self._calculate_avg_delay(logs)
                }
            return stats

    def _calculate_avg_delay(self, logs):
        """Tính thời gian trễ trung bình"""
        if not logs:
            return 0
        return sum(log['delay'] for log in logs) / len(logs) 