import logging
import json
import os

logger = logging.getLogger(__name__)

# Đường dẫn đến file lưu trữ cơ sở tri thức
KNOWLEDGE_FILE = os.path.join(os.path.dirname(__file__), 'knowledge_base.json')

class KnowledgeBase:
    def __init__(self):
        self.rules = self._load_rules()

    def _load_rules(self):
        """Tải các quy tắc từ cơ sở tri thức (ưu tiên từ file, sau đó hardcode)."""
        if os.path.exists(KNOWLEDGE_FILE):
            try:
                with open(KNOWLEDGE_FILE, 'r', encoding='utf-8') as f:
                    rules = json.load(f)
                logger.info(f"Loaded {len(rules)} rules from {KNOWLEDGE_FILE}.")
                return rules
            except json.JSONDecodeError as e:
                logger.error(f"Error decoding JSON from knowledge base file: {e}. Using default rules.")
            except Exception as e:
                logger.error(f"Error loading knowledge base file: {e}. Using default rules.")

        logger.info("Knowledge base file not found or error occurred. Loading default rules.")
        rules = {
            "rule_1_rainy_gym": {
                "description": "Nếu trời mưa và có lịch tập Gym, đề xuất mang ô/áo mưa.",
                "conditions": [
                    {"fact": "weather_condition", "operator": "contains", "value": "mưa"},
                    {"fact": "schedule_activity", "operator": "==", "value": "Gym"}
                ],
                "actions": [
                    {"type": "recommendation", "message": "Thời tiết đang mưa, hãy mang theo ô hoặc áo mưa khi đi tập Gym nhé!"}
                ]
            },
            "rule_2_morning_vscode": {
                "description": "Nếu là buổi sáng và VSCode chưa mở, đề xuất mở VSCode.",
                "conditions": [
                    {"fact": "time_category", "operator": "==", "value": "morning"},
                    {"fact": "vscode_status", "operator": "==", "value": "closed"}
                ],
                "actions": [
                    {"type": "recommendation", "message": "Buổi sáng rồi, bạn có muốn mở VSCode để bắt đầu công việc không?"},
                    {"type": "action", "command": "open_vscode"}
                ]
            },
            "rule_3_weekend_relax": {
                "description": "Nếu là cuối tuần và không có lịch trình cụ thể, đề xuất nghỉ ngơi/giải trí.",
                "conditions": [
                    {"fact": "day_of_week", "operator": "in", "value": ["Saturday", "Sunday"]},
                    {"fact": "schedule_empty_or_flexible", "operator": "==", "value": True}
                ],
                "actions": [
                    {"type": "recommendation", "message": "Cuối tuần rồi, hãy thư giãn và tận hưởng thời gian rảnh nhé!"}
                ]
            },
            "rule_4_afternoon_break": {
                "description": "Nếu là buổi chiều và lịch trình trống, đề xuất nghỉ ngơi.",
                "conditions": [
                    {"fact": "time_category", "operator": "==", "value": "afternoon"},
                    {"fact": "schedule_empty_or_flexible", "operator": "==", "value": True}
                ],
                "actions": [
                    {"type": "recommendation", "message": "Buổi chiều rảnh rỗi, bạn có thể nghỉ ngơi một chút để lấy lại năng lượng!"}
                ]
            },
            "rule_5_evening_relax": {
                "description": "Nếu là buổi tối và lịch trình trống, đề xuất thư giãn.",
                "conditions": [
                    {"fact": "time_category", "operator": "==", "value": "evening"},
                    {"fact": "schedule_empty_or_flexible", "operator": "==", "value": True}
                ],
                "actions": [
                    {"type": "recommendation", "message": "Buổi tối rồi, bạn có thể thư giãn và tận hưởng thời gian rảnh rỗi!"}
                ]
            }
        }
        self._save_rules(rules) # Lưu các quy tắc mặc định nếu file không tồn tại
        logger.info(f"Loaded {len(rules)} default rules and saved to file.")
        return rules

    def _save_rules(self, rules_to_save: dict):
        """Lưu các quy tắc vào file JSON."""
        try:
            with open(KNOWLEDGE_FILE, 'w', encoding='utf-8') as f:
                json.dump(rules_to_save, f, indent=4, ensure_ascii=False)
            logger.info(f"Rules saved to {KNOWLEDGE_FILE}.")
        except Exception as e:
            logger.error(f"Error saving rules to file: {e}")

    def get_rules(self):
        """Trả về tất cả các quy tắc."""
        return self.rules

    def add_rule(self, rule_name: str, rule_data: dict):
        """Thêm một quy tắc mới vào cơ sở tri thức và lưu lại."""
        if rule_name not in self.rules:
            self.rules[rule_name] = rule_data
            self._save_rules(self.rules)
            logger.info(f"Added new rule: {rule_name}")
            return True
        logger.warning(f"Rule {rule_name} already exists.")
        return False

    def remove_rule(self, rule_name: str):
        """Xóa một quy tắc khỏi cơ sở tri thức và lưu lại."""
        if rule_name in self.rules:
            del self.rules[rule_name]
            self._save_rules(self.rules)
            logger.info(f"Removed rule: {rule_name}")
            return True
        logger.warning(f"Rule {rule_name} not found.")
        return False 