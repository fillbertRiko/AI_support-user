import os
import logging
from models.schedule import Schedule
from services.update_optimizer_service import UpdateOptimizerService

logger = logging.getLogger(__name__)

class ScheduleController:
    def __init__(self, db, fact_collector):
        self.schedule_model = Schedule()
        self.update_optimizer = UpdateOptimizerService()
        self.db = db
        self.fact_collector = fact_collector

    def open_schedule(self):
        """Mở file thời khóa biểu"""
        try:
            schedule_path = r"H:\work\Thời khoá biểu.xlsx"
            if os.path.exists(schedule_path):
                os.startfile(schedule_path)
                logger.info(f"Opened schedule file at {schedule_path}")
                
                # Lấy facts hiện tại và ghi log tương tác người dùng
                current_facts = self.fact_collector()
                self.db.log_user_interaction("open_schedule", current_facts)

                self.update_optimizer.log_update(
                    service_type='schedule',
                    data_changed=False,
                    user_interaction=True,
                    response_time=0.1
                )
                return True
            else:
                logger.error(f"Schedule file not found at {schedule_path}")
                return False
        except Exception as e:
            logger.error(f"Error opening schedule file: {str(e)}")
            return False

    def get_schedule_data(self):
        """Lấy dữ liệu thời khóa biểu"""
        return self.schedule_model.get_schedule_from_excel()

    def update_schedule_data(self, data):
        """Cập nhật dữ liệu thời khóa biểu"""
        return self.schedule_model.update_schedule(data) 
    
    def save_schedule_to_db(self, df):
        #xoa toan bo du lieu cu
        with self.db.transaction() as conn:
            #cot dau la thoi gian, cac cot sau la cac ngay
            for i, row in df.iterrows():
                time_slot = row['Thời gian']
                for day in df.columns[1:]:
                    subject = row[day]
                    conn.execute(
                        "INSERT INTO schedule (day_of_week, start_time, end_time, subject, location) VALUES (?, ?, ?, ?, ?)",
                        (day, time_slot.split('-')[0].strip(), time_slot.split('-')[1].strip(), subject, "")
                    )