import os
import pytest

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Thiết lập môi trường test"""
    # Tạo thư mục test data
    os.makedirs("tests/data", exist_ok=True)
    
    # Thiết lập biến môi trường test
    os.environ["TESTING"] = "true"
    
    yield
    
    # Dọn dẹp sau khi test
    if os.path.exists("tests/data"):
        for file in os.listdir("tests/data"):
            os.remove(os.path.join("tests/data", file))
        os.rmdir("tests/data") 