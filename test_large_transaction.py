import requests

# Test a large transaction
transaction = {
    'transaction_id': '12345',
    'amount': 60000,
    'payer_id': 'P123',
    'payee_id': 'P456',
    'payment_mode': 'credit_card',
    'channel': 'web'
}

print(f"Testing transaction with amount: {transaction['amount']}")
response = requests.post('http://localhost:8000/api/detect', json=transaction)
result = response.json()

print(f"Fraud detected: {result['is_fraud_predicted']}")
print(f"Fraud score: {result['fraud_score']}")
print(f"Rule score: {result.get('rule_score', 'N/A')}")
print(f"AI score: {result.get('ai_score', 'N/A')}")
