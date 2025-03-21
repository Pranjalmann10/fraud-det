from .rule_based import RuleBasedFraudDetector
from .ai_model import AIFraudDetector

class CombinedFraudDetector:
    """
    A combined fraud detection model that uses both rule-based and AI approaches
    """
    
    def __init__(self, rule_config=None, custom_rules=None, ai_model_path=None, ai_weight=0.7):
        """
        Initialize the combined detector
        
        Args:
            rule_config (dict): Configuration for the rule-based detector
            custom_rules (list): List of custom rules from the database
            ai_model_path (str): Path to the pre-trained AI model
            ai_weight (float): Weight given to the AI model's prediction (between 0 and 1)
        """
        self.rule_detector = RuleBasedFraudDetector(config=rule_config, custom_rules=custom_rules)
        self.ai_detector = AIFraudDetector(model_path=ai_model_path)
        self.ai_weight = ai_weight
    
    def set_custom_rules(self, custom_rules):
        """
        Update the custom rules for the rule-based detector
        
        Args:
            custom_rules (list): List of custom rules
        """
        self.rule_detector.set_custom_rules(custom_rules)
    
    def detect_fraud(self, transaction, transaction_history=None, threshold=0.5):
        """
        Detect fraud using both rule-based and AI approaches
        
        Args:
            transaction (dict): The transaction data
            transaction_history (list): Optional list of previous transactions
            threshold (float): The threshold for considering a transaction fraudulent
            
        Returns:
            tuple: (is_fraudulent (bool), combined_score (float), rule_score (float), ai_score (float), reasons (dict))
        """
        # Get rule-based prediction
        rule_is_fraud, rule_score, rule_reason = self.rule_detector.is_fraudulent(
            transaction, 
            transaction_history, 
            threshold
        )
        
        # Get AI prediction
        ai_is_fraud, ai_score = self.ai_detector.predict(transaction)
        
        # Adjust weights based on transaction amount
        amount = transaction.get("amount", 0)
        adjusted_ai_weight = self.ai_weight
        
        # For large transactions, give more weight to rule-based detection
        if amount > 25000:
            adjusted_ai_weight = 0.4  # Give more weight to rule-based for large amounts
        
        # Combine scores with adjusted weights
        combined_score = (adjusted_ai_weight * ai_score) + ((1 - adjusted_ai_weight) * rule_score)
        
        # For very large transactions, ensure a minimum fraud score
        if amount > 50000:
            combined_score = max(combined_score, 0.7)
        elif amount > 25000:
            combined_score = max(combined_score, 0.5)
        elif amount > 10000:
            combined_score = max(combined_score, 0.3)
        
        # Determine if transaction is fraudulent based on combined score
        is_fraudulent = combined_score >= threshold
        
        # Prepare reasons
        reasons = {
            "rule_reason": rule_reason,
            "ai_weight": adjusted_ai_weight,
            "rule_weight": 1 - adjusted_ai_weight,
            "amount_threshold_applied": amount > 10000
        }
        
        return is_fraudulent, combined_score, rule_score, ai_score, reasons
