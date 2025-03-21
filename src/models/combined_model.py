from .rule_based import RuleBasedFraudDetector
from .ai_model import AIFraudDetector

class CombinedFraudDetector:
    """
    A combined fraud detection model that uses both rule-based and AI approaches
    """
    
    def __init__(self, rule_config=None, ai_model_path=None, ai_weight=0.7):
        """
        Initialize the combined detector
        
        Args:
            rule_config (dict): Configuration for the rule-based detector
            ai_model_path (str): Path to the pre-trained AI model
            ai_weight (float): Weight given to the AI model's prediction (between 0 and 1)
        """
        self.rule_detector = RuleBasedFraudDetector(config=rule_config)
        self.ai_detector = AIFraudDetector(model_path=ai_model_path)
        self.ai_weight = ai_weight
    
    def detect_fraud(self, transaction, transaction_history=None, threshold=0.5):
        """
        Detect fraud using both rule-based and AI approaches
        
        Args:
            transaction (dict): The transaction data
            transaction_history (list): Optional list of previous transactions
            threshold (float): The threshold for considering a transaction fraudulent
            
        Returns:
            tuple: (is_fraudulent (bool), combined_score (float), rule_score (float), ai_score (float))
        """
        # Get rule-based prediction
        rule_is_fraud, rule_score = self.rule_detector.is_fraudulent(
            transaction, 
            transaction_history, 
            threshold
        )
        
        # Get AI prediction
        ai_is_fraud, ai_score = self.ai_detector.predict(transaction)
        
        # Combine scores
        combined_score = (self.ai_weight * ai_score) + ((1 - self.ai_weight) * rule_score)
        
        # Determine if transaction is fraudulent based on combined score
        is_fraudulent = combined_score >= threshold
        
        return is_fraudulent, combined_score, rule_score, ai_score
