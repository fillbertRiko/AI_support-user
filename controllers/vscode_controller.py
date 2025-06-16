import os
import subprocess
import logging
from models.vscode import VSCode
from services.update_optimizer_service import UpdateOptimizerService

logger = logging.getLogger(__name__)

class VSCodeController:
    def __init__(self, db, fact_collector):
        self.vscode_model = VSCode()
        self.update_optimizer = UpdateOptimizerService()
        self.db = db
        self.fact_collector = fact_collector

    def open_vscode(self):
        """Mở VSCode"""
        try:
            vscode_path = r"H:\Microsoft VS Code\Code.exe"
            subprocess.Popen([vscode_path])
            logger.info(f"Opened VSCode at {vscode_path}")

            # Lấy facts hiện tại và ghi log tương tác người dùng
            current_facts = self.fact_collector()
            self.db.log_user_interaction("open_vscode", current_facts)

            self.update_optimizer.log_update(
                service_type='vscode',
                data_changed=False,
                user_interaction=True,
                response_time=0.1
            )
            return True
        except Exception as e:
            logger.error(f"Error opening VSCode: {str(e)}")
            return False

    def get_settings(self):
        """Lấy cài đặt VSCode"""
        return self.vscode_model.get_settings()

    def update_settings(self, data):
        """Cập nhật cài đặt VSCode"""
        return self.vscode_model.update_settings(data) 