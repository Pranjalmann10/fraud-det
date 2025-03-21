import requests
import json
import uuid
import random
from datetime import datetime

API_BASE_URL = "http://localhost:8001/api"

def test_regular_transaction(amount):
    """Test a transaction using the /detect endpoint"""
    # Create transaction
    transaction_id = str(uuid.uuid4())
    transaction = {
        'transaction_id': transaction_id,
        'amount': amount,
        'payer_id': f'P{random.randint(1000, 9999)}',
        'payee_id': f'P{random.randint(1000, 9999)}',
        'payment_mode': 'credit_card',
        'channel': 'web',
        'bank': 'Test Bank',
        'additional_data': {
            'ip_address': '192.168.1.1',
            'user_agent': 'Test Script',
            'device_id': f'D{random.randint(10000, 99999)}'
        }
    }
    
    print(f"\n=== Regular Transaction Amount: ${amount:,} ===")
    print(f"Transaction ID: {transaction_id}")
    
    # Send transaction to API
    try:
        response = requests.post(f"{API_BASE_URL}/detect", json=transaction)
        print(f"API Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Fraud Detected: {result['is_fraud_predicted']}")
            print(f"Fraud Score: {result['fraud_score']:.4f}")
            print(f"Processing Time: {result['prediction_time_ms']} ms")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {str(e)}")

def test_json_transaction(amount):
    """Test a transaction using the /detect-json endpoint"""
    # Create transaction
    transaction_id = str(uuid.uuid4())
    transaction = {
        'transaction_id': transaction_id,
        'amount': amount,
        'payer_id': f'P{random.randint(1000, 9999)}',
        'payee_id': f'P{random.randint(1000, 9999)}',
        'payment_mode': 'credit_card',
        'channel': 'web',
        'bank': 'Test Bank',
        'additional_data': {
            'ip_address': '192.168.1.1',
            'user_agent': 'Test Script',
            'device_id': f'D{random.randint(10000, 99999)}'
        }
    }
    
    print(f"\n=== JSON Transaction Amount: ${amount:,} ===")
    print(f"Transaction ID: {transaction_id}")
    
    # Send transaction to API
    try:
        response = requests.post(f"{API_BASE_URL}/detect-json", json={"transaction_data": transaction})
        print(f"API Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Fraud Detected: {result['is_fraud']}")
            print(f"Fraud Score: {result['fraud_score']:.4f}")
            print(f"Fraud Source: {result['fraud_source']}")
            print(f"Fraud Reason: {result['fraud_reason']}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {str(e)}")

def check_metrics():
    """Check the current metrics"""
    try:
        response = requests.get(f"{API_BASE_URL}/metrics")
        print("\n=== Current Metrics ===")
        
        if response.status_code == 200:
            metrics = response.json()
            print(f"Total Transactions: {metrics['total_transactions']}")
            print(f"Predicted Frauds: {metrics['predicted_frauds']}")
            print(f"Reported Frauds: {metrics['reported_frauds']}")
            print(f"Precision: {metrics['precision']:.4f}")
            print(f"Recall: {metrics['recall']:.4f}")
            print(f"F1 Score: {metrics['f1_score']:.4f}")
            
            cm = metrics['confusion_matrix']
            print(f"Confusion Matrix:")
            print(f"  True Positives: {cm['true_positives']}")
            print(f"  False Positives: {cm['false_positives']}")
            print(f"  True Negatives: {cm['true_negatives']}")
            print(f"  False Negatives: {cm['false_negatives']}")
        else:
            print(f"Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Exception: {str(e)}")

def check_transactions():
    """Check the recent transactions"""
    try:
        response = requests.get(f"{API_BASE_URL}/transactions?limit=5")
        print("\n=== Recent Transactions ===")
        
        if response.status_code == 200:
            transactions = response.json()
            print(f"Number of transactions: {len(transactions)}")
            
            for i, tx in enumerate(transactions):
                print(f"\nTransaction {i+1}:")
                print(f"  ID: {tx['transaction_id']}")
                print(f"  Amount: ${tx['amount']:,.2f}")
                print(f"  Fraud: {tx['is_fraud_predicted']}")
                print(f"  Score: {tx['fraud_score']:.4f}")
                print(f"  Time: {tx['timestamp']}")
        else:
            print(f"Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Exception: {str(e)}")

if __name__ == "__main__":
    # Check initial metrics
    check_metrics()
    
    # Test regular transactions
    test_regular_transaction(1000)
    test_regular_transaction(15000)
    test_regular_transaction(50000)
    
    # Test JSON transactions
    test_json_transaction(2000)
    test_json_transaction(25000)
    test_json_transaction(75000)
    
    # Check metrics after transactions
    check_metrics()
    
    # Check recent transactions
    check_transactions()
