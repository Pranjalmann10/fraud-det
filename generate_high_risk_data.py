import requests
import random
import uuid
import time
from datetime import datetime, timedelta

# API endpoint
API_URL = "http://localhost:8000/api/detect"

# Payment modes and channels
PAYMENT_MODES = ["credit_card", "debit_card", "bank_transfer", "wallet", "upi"]
CHANNELS = ["web", "mobile_app", "pos", "atm", "branch"]
BANKS = ["Chase", "Bank of America", "Wells Fargo", "Citibank", "Capital One", None]

# Generate high-risk transaction data
def generate_high_risk_transaction():
    # Generate high amount (more likely to be fraudulent)
    amount = round(random.uniform(5000, 10000), 2)
    
    # Generate random payer and payee IDs
    payer_id = f"P{random.randint(1000, 5000)}"
    payee_id = f"M{random.randint(1000, 5000)}"
    
    # Select random payment mode and channel
    payment_mode = random.choice(PAYMENT_MODES)
    channel = random.choice(CHANNELS)
    bank = random.choice(BANKS)
    
    # Generate unique transaction ID
    transaction_id = str(uuid.uuid4())
    
    # Generate additional data with suspicious patterns
    additional_data = {
        "ip_address": f"192.168.{random.randint(1, 255)}.{random.randint(1, 255)}",
        "user_agent": "Mozilla/5.0",
        "device_id": f"D{random.randint(10000, 30000)}",
        "location": "Unknown",
        "time_of_day": "night"
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
def generate_and_send_high_risk_transactions(count=10):
    print(f"Generating and sending {count} high-risk transactions...")
    success_count = 0
    
    for i in range(count):
        transaction = generate_high_risk_transaction()
        if send_transaction(transaction):
            success_count += 1
        time.sleep(0.5)  # Small delay between transactions
    
    print(f"Successfully processed {success_count} out of {count} high-risk transactions")

if __name__ == "__main__":
    generate_and_send_high_risk_transactions(10)
