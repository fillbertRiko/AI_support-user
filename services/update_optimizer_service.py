import logging
import time
from datetime import datetime

logger = logging.getLogger(__name__)

class UpdateOptimizerService:
    def __init__(self):
        self.update_logs = {}
        self.optimal_intervals = {
            'greeting': 3600,  # 1 giờ
            'weather': 300,    # 5 phút
            'schedule': 3600,  # 1 giờ
            'vscode': 3600    # 1 giờ
        }

    def log_update(self, service_type: str, data_changed: bool, user_interaction: bool, response_time: float):
        """Ghi lại thông tin cập nhật"""
        if service_type not in self.update_logs:
            self.update_logs[service_type] = []

        self.update_logs[service_type].append({
            'timestamp': datetime.now(),
            'data_changed': data_changed,
            'user_interaction': user_interaction,
            'response_time': response_time
        })

        # Giới hạn số lượng log
        if len(self.update_logs[service_type]) > 100:
            self.update_logs[service_type] = self.update_logs[service_type][-100:]

        # Cập nhật khoảng thời gian tối ưu
        self._update_optimal_interval(service_type)

    def get_optimal_interval(self, service_type: str) -> int:
        """Lấy khoảng thời gian tối ưu cho việc cập nhật"""
        return self.optimal_intervals.get(service_type, 3600)

    def _update_optimal_interval(self, service_type: str):
        """Cập nhật khoảng thời gian tối ưu dựa trên dữ liệu log"""
        if service_type not in self.update_logs or len(self.update_logs[service_type]) < 10:
            return

        logs = self.update_logs[service_type]
        recent_logs = logs[-10:]  # Xét 10 log gần nhất

        # Tính tỷ lệ thay đổi dữ liệu
        data_change_rate = sum(1 for log in recent_logs if log['data_changed']) / len(recent_logs)

        # Tính thời gian phản hồi trung bình
        avg_response_time = sum(log['response_time'] for log in recent_logs) / len(recent_logs)

        # Điều chỉnh khoảng thời gian dựa trên tỷ lệ thay đổi và thời gian phản hồi
        if data_change_rate > 0.7:  # Dữ liệu thay đổi nhiều
            self.optimal_intervals[service_type] = max(60, int(self.optimal_intervals[service_type] * 0.8))
        elif data_change_rate < 0.3:  # Dữ liệu ít thay đổi
            self.optimal_intervals[service_type] = min(3600, int(self.optimal_intervals[service_type] * 1.2))

        # Điều chỉnh dựa trên thời gian phản hồi
        if avg_response_time > 1.0:  # Thời gian phản hồi cao
            self.optimal_intervals[service_type] = max(300, int(self.optimal_intervals[service_type] * 1.1))

        logger.debug(f"Updated optimal interval for {service_type}: {self.optimal_intervals[service_type]}s") 