import logging
from models.knowledge_base import KnowledgeBase

logger = logging.getLogger(__name__)

class InferenceEngine:
    def __init__(self, knowledge_base: KnowledgeBase):
        self.knowledge_base = knowledge_base
        logger.info("Inference Engine initialized.")

    def _evaluate_condition(self, fact_value: any, operator: str, condition_value: any) -> bool:
        """Đánh giá một điều kiện đơn lẻ."""
        logger.debug(f"Đánh giá điều kiện: fact_value={fact_value}, operator={operator}, condition_value={condition_value}")
        
        if operator == "==":
            result = fact_value == condition_value
        elif operator == "!=":
            result = fact_value != condition_value
        elif operator == ">":
            result = fact_value > condition_value
        elif operator == "<":
            result = fact_value < condition_value
        elif operator == ">=":
            result = fact_value >= condition_value
        elif operator == "<=":
            result = fact_value <= condition_value
        elif operator == "contains":
            result = condition_value in fact_value if isinstance(fact_value, str) else False
        elif operator == "in":
            result = fact_value in condition_value if isinstance(condition_value, list) else False
        else:
            result = False
            
        logger.debug(f"Kết quả đánh giá: {result}")
        return result

    def run_inference(self, facts: dict) -> list:
        """Chạy quá trình suy luận dựa trên các dữ kiện đã cho.
        Trả về danh sách các từ điển chứa { 'type': ..., 'message': ..., 'command': ..., 'rule_description': ... }
        """
        activated_results = []
        rules = self.knowledge_base.get_rules()

        logger.info(f"Bắt đầu suy luận với facts: {facts}")
        logger.info(f"Số lượng quy tắc: {len(rules)}")

        for rule_name, rule_data in rules.items():
            logger.info(f"\nĐánh giá quy tắc: {rule_name}")
            logger.info(f"Mô tả: {rule_data['description']}")
            
            all_conditions_met = True
            for condition in rule_data["conditions"]:
                fact_name = condition["fact"]
                operator = condition["operator"]
                condition_value = condition["value"]

                if fact_name not in facts:
                    all_conditions_met = False
                    logger.warning(f"Fact '{fact_name}' không tồn tại cho quy tắc '{rule_name}'")
                    break
                
                fact_value = facts[fact_name]
                logger.info(f"Đánh giá điều kiện: {fact_name} {operator} {condition_value}")
                logger.info(f"Giá trị thực tế: {fact_value}")

                if not self._evaluate_condition(fact_value, operator, condition_value):
                    all_conditions_met = False
                    logger.info(f"Điều kiện không thỏa mãn cho quy tắc '{rule_name}'")
                    break
            
            if all_conditions_met:
                logger.info(f"Quy tắc '{rule_name}' được kích hoạt")
                # Add rule description to each action
                for action in rule_data["actions"]:
                    action_with_description = action.copy()
                    action_with_description["rule_description"] = rule_data["description"]
                    activated_results.append(action_with_description)
                    logger.info(f"Thêm hành động: {action_with_description}")
            else:
                logger.info(f"Quy tắc '{rule_name}' không được kích hoạt")
        
        logger.info(f"Kết thúc suy luận. Số hành động được kích hoạt: {len(activated_results)}")
        return activated_results 