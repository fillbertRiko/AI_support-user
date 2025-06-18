import logging
import json
from collections import defaultdict
from models.database import DatabaseManager
from models.knowledge_base import KnowledgeBase

logger = logging.getLogger(__name__)

class RuleSuggester:
    def __init__(self, db: DatabaseManager, knowledge_base: KnowledgeBase):
        self.db = db
        self.knowledge_base = knowledge_base
        logger.info("Rule Suggester initialized.")

    def suggest_rules(self) -> list:
        """Phân tích nhật ký tương tác của người dùng để đề xuất các quy tắc mới.
        Trả về danh sách các quy tắc được đề xuất (chưa được thêm vào KB).
        """
        logger.info("Bắt đầu đề xuất quy tắc...")
        interactions = self.db.execute_query("SELECT action_type, facts FROM user_interactions_log ORDER BY timestamp DESC LIMIT 100")
        
        # Bỏ qua các tương tác cũ hơn 7 ngày
        # TODO: Thêm logic lọc theo thời gian vào query SQL để hiệu quả hơn

        fact_action_counts = defaultdict(lambda: defaultdict(int))

        for interaction in interactions:
            action_type = interaction["action_type"]
            try:
                facts = json.loads(interaction["facts"])
                # Chuyển đổi facts thành tuple để có thể dùng làm key trong dict
                # Sắp xếp các fact để đảm bảo thứ tự không ảnh hưởng đến key
                fact_key = tuple(sorted(facts.items()))
                fact_action_counts[fact_key][action_type] += 1
            except json.JSONDecodeError as e:
                logger.error(f"Lỗi giải mã facts từ log: {e}")
                continue
            except TypeError as e:
                logger.error(f"Lỗi kiểu dữ liệu khi xử lý facts: {e}")
                continue
        
        suggested_rules = []
        existing_rules = self.knowledge_base.get_rules()
        existing_rule_conditions = [
            tuple(sorted({"fact": cond["fact"], "operator": cond["operator"], "value": cond["value"]} for cond in rule_data["conditions"]))
            for rule_name, rule_data in existing_rules.items()
        ]

        for fact_key, action_counts in fact_action_counts.items():
            # Tìm hành động phổ biến nhất cho tập hợp facts này
            most_common_action = max(action_counts, key=action_counts.get)
            count = action_counts[most_common_action]

            # Đặt ngưỡng để đề xuất (ví dụ: hành động xảy ra ít nhất 3 lần với cùng một tập facts)
            if count >= 3:
                # Chuyển đổi fact_key trở lại dạng dict để xây dựng điều kiện
                facts_dict = dict(fact_key)
                conditions = []
                for fact_name, fact_value in facts_dict.items():
                    # Đối với ví dụ đơn giản, chúng ta chỉ dùng toán tử '==' hoặc 'contains'
                    if isinstance(fact_value, str):
                        if fact_value == "mưa" or fact_value == "mây đen u ám": # Các trường hợp đặc biệt cho thời tiết có thể dùng contains
                            operator = "contains"
                        else:
                            operator = "=="
                    elif isinstance(fact_value, bool):
                        operator = "=="
                    else:
                        operator = "=="

                    conditions.append({"fact": fact_name, "operator": operator, "value": fact_value})
                
                # Kiểm tra xem quy tắc có trùng lặp không
                new_rule_conditions_tuple = tuple(sorted({"fact": cond["fact"], "operator": cond["operator"], "value": cond["value"]} for cond in conditions))
                if new_rule_conditions_tuple in existing_rule_conditions:
                    logger.debug(f"Quy tắc trùng lặp đã tồn tại: {facts_dict} -> {most_common_action}")
                    continue

                # Xây dựng mô tả quy tắc
                description = f"Nếu " + ", ".join([f"{k} là {v}" for k, v in facts_dict.items()]) + f", thì đề xuất {most_common_action}."
                
                # Xây dựng hành động đề xuất
                actions = []
                if most_common_action == "open_vscode":
                    actions.append({"type": "recommendation", "message": "Có vẻ bạn thường mở VSCode khi..."})
                    actions.append({"type": "action", "command": "open_vscode"})
                elif most_common_action == "open_schedule":
                    actions.append({"type": "recommendation", "message": "Có vẻ bạn thường mở lịch trình khi..."})
                    actions.append({"type": "action", "command": "open_schedule"})
                # Thêm các hành động khác nếu cần

                if not actions:
                    logger.warning(f"Không thể tạo hành động cho hành động: {most_common_action}")
                    continue

                suggested_rules.append({
                    "description": description,
                    "conditions": conditions,
                    "actions": actions
                })
        logger.info(f"Đã đề xuất {len(suggested_rules)} quy tắc mới.")
        return suggested_rules

    def infer_rules(self, facts: dict) -> list:
        """Suy luận quy tắc dựa trên facts hiện tại. Đây là alias cho suggest_rules để tương thích."""
        logger.info("Bắt đầu suy luận quy tắc từ facts...")
        
        # Sử dụng InferenceEngine để chạy suy luận
        from controllers.inference_engine import InferenceEngine
        inference_engine = InferenceEngine(self.knowledge_base)
        results = inference_engine.run_inference(facts)
        
        # Chuyển đổi kết quả thành danh sách recommendations
        recommendations = []
        for result in results:
            if result.get('type') == 'recommendation':
                recommendations.append(result.get('message', ''))
        
        logger.info(f"Đã suy luận được {len(recommendations)} recommendations")
        return recommendations 