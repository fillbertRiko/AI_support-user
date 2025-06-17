import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import logging
import json
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class SecurityManager:
    def __init__(self):
        self._key = None
        self._fernet = None
        self._initialize()

    def _initialize(self):
        """Khởi tạo security manager với key được tạo từ master password"""
        try:
            # Tạo hoặc load key từ file
            key_file = os.path.join("data", "security", ".key")
            os.makedirs(os.path.dirname(key_file), exist_ok=True)

            if os.path.exists(key_file):
                with open(key_file, "rb") as f:
                    self._key = f.read()
            else:
                # Tạo key mới
                self._key = Fernet.generate_key()
                with open(key_file, "wb") as f:
                    f.write(self._key)

            self._fernet = Fernet(self._key)
            logger.info("Security manager initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize security manager: {str(e)}")
            raise

    def encrypt_data(self, data: Dict[str, Any]) -> str:
        """Mã hóa dữ liệu"""
        try:
            json_data = json.dumps(data)
            encrypted_data = self._fernet.encrypt(json_data.encode())
            return base64.b64encode(encrypted_data).decode()
        except Exception as e:
            logger.error(f"Encryption failed: {str(e)}")
            raise

    def decrypt_data(self, encrypted_data: str) -> Dict[str, Any]:
        """Giải mã dữ liệu"""
        try:
            decoded_data = base64.b64decode(encrypted_data)
            decrypted_data = self._fernet.decrypt(decoded_data)
            return json.loads(decrypted_data.decode())
        except Exception as e:
            logger.error(f"Decryption failed: {str(e)}")
            raise

    def secure_store(self, key: str, data: Dict[str, Any]) -> None:
        """Lưu trữ dữ liệu an toàn"""
        try:
            storage_file = os.path.join("data", "security", f"{key}.enc")
            encrypted_data = self.encrypt_data(data)
            
            with open(storage_file, "w") as f:
                f.write(encrypted_data)
            
            logger.info(f"Data securely stored for key: {key}")
        except Exception as e:
            logger.error(f"Secure storage failed: {str(e)}")
            raise

    def secure_retrieve(self, key: str) -> Optional[Dict[str, Any]]:
        """Lấy dữ liệu đã được lưu trữ an toàn"""
        try:
            storage_file = os.path.join("data", "security", f"{key}.enc")
            
            if not os.path.exists(storage_file):
                return None
                
            with open(storage_file, "r") as f:
                encrypted_data = f.read()
                
            return self.decrypt_data(encrypted_data)
        except Exception as e:
            logger.error(f"Secure retrieval failed: {str(e)}")
            raise

    def secure_delete(self, key: str) -> None:
        """Xóa dữ liệu đã được lưu trữ an toàn"""
        try:
            storage_file = os.path.join("data", "security", f"{key}.enc")
            
            if os.path.exists(storage_file):
                os.remove(storage_file)
                logger.info(f"Securely deleted data for key: {key}")
        except Exception as e:
            logger.error(f"Secure deletion failed: {str(e)}")
            raise

    def hash_password(self, password: str, salt: Optional[bytes] = None) -> tuple[bytes, bytes]:
        """Tạo hash cho password với salt"""
        if salt is None:
            salt = os.urandom(16)
            
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key, salt

    def verify_password(self, password: str, stored_key: bytes, salt: bytes) -> bool:
        """Xác thực password"""
        try:
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            
            key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
            return key == stored_key
        except Exception as e:
            logger.error(f"Password verification failed: {str(e)}")
            return False 