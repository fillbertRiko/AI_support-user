import logging
import traceback
import sys
from typing import Optional, Dict, Any
from datetime import datetime
import json
import os

logger = logging.getLogger(__name__)

class AppError(Exception):
    """Base exception class for application errors"""
    def __init__(self, message: str, error_code: str = "UNKNOWN_ERROR", details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.timestamp = datetime.now()
        super().__init__(self.message)

class DatabaseError(AppError):
    """Database related errors"""
    pass

class NetworkError(AppError):
    """Network related errors"""
    pass

class ValidationError(AppError):
    """Data validation errors"""
    pass

class SecurityError(AppError):
    """Security related errors"""
    pass

class ErrorHandler:
    def __init__(self):
        self.error_log_file = os.path.join("logs", "errors.json")
        os.makedirs(os.path.dirname(self.error_log_file), exist_ok=True)

    def handle_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
        """Xử lý và ghi log lỗi"""
        error_data = {
            "timestamp": datetime.now().isoformat(),
            "error_type": error.__class__.__name__,
            "message": str(error),
            "traceback": traceback.format_exc(),
            "context": context or {}
        }
        # Không ghi log lỗi ra file hoặc logger nữa
        pass
        # logger.error(f"Error occurred: {error_data['message']}")
        # logger.debug(f"Error details: {json.dumps(error_data, indent=2)}")
        # self._save_error_log(error_data)

    def _save_error_log(self, error_data: Dict[str, Any]) -> None:
        """Không lưu thông tin lỗi vào file nữa"""
        pass

    def _handle_database_error(self, error: DatabaseError) -> None:
        """Xử lý lỗi database"""
        logger.error(f"Database error: {error.message}")
        # Thêm logic xử lý lỗi database ở đây

    def _handle_network_error(self, error: NetworkError) -> None:
        """Xử lý lỗi mạng"""
        logger.error(f"Network error: {error.message}")
        # Thêm logic xử lý lỗi mạng ở đây

    def _handle_validation_error(self, error: ValidationError) -> None:
        """Xử lý lỗi validation"""
        logger.error(f"Validation error: {error.message}")
        # Thêm logic xử lý lỗi validation ở đây

    def _handle_security_error(self, error: SecurityError) -> None:
        """Xử lý lỗi bảo mật"""
        logger.error(f"Security error: {error.message}")
        # Thêm logic xử lý lỗi bảo mật ở đây

    def _handle_unknown_error(self, error: Exception) -> None:
        """Xử lý lỗi không xác định"""
        logger.error(f"Unknown error: {str(error)}")
        # Thêm logic xử lý lỗi không xác định ở đây

    def get_error_logs(self, limit: int = 100) -> list:
        """Lấy danh sách lỗi gần đây"""
        try:
            if os.path.exists(self.error_log_file):
                with open(self.error_log_file, "r") as f:
                    logs = json.load(f)
                    return logs[-limit:]
            return []
        except Exception as e:
            logger.error(f"Failed to read error logs: {str(e)}")
            return []

    def clear_error_logs(self) -> None:
        """Xóa tất cả log lỗi"""
        try:
            if os.path.exists(self.error_log_file):
                os.remove(self.error_log_file)
            logger.info("Error logs cleared")
        except Exception as e:
            logger.error(f"Failed to clear error logs: {str(e)}")

# Khởi tạo error handler toàn cục
error_handler = ErrorHandler()

def handle_exception(exc_type, exc_value, exc_traceback):
    """Global exception handler"""
    if issubclass(exc_type, KeyboardInterrupt):
        # Gọi handler mặc định cho KeyboardInterrupt
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    error_handler.handle_error(exc_value)

# Đăng ký global exception handler
sys.excepthook = handle_exception 