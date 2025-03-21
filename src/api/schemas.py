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
