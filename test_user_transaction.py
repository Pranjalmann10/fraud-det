import requests
import json
import uuid
from datetime import datetime

# API endpoint
API_BASE_URL = "http://localhost:8001/api"

def submit_user_transaction(transaction_data):
    """
    Submit a transaction to the API using the data provided by the user
    
    Args:
        transaction_data (dict): Transaction data from the user
    
    Returns:
        dict: API response
    """
    # Ensure transaction_id exists
    if "transaction_id" not in transaction_data:
        transaction_data["transaction_id"] = str(uuid.uuid4())
    
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
            return result
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Exception: {str(e)}")
        return None

def submit_user_json_transaction(transaction_data):
    """
    Submit a transaction to the API using the JSON data provided by the user
    
    Args:
        transaction_data (dict): Transaction data from the user
    
    Returns:
        dict: API response
    """
    # Ensure transaction_id exists
    if "transaction_id" not in transaction_data:
        transaction_data["transaction_id"] = str(uuid.uuid4())
    
    # Print transaction data for debugging
    print(f"Submitting JSON transaction: {json.dumps(transaction_data)}")
    
    # Send transaction to API
    try:
        response = requests.post(
            f"{API_BASE_URL}/detect-json", 
            json={"transaction_data": transaction_data}
        )
        
        print(f"API response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Transaction ID: {result['transaction_id']}")
            print(f"Fraud Detected: {result.get('is_fraud_predicted', 'Unknown')}")
            print(f"Fraud Score: {result.get('fraud_score', 0):.4f}")
            print(f"Fraud Source: {result.get('fraud_source', 'N/A')}")
            print(f"Fraud Reason: {result.get('fraud_reason', 'N/A')}")
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

def get_user_input():
    """
    Get transaction data from user input
    
    Returns:
        dict: Transaction data
    """
    print("\n=== Enter Transaction Details ===")
    
    # Generate a unique transaction ID
    transaction_id = f"user-{uuid.uuid4()}"
    
    # Get transaction details from user
    try:
        amount = float(input("Amount: "))
        payer_id = input("Payer ID: ")
        payee_id = input("Payee ID: ")
        
        # Payment mode options
        print("\nPayment Mode Options:")
        print("1. Credit Card")
        print("2. Debit Card")
        print("3. Bank Transfer")
        print("4. Wallet")
        print("5. UPI")
        payment_mode_choice = int(input("Choose payment mode (1-5): "))
        payment_modes = ["credit_card", "debit_card", "bank_transfer", "wallet", "upi"]
        payment_mode = payment_modes[payment_mode_choice - 1]
        
        # Channel options
        print("\nChannel Options:")
        print("1. Web")
        print("2. Mobile App")
        print("3. POS")
        print("4. ATM")
        print("5. Branch")
        channel_choice = int(input("Choose channel (1-5): "))
        channels = ["web", "mobile_app", "pos", "atm", "branch"]
        channel = channels[channel_choice - 1]
        
        bank = input("Bank (optional, press Enter to skip): ")
        if not bank:
            bank = None
        
        # Create transaction data
        transaction_data = {
            "transaction_id": transaction_id,
            "amount": amount,
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
        
        return transaction_data
    except Exception as e:
        print(f"Error in input: {str(e)}")
        return None

if __name__ == "__main__":
    print("Fraud Detection System - Transaction Submission Tool")
    print("===================================================")
    
    while True:
        print("\nOptions:")
        print("1. Submit a new transaction")
        print("2. Check recent transactions")
        print("3. Exit")
        
        choice = input("\nEnter your choice (1-3): ")
        
        if choice == "1":
            # Get transaction data from user
            transaction_data = get_user_input()
            
            if transaction_data:
                # Ask which API to use
                print("\nAPI Options:")
                print("1. Regular API (/detect)")
                print("2. JSON API (/detect-json)")
                api_choice = input("Choose API (1-2): ")
                
                if api_choice == "1":
                    submit_user_transaction(transaction_data)
                else:
                    submit_user_json_transaction(transaction_data)
        
        elif choice == "2":
            check_recent_transactions()
        
        elif choice == "3":
            print("Exiting...")
            break
        
        else:
            print("Invalid choice. Please try again.")
