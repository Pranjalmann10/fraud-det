import dash
from dash import dcc, html, dash_table, Input, Output, State, callback
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objs as go
import pandas as pd
import numpy as np
import requests
import json
import uuid
from datetime import datetime, timedelta
import os

# Initialize the Dash app with a Bootstrap theme
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True,
)

app.title = "Fraud Detection Dashboard"

# API base URL - configurable through environment variables
API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8001/api")
TRANSACTIONS_URL = f"{API_BASE_URL}/transactions"
METRICS_URL = f"{API_BASE_URL}/metrics"
RULES_URL = f"{API_BASE_URL}/rules"

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

def fetch_rules(active_only=False):
    """Fetch custom rules from the API"""
    params = {"active_only": active_only}
    try:
        response = requests.get(RULES_URL, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error fetching rules: {response.status_code}")
            return []
    except Exception as e:
        print(f"Error connecting to API: {str(e)}")
        return []

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
        
        # Add JSON Transaction Section
        html.Hr(),
        html.H5("Process JSON Transaction", className="display-7"),
        dcc.Textarea(
            id="json-transaction-input",
            placeholder='Enter transaction data in JSON format, e.g.:\n{\n  "amount": 1000,\n  "payer_id": "P12345",\n  "payee_id": "M67890",\n  "payment_mode": "credit_card",\n  "channel": "web"\n}',
            style={'width': '100%', 'height': 200},
            className="mb-2"
        ),
        dbc.Button("Process JSON Transaction", id="submit-json-transaction", color="primary", className="w-100"),
        html.Div(id="json-transaction-result", className="mt-2"),
    ],
    style={"padding": "20px", "backgroundColor": "#f8f9fa"},
)

# Create rule management tab
rule_management = html.Div(
    [
        html.H5("Rule Engine", className="display-7"),
        html.Hr(),
        html.P("Create and manage custom rules for fraud detection", className="lead mb-3"),
        dbc.Button("Create New Rule", id="create-rule-button", color="primary", className="mb-3 w-100"),
        html.Div(
            [
                dbc.Spinner(id="rules-loading-spinner", size="sm", color="primary"),
                html.Div(id="rules-list-container"),
            ]
        ),
    ],
    style={"padding": "20px", "backgroundColor": "#f8f9fa"},
)

# Create the rules management modal
rule_modal = dbc.Modal(
    [
        dbc.ModalHeader(dbc.ModalTitle(id="rule-modal-title")),
        dbc.ModalBody([
            # Form for rule creation/editing
            dbc.Form([
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Rule Name", html_for="rule-name-input"),
                        dbc.Input(
                            id="rule-name-input", 
                            type="text", 
                            placeholder="Enter a unique name for this rule"
                        ),
                        dbc.FormText("Must be unique"),
                    ], width=12),
                ], className="mb-3"),
                
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Description", html_for="rule-description-input"),
                        dbc.Textarea(
                            id="rule-description-input", 
                            placeholder="Enter a description explaining what this rule detects"
                        ),
                    ], width=12),
                ], className="mb-3"),
                
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Rule Type", html_for="rule-type-input"),
                        dbc.Select(
                            id="rule-type-input",
                            options=[
                                {"label": "Threshold", "value": "threshold"},
                                {"label": "Pattern", "value": "pattern"},
                                {"label": "Combination", "value": "combination"},
                                {"label": "Velocity", "value": "velocity"},
                                {"label": "Custom", "value": "custom"},
                            ],
                        ),
                    ], width=6),
                    
                    dbc.Col([
                        dbc.Label("Field", html_for="rule-field-input"),
                        dbc.Select(
                            id="rule-field-input",
                            options=[
                                {"label": "Amount", "value": "amount"},
                                {"label": "Payment Mode", "value": "payment_mode"},
                                {"label": "Channel", "value": "channel"},
                                {"label": "Bank", "value": "bank"},
                                {"label": "Payer ID", "value": "payer_id"},
                                {"label": "Payee ID", "value": "payee_id"},
                                {"label": "Custom", "value": "custom"},
                            ],
                        ),
                    ], width=6),
                ], className="mb-3"),
                
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Operator", html_for="rule-operator-input"),
                        dbc.Select(
                            id="rule-operator-input",
                            options=[
                                {"label": "Equals (==)", "value": "=="},
                                {"label": "Not Equals (!=)", "value": "!="},
                                {"label": "Greater Than (>)", "value": ">"},
                                {"label": "Less Than (<)", "value": "<"},
                                {"label": "Greater Than or Equal (>=)", "value": ">="},
                                {"label": "Less Than or Equal (<=)", "value": "<="},
                                {"label": "In List", "value": "in"},
                                {"label": "Not In List", "value": "not_in"},
                                {"label": "Contains", "value": "contains"},
                                {"label": "Not Contains", "value": "not_contains"},
                                {"label": "Starts With", "value": "starts_with"},
                                {"label": "Ends With", "value": "ends_with"},
                            ],
                        ),
                    ], width=6),
                    
                    dbc.Col([
                        dbc.Label("Value", html_for="rule-value-input"),
                        dbc.Input(
                            id="rule-value-input", 
                            type="text", 
                            placeholder="Value to compare with"
                        ),
                        dbc.FormText("For 'In List' use comma-separated values", id="rule-value-help"),
                    ], width=6),
                ], className="mb-3"),
                
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Risk Score", html_for="rule-score-input"),
                        dbc.Input(
                            id="rule-score-input", 
                            type="number", 
                            min=0.0, 
                            max=1.0, 
                            step=0.05, 
                            value=0.5,
                            placeholder="Score between 0.0 and 1.0"
                        ),
                        dbc.FormText("Risk score to apply when rule matches (0.0-1.0)"),
                    ], width=6),
                    
                    dbc.Col([
                        dbc.Label("Priority", html_for="rule-priority-input"),
                        dbc.Input(
                            id="rule-priority-input", 
                            type="number", 
                            min=1, 
                            value=1,
                            placeholder="Rule priority"
                        ),
                        dbc.FormText("Higher number = higher priority"),
                    ], width=6),
                ], className="mb-3"),
                
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Status"),
                        dbc.Checklist(
                            options=[{"label": "Active", "value": True}],
                            value=[True],
                            id="rule-active-checklist",
                            switch=True,
                        ),
                    ], width=12),
                ], className="mb-3"),
                
                # Hidden fields for rule ID when editing
                dcc.Store(id="rule-id-store", data=None),
                
                # Advanced config (initially hidden)
                dbc.Collapse(
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Advanced Configuration (JSON)", html_for="rule-advanced-input"),
                            dbc.Textarea(
                                id="rule-advanced-input", 
                                placeholder='{"key": "value"}',
                                style={"height": "150px"},
                            ),
                            dbc.FormText("JSON format for complex rule configuration"),
                        ], width=12),
                    ], className="mb-3"),
                    id="advanced-config-collapse",
                    is_open=False,
                ),
                
                dbc.Button(
                    "Show Advanced Options", 
                    id="toggle-advanced-config", 
                    color="secondary", 
                    outline=True,
                    size="sm",
                    className="mb-3"
                ),
                
                html.Div(id="rule-submit-feedback"),
            ]),
        ]),
        dbc.ModalFooter([
            dbc.Button("Cancel", id="cancel-rule-button", className="me-2"),
            dbc.Button("Save Rule", id="save-rule-button", color="primary"),
        ]),
    ],
    id="rule-modal",
    size="lg",
    is_open=False,
)

# Create a component to display the list of rules
def create_rule_list(rules):
    if not rules or len(rules) == 0:
        return html.Div([
            html.P("No rules defined yet. Click 'Create New Rule' to add one.", className="text-muted fst-italic")
        ])
    
    rule_cards = []
    for rule in rules:
        # Format the rule condition for display
        field = rule.get("field", "")
        operator = rule.get("operator", "")
        value = rule.get("value", "")
        
        # Convert operators to readable format
        operator_map = {
            "==": "equals",
            "!=": "not equals",
            ">": "greater than",
            "<": "less than",
            ">=": "greater than or equal to",
            "<=": "less than or equal to",
            "in": "is in list",
            "not_in": "is not in list",
            "contains": "contains",
            "not_contains": "does not contain",
            "starts_with": "starts with",
            "ends_with": "ends with"
        }
        readable_operator = operator_map.get(operator, operator)
        
        # Create condition text
        condition = f"{field} {readable_operator} {value}"
        
        # Create a card for each rule
        card = dbc.Card([
            dbc.CardHeader([
                html.Div([
                    html.H5(rule.get("name", "Unnamed Rule"), className="mb-0 d-inline"),
                    html.Span(
                        "Active" if rule.get("is_active", False) else "Inactive",
                        className=f"ms-2 badge {'bg-success' if rule.get('is_active', False) else 'bg-secondary'}"
                    ),
                    html.Span(
                        f"Priority: {rule.get('priority', 1)}",
                        className="ms-2 badge bg-info"
                    ),
                    html.Span(
                        f"Score: {rule.get('score', 0.0)}",
                        className="ms-2 badge bg-warning text-dark"
                    ),
                ]),
            ]),
            dbc.CardBody([
                html.P(rule.get("description", "No description"), className="card-text text-muted"),
                html.P([
                    html.Strong("Condition: "),
                    condition
                ], className="card-text"),
                html.P([
                    html.Strong("Rule Type: "),
                    rule.get("rule_type", "")
                ], className="card-text small"),
            ]),
            dbc.CardFooter([
                dbc.ButtonGroup([
                    dbc.Button("Edit", color="primary", outline=True, size="sm", 
                               id={"type": "edit-rule-button", "index": rule.get("id")}),
                    dbc.Button("Delete", color="danger", outline=True, size="sm",
                               id={"type": "delete-rule-button", "index": rule.get("id")}),
                    dbc.Button(
                        "Deactivate" if rule.get("is_active", False) else "Activate", 
                        color="warning" if rule.get("is_active", False) else "success", 
                        outline=True, 
                        size="sm",
                        id={"type": "toggle-rule-status-button", "index": rule.get("id")},
                    ),
                ]),
            ]),
        ], className="mb-3", outline=True,
        color="success" if rule.get("is_active", False) else "secondary")
        
        rule_cards.append(card)
    
    return html.Div(rule_cards)

# Create delete confirmation modal
delete_rule_modal = dbc.Modal(
    [
        dbc.ModalHeader(dbc.ModalTitle("Confirm Deletion")),
        dbc.ModalBody("Are you sure you want to delete this rule? This action cannot be undone."),
        dbc.ModalFooter([
            dbc.Button("Cancel", id="cancel-delete-rule", className="me-2"),
            dbc.Button("Delete", id="confirm-delete-rule", color="danger"),
        ]),
    ],
    id="delete-rule-modal",
    is_open=False,
)

# Store for the rule to be deleted
dcc.Store(id="delete-rule-id-store", data=None)

# Create a container for rules storage
dcc.Store(id="rules-store", data=[])

# Create tabbed interface for the sidebar
sidebar_tabs = dbc.Tabs(
    [
        dbc.Tab(sidebar, label="Dashboard", tab_id="dashboard-tab"),
        dbc.Tab(rule_management, label="Rule Engine", tab_id="rule-engine-tab"),
    ],
    id="sidebar-tabs",
    active_tab="dashboard-tab",
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
            width=6,
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
            width=6,
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
                            id="table-search",
                            type="text",
                            placeholder="Search transactions...",
                            className="mb-3",
                        ),
                        # Add a div to show transaction submission results
                        html.Div(id="transaction-submission-result", className="mb-3"),
                        # Add a collapsible for JSON input/output
                        html.Div(id="json-display-container", className="mb-3"),
                        # Data table for showing all transactions
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
                                {"name": "Fraud Score", "id": "fraud_score", "type": "numeric", "format": {"specifier": ".2f"}},
                                {"name": "Timestamp", "id": "timestamp"},
                            ],
                            data=[],
                            page_size=10,
                            style_table={"overflowX": "auto"},
                            style_cell={
                                "textAlign": "left",
                                "padding": "10px",
                                "whiteSpace": "normal",
                                "height": "auto",
                                "font-family": "Arial, sans-serif",
                            },
                            style_header={
                                "backgroundColor": "#e6e6e6",
                                "fontWeight": "bold",
                                "border": "1px solid #d3d3d3",
                            },
                            style_data={
                                "border": "1px solid #d3d3d3",
                            },
                            style_data_conditional=[
                                {
                                    "if": {"column_id": "is_fraud_predicted", "filter_query": "{is_fraud_predicted} eq true"},
                                    "backgroundColor": "#ffcccc",
                                    "color": "red",
                                },
                                {
                                    "if": {"column_id": "is_fraud_predicted", "filter_query": "{is_fraud_predicted} eq false"},
                                    "backgroundColor": "#ccffcc",
                                    "color": "green",
                                },
                            ],
                            sort_action="native",
                            filter_action="native",
                            row_selectable="single",
                            selected_rows=[],
                        ),
                    ],
                    id="data-table-container",
                )
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

# Create a collapse component for JSON display when the app starts
json_collapse_init = html.Div(id="json-collapse-init")

# Create app layout
app.layout = dbc.Container(
    [
        header,
        html.Hr(),
        dbc.Row(
            [
                dbc.Col(sidebar_tabs, width=3),
                dbc.Col(
                    [
                        dcc.Interval(
                            id='interval-component',
                            interval=5*1000,  # in milliseconds (5 seconds)
                            n_intervals=0
                        ),
                        dcc.Store(id="transactions-store", data=[]),
                        dcc.Store(id="metrics-store", data=default_metrics()),
                        dcc.Store(id="rules-store", data=[]),
                        dcc.Store(id="delete-rule-id-store", data=None),
                        metrics_cards,
                        graphs,
                        more_graphs,
                        data_table,
                        transaction_details_modal,
                        rule_modal,
                        delete_rule_modal,
                        # Add this to initialize the collapse component
                        json_collapse_init,
                    ],
                    width=9,
                ),
            ]
        ),
    ],
    fluid=True,
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
    Output("metrics-store", "data"),
    [Input("interval-component", "n_intervals"),
     Input("transactions-store", "data")]
)
def update_metrics(n_intervals, transactions_data):
    """Update metrics store every interval"""
    return fetch_metrics()

@app.callback(
    [
        Output("transaction-table", "data"),
        Output("payment-mode-graph", "figure"),
        Output("channel-graph", "figure"),
        Output("confusion-matrix", "figure"),
        Output("amount-distribution", "figure"),
        Output("total-transactions", "children"),
        Output("predicted-frauds", "children"),
    ],
    [
        Input("transactions-store", "data"),
        Input("table-search", "value"),
        Input("metrics-store", "data"),
    ],
)
def update_dashboard(transactions, search_value, metrics):
    # Convert transactions to dataframe
    if not transactions:
        transactions = []
    
    df = pd.DataFrame(transactions)
    
    # Add empty dataframe if no data
    if len(df) == 0:
        df = pd.DataFrame(columns=["transaction_id", "amount", "payer_id", "payee_id", "payment_mode", "channel", "bank", "is_fraud_predicted", "fraud_score", "created_at"])
    
    # Filter data based on search value
    filtered_transactions = transactions
    if search_value:
        filtered_transactions = []
        search_value = search_value.lower()
        for tx in transactions:
            for key, value in tx.items():
                if isinstance(value, str) and search_value in value.lower():
                    filtered_transactions.append(tx)
                    break
                elif isinstance(value, (int, float)) and search_value in str(value).lower():
                    filtered_transactions.append(tx)
                    break
    
    # Create payment mode graph
    if len(df) > 0 and "payment_mode" in df.columns and "is_fraud_predicted" in df.columns:
        payment_mode_counts = df.groupby(["payment_mode", "is_fraud_predicted"]).size().reset_index(name="count")
        payment_mode_fig = px.bar(
            payment_mode_counts,
            x="payment_mode",
            y="count",
            color="is_fraud_predicted",
            barmode="group",
            title="Fraud Distribution by Payment Mode",
            labels={"payment_mode": "Payment Mode", "count": "Count", "is_fraud_predicted": "Fraud Predicted"},
            color_discrete_map={True: "red", False: "green"},
        )
    else:
        payment_mode_fig = go.Figure()
        payment_mode_fig.update_layout(title="No data available")
    
    # Create channel graph
    if len(df) > 0 and "channel" in df.columns and "is_fraud_predicted" in df.columns:
        channel_counts = df.groupby(["channel", "is_fraud_predicted"]).size().reset_index(name="count")
        channel_fig = px.bar(
            channel_counts,
            x="channel",
            y="count",
            color="is_fraud_predicted",
            barmode="group",
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
    
    return (
        filtered_transactions,
        payment_mode_fig,
        channel_fig,
        confusion_matrix_fig,
        amount_fig,
        total_transactions,
        predicted_frauds,
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

# Load rules from API
@app.callback(
    Output("rules-store", "data"),
    Input("interval-component", "n_intervals"),
    Input("sidebar-tabs", "active_tab"),
)
def update_rules_store(n_intervals, active_tab):
    """Fetch rules from the API and update the store"""
    if active_tab == "rule-engine-tab":
        return fetch_rules()
    # Don't refresh if we're not on the rules tab
    return dash.no_update

# Display rules list
@app.callback(
    Output("rules-list-container", "children"),
    Input("rules-store", "data"),
)
def display_rules(rules):
    """Display the list of rules from the store"""
    return create_rule_list(rules)

# Toggle advanced config collapse
@app.callback(
    Output("advanced-config-collapse", "is_open"),
    Input("toggle-advanced-config", "n_clicks"),
    State("advanced-config-collapse", "is_open"),
)
def toggle_advanced_config(n_clicks, is_open):
    if n_clicks:
        return not is_open
    return is_open

# Show rule modal when create button is clicked
@app.callback(
    [
        Output("rule-modal", "is_open"),
        Output("rule-modal-title", "children"),
        Output("rule-id-store", "data"),
        Output("rule-name-input", "value"),
        Output("rule-description-input", "value"),
        Output("rule-type-input", "value"),
        Output("rule-field-input", "value"),
        Output("rule-operator-input", "value"),
        Output("rule-value-input", "value"),
        Output("rule-score-input", "value"),
        Output("rule-priority-input", "value"),
        Output("rule-active-checklist", "value"),
        Output("rule-advanced-input", "value"),
    ],
    [
        Input("create-rule-button", "n_clicks"),
        Input({"type": "edit-rule-button", "index": dash.ALL}, "n_clicks"),
        Input("cancel-rule-button", "n_clicks"),
        Input("save-rule-button", "n_clicks"),
    ],
    [
        State("rule-modal", "is_open"),
        State("rules-store", "data"),
        State("rule-id-store", "data"),
    ],
    prevent_initial_call=True
)
def toggle_rule_modal(create_clicks, edit_clicks, cancel_clicks, save_clicks, is_open, rules, rule_id):
    ctx = dash.callback_context
    
    if not ctx.triggered:
        return dash.no_update
    
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    # Close modal on cancel or save
    if trigger_id in ["cancel-rule-button", "save-rule-button"]:
        return False, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, \
               dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
    
    # Create new rule
    if trigger_id == "create-rule-button":
        return True, "Create New Rule", None, "", "", "threshold", "amount", ">", "", 0.5, 1, [True], "{}"
    
    # Edit existing rule
    if "edit-rule-button" in trigger_id:
        # Extract rule ID from the trigger ID
        # The format is {"type":"edit-rule-button","index":rule_id}
        button_id = json.loads(trigger_id)
        rule_id_to_edit = button_id["index"]
        
        # Find the rule with this ID
        rule_to_edit = None
        for rule in rules:
            if rule.get("id") == rule_id_to_edit:
                rule_to_edit = rule
                break
        
        if rule_to_edit:
            # Set form values from the rule
            advanced_config = rule_to_edit.get("advanced_config", {})
            advanced_json = "{}" if advanced_config is None else json.dumps(advanced_config)
            is_active = rule_to_edit.get("is_active", False)
            
            return True, f"Edit Rule: {rule_to_edit.get('name', '')}", rule_id_to_edit, \
                   rule_to_edit.get("name", ""), rule_to_edit.get("description", ""), \
                   rule_to_edit.get("rule_type", "threshold"), rule_to_edit.get("field", "amount"), \
                   rule_to_edit.get("operator", ">"), rule_to_edit.get("value", ""), \
                   rule_to_edit.get("score", 0.5), rule_to_edit.get("priority", 1), \
                   [True] if is_active else [], advanced_json
    
    # Default fallback for any other case
    return dash.no_update

# Save Rule
@app.callback(
    [
        Output("rule-submit-feedback", "children"),
        Output("rules-store", "data", allow_duplicate=True),
    ],
    Input("save-rule-button", "n_clicks"),
    [
        State("rule-id-store", "data"),
        State("rule-name-input", "value"),
        State("rule-description-input", "value"),
        State("rule-type-input", "value"),
        State("rule-field-input", "value"),
        State("rule-operator-input", "value"),
        State("rule-value-input", "value"),
        State("rule-score-input", "value"),
        State("rule-priority-input", "value"),
        State("rule-active-checklist", "value"),
        State("rule-advanced-input", "value"),
        State("rules-store", "data"),
    ],
    prevent_initial_call=True
)
def save_rule(n_clicks, rule_id, name, description, rule_type, field, operator, value, score, priority, is_active, advanced_json, current_rules):
    if not n_clicks:
        return dash.no_update, dash.no_update
    
    # Validate inputs
    if not name or not field or not operator:
        return dbc.Alert("Rule name, field, and operator are required", color="danger"), dash.no_update
    
    # Process the values
    try:
        score = float(score) if score is not None else 0.5
        priority = int(priority) if priority is not None else 1
        is_active_bool = True if is_active and True in is_active else False
        
        # Parse advanced JSON
        try:
            advanced_config = json.loads(advanced_json) if advanced_json else {}
        except json.JSONDecodeError:
            return dbc.Alert("Invalid JSON in advanced configuration", color="danger"), dash.no_update
        
        # Create the rule data
        rule_data = {
            "name": name,
            "description": description or "",
            "rule_type": rule_type,
            "field": field,
            "operator": operator,
            "value": value,
            "score": score,
            "priority": priority,
            "is_active": is_active_bool,
            "advanced_config": advanced_config
        }
        
        # Create or update rule
        if rule_id is None:
            # Create new rule
            try:
                response = requests.post(RULES_URL, json=rule_data)
                if response.status_code == 200:
                    return dbc.Alert("Rule created successfully", color="success"), fetch_rules()
                else:
                    return dbc.Alert(f"Error creating rule: {response.text}", color="danger"), dash.no_update
            except Exception as e:
                return dbc.Alert(f"Error: {str(e)}", color="danger"), dash.no_update
        else:
            # Update existing rule
            try:
                response = requests.put(f"{RULES_URL}/{rule_id}", json=rule_data)
                if response.status_code == 200:
                    return dbc.Alert("Rule updated successfully", color="success"), fetch_rules()
                else:
                    return dbc.Alert(f"Error updating rule: {response.text}", color="danger"), dash.no_update
            except Exception as e:
                return dbc.Alert(f"Error: {str(e)}", color="danger"), dash.no_update
    
    except Exception as e:
        return dbc.Alert(f"Error: {str(e)}", color="danger"), dash.no_update

# Handle rule deletion
@app.callback(
    [
        Output("delete-rule-modal", "is_open"),
        Output("delete-rule-id-store", "data"),
    ],
    [
        Input({"type": "delete-rule-button", "index": dash.ALL}, "n_clicks"),
        Input("cancel-delete-rule", "n_clicks"),
        Input("confirm-delete-rule", "n_clicks"),
    ],
    [
        State("delete-rule-modal", "is_open"),
        State("delete-rule-id-store", "data"),
    ],
    prevent_initial_call=True
)
def handle_delete_modal(delete_clicks, cancel_clicks, confirm_clicks, is_open, current_rule_id):
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update, dash.no_update
    
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    # Close modal on cancel or confirm
    if trigger_id in ["cancel-delete-rule", "confirm-delete-rule"]:
        return False, current_rule_id if trigger_id == "confirm-delete-rule" else None
    
    # Open modal on delete button click
    if "delete-rule-button" in trigger_id:
        button_id = json.loads(trigger_id)
        rule_id_to_delete = button_id["index"]
        return True, rule_id_to_delete
    
    return dash.no_update, dash.no_update

# Perform rule deletion
@app.callback(
    Output("rules-store", "data", allow_duplicate=True),
    Input("delete-rule-id-store", "data"),
    prevent_initial_call=True
)
def delete_rule(rule_id):
    if rule_id is None:
        return dash.no_update
    
    try:
        response = requests.delete(f"{RULES_URL}/{rule_id}")
        if response.status_code == 200:
            return fetch_rules()
        else:
            print(f"Error deleting rule: {response.status_code} - {response.text}")
            return dash.no_update
    except Exception as e:
        print(f"Error deleting rule: {str(e)}")
        return dash.no_update

# Toggle rule active status
@app.callback(
    Output("rules-store", "data", allow_duplicate=True),
    Input({"type": "toggle-rule-status-button", "index": dash.ALL}, "n_clicks"),
    State("rules-store", "data"),
    prevent_initial_call=True
)
def toggle_rule_status(toggle_clicks, rules):
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update
    
    # Get button that was clicked
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    button_id = json.loads(trigger_id)
    rule_id = button_id["index"]
    
    # Find the rule in our current list
    rule_to_toggle = None
    for rule in rules:
        if rule.get("id") == rule_id:
            rule_to_toggle = rule
            break
    
    if not rule_to_toggle:
        return dash.no_update
    
    # Determine new status (opposite of current)
    current_status = rule_to_toggle.get("is_active", False)
    new_status = not current_status
    
    # Make API call to toggle status
    try:
        if new_status:
            response = requests.patch(f"{RULES_URL}/{rule_id}/activate")
        else:
            response = requests.patch(f"{RULES_URL}/{rule_id}/deactivate")
        
        if response.status_code == 200:
            return fetch_rules()
        else:
            print(f"Error toggling rule status: {response.status_code} - {response.text}")
            return dash.no_update
    except Exception as e:
        print(f"Error toggling rule status: {str(e)}")
        return dash.no_update

# Add callback for submitting a new transaction
@app.callback(
    [
        Output("transaction-submission-result", "children"),
        Output("json-display-container", "children"),
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
        return "", "", dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
    
    if not all([amount, payer_id, payee_id, payment_mode, channel]):
        return html.Div("Please fill all required fields", className="text-danger"), "", dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
    
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
    
    # Print transaction data for debugging
    print(f"Submitting transaction: {json.dumps(transaction)}")
    
    # Send transaction to API
    try:
        # First try the detailed JSON endpoint which has better support for custom rules
        response = requests.post(f"{API_BASE_URL}/detect-json", json={"transaction_data": transaction})
        print(f"API response status: {response.status_code}")
        print(f"API response content: {response.text}")
        
        detailed_response = False
        if response.status_code == 200:
            result = response.json()
            detailed_response = True
        else:
            # Fall back to the regular endpoint
            response = requests.post(f"{API_BASE_URL}/detect", json=transaction)
            print(f"API response status: {response.status_code}")
            print(f"API response content: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
            else:
                error_card = dbc.Card(
                    [
                        dbc.CardHeader("Error Processing Transaction", className="text-danger"),
                        dbc.CardBody(
                            html.P([
                                html.Strong("Error: "), 
                                f"Status code {response.status_code} - {response.text}"
                            ])
                        )
                    ],
                    className="mb-4 border-danger",
                    outline=True,
                )
                return (
                    error_card,  # result card
                    "",  # json display
                    dash.no_update,  # transactions
                    dash.no_update,  # amount
                    dash.no_update,  # payer_id
                    dash.no_update,  # payee_id
                    dash.no_update,  # payment_mode
                    dash.no_update,  # channel
                    dash.no_update,  # bank
                )
        
        # Create a new transaction object for the dashboard
        new_transaction = {
            "transaction_id": transaction_id,
            "amount": float(amount),
            "payer_id": payer_id,
            "payee_id": payee_id,
            "payment_mode": payment_mode,
            "channel": channel,
            "bank": bank if bank else None,
            "timestamp": datetime.now().isoformat(),
            "is_fraud_predicted": result.get('is_fraud_predicted', result.get('is_fraud', False)),
            "fraud_score": result.get('fraud_score', 0),
            "prediction_time_ms": result.get('prediction_time_ms', 0),
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
        
        # Create a detailed transaction result display
        result_card = dbc.Card(
            [
                dbc.CardHeader(f"Transaction Result: {transaction_id}", className="text-center"),
                dbc.CardBody(
                    [
                        html.Div([
                            html.H5("Transaction Details:", className="mb-3"),
                            html.P([html.Strong("Transaction ID: "), transaction_id]),
                            html.P([html.Strong("Amount: "), f"${float(amount):.2f}"]),
                            html.P([html.Strong("Payer ID: "), payer_id]),
                            html.P([html.Strong("Payee ID: "), payee_id]),
                            html.P([html.Strong("Payment Mode: "), payment_mode]),
                            html.P([html.Strong("Channel: "), channel]),
                            html.P([html.Strong("Bank: "), bank if bank else "None"]),
                            html.Hr(),
                            html.H5("API Response:"),
                            html.P([
                                html.Strong("Fraud Detected: "), 
                                html.Span(
                                    "YES" if result.get('is_fraud_predicted', result.get('is_fraud', False)) else "NO", 
                                    className="text-danger" if result.get('is_fraud_predicted', result.get('is_fraud', False)) else "text-success", 
                                    style={"font-weight": "bold"}
                                )
                            ]),
                            html.P([html.Strong("Fraud Score: "), f"{result.get('fraud_score', 0):.2f}"]),
                            
                            # Add fraud source and reason if available from detailed response
                            html.Div([
                                html.P([html.Strong("Fraud Source: "), result.get("fraud_source", "Unknown").capitalize()]),
                                html.P([html.Strong("Fraud Reason: "), result.get("fraud_reason", "Not specified")]),
                                html.Hr(),
                                html.H6("Custom Rule Details:"),
                                html.P("This transaction was flagged by one or more custom rules that you've configured."),
                            ]) if detailed_response and result.get("fraud_source") == "rule" else html.Div(),
                            
                            html.P([html.Strong("Processing Time: "), f"{result.get('prediction_time_ms', 0)} ms"]),
                            html.P(f"Transaction submitted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"),
                        ]),
                    ]
                ),
            ],
            className="mb-4 border-primary",
            outline=True,
        )
        
        # Create JSON display
        json_display = dbc.Card(
            [
                dbc.CardHeader(
                    dbc.Button(
                        "View JSON Input/Output",
                        id="toggle-json-collapse",
                        color="link",
                        className="text-decoration-none",
                    )
                ),
                dbc.Collapse(
                    dbc.CardBody(
                        [
                            html.H5("JSON Input:", className="mb-2"),
                            dbc.Card(
                                dbc.CardBody(
                                    dcc.Markdown(f"```json\n{json.dumps(transaction, indent=2)}\n```"),
                                    className="bg-light"
                                ),
                                className="mb-3"
                            ),
                            html.H5("JSON Output:", className="mb-2"),
                            dbc.Card(
                                dbc.CardBody(
                                    dcc.Markdown(f"```json\n{json.dumps(result, indent=2)}\n```"),
                                    className="bg-light"
                                )
                            )
                        ]
                    ),
                    id="json-collapse",
                    is_open=True,
                ),
            ],
            className="mb-4",
        )
        
        # Return success message and updated transactions
        return (
            result_card,  # result card
            json_display,  # json display
            updated_transactions,  # transactions
            None,  # Reset form fields
            None,
            None,
            None,
            None,
            None
        )
    except Exception as e:
        print(f"Exception: {str(e)}")
        error_card = dbc.Card(
            [
                dbc.CardHeader("Error Processing Transaction", className="text-danger"),
                dbc.CardBody(
                    html.P([
                        html.Strong("Exception: "), 
                        str(e)
                    ])
                )
            ],
            className="mb-4 border-danger",
            outline=True,
        )
        return (
            error_card,  # result card 
            "",  # json display
            dash.no_update,  # transactions
            dash.no_update,  # amount
            dash.no_update,  # payer_id
            dash.no_update,  # payee_id
            dash.no_update,  # payment_mode
            dash.no_update,  # channel
            dash.no_update,  # bank
        )

# Toggle JSON collapse
@app.callback(
    Output("json-collapse", "is_open"),
    [Input("toggle-json-collapse", "n_clicks")],
    [State("json-collapse", "is_open")],
    prevent_initial_call=True,
)
def toggle_json_collapse(n_clicks, is_open):
    if n_clicks:
        return not is_open
    return is_open

# Add callback for submitting a JSON transaction
@app.callback(
    [
        Output("json-transaction-result", "children"),
        Output("transactions-store", "data", allow_duplicate=True),
    ],
    Input("submit-json-transaction", "n_clicks"),
    [
        State("json-transaction-input", "value"),
        State("transactions-store", "data"),
    ],
    prevent_initial_call=True,
)
def submit_json_transaction(n_clicks, json_input, current_transactions):
    if n_clicks is None or not json_input:
        return "", dash.no_update
    
    try:
        # Parse the JSON input
        transaction_data = json.loads(json_input)
        
        # Ensure transaction_id exists
        if "transaction_id" not in transaction_data:
            transaction_data["transaction_id"] = str(uuid.uuid4())
        
        # Print transaction data for debugging
        print(f"Submitting JSON transaction: {json.dumps(transaction_data)}")
        
        # Send transaction to API
        response = requests.post(
            f"{API_BASE_URL}/detect-json", 
            json={"transaction_data": transaction_data}
        )
        
        print(f"JSON API response status: {response.status_code}")
        print(f"JSON API response content: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            
            # Create a new transaction object for the dashboard
            new_transaction = {
                "transaction_id": result["transaction_id"],
                "amount": float(transaction_data.get("amount", 0)),
                "payer_id": transaction_data.get("payer_id", ""),
                "payee_id": transaction_data.get("payee_id", ""),
                "payment_mode": transaction_data.get("payment_mode", ""),
                "channel": transaction_data.get("channel", ""),
                "bank": transaction_data.get("bank", None),
                "timestamp": datetime.now().isoformat(),
                "is_fraud_predicted": result["is_fraud"],
                "fraud_score": result["fraud_score"],
                "prediction_time_ms": 0,  # Not provided in the response
                "additional_data": json.dumps(transaction_data.get("additional_data", {}))
            }
            
            # Update the transactions store
            if current_transactions:
                updated_transactions = current_transactions.copy()
                updated_transactions.insert(0, new_transaction)  # Add to the beginning
            else:
                updated_transactions = [new_transaction]
            
            # Format the response
            result_card = dbc.Card(
                [
                    dbc.CardHeader("Fraud Detection Results:", className="bg-primary text-white"),
                    dbc.CardBody([
                        html.P([html.Strong("Transaction ID: "), html.Span(result["transaction_id"])]),
                        html.P([
                            html.Strong("Fraud Detected: "), 
                            html.Span(
                                "Yes" if result["is_fraud"] else "No",
                                style={"color": "red" if result["is_fraud"] else "green", "fontWeight": "bold"}
                            )
                        ]),
                        html.P([html.Strong("Fraud Source: "), html.Span(result["fraud_source"].capitalize())]),
                        html.P([html.Strong("Fraud Reason: "), html.Span(result["fraud_reason"])]),
                        html.P([html.Strong("Fraud Score: "), html.Span(f"{result['fraud_score']:.2f}")]),
                        # Add rule information if relevant
                        html.Div([
                            html.Hr(),
                            html.H6("Custom Rule Details:"),
                            html.P("This transaction was flagged by one or more custom rules that you've configured."),
                        ]) if result["fraud_source"] == "rule" else html.Div(),
                    ]),
                ],
                className="mb-3 shadow-sm"
            )
            return result_card, updated_transactions
        else:
            error_card = dbc.Card(
                [
                    dbc.CardHeader("Error Processing Transaction", className="bg-danger text-white"),
                    dbc.CardBody(f"Error: {response.status_code} - {response.text}")
                ],
                className="mb-3 shadow-sm"
            )
            return error_card, dash.no_update
    except json.JSONDecodeError:
        error_card = dbc.Card(
            [
                dbc.CardHeader("JSON Error", className="bg-danger text-white"),
                dbc.CardBody("Invalid JSON format. Please check your input.")
            ],
            className="mb-3 shadow-sm"
        )
        return error_card, dash.no_update
    except Exception as e:
        error_card = dbc.Card(
            [
                dbc.CardHeader("Error Processing Transaction", className="bg-danger text-white"),
                dbc.CardBody(f"Error: {str(e)}")
            ],
            className="mb-3 shadow-sm"
        )
        return error_card, dash.no_update

# Run the app
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8050))
    app.run_server(debug=True, port=port)
