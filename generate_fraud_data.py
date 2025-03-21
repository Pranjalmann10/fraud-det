import requests
import random
import uuid
import time
from datetime import datetime, timedelta

# API endpoint
API_URL = "http://localhost:8000/api/detect"

# Generate fraudulent transaction data
def generate_fraudulent_transaction():
    # Generate very high amount (more likely to be fraudulent)
    amount = round(random.uniform(9000, 15000), 2)
    
    # Generate random payer and payee IDs
    payer_id = f"P{random.randint(1000, 5000)}"
    payee_id = f"M{random.randint(1000, 5000)}"
    
    # Select payment mode and channel that are more likely to be fraudulent
    payment_mode = random.choice(["credit_card", "wallet"])
    channel = random.choice(["web", "mobile_app"])
    bank = None
    
    # Generate unique transaction ID
    transaction_id = str(uuid.uuid4())
    
    # Generate additional data with suspicious patterns
    additional_data = {
        "ip_address": f"103.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}",
        "user_agent": "Mozilla/5.0 (compatible; Bot/1.0)",
        "device_id": f"UNKNOWN_{random.randint(1000, 9999)}",
        "location": "Unknown",
        "time_of_day": "night",
        "suspicious_pattern": True,
        "multiple_attempts": random.randint(3, 10)
    }
    
    # Create transaction data
    transaction = {
        "transaction_id": transaction_id,
        "amount": amount,
        "payer_id": payer_id,
        "payee_id": payee_id,
        "payment_mode": payment_mode,
        "channel": channel,
        "bank": bank,
        "additional_data": additional_data
    }
    
    return transaction

# Send transaction to API
def send_transaction(transaction):
    try:
        response = requests.post(API_URL, json=transaction)
        if response.status_code == 200:
            result = response.json()
            print(f"Transaction {transaction['transaction_id']} processed")
            print(f"Amount: ${transaction['amount']:,.2f}")
            print(f"Payment Mode: {transaction['payment_mode']}")
            print(f"Channel: {transaction['channel']}")
            print(f"Fraud detected: {result['is_fraud_predicted']}")
            print(f"Fraud score: {result['fraud_score']}")
            print(f"Processing time: {result['prediction_time_ms']} ms")
            print("-" * 50)
            return True
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"Exception: {str(e)}")
        return False

# Generate and send multiple transactions
def generate_and_send_fraudulent_transactions(count=5):
    print(f"Generating and sending {count} potentially fraudulent transactions...")
    success_count = 0
    
    for i in range(count):
        transaction = generate_fraudulent_transaction()
        if send_transaction(transaction):
            success_count += 1
        time.sleep(0.5)  # Small delay between transactions
    
    print(f"Successfully processed {success_count} out of {count} potentially fraudulent transactions")

if __name__ == "__main__":
    generate_and_send_fraudulent_transactions(5)
