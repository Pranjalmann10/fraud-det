import requests
import json
import sys

# API endpoint
API_BASE_URL = "http://localhost:8001/api"

def check_transactions(limit=10):
    """
    Check transactions in the database
    
    Args:
        limit (int, optional): Maximum number of transactions to retrieve. Defaults to 10.
    
    Returns:
        list: Transactions
    """
    try:
        response = requests.get(f"{API_BASE_URL}/transactions", params={"limit": limit})
        
        if response.status_code == 200:
            transactions = response.json()
            print(f"\n=== Recent Transactions ===")
            print(f"Number of transactions: {len(transactions)}")
            
            for i, tx in enumerate(transactions, 1):
                print(f"\nTransaction {i}:")
                print(f"  ID: {tx['transaction_id']}")
                print(f"  Amount: ${tx['amount']:,.2f}")
                print(f"  Payer: {tx.get('payer_id', 'N/A')}")
                print(f"  Payee: {tx.get('payee_id', 'N/A')}")
                print(f"  Payment Mode: {tx.get('payment_mode', 'N/A')}")
                print(f"  Channel: {tx.get('channel', 'N/A')}")
                print(f"  Bank: {tx.get('bank', 'N/A')}")
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
    # Get limit from command line argument if provided
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    
    # Check transactions
    check_transactions(limit)
