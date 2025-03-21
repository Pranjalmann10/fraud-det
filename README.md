# Fraud Detection, Alert, and Monitoring (FDAM) System

A comprehensive system for detecting, reporting, and monitoring fraudulent transactions in a payment gateway.

## Core Components

1. **Real-Time Fraud Detection API**
   - Processes single transactions in real-time
   - Combines rule-based checks with AI model predictions
   - Response time under 300ms

2. **Batch Fraud Detection API**
   - Processes multiple transactions in parallel
   - Uses the same logic as the real-time API

3. **Fraud Reporting API**
   - Accepts fraud report submissions
   - Stores reports in the database

4. **Monitoring Dashboard**
   - Displays transaction data in tabular format
   - Provides filtering and search functionalities
   - Includes dynamic graphs and evaluation metrics

## Setup and Installation

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Set up environment variables in `.env` file
4. Load your pre-trained model (if available):
   ```
   python src/models/load_model.py path/to/your/fraud_model.pkl
   ```
5. Initialize the database:
   ```
   python src/database/init_db.py
   ```
6. Start the API server:
   ```
   uvicorn src.api.main:app --reload
   ```
7. Start the dashboard:
   ```
   python src/dashboard/app.py
   ```

## API Documentation

Once the server is running, access the API documentation at `http://localhost:8000/docs`

## Storing Data from the Frontend

The system provides three ways to store transaction data:

1. **Using the Dashboard Form**:
   - Navigate to the dashboard at `http://localhost:8050`
   - Use the "Add New Transaction" form in the sidebar
   - Fill in the required fields (Amount, Payer ID, Payee ID, Payment Mode, Channel)
   - Click "Submit Transaction"
   - The transaction will be processed by the API and stored in the database
   - Results will be displayed immediately on the dashboard

2. **Using JSON Transaction Processing**:
   - Navigate to the dashboard at `http://localhost:8050`
   - Scroll down to the "Process JSON Transaction" section in the sidebar
   - Enter your transaction data in JSON format
   - Click "Process JSON Transaction"
   - The transaction will be processed and the detailed fraud detection results will be displayed
   - The response includes transaction ID, fraud status, source (rule/model), reason, and score
   
   Example JSON input:
   ```json
   {
     "amount": 5000.00,
     "payer_id": "P12345",
     "payee_id": "M67890",
     "payment_mode": "credit_card",
     "channel": "web",
     "bank": "Chase",
     "additional_data": {
       "ip_address": "192.168.1.1",
       "user_agent": "Mozilla/5.0",
       "device_id": "D12345",
       "location": "New York",
       "time_of_day": "day"
     }
   }
   ```

3. **Using the Data Generation Scripts**:
   - Run `python generate_data.py` to generate random transactions
   - Run `python generate_high_risk_data.py` to generate high-risk transactions
   - Run `python generate_fraud_data.py` to generate potentially fraudulent transactions
   - All generated transactions are stored in the database and displayed on the dashboard

## Testing API Endpoints with Postman

1. **Import the Postman Collection**:
   - Open Postman
   - Click "Import" and select the `FDAM_Postman_Collection.json` file
   - The collection includes pre-configured requests for all API endpoints

2. **Testing the Process Transaction Endpoint**:
   - Select the "Process Transaction" request
   - The request body contains a sample transaction
   - Click "Send" to process the transaction
   - The response will include the transaction ID, fraud detection results, and processing time
   - The transaction will be stored in the database

3. **Testing the High-Risk Transaction Endpoint**:
   - Select the "High-Risk Transaction" request
   - This request contains a transaction with suspicious patterns
   - Click "Send" to process the transaction
   - The response will show a higher fraud score

4. **Getting All Transactions**:
   - Select the "Get All Transactions" request
   - Click "Send" to retrieve all transactions from the database

5. **Getting a Specific Transaction**:
   - After processing a transaction, its ID will be automatically saved as a collection variable
   - Select the "Get Transaction by ID" request
   - Click "Send" to retrieve the specific transaction

6. **Reporting Fraud**:
   - Select the "Report Fraud" request
   - The request body contains a sample fraud report
   - Click "Send" to submit the report
   - The report will be stored in the database and linked to the transaction

7. **Getting Metrics**:
   - Select the "Get Metrics" request
   - Click "Send" to retrieve fraud detection metrics

## Data Storage

All data is stored in an SQLite database located at `./fraud_detection.db`. The database schema includes:

1. **Transaction Table** (`fraud_detection`):
   - Stores all transaction details
   - Includes fraud detection results
   - Contains timestamps for analysis

2. **Fraud Report Table** (`fraud_reports`):
   - Stores user-submitted fraud reports
   - Links to transactions via transaction_id

The dashboard automatically refreshes to display the latest data from the database.
