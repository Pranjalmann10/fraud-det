class RuleBasedFraudDetector:
    """
    A rule-based fraud detection model that applies configurable rules to transactions
    """
    
    def __init__(self, config=None, custom_rules=None):
        """
        Initialize the rule-based detector with configuration
        
        Args:
            config (dict): Configuration for the rules
            custom_rules (list): List of custom rules from the database
        """
        self.config = config or self.get_default_config()
        self.custom_rules = custom_rules or []
    
    def get_default_config(self):
        """
        Get the default configuration for the rules
        """
        return {
            "amount_threshold": 50000.0,  # Transactions above this amount are suspicious
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
    
    def set_custom_rules(self, custom_rules):
        """
        Set the custom rules from the database
        
        Args:
            custom_rules (list): List of custom rules
        """
        self.custom_rules = custom_rules
    
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
    
    def apply_custom_rule(self, rule, transaction):
        """
        Apply a custom rule to a transaction
        
        Args:
            rule (dict): The custom rule to apply
            transaction (dict): Transaction data
            
        Returns:
            tuple: (matches (bool), score (float), reason (str))
        """
        # Handle both attribute-style access and dictionary-style access for rules
        field = rule.field if hasattr(rule, 'field') else rule.get('field')
        operator = rule.operator if hasattr(rule, 'operator') else rule.get('operator')
        value = rule.value if hasattr(rule, 'value') else rule.get('value')
        score = rule.score if hasattr(rule, 'score') else rule.get('score', 0.5)
        
        # If field doesn't exist in transaction, return False
        if field not in transaction and field != "custom":
            return False, 0.0, ""
        
        # For custom field type, use advanced_config
        advanced_config = rule.advanced_config if hasattr(rule, 'advanced_config') else rule.get('advanced_config')
        if field == "custom" and advanced_config:
            # Implement custom logic based on advanced_config
            return False, 0.0, ""
        
        # Extract transaction value
        transaction_value = transaction.get(field)
        
        # Apply operator comparison
        matches = False
        reason = ""
        
        # Convert string value to appropriate type if needed
        if operator in [">", "<", ">=", "<="]:
            try:
                value = float(value)
                transaction_value = float(transaction_value) if transaction_value is not None else 0
            except (ValueError, TypeError):
                return False, 0.0, ""
                
        if operator == "==":
            matches = str(transaction_value) == str(value)
            reason = f"{field} equals {value}"
        elif operator == "!=":
            matches = str(transaction_value) != str(value)
            reason = f"{field} not equals {value}"
        elif operator == ">":
            matches = transaction_value > value
            reason = f"{field} greater than {value}"
        elif operator == "<":
            matches = transaction_value < value
            reason = f"{field} less than {value}"
        elif operator == ">=":
            matches = transaction_value >= value
            reason = f"{field} greater than or equal to {value}"
        elif operator == "<=":
            matches = transaction_value <= value
            reason = f"{field} less than or equal to {value}"
        elif operator == "in":
            if isinstance(value, str):
                try:
                    value_list = value.split(",")
                    matches = str(transaction_value) in [v.strip() for v in value_list]
                    reason = f"{field} in list {value}"
                except:
                    matches = False
            else:
                matches = False
        elif operator == "not_in":
            if isinstance(value, str):
                try:
                    value_list = value.split(",")
                    matches = str(transaction_value) not in [v.strip() for v in value_list]
                    reason = f"{field} not in list {value}"
                except:
                    matches = False
            else:
                matches = False
        elif operator == "contains":
            matches = isinstance(transaction_value, str) and isinstance(value, str) and value in transaction_value
            reason = f"{field} contains {value}"
        elif operator == "not_contains":
            matches = isinstance(transaction_value, str) and isinstance(value, str) and value not in transaction_value
            reason = f"{field} does not contain {value}"
        elif operator == "starts_with":
            matches = isinstance(transaction_value, str) and isinstance(value, str) and transaction_value.startswith(value)
            reason = f"{field} starts with {value}"
        elif operator == "ends_with":
            matches = isinstance(transaction_value, str) and isinstance(value, str) and transaction_value.endswith(value)
            reason = f"{field} ends with {value}"
        
        return matches, score if matches else 0.0, reason if matches else ""
    
    def calculate_risk_score(self, transaction, transaction_history=None):
        """
        Calculate a risk score for the transaction based on rules
        
        Args:
            transaction (dict): The transaction data
            transaction_history (list): Optional list of previous transactions
            
        Returns:
            tuple: (score (float), reason (str))
        """
        score = 0.0
        reasons = []
        
        # Check amount threshold - add progressive scoring for large amounts
        amount = transaction["amount"]
        if amount > self.config["amount_threshold"]:
            score += 0.5  # Higher score for exceeding the threshold
            reasons.append(f"Amount ({amount}) exceeds threshold ({self.config['amount_threshold']})")
        elif amount > self.config["amount_threshold"] / 2:
            score += 0.3  # Medium score for amounts above half the threshold
            reasons.append(f"Amount ({amount}) exceeds half threshold ({self.config['amount_threshold']/2})")
        elif amount > 10000:
            score += 0.2  # Small score for amounts above 10,000
            reasons.append(f"Amount ({amount}) exceeds 10,000")
        
        # Check high-risk channel
        if self.check_high_risk_channel(transaction):
            score += 0.2
            reasons.append(f"High-risk channel: {transaction['channel']}")
        
        # Check high-risk payment mode
        if self.check_high_risk_payment_mode(transaction):
            score += 0.2
            reasons.append(f"High-risk payment mode: {transaction['payment_mode']}")
        
        # Apply custom rules
        custom_score = 0.0
        for rule in sorted(self.custom_rules, key=lambda x: x.priority if hasattr(x, 'priority') else x.get('priority', 1), reverse=True):
            # Check if rule is active
            is_active = rule.is_active if hasattr(rule, 'is_active') else rule.get('is_active', True)
            if is_active:
                matches, rule_score, reason = self.apply_custom_rule(rule, transaction)
                if matches:
                    custom_score += rule_score
                    rule_name = rule.name if hasattr(rule, 'name') else rule.get('name', 'Unnamed rule')
                    reasons.append(f"Custom rule '{rule_name}': {reason}")
        
        # Add custom rules score
        score += custom_score
        
        # Normalize score to be between 0 and 1
        score = min(score, 1.0)
        
        return score, "; ".join(reasons) if reasons else "No rules triggered"
    
    def is_fraudulent(self, transaction, transaction_history=None, threshold=0.5):
        """
        Determine if a transaction is fraudulent based on the risk score
        
        Args:
            transaction (dict): The transaction data
            transaction_history (list): Optional list of previous transactions
            threshold (float): The threshold for considering a transaction fraudulent
            
        Returns:
            tuple: (is_fraudulent (bool), risk_score (float), reason (str))
        """
        risk_score, reason = self.calculate_risk_score(transaction, transaction_history)
        return risk_score >= threshold, risk_score, reason
