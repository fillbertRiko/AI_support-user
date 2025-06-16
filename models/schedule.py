import pandas as pd
import os
import logging

logger = logging.getLogger(__name__)

class Schedule:
    def __init__(self):
        self.excel_dir = os.path.join('data', 'excel')
        self.schedule_file = os.path.join(self.excel_dir, 'thoi_khoa_bieu.xlsx')
        # self._ensure_schedule_file_exists() # Tạm thời bỏ qua việc kiểm tra và tạo file Excel

    def _ensure_schedule_file_exists(self):
        """Đảm bảo file thời khóa biểu tồn tại - Không sử dụng khi hardcode data"""
        # Logic này sẽ không được gọi khi dữ liệu được hardcode trong get_schedule
        if not os.path.exists(self.excel_dir):
            os.makedirs(self.excel_dir)
            logger.info(f"Created directory: {self.excel_dir}")

        if not os.path.exists(self.schedule_file):
            logger.info("Creating schedule template...")
            data = {
                'Thứ 2': [''] * 10,
                'Thứ 3': [''] * 10,
                'Thứ 4': [''] * 10,
                'Thứ 5': [''] * 10,
                'Thứ 6': [''] * 10,
                'Thứ 7': [''] * 10,
                'Chủ Nhật': [''] * 10
            }
            df = pd.DataFrame(data)
            try:
                df.to_excel(self.schedule_file, index=False, engine='openpyxl')
                logger.info(f"Created new schedule template at: {self.schedule_file}")
            except Exception as e:
                logger.error(f"Error creating schedule file: {str(e)}")

    def get_schedule(self) -> pd.DataFrame:
        """Trả về dữ liệu thời khóa biểu đã hardcode để hiển thị UI."""
        # Dữ liệu thời khóa biểu đã hardcode dựa trên hình ảnh bạn cung cấp
        data = {
            'Thời gian': ['06:00 – 08:00', '08:30 – 10:30', '14:00 – 16:00', '16:30 – 18:00', '20:00 – 22:00'],
            'Thứ Hai': [
                'Lập trình hướng đối\ntượng',
                'Trí tuệ nhân tạo',
                'Nguyên lý Hệ điều\nhành',
                'Tư tưởng HCM',
                'Gym (tối)'
            ],
            'Thứ Ba': [
                'Trí tuệ nhân tạo',
                'Nguyên lý Hệ ĐH',
                'Tư tưởng HCM',
                'Tiếng Anh 1',
                'Gym (tối)'
            ],
            'Thứ Tư': [
                'Nguyên lý Hệ điều\nhành',
                'Tư tưởng HCM',
                'Tiếng Anh 1',
                'Lập trình HĐTD',
                'Gym (tối)'
            ],
            'Thứ Năm': [
                'Tư tưởng HCM',
                'Tiếng Anh 1',
                'Lập trình HĐTD',
                'Trí tuệ nhân tạo',
                'Gym (tối)'
            ],
            'Thứ Sáu': [
                'Tiếng Anh 1',
                'Lập trình HĐTD',
                'Trí tuệ nhân tạo',
                'Nguyên lý HĐH',
                'Gym (tối)'
            ],
            'Thứ Bảy': [
                '(Đang đi làm)',
                '(Đang đi làm)',
                '(Đang đi làm đến\n17:00)',
                '17:00 – 18:30:\nGym\n18:30 – 20:00:\nĂn tối/ nghỉ',
                '20:00 – 22:00: Dự án\nnhỏ hàng tuần'
            ],
            'Chủ Nhật': [
                'Ôn tập nhanh tất cả\nmôn (2h)',
                'Hoàn thiện dự án\nnhỏ hàng tuần (2h)',
                'Buffer & ôn chuyên\nsâu (2h)',
                'Nghỉ/nghỉ linh hoạt',
                '20:00 – 21:30: Gym\n(tùy chọn)'
            ]
        }
        df = pd.DataFrame(data)
        return df

    def update_schedule(self, df: pd.DataFrame) -> bool:
        """Cập nhật dữ liệu thời khóa biểu - Không sử dụng khi hardcode data"""
        logger.warning("Schedule update method is not active as data is hardcoded.")
        return False 