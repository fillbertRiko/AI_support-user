import unittest
from src.utils.security import Security # type: ignore

class TestSecurity(unittest.TestCase):
    def setUp(self):
        self.security = Security()

    def test_encrypt_decrypt(self):
        original_data = 'test data'
        encrypted_data = self.security.encrypt(original_data)
        decrypted_data = self.security.decrypt(encrypted_data)
        self.assertEqual(original_data, decrypted_data)

if __name__ == '__main__':
    unittest.main() 