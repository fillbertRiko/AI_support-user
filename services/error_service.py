# This is a temporary line to force file rewrite.
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ErrorService:
    def __init__(self):
        self.error_logs = {}

    def log_error(self, service: str, error_type: str, error_message: str, context: str):
        """Ghi lại thông tin lỗi"""
        if service not in self.error_logs:
            self.error_logs[service] = []

        self.error_logs[service].append({
            'timestamp': datetime.now(),
            'error_type': error_type,
            'error_message': error_message,
            'context': context
        })

        # Giới hạn số lượng log
        if len(self.error_logs[service]) > 100:
            self.error_logs[service] = self.error_logs[service][-100:]

        logger.error(f"Error in {service}: {error_type} - {error_message}")
        logger.debug(f"Context: {context}")

    def get_error_stats(self, service: str = None):
        """Lấy thống kê lỗi"""
        if service:
            if service not in self.error_logs:
                return {}
            return {
                'total_errors': len(self.error_logs[service]),
                'error_types': self._count_error_types(self.error_logs[service])
            }
        else:
            stats = {}
            for service_name, logs in self.error_logs.items():
                stats[service_name] = {
                    'total_errors': len(logs),
                    'error_types': self._count_error_types(logs)
                }
            return stats

    def _count_error_types(self, logs):
        """Đếm số lượng lỗi theo loại"""
        error_types = {}
        for log in logs:
            error_type = log['error_type']
            if error_type not in error_types:
                error_types[error_type] = 0
            error_types[error_type] += 1
        return error_types 