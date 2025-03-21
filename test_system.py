import requests
import json
import time
import os
import sys
from src.utils.generate_test_data import generate_transaction, generate_batch_request

# API URL
API_URL = "http://localhost:8000/api"

def test_real_time_api():
    """
    Test the real-time fraud detection API
    """
    print("\n=== Testing Real-Time Fraud Detection API ===")
    
    # Generate a transaction
    transaction = generate_transaction()
    
    # Make the transaction more likely to be fraudulent
    transaction["amount"] = 15000
    transaction["payment_mode"] = "credit_card"
    transaction["channel"] = "web"
    
    print(f"Sending transaction: {transaction['transaction_id']}")
    
    # Measure response time
    start_time = time.time()
    
    # Send request
    response = requests.post(f"{API_URL}/detect", json=transaction)
    
    # Calculate response time
    response_time = (time.time() - start_time) * 1000
    
    # Check response
    if response.status_code == 200:
        result = response.json()
        print(f"Response time: {response_time:.2f} ms")
        print(f"Fraud detected: {result['is_fraud_predicted']}")
        print(f"Fraud score: {result['fraud_score']:.2f}")
        print(f"Prediction time: {result['prediction_time_ms']} ms")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

def test_batch_api():
    """
    Test the batch fraud detection API
    """
    print("\n=== Testing Batch Fraud Detection API ===")
    
    # Generate a batch request
    batch_request = generate_batch_request(num_transactions=5)
    
    print(f"Sending batch with {len(batch_request['transactions'])} transactions")
    
    # Measure response time
    start_time = time.time()
    
    # Send request
    response = requests.post(f"{API_URL}/batch-detect", json=batch_request)
    
    # Calculate response time
    response_time = (time.time() - start_time) * 1000
    
    # Check response
    if response.status_code == 200:
        result = response.json()
        print(f"Response time: {response_time:.2f} ms")
        print(f"Total processing time: {result['total_time_ms']} ms")
        
        # Count fraudulent transactions
        fraud_count = sum(1 for r in result['results'].values() if r['is_fraud_predicted'])
        print(f"Fraudulent transactions: {fraud_count}/{len(batch_request['transactions'])}")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

def test_reporting_api():
    """
    Test the fraud reporting API
    """
    print("\n=== Testing Fraud Reporting API ===")
    
    # First, get a transaction ID from the system
    response = requests.get(f"{API_URL}/transactions", params={"limit": 1})
    
    if response.status_code == 200 and response.json():
        transaction = response.json()[0]
        transaction_id = transaction["transaction_id"]
        
        # Create a fraud report
        report = {
            "transaction_id": transaction_id,
            "reporting_entity_id": "TEST001",
            "fraud_details": "This is a test fraud report"
        }
        
        print(f"Reporting transaction as fraud: {transaction_id}")
        
        # Send request
        response = requests.post(f"{API_URL}/report", json=report)
        
        # Check response
        if response.status_code == 200:
            result = response.json()
            print(f"Report created with ID: {result['id']}")
            print(f"Reported at: {result['reported_at']}")
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
    else:
        print("No transactions found to report")

def test_metrics_api():
    """
    Test the metrics API
    """
    print("\n=== Testing Metrics API ===")
    
    # Send request
    response = requests.get(f"{API_URL}/metrics")
    
    # Check response
    if response.status_code == 200:
        metrics = response.json()
        print("Confusion Matrix:")
        print(f"  True Positives: {metrics['confusion_matrix']['true_positives']}")
        print(f"  False Positives: {metrics['confusion_matrix']['false_positives']}")
        print(f"  True Negatives: {metrics['confusion_matrix']['true_negatives']}")
        print(f"  False Negatives: {metrics['confusion_matrix']['false_negatives']}")
        
        print("\nPerformance Metrics:")
        print(f"  Precision: {metrics['precision']:.2%}")
        print(f"  Recall: {metrics['recall']:.2%}")
        print(f"  F1 Score: {metrics['f1_score']:.2%}")
        
        print("\nStatistics:")
        print(f"  Total Transactions: {metrics['total_transactions']}")
        print(f"  Predicted Frauds: {metrics['predicted_frauds']}")
        print(f"  Reported Frauds: {metrics['reported_frauds']}")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

def main():
    """
    Main function to test the system
    """
    print("=== Fraud Detection System Test ===")
    
    # Check if the API is running
    try:
        response = requests.get("http://localhost:8000/")
        if response.status_code != 200:
            print("Error: API is not running or not responding correctly")
            return
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the API. Make sure it's running at http://localhost:8000")
        print("Run the API with: uvicorn src.api.main:app --reload")
        return
    
    # Run tests
    test_real_time_api()
    test_batch_api()
    test_reporting_api()
    test_metrics_api()
    
    print("\n=== All tests completed ===")

if __name__ == "__main__":
    main()
