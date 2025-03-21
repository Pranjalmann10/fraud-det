import requests
import json
import uuid
import sys
from datetime import datetime

# API endpoint
API_BASE_URL = "http://localhost:8001/api"

def submit_transaction(amount, payer_id, payee_id, payment_mode, channel, bank=None):
    """
    Submit a transaction to the API
    
    Args:
        amount (float): Transaction amount
        payer_id (str): Payer ID
        payee_id (str): Payee ID
        payment_mode (str): Payment mode (credit_card, debit_card, bank_transfer, wallet, upi)
        channel (str): Channel (web, mobile_app, pos, atm, branch)
        bank (str, optional): Bank name. Defaults to None.
    
    Returns:
        dict: API response
    """
    # Create transaction data
    transaction_id = f"user-{uuid.uuid4()}"
    transaction_data = {
        "transaction_id": transaction_id,
        "amount": float(amount),
        "payer_id": payer_id,
        "payee_id": payee_id,
        "payment_mode": payment_mode,
        "channel": channel,
        "bank": bank,
        "additional_data": {
            "ip_address": "192.168.1.1",
            "user_agent": "Mozilla/5.0",
            "device_id": "USER_DEVICE_123",
            "location": "User Location",
            "time_of_day": "day" if 6 <= datetime.now().hour < 18 else "night"
        }
    }
    
    # Print transaction data for debugging
    print(f"Submitting transaction: {json.dumps(transaction_data)}")
    
    # Send transaction to API
    try:
        response = requests.post(f"{API_BASE_URL}/detect", json=transaction_data)
        print(f"API response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Transaction ID: {result['transaction_id']}")
            print(f"Fraud Detected: {result['is_fraud_predicted']}")
            print(f"Fraud Score: {result['fraud_score']:.4f}")
            print(f"Processing Time: {result['prediction_time_ms']} ms")
            
            # Check recent transactions
            check_recent_transactions()
            
            return result
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Exception: {str(e)}")
        return None

def check_recent_transactions():
    """
    Check recent transactions in the database
    
    Returns:
        list: Recent transactions
    """
    try:
        response = requests.get(f"{API_BASE_URL}/transactions", params={"limit": 5})
        
        if response.status_code == 200:
            transactions = response.json()
            print(f"\n=== Recent Transactions ===")
            print(f"Number of transactions: {len(transactions)}")
            
            for i, tx in enumerate(transactions, 1):
                print(f"\nTransaction {i}:")
                print(f"  ID: {tx['transaction_id']}")
                print(f"  Amount: ${tx['amount']:,.2f}")
                print(f"  Fraud: {tx['is_fraud_predicted']}")
                print(f"  Score: {tx['fraud_score']:.4f}")
                if 'timestamp' in tx:
                    print(f"  Time: {tx['timestamp']}")
            
            return transactions
        else:
            print(f"Error retrieving transactions: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        print(f"Exception retrieving transactions: {str(e)}")
        return []

if __name__ == "__main__":
    # Check if arguments are provided
    if len(sys.argv) < 6:
        print("Usage: python submit_transaction.py <amount> <payer_id> <payee_id> <payment_mode> <channel> [bank]")
        print("\nPayment modes: credit_card, debit_card, bank_transfer, wallet, upi")
        print("Channels: web, mobile_app, pos, atm, branch")
        print("\nExample: python submit_transaction.py 1000 USER123 MERCHANT456 credit_card web 'Example Bank'")
        sys.exit(1)
    
    # Get arguments
    amount = float(sys.argv[1])
    payer_id = sys.argv[2]
    payee_id = sys.argv[3]
    payment_mode = sys.argv[4]
    channel = sys.argv[5]
    bank = sys.argv[6] if len(sys.argv) > 6 else None
    
    # Submit transaction
    submit_transaction(amount, payer_id, payee_id, payment_mode, channel, bank)
