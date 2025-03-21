class RuleBasedFraudDetector:
    """
    A rule-based fraud detection model that applies configurable rules to transactions
    """
    
    def __init__(self, config=None):
        """
        Initialize the rule-based detector with configuration
        
        Args:
            config (dict): Configuration for the rules
        """
        self.config = config or self.get_default_config()
    
    def get_default_config(self):
        """
        Get the default configuration for the rules
        """
        return {
            "amount_threshold": 10000.0,  # Transactions above this amount are suspicious
            "high_risk_channels": ["web", "mobile_app"],  # Channels with higher fraud risk
            "high_risk_payment_modes": ["credit_card", "digital_wallet"],  # Payment modes with higher fraud risk
            "suspicious_time_window": {  # Time window for suspicious activity (24-hour format)
                "start": "00:00",
                "end": "05:00"
            },
            "velocity_check": {  # Check for multiple transactions in a short time
                "max_transactions": 5,
                "time_window_minutes": 10
            }
        }
    
    def update_config(self, new_config):
        """
        Update the configuration with new values
        
        Args:
            new_config (dict): New configuration values
        """
        self.config.update(new_config)
    
    def check_amount_threshold(self, transaction):
        """
        Check if the transaction amount exceeds the threshold
        """
        return transaction["amount"] > self.config["amount_threshold"]
    
    def check_high_risk_channel(self, transaction):
        """
        Check if the transaction is from a high-risk channel
        """
        return transaction["channel"] in self.config["high_risk_channels"]
    
    def check_high_risk_payment_mode(self, transaction):
        """
        Check if the transaction uses a high-risk payment mode
        """
        return transaction["payment_mode"] in self.config["high_risk_payment_modes"]
    
    def calculate_risk_score(self, transaction, transaction_history=None):
        """
        Calculate a risk score for the transaction based on rules
        
        Args:
            transaction (dict): The transaction data
            transaction_history (list): Optional list of previous transactions
            
        Returns:
            float: Risk score between 0.0 and 1.0
        """
        score = 0.0
        
        # Check amount threshold
        if self.check_amount_threshold(transaction):
            score += 0.3
        
        # Check high-risk channel
        if self.check_high_risk_channel(transaction):
            score += 0.2
        
        # Check high-risk payment mode
        if self.check_high_risk_payment_mode(transaction):
            score += 0.2
        
        # Additional rules can be implemented here
        
        # Normalize score to be between 0 and 1
        score = min(score, 1.0)
        
        return score
    
    def is_fraudulent(self, transaction, transaction_history=None, threshold=0.5):
        """
        Determine if a transaction is fraudulent based on the risk score
        
        Args:
            transaction (dict): The transaction data
            transaction_history (list): Optional list of previous transactions
            threshold (float): The threshold for considering a transaction fraudulent
            
        Returns:
            tuple: (is_fraudulent (bool), risk_score (float))
        """
        risk_score = self.calculate_risk_score(transaction, transaction_history)
        return risk_score >= threshold, risk_score
