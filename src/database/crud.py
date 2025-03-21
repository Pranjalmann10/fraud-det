from sqlalchemy.orm import Session
from . import models
from datetime import datetime, timedelta
import json

def create_transaction(db: Session, transaction_data: dict, is_fraud_predicted: bool, fraud_score: float, prediction_time_ms: int):
    """
    Create a new transaction record in the database
    """
    # Convert additional_data to JSON string if it's a dict
    if isinstance(transaction_data.get("additional_data"), dict):
        transaction_data["additional_data"] = json.dumps(transaction_data["additional_data"])
    
    db_transaction = models.Transaction(
        transaction_id=transaction_data["transaction_id"],
        amount=transaction_data["amount"],
        payer_id=transaction_data["payer_id"],
        payee_id=transaction_data["payee_id"],
        payment_mode=transaction_data["payment_mode"],
        channel=transaction_data["channel"],
        bank=transaction_data.get("bank"),
        is_fraud_predicted=is_fraud_predicted,
        fraud_score=fraud_score,
        prediction_time_ms=prediction_time_ms,
        additional_data=transaction_data.get("additional_data")
    )
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction

def create_fraud_report(db: Session, report_data: dict):
    """
    Create a new fraud report in the database
    """
    db_report = models.FraudReport(
        transaction_id=report_data["transaction_id"],
        reporting_entity_id=report_data["reporting_entity_id"],
        fraud_details=report_data["fraud_details"],
        is_fraud_reported=True
    )
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    return db_report

def get_transaction_by_id(db: Session, transaction_id: str):
    """
    Get a transaction by its ID
    """
    return db.query(models.Transaction).filter(models.Transaction.transaction_id == transaction_id).first()

def get_transactions(
    db: Session, 
    skip: int = 0, 
    limit: int = 100, 
    start_date: datetime = None, 
    end_date: datetime = None,
    payer_id: str = None,
    payee_id: str = None,
    payment_mode: str = None,
    channel: str = None,
    bank: str = None,
    is_fraud_predicted: bool = None
):
    """
    Get transactions with optional filters
    """
    query = db.query(models.Transaction)
    
    if start_date:
        query = query.filter(models.Transaction.timestamp >= start_date)
    if end_date:
        query = query.filter(models.Transaction.timestamp <= end_date)
    if payer_id:
        query = query.filter(models.Transaction.payer_id == payer_id)
    if payee_id:
        query = query.filter(models.Transaction.payee_id == payee_id)
    if payment_mode:
        query = query.filter(models.Transaction.payment_mode == payment_mode)
    if channel:
        query = query.filter(models.Transaction.channel == channel)
    if bank:
        query = query.filter(models.Transaction.bank == bank)
    if is_fraud_predicted is not None:
        query = query.filter(models.Transaction.is_fraud_predicted == is_fraud_predicted)
    
    return query.order_by(models.Transaction.timestamp.desc()).offset(skip).limit(limit).all()

def get_fraud_reports(db: Session, skip: int = 0, limit: int = 100):
    """
    Get fraud reports
    """
    return db.query(models.FraudReport).order_by(models.FraudReport.reported_at.desc()).offset(skip).limit(limit).all()

def get_fraud_report_by_transaction_id(db: Session, transaction_id: str):
    """
    Get a fraud report by transaction ID
    """
    return db.query(models.FraudReport).filter(models.FraudReport.transaction_id == transaction_id).first()

def get_metrics(db: Session, start_date: datetime = None, end_date: datetime = None):
    """
    Get fraud detection metrics for a given time period
    """
    try:
        # Define query filters
        filters = []
        if start_date:
            filters.append(models.Transaction.created_at >= start_date)
        if end_date:
            filters.append(models.Transaction.created_at <= end_date)
        
        # Get all transactions matching the filters
        transactions = db.query(models.Transaction).filter(*filters).all()
        
        # Initialize metrics
        true_positives = 0
        false_positives = 0
        true_negatives = 0
        false_negatives = 0
        
        # Calculate confusion matrix
        for tx in transactions:
            # Get fraud report for this transaction
            report = get_fraud_report_by_transaction_id(db, tx.transaction_id)
            
            # Determine if this transaction was actually fraudulent
            is_actually_fraud = report is not None and report.is_fraud_reported
            
            # Update confusion matrix
            if tx.is_fraud_predicted and is_actually_fraud:
                true_positives += 1
            elif tx.is_fraud_predicted and not is_actually_fraud:
                false_positives += 1
            elif not tx.is_fraud_predicted and not is_actually_fraud:
                true_negatives += 1
            elif not tx.is_fraud_predicted and is_actually_fraud:
                false_negatives += 1
        
        # Calculate metrics
        total_transactions = len(transactions)
        predicted_frauds = sum(1 for tx in transactions if tx.is_fraud_predicted)
        reported_frauds = sum(1 for tx in transactions if get_fraud_report_by_transaction_id(db, tx.transaction_id) is not None)
        
        # Calculate precision, recall, and F1 score
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
        f1_score = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        
        # Return metrics
        return {
            "confusion_matrix": {
                "true_positives": true_positives,
                "false_positives": false_positives,
                "true_negatives": true_negatives,
                "false_negatives": false_negatives
            },
            "precision": precision,
            "recall": recall,
            "f1_score": f1_score,
            "total_transactions": total_transactions,
            "predicted_frauds": predicted_frauds,
            "reported_frauds": reported_frauds
        }
    except Exception as e:
        print(f"Error calculating metrics: {str(e)}")
        # Return default metrics in case of error
        return {
            "confusion_matrix": {
                "true_positives": 0,
                "false_positives": 0,
                "true_negatives": 0,
                "false_negatives": 0
            },
            "precision": 0,
            "recall": 0,
            "f1_score": 0,
            "total_transactions": 0,
            "predicted_frauds": 0,
            "reported_frauds": 0
        }

# Custom Rule CRUD operations

def create_custom_rule(db: Session, rule_data: dict):
    """
    Create a new custom rule in the database
    """
    db_rule = models.CustomRule(
        name=rule_data["name"],
        description=rule_data.get("description"),
        rule_type=rule_data["rule_type"],
        field=rule_data["field"],
        operator=rule_data["operator"],
        value=str(rule_data["value"]),
        score=float(rule_data["score"]),
        is_active=rule_data.get("is_active", True),
        priority=rule_data.get("priority", 1),
        advanced_config=rule_data.get("advanced_config")
    )
    db.add(db_rule)
    db.commit()
    db.refresh(db_rule)
    return db_rule

def get_custom_rule(db: Session, rule_id: int):
    """
    Get a custom rule by its ID
    """
    return db.query(models.CustomRule).filter(models.CustomRule.id == rule_id).first()

def get_custom_rule_by_name(db: Session, name: str):
    """
    Get a custom rule by its name
    """
    return db.query(models.CustomRule).filter(models.CustomRule.name == name).first()

def get_all_custom_rules(db: Session, skip: int = 0, limit: int = 100, active_only: bool = False):
    """
    Get all custom rules with optional pagination and filtering
    """
    query = db.query(models.CustomRule)
    
    if active_only:
        query = query.filter(models.CustomRule.is_active == True)
    
    # Order by priority (highest first) and then by ID
    return query.order_by(models.CustomRule.priority.desc(), models.CustomRule.id).offset(skip).limit(limit).all()

def update_custom_rule(db: Session, rule_id: int, rule_data: dict):
    """
    Update an existing custom rule
    """
    db_rule = get_custom_rule(db, rule_id)
    if not db_rule:
        return None
    
    # Update fields if they exist in the rule_data
    for key, value in rule_data.items():
        if key in ["name", "description", "rule_type", "field", "operator", "priority", "is_active", "advanced_config"]:
            setattr(db_rule, key, value)
        elif key == "value":
            setattr(db_rule, key, str(value))
        elif key == "score":
            setattr(db_rule, key, float(value))
    
    db.commit()
    db.refresh(db_rule)
    return db_rule

def delete_custom_rule(db: Session, rule_id: int):
    """
    Delete a custom rule
    """
    db_rule = get_custom_rule(db, rule_id)
    if not db_rule:
        return False
    
    db.delete(db_rule)
    db.commit()
    return True

def activate_deactivate_rule(db: Session, rule_id: int, is_active: bool):
    """
    Activate or deactivate a custom rule
    """
    db_rule = get_custom_rule(db, rule_id)
    if not db_rule:
        return None
    
    db_rule.is_active = is_active
    db.commit()
    db.refresh(db_rule)
    return db_rule
