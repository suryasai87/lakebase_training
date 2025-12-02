"""
Databricks Lakebase Training Dashboard - Simple Working Version
Displays data from ecommerce schema tables: users, products, orders, order_items
"""

import os
import json
import dash
from dash import dcc, html, Input, Output, callback, dash_table
import dash_bootstrap_components as dbc
import psycopg
from psycopg.rows import dict_row
import pandas as pd
import time
from databricks import sdk

# ========================================
# OAuth Token Management
# ========================================
workspace_client = None
postgres_password = None
last_password_refresh = 0

def get_oauth_token():
    """Get OAuth token from Databricks SDK with auto-refresh."""
    global workspace_client, postgres_password, last_password_refresh

    if postgres_password is None or time.time() - last_password_refresh > 900:
        print("Refreshing OAuth token...")
        try:
            if workspace_client is None:
                workspace_client = sdk.WorkspaceClient()
            postgres_password = workspace_client.config.oauth_token().access_token
            last_password_refresh = time.time()
            print("OAuth token refreshed successfully")
        except Exception as e:
            print(f"Failed to get OAuth token: {e}")
            raise
    return postgres_password

# ========================================
# Database Configuration - CORRECTED
# ========================================
PGHOST = os.getenv('PGHOST', 'instance-6b59171b-cee8-4acc-9209-6c848ffbfbfe.database.cloud.databricks.com')
PGDATABASE = os.getenv('PGDATABASE', 'databricks_postgres')
PGUSER = os.getenv('PGUSER', '1e6260c5-f44b-4d66-bb19-ccd360f98b36')
PGPORT = os.getenv('PGPORT', '5432')

def get_db_connection():
    """Get a fresh database connection."""
    token = get_oauth_token()
    conn_string = (
        f"dbname={PGDATABASE} "
        f"user={PGUSER} "
        f"password={token} "
        f"host={PGHOST} "
        f"port={PGPORT} "
        f"sslmode=require"
    )
    return psycopg.connect(conn_string, row_factory=dict_row)

# ========================================
# Database Connection Manager
# ========================================
class LakebaseConnection:
    """Manage Lakebase database connections"""

    def __init__(self):
        self.connection = None
        self.cursor = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def connect(self):
        try:
            self.connection = get_db_connection()
            self.cursor = self.connection.cursor()
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            return False

    def execute_query(self, query, params=None):
        if not self.connection or not self.cursor:
            raise Exception("Database connection not established")
        try:
            self.cursor.execute(query, params)
            if query.strip().upper().startswith('SELECT'):
                return self.cursor.fetchall()
            else:
                self.connection.commit()
                return self.cursor.rowcount
        except Exception as e:
            if self.connection:
                try:
                    self.connection.rollback()
                except Exception:
                    pass
            raise e

    def close(self):
        try:
            if self.cursor:
                self.cursor.close()
        except Exception:
            pass
        try:
            if self.connection:
                self.connection.close()
        except Exception:
            pass
        self.cursor = None
        self.connection = None

def convert_for_datatable(df):
    """Convert JSONB columns to strings for DataTable display."""
    if df.empty:
        return df
    for col in df.columns:
        if df[col].apply(lambda x: isinstance(x, (dict, list))).any():
            df[col] = df[col].apply(lambda x: json.dumps(x) if isinstance(x, (dict, list)) else x)
    return df

# ========================================
# Initialize Dash App
# ========================================
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True,
    title="Lakebase Training Dashboard"
)

# ========================================
# App Layout - Simple Table Display
# ========================================
app.layout = dbc.Container([
    # Header
    dbc.Row([
        dbc.Col([
            html.H1("Lakebase Training Dashboard", className="text-primary mb-2"),
            html.P("Connected to Databricks Lakebase - ecommerce schema", className="text-muted"),
            html.Hr()
        ])
    ], className="mt-4 mb-4"),

    # Connection Status
    dbc.Row([
        dbc.Col([
            html.Div(id="connection-status")
        ])
    ], className="mb-3"),

    # Tables Section
    dbc.Row([
        dbc.Col([
            html.H4("Users Table"),
            html.Div(id="users-table", className="mb-4")
        ], width=12)
    ]),

    dbc.Row([
        dbc.Col([
            html.H4("Products Table"),
            html.Div(id="products-table", className="mb-4")
        ], width=12)
    ]),

    dbc.Row([
        dbc.Col([
            html.H4("Orders Table"),
            html.Div(id="orders-table", className="mb-4")
        ], width=12)
    ]),

    dbc.Row([
        dbc.Col([
            html.H4("Order Items Table"),
            html.Div(id="order-items-table", className="mb-4")
        ], width=12)
    ]),

    # Refresh interval
    dcc.Interval(id="interval-component", interval=30000, n_intervals=0),

], fluid=True, className="pb-5")

# ========================================
# Callbacks
# ========================================

@app.callback(
    Output("connection-status", "children"),
    Input("interval-component", "n_intervals")
)
def update_connection_status(n):
    try:
        with LakebaseConnection() as db:
            db.execute_query("SELECT 1")
        return dbc.Alert([
            html.Strong("Connected: "),
            f"{PGHOST} / {PGDATABASE}"
        ], color="success", className="mb-0")
    except Exception as e:
        return dbc.Alert([
            html.Strong("Connection Error: "),
            str(e)[:100]
        ], color="danger", className="mb-0")

@app.callback(
    Output("users-table", "children"),
    Input("interval-component", "n_intervals")
)
def update_users_table(n):
    try:
        with LakebaseConnection() as db:
            results = db.execute_query("SELECT * FROM ecommerce.users ORDER BY user_id LIMIT 20")
            if results:
                df = pd.DataFrame(results)
                df = convert_for_datatable(df)
                return dash_table.DataTable(
                    data=df.to_dict('records'),
                    columns=[{"name": i, "id": i} for i in df.columns],
                    style_cell={'textAlign': 'left', 'padding': '10px'},
                    style_header={'backgroundColor': '#0d6efd', 'color': 'white', 'fontWeight': 'bold'},
                    style_data_conditional=[{'if': {'row_index': 'odd'}, 'backgroundColor': '#f8f9fa'}],
                    page_size=10
                )
            return html.P("No users found", className="text-muted")
    except Exception as e:
        return dbc.Alert(f"Error: {str(e)}", color="danger")

@app.callback(
    Output("products-table", "children"),
    Input("interval-component", "n_intervals")
)
def update_products_table(n):
    try:
        with LakebaseConnection() as db:
            results = db.execute_query("SELECT * FROM ecommerce.products ORDER BY product_id LIMIT 20")
            if results:
                df = pd.DataFrame(results)
                df = convert_for_datatable(df)
                return dash_table.DataTable(
                    data=df.to_dict('records'),
                    columns=[{"name": i, "id": i} for i in df.columns],
                    style_cell={'textAlign': 'left', 'padding': '10px'},
                    style_header={'backgroundColor': '#198754', 'color': 'white', 'fontWeight': 'bold'},
                    style_data_conditional=[{'if': {'row_index': 'odd'}, 'backgroundColor': '#f8f9fa'}],
                    page_size=10
                )
            return html.P("No products found", className="text-muted")
    except Exception as e:
        return dbc.Alert(f"Error: {str(e)}", color="danger")

@app.callback(
    Output("orders-table", "children"),
    Input("interval-component", "n_intervals")
)
def update_orders_table(n):
    try:
        with LakebaseConnection() as db:
            results = db.execute_query("SELECT * FROM ecommerce.orders ORDER BY order_id LIMIT 20")
            if results:
                df = pd.DataFrame(results)
                df = convert_for_datatable(df)
                return dash_table.DataTable(
                    data=df.to_dict('records'),
                    columns=[{"name": i, "id": i} for i in df.columns],
                    style_cell={'textAlign': 'left', 'padding': '10px'},
                    style_header={'backgroundColor': '#0dcaf0', 'color': 'white', 'fontWeight': 'bold'},
                    style_data_conditional=[{'if': {'row_index': 'odd'}, 'backgroundColor': '#f8f9fa'}],
                    page_size=10
                )
            return html.P("No orders found", className="text-muted")
    except Exception as e:
        return dbc.Alert(f"Error: {str(e)}", color="danger")

@app.callback(
    Output("order-items-table", "children"),
    Input("interval-component", "n_intervals")
)
def update_order_items_table(n):
    try:
        with LakebaseConnection() as db:
            results = db.execute_query("SELECT * FROM ecommerce.order_items ORDER BY order_item_id LIMIT 20")
            if results:
                df = pd.DataFrame(results)
                df = convert_for_datatable(df)
                return dash_table.DataTable(
                    data=df.to_dict('records'),
                    columns=[{"name": i, "id": i} for i in df.columns],
                    style_cell={'textAlign': 'left', 'padding': '10px'},
                    style_header={'backgroundColor': '#ffc107', 'color': 'black', 'fontWeight': 'bold'},
                    style_data_conditional=[{'if': {'row_index': 'odd'}, 'backgroundColor': '#f8f9fa'}],
                    page_size=10
                )
            return html.P("No order items found", className="text-muted")
    except Exception as e:
        return dbc.Alert(f"Error: {str(e)}", color="danger")

# ========================================
# Run the app
# ========================================
if __name__ == '__main__':
    port = int(os.environ.get('DATABRICKS_APP_PORT', os.environ.get('PORT', '8080')))
    print(f"Starting Lakebase Training Dashboard on port {port}")
    print(f"Database: {PGHOST} / {PGDATABASE}")
    print(f"User: {PGUSER}")
    app.run_server(debug=False, host='0.0.0.0', port=port)
