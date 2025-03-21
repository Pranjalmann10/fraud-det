from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import time
import concurrent.futures
from datetime import datetime
import json
from typing import Optional

from ..database import crud, database, models
from ..models.combined_model import CombinedFraudDetector
from . import schemas
import os

# Create router
router = APIRouter()

# Initialize fraud detector with pre-trained model
model_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                          "models", "trained", "fraud_model.pkl")
fraud_detector = CombinedFraudDetector(ai_model_path=model_path if os.path.exists(model_path) else None)

# Dependency to get the database session
def get_db():
    return next(database.get_db())

def process_transaction(transaction_dict, db):
    """
    Process a transaction and detect fraud
    
    Args:
        transaction_dict (dict): Transaction data
        db (Session): Database session
        
    Returns:
        tuple: (is_fraud, fraud_score, prediction_time_ms, transaction_id)
    """
    start_time = time.time()
    
    # Detect fraud with a lower threshold for high-value transactions
    threshold = 0.1 if transaction_dict.get("amount", 0) > 5000 else 0.5
    is_fraud, fraud_score, rule_score, ai_score = fraud_detector.detect_fraud(transaction_dict, threshold=threshold)
    
    # Calculate prediction time
    prediction_time_ms = int((time.time() - start_time) * 1000)
    
    # Store transaction in database
    try:
        # Convert additional_data to JSON string if it's a dict
        additional_data = transaction_dict.get("additional_data", {})
        if isinstance(additional_data, dict):
            additional_data_str = json.dumps(additional_data)
        else:
            additional_data_str = None
            
        # Create a new transaction record
        transaction = models.Transaction(
            transaction_id=transaction_dict["transaction_id"],
            amount=transaction_dict["amount"],
            payer_id=transaction_dict["payer_id"],
            payee_id=transaction_dict["payee_id"],
            payment_mode=transaction_dict["payment_mode"],
            channel=transaction_dict["channel"],
            bank=transaction_dict.get("bank"),
            additional_data=additional_data_str,
            is_fraud_predicted=is_fraud,
            fraud_score=fraud_score,
            prediction_time_ms=prediction_time_ms
        )
        
        # Add and commit
        db.add(transaction)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error storing transaction {transaction_dict['transaction_id']}: {str(e)}")
    
    return is_fraud, fraud_score, prediction_time_ms, transaction_dict["transaction_id"]

@router.post("/detect", response_model=schemas.TransactionResponse)
def detect_fraud(transaction: schemas.TransactionCreate, db: Session = Depends(get_db)):
    """
    Detect fraud for a single transaction
    
    Args:
        transaction (schemas.TransactionCreate): Transaction data
        db (Session): Database session
        
    Returns:
        schemas.TransactionResponse: Fraud detection result
    """
    # Convert Pydantic model to dict
    transaction_dict = transaction.dict()
    
    # Process transaction
    is_fraud, fraud_score, prediction_time_ms, transaction_id = process_transaction(transaction_dict, db)
    
    # Convert additional_data from string to dict if needed
    additional_data = transaction_dict.get("additional_data", {})
    if additional_data is None:
        additional_data = {}
    
    # Return response
    return schemas.TransactionResponse(
        transaction_id=transaction_id,
        amount=transaction_dict["amount"],
        payer_id=transaction_dict["payer_id"],
        payee_id=transaction_dict["payee_id"],
        payment_mode=transaction_dict["payment_mode"],
        channel=transaction_dict["channel"],
        bank=transaction_dict.get("bank"),
        additional_data=additional_data,
        is_fraud_predicted=is_fraud,
        fraud_score=fraud_score,
        prediction_time_ms=prediction_time_ms
    )

@router.post("/batch-detect", response_model=schemas.BatchTransactionResponse)
def batch_detect_fraud(batch_request: schemas.BatchTransactionRequest, db: Session = Depends(get_db)):
    """
    Batch fraud detection for multiple transactions
    """
    # Record start time
    start_time = time.time()
    
    # Process transactions in parallel
    results = {}
    
    def process_single_transaction(transaction):
        # Convert Pydantic model to dict
        transaction_dict = transaction.dict()
        
        # Process transaction
        is_fraud, fraud_score, prediction_time_ms, transaction_id = process_transaction(transaction_dict, db)
        
        # Create response
        response = schemas.TransactionResponse(
            transaction_id=transaction_id,
            amount=transaction_dict["amount"],
            payer_id=transaction_dict["payer_id"],
            payee_id=transaction_dict["payee_id"],
            payment_mode=transaction_dict["payment_mode"],
            channel=transaction_dict["channel"],
            bank=transaction_dict.get("bank"),
            additional_data=transaction_dict.get("additional_data", {}),
            is_fraud_predicted=is_fraud,
            fraud_score=fraud_score,
            prediction_time_ms=prediction_time_ms
        )
        
        return transaction_id, response
    
    # Use ThreadPoolExecutor to process transactions in parallel
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(process_single_transaction, tx) for tx in batch_request.transactions]
        for future in concurrent.futures.as_completed(futures):
            try:
                transaction_id, response = future.result()
                results[transaction_id] = response
            except Exception as e:
                print(f"Error processing transaction: {str(e)}")
    
    # Calculate total processing time
    total_time_ms = int((time.time() - start_time) * 1000)
    
    # Return batch response
    return schemas.BatchTransactionResponse(
        results=results,
        total_time_ms=total_time_ms
    )

@router.post("/report", response_model=schemas.FraudReportResponse)
def report_fraud(report: schemas.FraudReportCreate, db: Session = Depends(get_db)):
    """
    Report a fraudulent transaction
    """
    # Check if transaction exists
    transaction = crud.get_transaction_by_id(db, report.transaction_id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Check if fraud report already exists
    existing_report = crud.get_fraud_report_by_transaction_id(db, report.transaction_id)
    if existing_report:
        raise HTTPException(status_code=400, detail="Fraud report already exists for this transaction")
    
    # Create fraud report
    db_report = crud.create_fraud_report(db, report.dict())
    
    return schemas.FraudReportResponse(
        id=db_report.id,
        transaction_id=db_report.transaction_id,
        reporting_entity_id=db_report.reporting_entity_id,
        fraud_details=db_report.fraud_details,
        is_fraud_reported=db_report.is_fraud_reported,
        reported_at=db_report.reported_at
    )

@router.get("/transactions", response_model=List[schemas.TransactionResponse])
def get_transactions(
    limit: int = 100, 
    offset: int = 0,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    payment_mode: Optional[str] = None,
    channel: Optional[str] = None,
    is_fraud: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """
    Get a list of transactions with optional filtering
    
    Args:
        limit (int): Maximum number of transactions to return
        offset (int): Offset for pagination
        start_date (datetime): Filter by start date
        end_date (datetime): Filter by end date
        payment_mode (str): Filter by payment mode
        channel (str): Filter by channel
        is_fraud (bool): Filter by fraud status
        db (Session): Database session
        
    Returns:
        List[schemas.TransactionResponse]: List of transactions
    """
    # Query transactions with filters
    query = db.query(models.Transaction)
    
    if start_date:
        query = query.filter(models.Transaction.created_at >= start_date)
    if end_date:
        query = query.filter(models.Transaction.created_at <= end_date)
    if payment_mode:
        query = query.filter(models.Transaction.payment_mode == payment_mode)
    if channel:
        query = query.filter(models.Transaction.channel == channel)
    if is_fraud is not None:
        query = query.filter(models.Transaction.is_fraud_predicted == is_fraud)
    
    # Apply limit and offset
    transactions = query.order_by(models.Transaction.created_at.desc()).offset(offset).limit(limit).all()
    
    # Convert to response models
    result = []
    for tx in transactions:
        try:
            # Parse additional_data from JSON string to dict
            additional_data = {}
            if tx.additional_data:
                try:
                    additional_data = json.loads(tx.additional_data)
                except:
                    additional_data = {}
            
            result.append(schemas.TransactionResponse(
                transaction_id=tx.transaction_id,
                amount=tx.amount,
                payer_id=tx.payer_id,
                payee_id=tx.payee_id,
                payment_mode=tx.payment_mode,
                channel=tx.channel,
                bank=tx.bank,
                additional_data=additional_data,
                is_fraud_predicted=tx.is_fraud_predicted,
                fraud_score=tx.fraud_score,
                prediction_time_ms=tx.prediction_time_ms
            ))
        except Exception as e:
            print(f"Error converting transaction {tx.transaction_id}: {str(e)}")
    
    return result

@router.get("/reports", response_model=List[schemas.FraudReportResponse])
def get_fraud_reports(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Get fraud reports
    """
    reports = crud.get_fraud_reports(db, skip=skip, limit=limit)
    
    return [
        schemas.FraudReportResponse(
            id=r.id,
            transaction_id=r.transaction_id,
            reporting_entity_id=r.reporting_entity_id,
            fraud_details=r.fraud_details,
            is_fraud_reported=r.is_fraud_reported,
            reported_at=r.reported_at
        )
        for r in reports
    ]

@router.get("/metrics", response_model=schemas.MetricsResponse)
def get_metrics(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    """
    Get fraud detection metrics
    """
    # Get metrics from database
    metrics = crud.get_metrics(db, start_date, end_date)
    
    # Return metrics response
    return schemas.MetricsResponse(
        confusion_matrix=metrics["confusion_matrix"],
        precision=metrics["precision"],
        recall=metrics["recall"],
        f1_score=metrics["f1_score"],
        total_transactions=metrics["total_transactions"],
        predicted_frauds=metrics["predicted_frauds"],
        reported_frauds=metrics["reported_frauds"]
    )
