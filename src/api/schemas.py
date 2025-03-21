from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

class TransactionBase(BaseModel):
    transaction_id: str = Field(..., description="Unique identifier for the transaction")
    amount: float = Field(..., description="Transaction amount")
    payer_id: str = Field(..., description="ID of the payer")
    payee_id: str = Field(..., description="ID of the payee")
    payment_mode: str = Field(..., description="Payment mode (e.g., credit_card, debit_card, bank_transfer)")
    channel: str = Field(..., description="Transaction channel (e.g., web, mobile_app, in_store)")
    bank: Optional[str] = Field(None, description="Bank name if applicable")
    additional_data: Optional[Dict[str, Any]] = Field(None, description="Additional transaction data")

    @validator('amount')
    def amount_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Amount must be positive')
        return v

class TransactionCreate(TransactionBase):
    pass

class TransactionResponse(TransactionBase):
    is_fraud_predicted: bool = Field(..., description="Whether the transaction is predicted as fraudulent")
    fraud_score: float = Field(..., description="Fraud score between 0 and 1")
    prediction_time_ms: int = Field(..., description="Time taken to make the prediction in milliseconds")
    timestamp: Optional[datetime] = Field(None, description="Timestamp when the transaction was created")

class BatchTransactionRequest(BaseModel):
    transactions: List[TransactionBase] = Field(..., description="List of transactions to process")

class BatchTransactionResponse(BaseModel):
    results: Dict[str, TransactionResponse] = Field(..., description="Mapping of transaction IDs to fraud detection results")
    total_time_ms: int = Field(..., description="Total time taken to process all transactions in milliseconds")

class FraudReportCreate(BaseModel):
    transaction_id: str = Field(..., description="ID of the fraudulent transaction")
    reporting_entity_id: str = Field(..., description="ID of the entity reporting the fraud")
    fraud_details: str = Field(..., description="Details about the fraud")

class FraudReportResponse(FraudReportCreate):
    id: int = Field(..., description="Unique identifier for the fraud report")
    is_fraud_reported: bool = Field(..., description="Whether the transaction is reported as fraudulent")
    reported_at: datetime = Field(..., description="Timestamp when the fraud was reported")

class FilterParams(BaseModel):
    start_date: Optional[datetime] = Field(None, description="Start date for filtering")
    end_date: Optional[datetime] = Field(None, description="End date for filtering")
    payer_id: Optional[str] = Field(None, description="Filter by payer ID")
    payee_id: Optional[str] = Field(None, description="Filter by payee ID")
    payment_mode: Optional[str] = Field(None, description="Filter by payment mode")
    channel: Optional[str] = Field(None, description="Filter by channel")
    bank: Optional[str] = Field(None, description="Filter by bank")
    is_fraud_predicted: Optional[bool] = Field(None, description="Filter by fraud prediction")
    skip: int = Field(0, description="Number of records to skip")
    limit: int = Field(100, description="Maximum number of records to return")

class MetricsResponse(BaseModel):
    confusion_matrix: Dict[str, int] = Field(..., description="Confusion matrix (TP, FP, TN, FN)")
    precision: float = Field(..., description="Precision metric")
    recall: float = Field(..., description="Recall metric")
    f1_score: float = Field(..., description="F1 score")
    total_transactions: int = Field(..., description="Total number of transactions")
    predicted_frauds: int = Field(..., description="Number of transactions predicted as fraudulent")
    reported_frauds: int = Field(..., description="Number of transactions reported as fraudulent")

class JsonTransactionInput(BaseModel):
    """Schema for a single transaction input in JSON format"""
    transaction_data: Dict[str, Any] = Field(..., description="Raw transaction data in JSON format")

class DetailedFraudResponse(BaseModel):
    """Schema for a detailed fraud detection response"""
    transaction_id: str = Field(..., description="Unique identifier for the transaction")
    is_fraud: bool = Field(..., description="Whether the transaction is fraudulent")
    fraud_source: str = Field(..., description="Source of fraud detection (rule/model)")
    fraud_reason: str = Field(..., description="Reason for fraud detection")
    fraud_score: float = Field(..., description="Fraud score between 0 and 1")

# Custom Rule Schemas

class RuleOperator(str):
    """Valid operators for custom rules"""
    EQUALS = "=="
    NOT_EQUALS = "!="
    GREATER_THAN = ">"
    LESS_THAN = "<"
    GREATER_THAN_EQUALS = ">="
    LESS_THAN_EQUALS = "<="
    IN = "in"
    NOT_IN = "not_in"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"

class RuleType(str):
    """Valid rule types"""
    THRESHOLD = "threshold"
    PATTERN = "pattern"
    COMBINATION = "combination"
    VELOCITY = "velocity"
    CUSTOM = "custom"

class CustomRuleBase(BaseModel):
    """Base schema for custom rules"""
    name: str = Field(..., description="Unique name for the rule")
    description: Optional[str] = Field(None, description="Description of what the rule does")
    rule_type: str = Field(..., description="Type of rule (threshold, pattern, combination, velocity, custom)")
    field: str = Field(..., description="Transaction field to apply the rule to")
    operator: str = Field(..., description="Operator for comparison")
    value: Any = Field(..., description="Value to compare against")
    score: float = Field(..., description="Risk score to assign if rule matches (0.0 to 1.0)")
    is_active: bool = Field(True, description="Whether the rule is active")
    priority: int = Field(1, description="Priority of the rule (higher values = higher priority)")
    advanced_config: Optional[Dict[str, Any]] = Field(None, description="Advanced configuration for complex rules")
    
    @validator('score')
    def validate_score(cls, v):
        if v < 0.0 or v > 1.0:
            raise ValueError('Score must be between 0.0 and 1.0')
        return v
    
    @validator('rule_type')
    def validate_rule_type(cls, v):
        valid_types = [RuleType.THRESHOLD, RuleType.PATTERN, RuleType.COMBINATION, 
                       RuleType.VELOCITY, RuleType.CUSTOM]
        if v not in valid_types:
            raise ValueError(f'Rule type must be one of: {", ".join(valid_types)}')
        return v
    
    @validator('operator')
    def validate_operator(cls, v):
        valid_operators = [RuleOperator.EQUALS, RuleOperator.NOT_EQUALS, 
                          RuleOperator.GREATER_THAN, RuleOperator.LESS_THAN,
                          RuleOperator.GREATER_THAN_EQUALS, RuleOperator.LESS_THAN_EQUALS,
                          RuleOperator.IN, RuleOperator.NOT_IN,
                          RuleOperator.CONTAINS, RuleOperator.NOT_CONTAINS,
                          RuleOperator.STARTS_WITH, RuleOperator.ENDS_WITH]
        if v not in valid_operators:
            raise ValueError(f'Operator must be one of: {", ".join(valid_operators)}')
        return v

class CustomRuleCreate(CustomRuleBase):
    """Schema for creating a new custom rule"""
    pass

class CustomRuleUpdate(BaseModel):
    """Schema for updating an existing custom rule"""
    name: Optional[str] = None
    description: Optional[str] = None
    rule_type: Optional[str] = None
    field: Optional[str] = None
    operator: Optional[str] = None
    value: Optional[Any] = None
    score: Optional[float] = None
    is_active: Optional[bool] = None
    priority: Optional[int] = None
    advanced_config: Optional[Dict[str, Any]] = None
    
    @validator('score')
    def validate_score(cls, v):
        if v is not None and (v < 0.0 or v > 1.0):
            raise ValueError('Score must be between 0.0 and 1.0')
        return v
    
    @validator('rule_type')
    def validate_rule_type(cls, v):
        if v is None:
            return v
        valid_types = [RuleType.THRESHOLD, RuleType.PATTERN, RuleType.COMBINATION, 
                       RuleType.VELOCITY, RuleType.CUSTOM]
        if v not in valid_types:
            raise ValueError(f'Rule type must be one of: {", ".join(valid_types)}')
        return v
    
    @validator('operator')
    def validate_operator(cls, v):
        if v is None:
            return v
        valid_operators = [RuleOperator.EQUALS, RuleOperator.NOT_EQUALS, 
                          RuleOperator.GREATER_THAN, RuleOperator.LESS_THAN,
                          RuleOperator.GREATER_THAN_EQUALS, RuleOperator.LESS_THAN_EQUALS,
                          RuleOperator.IN, RuleOperator.NOT_IN,
                          RuleOperator.CONTAINS, RuleOperator.NOT_CONTAINS,
                          RuleOperator.STARTS_WITH, RuleOperator.ENDS_WITH]
        if v not in valid_operators:
            raise ValueError(f'Operator must be one of: {", ".join(valid_operators)}')
        return v

class CustomRuleResponse(CustomRuleBase):
    """Schema for custom rule response"""
    id: int = Field(..., description="Unique identifier for the rule")
    created_at: datetime = Field(..., description="Timestamp when the rule was created")
    updated_at: datetime = Field(..., description="Timestamp when the rule was last updated")
    
    class Config:
        orm_mode = True
