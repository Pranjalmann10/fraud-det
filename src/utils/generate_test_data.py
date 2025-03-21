import json
import random
import uuid
from datetime import datetime, timedelta

def generate_transaction():
    """
    Generate a random transaction for testing
    """
    payment_modes = ["credit_card", "debit_card", "bank_transfer", "digital_wallet"]
    channels = ["web", "mobile_app", "in_store", "phone"]
    banks = ["Bank of America", "Chase", "Wells Fargo", "Citibank", "Capital One"]
    
    # Generate a random amount (higher amounts are less common)
    amount_base = random.uniform(10, 1000)
    amount_multiplier = random.choices([1, 2, 5, 10], weights=[0.7, 0.2, 0.08, 0.02])[0]
    amount = round(amount_base * amount_multiplier, 2)
    
    # Generate random IDs
    transaction_id = str(uuid.uuid4())
    payer_id = f"P{random.randint(1000, 9999)}"
    payee_id = f"M{random.randint(1000, 9999)}"
    
    # Select random payment mode and channel
    payment_mode = random.choice(payment_modes)
    channel = random.choice(channels)
    
    # Bank is optional
    bank = random.choice(banks) if random.random() < 0.8 else None
    
    # Create transaction
    transaction = {
        "transaction_id": transaction_id,
        "amount": amount,
        "payer_id": payer_id,
        "payee_id": payee_id,
        "payment_mode": payment_mode,
        "channel": channel,
        "bank": bank,
        "additional_data": {
            "ip_address": f"192.168.{random.randint(0, 255)}.{random.randint(0, 255)}",
            "user_agent": "Mozilla/5.0",
            "device_id": f"D{random.randint(10000, 99999)}"
        }
    }
    
    return transaction

def generate_test_data(num_transactions=100, fraud_ratio=0.1, output_file="test_data.json"):
    """
    Generate test data for the fraud detection system
    
    Args:
        num_transactions (int): Number of transactions to generate
        fraud_ratio (float): Ratio of fraudulent transactions
        output_file (str): Output file path
    """
    transactions = []
    
    # Generate transactions
    for i in range(num_transactions):
        transaction = generate_transaction()
        
        # Make some transactions more likely to be fraudulent
        if random.random() < fraud_ratio:
            # High amount
            transaction["amount"] = round(random.uniform(5000, 20000), 2)
            
            # High-risk payment mode and channel
            transaction["payment_mode"] = random.choice(["credit_card", "digital_wallet"])
            transaction["channel"] = random.choice(["web", "mobile_app"])
            
            # Add suspicious IP
            transaction["additional_data"]["ip_address"] = f"{random.randint(1, 100)}.{random.randint(1, 100)}.{random.randint(1, 100)}.{random.randint(1, 100)}"
        
        transactions.append(transaction)
    
    # Save to file
    with open(output_file, "w") as f:
        json.dump(transactions, f, indent=2)
    
    print(f"Generated {num_transactions} test transactions and saved to {output_file}")
    return transactions

def generate_batch_request(num_transactions=10, output_file="batch_request.json"):
    """
    Generate a batch request for testing the batch API
    
    Args:
        num_transactions (int): Number of transactions in the batch
        output_file (str): Output file path
    """
    transactions = [generate_transaction() for _ in range(num_transactions)]
    
    batch_request = {
        "transactions": transactions
    }
    
    # Save to file
    with open(output_file, "w") as f:
        json.dump(batch_request, f, indent=2)
    
    print(f"Generated batch request with {num_transactions} transactions and saved to {output_file}")
    return batch_request

def generate_and_store_transactions(num_transactions=10):
    """
    Generate random transactions and store them in the database via the API
    
    Args:
        num_transactions (int): Number of transactions to generate
    """
    import requests
    
    API_BASE_URL = "http://localhost:8000/api"
    
    print(f"Generating and storing {num_transactions} random transactions...")
    
    for i in range(num_transactions):
        transaction = generate_transaction()
        
        try:
            response = requests.post(f"{API_BASE_URL}/detect", json=transaction)
            
            if response.status_code == 200:
                result = response.json()
                print(f"Transaction {i+1}/{num_transactions} stored with ID: {result['transaction_id']}")
                print(f"  Fraud Status: {'Fraudulent' if result['is_fraud_predicted'] else 'Legitimate'}")
                print(f"  Fraud Score: {result['fraud_score']:.4f}")
            else:
                print(f"Error storing transaction {i+1}: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"Exception while storing transaction {i+1}: {str(e)}")
    
    print("Transaction generation complete.")

if __name__ == "__main__":
    # Generate test data
    generate_test_data(num_transactions=100, output_file="test_data.json")
    
    # Generate batch request
    generate_batch_request(num_transactions=10, output_file="batch_request.json")
    
    # Generate and store transactions
    generate_and_store_transactions(num_transactions=10)
