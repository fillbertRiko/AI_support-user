import pandas as pd
import os
import logging

logger = logging.getLogger(__name__)

class VSCode:
    def __init__(self):
        self.vscode_settings_dir = 'data/excel'
        self.vscode_settings_file = os.path.join(self.vscode_settings_dir, 'vscode.xlsx')
        self._ensure_vscode_file_exists()

    def _ensure_vscode_file_exists(self):
        """Đảm bảo thư mục và file cài đặt VSCode tồn tại"""
        os.makedirs(self.vscode_settings_dir, exist_ok=True)
        if not os.path.exists(self.vscode_settings_file):
            # Tạo một mẫu cài đặt VSCode
            data = {
                'Extension Name': [
                    'Python',
                    'Jupyter',
                    'Pylance',
                    'GitLens',
                    'Docker',
                    'ESLint',
                    'Prettier',
                    'Live Server',
                    'Remote - SSH',
                    'REST Client'
                ],
                'Description': [
                    'Python IntelliSense, Linting, Debugging, etc.',
                    'Jupyter Notebooks, live code, and interactive programming.',
                    'Rich IntelliSense for Python.',
                    'Supercharge Git capabilities within VS Code.',
                    'Easily build, manage, and deploy containerized applications.',
                    'Integrates ESLint JavaScript into VS Code.',
                    'Code formatter.',
                    'Launch a development local Server with live reload feature.',
                    'Open any folder on a remote machine using SSH and take advantage of VS Code\'s full feature set.',
                    'Send HTTP request and view response in VS Code.'
                ],
                'Status': ['Installed'] * 10
            }
            df = pd.DataFrame(data)
            try:
                df.to_excel(self.vscode_settings_file, index=False, engine='openpyxl')
                logger.info(f"Created new VSCode settings template at: {self.vscode_settings_file}")
            except Exception as e:
                logger.error(f"Error creating VSCode settings file: {str(e)}")

    def get_settings(self) -> pd.DataFrame:
        """Lấy cài đặt VSCode"""
        try:
            if not os.path.exists(self.vscode_settings_file):
                self._ensure_vscode_file_exists() # Đảm bảo file tồn tại trước khi đọc
            return pd.read_excel(self.vscode_settings_file, engine='openpyxl')
        except Exception as e:
            logger.error(f"Error reading VSCode settings: {str(e)}")
            return pd.DataFrame()

    def update_settings(self, df: pd.DataFrame) -> bool:
        """Cập nhật cài đặt VSCode"""
        try:
            df.to_excel(self.vscode_settings_file, index=False, engine='openpyxl')
            logger.info(f"VSCode settings updated successfully at: {self.vscode_settings_file}")
            return True
        except Exception as e:
            logger.error(f"Error updating VSCode settings: {str(e)}")
            return False 