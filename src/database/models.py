from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class Transaction(Base):
    __tablename__ = "fraud_detection"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String, unique=True, index=True)
    amount = Column(Float)
    payer_id = Column(String)
    payee_id = Column(String)
    payment_mode = Column(String)
    channel = Column(String)
    bank = Column(String, nullable=True)
    timestamp = Column(DateTime, default=func.now())
    is_fraud_predicted = Column(Boolean, default=False)
    fraud_score = Column(Float, default=0.0)
    prediction_time_ms = Column(Integer, default=0)
    additional_data = Column(Text)

class FraudReport(Base):
    __tablename__ = "fraud_reporting"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String(50), ForeignKey("fraud_detection.transaction_id"), index=True, nullable=False)
    reporting_entity_id = Column(String(50), index=True, nullable=False)
    fraud_details = Column(Text, nullable=False)
    is_fraud_reported = Column(Boolean, default=True, index=True)
    reported_at = Column(DateTime, default=func.now(), index=True)

class CustomRule(Base):
    __tablename__ = "custom_rules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    rule_type = Column(String(50), nullable=False)  # e.g., "threshold", "pattern", "combination"
    field = Column(String(50), nullable=False)  # e.g., "amount", "payment_mode", "channel"
    operator = Column(String(20), nullable=False)  # e.g., ">", "<", "==", "in", "contains"
    value = Column(String(255), nullable=False)  # Value to compare against
    score = Column(Float, nullable=False)  # Risk score to assign if rule matches (0.0 to 1.0)
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=1)  # Higher priority rules are evaluated first
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # JSON field for storing complex conditions or additional configuration
    advanced_config = Column(JSON, nullable=True)
