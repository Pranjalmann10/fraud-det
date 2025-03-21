import dash
from dash import dcc, html, dash_table, Input, Output, State, callback
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objs as go
import pandas as pd
import requests
import json
from datetime import datetime, timedelta
import numpy as np
import uuid

# Initialize the Dash app with a Bootstrap theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])
app.title = "Fraud Detection Dashboard"

# API endpoints
API_BASE_URL = "http://localhost:8000/api"
TRANSACTIONS_URL = f"{API_BASE_URL}/transactions"
METRICS_URL = f"{API_BASE_URL}/metrics"

# Function to fetch data from API
def fetch_transactions(limit=1000, offset=0, **filters):
    params = {"limit": limit, "offset": offset, **filters}
    try:
        response = requests.get(TRANSACTIONS_URL, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error fetching transactions: {response.status_code}")
            return []
    except Exception as e:
        print(f"Error connecting to API: {str(e)}")
        return []

def fetch_metrics(start_date=None, end_date=None):
    params = {}
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date
        
    try:
        response = requests.get(METRICS_URL, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error fetching metrics: {response.status_code}")
            return default_metrics()
    except Exception as e:
        print(f"Error connecting to API: {str(e)}")
        return default_metrics()

def default_metrics():
    return {
        "confusion_matrix": {"true_positives": 0, "false_positives": 0, "true_negatives": 0, "false_negatives": 0},
        "precision": 0,
        "recall": 0,
        "f1_score": 0,
        "total_transactions": 0,
        "predicted_frauds": 0,
        "reported_frauds": 0
    }

# Create header
header = dbc.Navbar(
    dbc.Container(
        [
            html.A(
                dbc.Row(
                    [
                        dbc.Col(html.I(className="fas fa-shield-alt", style={"fontSize": 30, "marginRight": 10})),
                        dbc.Col(dbc.NavbarBrand("Fraud Detection, Alert, and Monitoring System", className="ms-2")),
                    ],
                    align="center",
                ),
                href="/",
                style={"textDecoration": "none"},
            ),
            dbc.NavbarToggler(id="navbar-toggler"),
        ]
    ),
    color="primary",
    dark=True,
)

# Create sidebar
sidebar = html.Div(
    [
        html.H5("Filters", className="display-7"),
        html.Hr(),
        html.P("Date Range", className="lead"),
        dcc.DatePickerRange(
            id="date-range",
            start_date=datetime.now() - timedelta(days=30),
            end_date=datetime.now(),
            display_format="YYYY-MM-DD",
            className="mb-3",
        ),
        html.P("Payment Mode", className="lead"),
        dcc.Dropdown(
            id="payment-mode-filter",
            options=[
                {"label": "All", "value": "all"},
                {"label": "Credit Card", "value": "credit_card"},
                {"label": "Debit Card", "value": "debit_card"},
                {"label": "Bank Transfer", "value": "bank_transfer"},
                {"label": "Wallet", "value": "wallet"},
                {"label": "UPI", "value": "upi"},
            ],
            value="all",
            className="mb-3",
        ),
        html.P("Channel", className="lead"),
        dcc.Dropdown(
            id="channel-filter",
            options=[
                {"label": "All", "value": "all"},
                {"label": "Web", "value": "web"},
                {"label": "Mobile App", "value": "mobile_app"},
                {"label": "POS", "value": "pos"},
                {"label": "ATM", "value": "atm"},
                {"label": "Branch", "value": "branch"},
            ],
            value="all",
            className="mb-3",
        ),
        html.P("Fraud Status", className="lead"),
        dcc.Dropdown(
            id="fraud-status-filter",
            options=[
                {"label": "All", "value": "all"},
                {"label": "Fraudulent", "value": "true"},
                {"label": "Legitimate", "value": "false"},
            ],
            value="all",
            className="mb-3",
        ),
        html.Div([
            dbc.Button("Apply Filters", id="apply-filters", color="primary", className="me-2"),
            dbc.Button("Reset Filters", id="reset-filters", color="secondary", className="me-2"),
            dbc.Button("Refresh Data", id="refresh-data", color="success"),
        ], className="d-grid gap-2"),
        html.Hr(),
        html.H5("Add New Transaction", className="display-7"),
        dbc.Input(id="new-transaction-amount", type="number", placeholder="Amount", className="mb-2"),
        dbc.Input(id="new-transaction-payer", type="text", placeholder="Payer ID", className="mb-2"),
        dbc.Input(id="new-transaction-payee", type="text", placeholder="Payee ID", className="mb-2"),
        dbc.Select(
            id="new-transaction-payment-mode",
            options=[
                {"label": "Credit Card", "value": "credit_card"},
                {"label": "Debit Card", "value": "debit_card"},
                {"label": "Bank Transfer", "value": "bank_transfer"},
                {"label": "Wallet", "value": "wallet"},
                {"label": "UPI", "value": "upi"},
            ],
            placeholder="Payment Mode",
            className="mb-2",
        ),
        dbc.Select(
            id="new-transaction-channel",
            options=[
                {"label": "Web", "value": "web"},
                {"label": "Mobile App", "value": "mobile_app"},
                {"label": "POS", "value": "pos"},
                {"label": "ATM", "value": "atm"},
                {"label": "Branch", "value": "branch"},
            ],
            placeholder="Channel",
            className="mb-2",
        ),
        dbc.Input(id="new-transaction-bank", type="text", placeholder="Bank (Optional)", className="mb-2"),
        dbc.Button("Submit Transaction", id="submit-transaction", color="primary", className="w-100"),
        html.Div(id="transaction-submission-result", className="mt-2"),
    ],
    style={"padding": "20px", "background-color": "#f8f9fa"},
)

# Create metrics cards
metrics_cards = dbc.Row(
    [
        dbc.Col(
            dbc.Card(
                [
                    dbc.CardHeader("Total Transactions", className="text-center"),
                    dbc.CardBody(
                        [
                            html.H4(id="total-transactions", className="card-title text-center"),
                        ]
                    ),
                ],
                className="mb-4",
            ),
            width=4,
        ),
        dbc.Col(
            dbc.Card(
                [
                    dbc.CardHeader("Predicted Frauds", className="card-title text-center"),
                    dbc.CardBody(
                        [
                            html.H4(id="predicted-frauds", className="card-title text-center"),
                        ]
                    ),
                ],
                className="mb-4",
            ),
            width=4,
        ),
        dbc.Col(
            dbc.Card(
                [
                    dbc.CardHeader("Reported Frauds", className="card-title text-center"),
                    dbc.CardBody(
                        [
                            html.H4(id="reported-frauds", className="card-title text-center"),
                        ]
                    ),
                ],
                className="mb-4",
            ),
            width=4,
        ),
    ]
)

performance_metrics = dbc.Row(
    [
        dbc.Col(
            dbc.Card(
                [
                    dbc.CardHeader("Precision", className="text-center"),
                    dbc.CardBody(
                        [
                            html.H4(id="precision-metric", className="card-title text-center"),
                        ]
                    ),
                ],
                className="mb-4",
            ),
            width=4,
        ),
        dbc.Col(
            dbc.Card(
                [
                    dbc.CardHeader("Recall", className="text-center"),
                    dbc.CardBody(
                        [
                            html.H4(id="recall-metric", className="card-title text-center"),
                        ]
                    ),
                ],
                className="mb-4",
            ),
            width=4,
        ),
        dbc.Col(
            dbc.Card(
                [
                    dbc.CardHeader("F1 Score", className="text-center"),
                    dbc.CardBody(
                        [
                            html.H4(id="f1-score-metric", className="card-title text-center"),
                        ]
                    ),
                ],
                className="mb-4",
            ),
            width=4,
        ),
    ]
)

# Create graphs
graphs = dbc.Row(
    [
        dbc.Col(
            dbc.Card(
                [
                    dbc.CardHeader("Fraud Distribution by Payment Mode"),
                    dbc.CardBody(
                        [
                            dcc.Graph(id="payment-mode-graph"),
                        ]
                    ),
                ],
                className="mb-4",
            ),
            width=6,
        ),
        dbc.Col(
            dbc.Card(
                [
                    dbc.CardHeader("Fraud Distribution by Channel"),
                    dbc.CardBody(
                        [
                            dcc.Graph(id="channel-graph"),
                        ]
                    ),
                ],
                className="mb-4",
            ),
            width=6,
        ),
    ]
)

more_graphs = dbc.Row(
    [
        dbc.Col(
            dbc.Card(
                [
                    dbc.CardHeader("Confusion Matrix"),
                    dbc.CardBody(
                        [
                            dcc.Graph(id="confusion-matrix"),
                        ]
                    ),
                ],
                className="mb-4",
            ),
            width=6,
        ),
        dbc.Col(
            dbc.Card(
                [
                    dbc.CardHeader("Transaction Amount Distribution"),
                    dbc.CardBody(
                        [
                            dcc.Graph(id="amount-distribution"),
                        ]
                    ),
                ],
                className="mb-4",
            ),
            width=6,
        ),
    ]
)

# Create data table
data_table = dbc.Card(
    [
        dbc.CardHeader("Transaction Data"),
        dbc.CardBody(
            [
                html.Div(
                    [
                        dbc.Input(
                            id="search-input",
                            type="text",
                            placeholder="Search transactions...",
                            className="mb-3",
                        ),
                        dash_table.DataTable(
                            id="transaction-table",
                            columns=[
                                {"name": "Transaction ID", "id": "transaction_id"},
                                {"name": "Amount", "id": "amount", "type": "numeric", "format": {"specifier": "$,.2f"}},
                                {"name": "Payer ID", "id": "payer_id"},
                                {"name": "Payee ID", "id": "payee_id"},
                                {"name": "Payment Mode", "id": "payment_mode"},
                                {"name": "Channel", "id": "channel"},
                                {"name": "Bank", "id": "bank"},
                                {"name": "Fraud Predicted", "id": "is_fraud_predicted"},
                                {"name": "Fraud Score", "id": "fraud_score", "type": "numeric", "format": {"specifier": ".2%"}},
                            ],
                            data=[],
                            page_size=10,
                            style_table={"overflowX": "auto"},
                            style_cell={
                                "textAlign": "left",
                                "padding": "10px",
                                "whiteSpace": "normal",
                                "height": "auto",
                            },
                            style_header={
                                "backgroundColor": "rgb(230, 230, 230)",
                                "fontWeight": "bold",
                            },
                            style_data_conditional=[
                                {
                                    "if": {"filter_query": "{is_fraud_predicted} eq true"},
                                    "backgroundColor": "rgba(255, 0, 0, 0.1)",
                                    "color": "red",
                                }
                            ],
                            sort_action="native",
                            filter_action="native",
                            row_selectable="single",
                        ),
                    ]
                ),
            ]
        ),
    ],
    className="mb-4",
)

# Create transaction details modal
transaction_details_modal = dbc.Modal(
    [
        dbc.ModalHeader(dbc.ModalTitle("Transaction Details")),
        dbc.ModalBody(id="transaction-details-body"),
        dbc.ModalFooter(
            dbc.Button("Close", id="close-transaction-details", className="ms-auto", n_clicks=0)
        ),
    ],
    id="transaction-details-modal",
    size="lg",
    is_open=False,
)

# Create app layout
app.layout = html.Div(
    [
        header,
        dbc.Container(
            [
                html.H1("Fraud Detection Dashboard", className="my-4"),
                dbc.Row(
                    [
                        dbc.Col(sidebar, width=3),
                        dbc.Col(
                            [
                                metrics_cards,
                                performance_metrics,
                                graphs,
                                more_graphs,
                                data_table,
                            ],
                            width=9,
                        ),
                    ]
                ),
                transaction_details_modal,
                # Store component to store the current transactions data
                dcc.Store(id="transactions-store"),
                # Interval component for automatic refresh
                dcc.Interval(
                    id="interval-component",
                    interval=60*1000,  # in milliseconds (1 minute)
                    n_intervals=0
                ),
            ],
            fluid=True,
            className="mt-4",
        ),
    ]
)

# Callbacks
@app.callback(
    Output("transactions-store", "data"),
    [
        Input("apply-filters", "n_clicks"),
        Input("reset-filters", "n_clicks"),
        Input("refresh-data", "n_clicks"),
        Input("interval-component", "n_intervals")
    ],
    [
        State("date-range", "start_date"),
        State("date-range", "end_date"),
        State("payment-mode-filter", "value"),
        State("channel-filter", "value"),
        State("fraud-status-filter", "value"),
    ],
)
def update_transactions_store(apply_clicks, reset_clicks, refresh_clicks, n_intervals, start_date, end_date, payment_mode, channel, fraud_status):
    ctx = dash.callback_context
    if not ctx.triggered:
        # Initial load
        transactions = fetch_transactions()
    else:
        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
        
        if trigger_id == "reset-filters":
            transactions = fetch_transactions()
        else:
            # Apply filters
            filters = {}
            if start_date:
                filters["start_date"] = start_date
            if end_date:
                filters["end_date"] = end_date
            if payment_mode and payment_mode != "all":
                filters["payment_mode"] = payment_mode
            if channel and channel != "all":
                filters["channel"] = channel
            if fraud_status and fraud_status != "all":
                filters["is_fraud"] = fraud_status == "true"
                
            transactions = fetch_transactions(**filters)
    
    return transactions

@app.callback(
    [
        Output("transaction-table", "data"),
        Output("payment-mode-graph", "figure"),
        Output("channel-graph", "figure"),
        Output("confusion-matrix", "figure"),
        Output("amount-distribution", "figure"),
        Output("total-transactions", "children"),
        Output("predicted-frauds", "children"),
        Output("reported-frauds", "children"),
        Output("precision-metric", "children"),
        Output("recall-metric", "children"),
        Output("f1-score-metric", "children"),
    ],
    [
        Input("transactions-store", "data"),
        Input("search-input", "value"),
    ],
)
def update_dashboard(transactions, search_value):
    # Get metrics
    metrics = fetch_metrics()
    
    # Convert transactions to dataframe
    if not transactions:
        transactions = []
    
    df = pd.DataFrame(transactions)
    
    # Filter by search value if provided
    filtered_transactions = transactions
    if search_value and len(df) > 0:
        search_value = search_value.lower()
        filtered_df = df[
            df.apply(
                lambda row: any(
                    str(val).lower().find(search_value) >= 0
                    for val in row.values
                    if val is not None
                ),
                axis=1,
            )
        ]
        filtered_transactions = filtered_df.to_dict("records")
    
    # Create visualizations
    if len(df) > 0 and "payment_mode" in df.columns and "is_fraud_predicted" in df.columns:
        # Payment mode distribution
        payment_mode_counts = df.groupby(["payment_mode", "is_fraud_predicted"]).size().reset_index(name="count")
        payment_mode_fig = px.bar(
            payment_mode_counts,
            x="payment_mode",
            y="count",
            color="is_fraud_predicted",
            title="Fraud Distribution by Payment Mode",
            labels={"payment_mode": "Payment Mode", "count": "Count", "is_fraud_predicted": "Fraud Predicted"},
            color_discrete_map={True: "red", False: "green"},
        )
    else:
        payment_mode_fig = go.Figure()
        payment_mode_fig.update_layout(title="No data available")
    
    # Channel distribution
    if len(df) > 0 and "channel" in df.columns and "is_fraud_predicted" in df.columns:
        channel_counts = df.groupby(["channel", "is_fraud_predicted"]).size().reset_index(name="count")
        channel_fig = px.bar(
            channel_counts,
            x="channel",
            y="count",
            color="is_fraud_predicted",
            title="Fraud Distribution by Channel",
            labels={"channel": "Channel", "count": "Count", "is_fraud_predicted": "Fraud Predicted"},
            color_discrete_map={True: "red", False: "green"},
        )
    else:
        channel_fig = go.Figure()
        channel_fig.update_layout(title="No data available")
    
    # Create confusion matrix
    confusion_matrix = metrics.get("confusion_matrix", {"true_positives": 0, "false_positives": 0, "true_negatives": 0, "false_negatives": 0})
    confusion_df = pd.DataFrame([
        ["Fraud", confusion_matrix.get("true_positives", 0), confusion_matrix.get("false_negatives", 0)],
        ["Not Fraud", confusion_matrix.get("false_positives", 0), confusion_matrix.get("true_negatives", 0)]
    ], columns=["Actual", "Predicted Fraud", "Predicted Not Fraud"])
    
    confusion_matrix_fig = px.imshow(
        confusion_df.iloc[:, 1:].values,
        x=["Predicted Fraud", "Predicted Not Fraud"],
        y=["Actual Fraud", "Actual Not Fraud"],
        color_continuous_scale="RdBu_r",
        labels=dict(color="Count"),
        text_auto=True
    )
    
    # Create amount distribution
    if len(df) > 0 and "amount" in df.columns and "is_fraud_predicted" in df.columns:
        amount_fig = px.histogram(
            df,
            x="amount",
            color="is_fraud_predicted",
            nbins=20,
            title="Transaction Amount Distribution",
            labels={"amount": "Amount", "is_fraud_predicted": "Fraud Predicted"},
            color_discrete_map={True: "red", False: "green"},
        )
    else:
        amount_fig = go.Figure()
        amount_fig.update_layout(title="No data available")
    
    # Format metrics
    total_transactions = f"{metrics['total_transactions']:,}"
    predicted_frauds = f"{metrics['predicted_frauds']:,}"
    reported_frauds = f"{metrics['reported_frauds']:,}"
    precision = f"{metrics['precision']:.2%}"
    recall = f"{metrics['recall']:.2%}"
    f1_score = f"{metrics['f1_score']:.2%}"
    
    return (
        filtered_transactions,
        payment_mode_fig,
        channel_fig,
        confusion_matrix_fig,
        amount_fig,
        total_transactions,
        predicted_frauds,
        reported_frauds,
        precision,
        recall,
        f1_score,
    )

@app.callback(
    [
        Output("transaction-details-modal", "is_open"),
        Output("transaction-details-body", "children"),
    ],
    [
        Input("transaction-table", "selected_rows"),
        Input("close-transaction-details", "n_clicks"),
    ],
    [
        State("transaction-table", "data"),
        State("transaction-details-modal", "is_open"),
    ],
)
def toggle_transaction_details(selected_rows, close_clicks, data, is_open):
    ctx = dash.callback_context
    if not ctx.triggered:
        return False, []
    
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    if trigger_id == "close-transaction-details":
        return False, []
    
    if selected_rows and data:
        transaction = data[selected_rows[0]]
        
        # Create transaction details
        details = [
            html.H5("Transaction Information"),
            html.Hr(),
            dbc.Row([
                dbc.Col([
                    html.P("Transaction ID:"),
                    html.P("Amount:"),
                    html.P("Payer ID:"),
                    html.P("Payee ID:"),
                    html.P("Payment Mode:"),
                    html.P("Channel:"),
                    html.P("Bank:"),
                ], width=4),
                dbc.Col([
                    html.P(transaction["transaction_id"], className="fw-bold"),
                    html.P(f"${transaction['amount']:,.2f}", className="fw-bold"),
                    html.P(transaction["payer_id"], className="fw-bold"),
                    html.P(transaction["payee_id"], className="fw-bold"),
                    html.P(transaction["payment_mode"], className="fw-bold"),
                    html.P(transaction["channel"], className="fw-bold"),
                    html.P(transaction["bank"] if transaction["bank"] else "N/A", className="fw-bold"),
                ], width=8),
            ]),
            html.Hr(),
            html.H5("Fraud Detection Results"),
            html.Hr(),
            dbc.Row([
                dbc.Col([
                    html.P("Fraud Predicted:"),
                    html.P("Fraud Score:"),
                    html.P("Prediction Time:"),
                ], width=4),
                dbc.Col([
                    html.P(
                        "Yes" if transaction["is_fraud_predicted"] else "No", 
                        className="fw-bold text-danger" if transaction["is_fraud_predicted"] else "fw-bold text-success"
                    ),
                    html.P(f"{transaction['fraud_score']:.2%}", className="fw-bold"),
                    html.P(f"{transaction['prediction_time_ms']} ms", className="fw-bold"),
                ], width=8),
            ]),
        ]
        
        # Add additional data if available
        if "additional_data" in transaction and transaction["additional_data"]:
            additional_data = transaction["additional_data"]
            if isinstance(additional_data, str):
                try:
                    additional_data = json.loads(additional_data)
                except:
                    additional_data = {"data": additional_data}
            
            details.extend([
                html.Hr(),
                html.H5("Additional Information"),
                html.Hr(),
                dbc.Row([
                    dbc.Col([
                        html.P(f"{key}:") for key in additional_data.keys()
                    ], width=4),
                    dbc.Col([
                        html.P(f"{value}", className="fw-bold") for value in additional_data.values()
                    ], width=8),
                ]),
            ])
        
        return True, details
    
    return is_open, []

# Add callback for submitting a new transaction
@app.callback(
    [
        Output("transaction-submission-result", "children"),
        Output("transactions-store", "data", allow_duplicate=True),
        Output("new-transaction-amount", "value"),
        Output("new-transaction-payer", "value"),
        Output("new-transaction-payee", "value"),
        Output("new-transaction-payment-mode", "value"),
        Output("new-transaction-channel", "value"),
        Output("new-transaction-bank", "value"),
    ],
    [Input("submit-transaction", "n_clicks")],
    [
        State("new-transaction-amount", "value"),
        State("new-transaction-payer", "value"),
        State("new-transaction-payee", "value"),
        State("new-transaction-payment-mode", "value"),
        State("new-transaction-channel", "value"),
        State("new-transaction-bank", "value"),
        State("transactions-store", "data"),
    ],
    prevent_initial_call=True,
)
def submit_transaction(n_clicks, amount, payer_id, payee_id, payment_mode, channel, bank, current_transactions):
    if n_clicks is None:
        return "", dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
    
    if not all([amount, payer_id, payee_id, payment_mode, channel]):
        return html.Div("Please fill all required fields", className="text-danger"), dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
    
    # Create transaction data
    transaction_id = str(uuid.uuid4())
    transaction = {
        "transaction_id": transaction_id,
        "amount": float(amount),
        "payer_id": payer_id,
        "payee_id": payee_id,
        "payment_mode": payment_mode,
        "channel": channel,
        "bank": bank if bank else None,
        "additional_data": {
            "ip_address": "127.0.0.1",
            "user_agent": "Dashboard",
            "device_id": "DASHBOARD_DEVICE",
            "location": "Dashboard",
            "time_of_day": "day" if 6 <= datetime.now().hour < 18 else "night"
        }
    }
    
    # Send transaction to API
    try:
        response = requests.post(f"{API_BASE_URL}/detect", json=transaction)
        if response.status_code == 200:
            result = response.json()
            
            # Create a new transaction object for the dashboard
            new_transaction = {
                "transaction_id": transaction_id,
                "amount": float(amount),
                "payer_id": payer_id,
                "payee_id": payee_id,
                "payment_mode": payment_mode,
                "channel": channel,
                "bank": bank if bank else None,
                "created_at": datetime.now().isoformat(),
                "is_fraud_predicted": result['is_fraud_predicted'],
                "fraud_score": result['fraud_score'],
                "prediction_time_ms": result['prediction_time_ms'],
                "additional_data": json.dumps({
                    "ip_address": "127.0.0.1",
                    "user_agent": "Dashboard",
                    "device_id": "DASHBOARD_DEVICE",
                    "location": "Dashboard",
                    "time_of_day": "day" if 6 <= datetime.now().hour < 18 else "night"
                })
            }
            
            # Update the transactions store
            if current_transactions:
                updated_transactions = current_transactions.copy()
                updated_transactions.insert(0, new_transaction)  # Add to the beginning
            else:
                updated_transactions = [new_transaction]
            
            # Return success message and updated transactions
            return (
                html.Div([
                    html.P(f"Transaction {transaction_id} submitted successfully", className="text-success"),
                    html.P(f"Fraud detected: {result['is_fraud_predicted']}", 
                           className="text-danger" if result['is_fraud_predicted'] else "text-success"),
                    html.P(f"Fraud score: {result['fraud_score']:.2f}"),
                    html.P(f"Processing time: {result['prediction_time_ms']} ms"),
                ]),
                updated_transactions,
                None,  # Reset form fields
                None,
                None,
                None,
                None,
                None
            )
        else:
            return html.Div(f"Error: {response.status_code} - {response.text}", className="text-danger"), dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
    except Exception as e:
        return html.Div(f"Exception: {str(e)}", className="text-danger"), dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

# Run the app
if __name__ == "__main__":
    app.run_server(debug=True)
