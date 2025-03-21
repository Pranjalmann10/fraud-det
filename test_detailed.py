import requests
import json

def test_transaction(amount):
    # Create transaction
    transaction = {
        'transaction_id': f'test-{amount}',
        'amount': amount,
        'payer_id': 'P123',
        'payee_id': 'P456',
        'payment_mode': 'credit_card',
        'channel': 'web'
    }
    
    # Get detailed response
    response = requests.post('http://localhost:8001/api/detect-json', json={"transaction_data": transaction})
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n=== Transaction Amount: ${amount:,} ===")
        print(f"Fraud Detected: {result['is_fraud']}")
        print(f"Fraud Score: {result['fraud_score']:.4f}")
        print(f"Fraud Source: {result['fraud_source']}")
        print(f"Fraud Reason: {result['fraud_reason']}")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

# Test different transaction amounts
test_transaction(1000)
test_transaction(8000)
test_transaction(15000)
test_transaction(30000)
test_transaction(60000)
