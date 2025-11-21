"""
Databricks Lakebase Training Dashboard - Dash Application with Framer Motion UI
A comprehensive training application showcasing Lakebase integration with modern UI
"""

import os
import dash
from dash import dcc, html, Input, Output, State, callback, dash_table
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
import plotly.express as px
import plotly.graph_objects as go
import psycopg2
from psycopg2.extras import RealDictCursor
import pandas as pd
from datetime import datetime
import json

# ========================================
# Database Configuration
# ========================================
LAKEBASE_CONFIG = {
    'host': os.environ.get('LAKEBASE_HOST', 'ep-training-lakebase.us-east-2.aws.neon.tech'),
    'database': os.environ.get('LAKEBASE_DB', 'trainingdb'),
    'user': os.environ.get('LAKEBASE_USER'),
    'password': os.environ.get('LAKEBASE_PASSWORD'),
    'port': int(os.environ.get('LAKEBASE_PORT', '5432')),
    'sslmode': 'require'
}

# ========================================
# Database Connection Manager
# ========================================
class LakebaseConnection:
    """Manage Lakebase database connections"""

    def __init__(self, config=None):
        self.config = config or LAKEBASE_CONFIG
        self.connection = None
        self.cursor = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def connect(self):
        """Establish connection to Lakebase"""
        try:
            self.connection = psycopg2.connect(**self.config)
            self.cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            return False

    def execute_query(self, query, params=None):
        """Execute a query and return results"""
        try:
            self.cursor.execute(query, params)
            if query.strip().upper().startswith('SELECT'):
                return self.cursor.fetchall()
            else:
                self.connection.commit()
                return self.cursor.rowcount
        except Exception as e:
            self.connection.rollback()
            raise e

    def close(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()

# ========================================
# Initialize Dash App with Bootstrap and custom CSS
# ========================================
app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css'
    ],
    suppress_callback_exceptions=True,
    title="Lakebase Training Dashboard"
)

# Custom CSS for Framer Motion-like animations
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(20px); }
                to { opacity: 1; transform: translateY(0); }
            }

            @keyframes slideInRight {
                from { opacity: 0; transform: translateX(100px); }
                to { opacity: 1; transform: translateX(0); }
            }

            @keyframes scaleIn {
                from { opacity: 0; transform: scale(0.8); }
                to { opacity: 1; transform: scale(1); }
            }

            .animate-fade-in {
                animation: fadeIn 0.6s ease-out;
            }

            .animate-slide-in {
                animation: slideInRight 0.8s ease-out;
            }

            .animate-scale-in {
                animation: scaleIn 0.5s ease-out;
            }

            .metric-card {
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                border-radius: 12px;
                padding: 24px;
                background: white;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }

            .metric-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 12px 24px rgba(0, 0, 0, 0.15);
            }

            .nav-tab {
                transition: all 0.3s ease;
                border-radius: 8px;
                padding: 12px 24px;
                margin: 0 8px;
            }

            .nav-tab:hover {
                background: #f0f0f0;
                transform: scale(1.05);
            }

            .form-control, .form-select {
                transition: all 0.3s ease;
                border-radius: 8px;
            }

            .form-control:focus, .form-select:focus {
                transform: scale(1.02);
                box-shadow: 0 0 0 3px rgba(66, 153, 225, 0.5);
            }

            .btn {
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                border-radius: 8px;
            }

            .btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2);
            }

            .btn:active {
                transform: translateY(0);
            }

            body {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
            }

            .main-container {
                background: white;
                border-radius: 16px;
                margin: 20px;
                padding: 32px;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            }

            .header-container {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 32px;
                border-radius: 12px;
                margin-bottom: 32px;
                animation: fadeIn 0.8s ease-out;
            }

            .chart-container {
                background: white;
                border-radius: 12px;
                padding: 24px;
                margin: 16px 0;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
                transition: all 0.3s ease;
            }

            .chart-container:hover {
                box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# ========================================
# Layout Components
# ========================================

# Header Component
header = html.Div([
    html.Div([
        html.H1([
            html.I(className="fas fa-database me-3"),
            "Databricks Lakebase Training Dashboard"
        ], className="mb-2"),
        html.P(
            "A comprehensive training application showcasing Lakebase integration with modern UI",
            className="mb-0 opacity-75"
        )
    ], className="header-container")
], className="animate-fade-in")

# Navigation Tabs
tabs = html.Div([
    dbc.Tabs([
        dbc.Tab(label="📊 Dashboard", tab_id="dashboard", className="nav-tab"),
        dbc.Tab(label="📝 Data Entry", tab_id="data-entry", className="nav-tab"),
        dbc.Tab(label="🔍 Query Builder", tab_id="query-builder", className="nav-tab"),
        dbc.Tab(label="🔮 Vector Search", tab_id="vector-search", className="nav-tab"),
        dbc.Tab(label="🔌 API Testing", tab_id="api-testing", className="nav-tab"),
    ], id="tabs", active_tab="dashboard", className="mb-4")
], className="animate-slide-in")

# Dashboard Tab Content
dashboard_content = html.Div([
    # Metrics Cards
    html.Div([
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.I(className="fas fa-users fa-2x text-primary mb-3"),
                    html.H3(id="metric-users", children="Loading...", className="mb-1"),
                    html.P("Total Users", className="text-muted mb-0")
                ], className="metric-card text-center animate-scale-in")
            ], width=3),
            dbc.Col([
                html.Div([
                    html.I(className="fas fa-box fa-2x text-success mb-3"),
                    html.H3(id="metric-products", children="Loading...", className="mb-1"),
                    html.P("Total Products", className="text-muted mb-0")
                ], className="metric-card text-center animate-scale-in")
            ], width=3),
            dbc.Col([
                html.Div([
                    html.I(className="fas fa-shopping-cart fa-2x text-info mb-3"),
                    html.H3(id="metric-orders", children="Loading...", className="mb-1"),
                    html.P("Total Orders", className="text-muted mb-0")
                ], className="metric-card text-center animate-scale-in")
            ], width=3),
            dbc.Col([
                html.Div([
                    html.I(className="fas fa-dollar-sign fa-2x text-warning mb-3"),
                    html.H3(id="metric-revenue", children="Loading...", className="mb-1"),
                    html.P("Total Revenue", className="text-muted mb-0")
                ], className="metric-card text-center animate-scale-in")
            ], width=3),
        ], className="mb-4")
    ]),

    # Charts
    dbc.Row([
        dbc.Col([
            html.Div([
                html.H4("📦 Product Inventory", className="mb-3"),
                dcc.Graph(id="product-inventory-chart")
            ], className="chart-container animate-fade-in")
        ], width=6),
        dbc.Col([
            html.Div([
                html.H4("📈 Revenue Trend", className="mb-3"),
                dcc.Graph(id="revenue-trend-chart")
            ], className="chart-container animate-fade-in")
        ], width=6),
    ], className="mb-4"),

    # Recent Orders Table
    html.Div([
        html.H4("🛒 Recent Orders", className="mb-3"),
        html.Div(id="recent-orders-table")
    ], className="chart-container animate-fade-in"),

    # Auto-refresh interval
    dcc.Interval(id='interval-component', interval=30000, n_intervals=0)
])

# Data Entry Tab Content
data_entry_content = html.Div([
    dbc.Tabs([
        dbc.Tab(label="Add Product", tab_id="add-product"),
        dbc.Tab(label="Add User", tab_id="add-user"),
    ], id="data-entry-tabs", active_tab="add-product", className="mb-4"),

    html.Div(id="data-entry-form-container")
])

# Product Form
product_form = html.Div([
    dbc.Row([
        dbc.Col([
            dbc.Label("Product Name *"),
            dbc.Input(id="product-name", type="text", placeholder="Enter product name"),
        ], width=6),
        dbc.Col([
            dbc.Label("Category *"),
            dbc.Select(id="product-category", options=[
                {"label": "Electronics", "value": "Electronics"},
                {"label": "Accessories", "value": "Accessories"},
                {"label": "Books", "value": "Books"},
                {"label": "Clothing", "value": "Clothing"},
                {"label": "Other", "value": "Other"},
            ]),
        ], width=6),
    ], className="mb-3"),

    dbc.Row([
        dbc.Col([
            dbc.Label("Price *"),
            dbc.Input(id="product-price", type="number", placeholder="0.00", min=0, step=0.01),
        ], width=4),
        dbc.Col([
            dbc.Label("Stock Quantity"),
            dbc.Input(id="product-stock", type="number", placeholder="0", value=0, min=0),
        ], width=4),
        dbc.Col([
            dbc.Label("Tags (comma-separated)"),
            dbc.Input(id="product-tags", type="text", placeholder="tag1, tag2, tag3"),
        ], width=4),
    ], className="mb-3"),

    dbc.Row([
        dbc.Col([
            dbc.Label("Description"),
            dbc.Textarea(id="product-description", placeholder="Product description", rows=4),
        ]),
    ], className="mb-3"),

    dbc.Button("Add Product", id="submit-product", color="primary", className="mt-3"),
    html.Div(id="product-form-feedback", className="mt-3")
], className="animate-fade-in p-4")

# User Form
user_form = html.Div([
    dbc.Row([
        dbc.Col([
            dbc.Label("Email *"),
            dbc.Input(id="user-email", type="email", placeholder="user@example.com"),
        ], width=6),
        dbc.Col([
            dbc.Label("Username *"),
            dbc.Input(id="user-username", type="text", placeholder="username"),
        ], width=6),
    ], className="mb-3"),

    dbc.Row([
        dbc.Col([
            dbc.Label("Full Name"),
            dbc.Input(id="user-fullname", type="text", placeholder="Full Name"),
        ], width=6),
        dbc.Col([
            dbc.Label("Role"),
            dbc.Select(id="user-role", options=[
                {"label": "Customer", "value": "customer"},
                {"label": "Admin", "value": "admin"},
                {"label": "Vendor", "value": "vendor"},
            ], value="customer"),
        ], width=6),
    ], className="mb-3"),

    dbc.Button("Add User", id="submit-user", color="success", className="mt-3"),
    html.Div(id="user-form-feedback", className="mt-3")
], className="animate-fade-in p-4")

# Query Builder Tab Content
query_builder_content = html.Div([
    dbc.Row([
        dbc.Col([
            dbc.Label("Sample Queries"),
            dbc.Select(
                id="sample-queries",
                options=[
                    {"label": "Top selling products", "value": "top_products"},
                    {"label": "User purchase history", "value": "user_history"},
                    {"label": "Low stock alert", "value": "low_stock"},
                    {"label": "Revenue by category", "value": "revenue_category"},
                ],
                value="top_products"
            ),
        ], width=12),
    ], className="mb-3"),

    dbc.Row([
        dbc.Col([
            dbc.Label("Custom SQL Query"),
            dbc.Textarea(id="custom-query", placeholder="Enter SQL query...", rows=8),
        ]),
    ], className="mb-3"),

    dbc.Button("Execute Query", id="execute-query", color="primary", className="me-2"),
    dbc.Button("Download CSV", id="download-csv", color="secondary", disabled=True),

    html.Div(id="query-results", className="mt-4"),
    dcc.Download(id="download-dataframe-csv")
], className="animate-fade-in p-4")

# Vector Search Tab Content
vector_search_content = html.Div([
    dbc.Row([
        dbc.Col([
            dbc.Label("Search Query"),
            dbc.Input(id="vector-search-query", type="text", placeholder="e.g., laptop for AI development"),
        ], width=8),
        dbc.Col([
            dbc.Label("Number of Results"),
            dbc.Input(id="vector-top-k", type="number", value=5, min=1, max=20),
        ], width=4),
    ], className="mb-3"),

    dbc.Row([
        dbc.Col([
            dbc.Label("Search Type"),
            dbc.RadioItems(
                id="vector-search-type",
                options=[
                    {"label": "Semantic", "value": "semantic"},
                    {"label": "Hybrid", "value": "hybrid"},
                    {"label": "Traditional", "value": "traditional"},
                ],
                value="semantic",
                inline=True
            ),
        ]),
    ], className="mb-3"),

    dbc.Button("Search", id="execute-vector-search", color="primary", className="mb-4"),

    html.Div(id="vector-search-results")
], className="animate-fade-in p-4")

# API Testing Tab Content
api_testing_content = html.Div([
    dbc.Row([
        dbc.Col([
            dbc.Label("API Base URL"),
            dbc.Input(id="api-base-url", value="http://localhost:3000", type="url"),
        ], width=12),
    ], className="mb-3"),

    dbc.Row([
        dbc.Col([
            dbc.Label("HTTP Method"),
            dbc.Select(
                id="api-method",
                options=[
                    {"label": "GET", "value": "GET"},
                    {"label": "POST", "value": "POST"},
                    {"label": "PATCH", "value": "PATCH"},
                    {"label": "DELETE", "value": "DELETE"},
                ],
                value="GET"
            ),
        ], width=3),
        dbc.Col([
            dbc.Label("Endpoint"),
            dbc.Input(id="api-endpoint", value="/products", type="text"),
        ], width=9),
    ], className="mb-3"),

    dbc.Row([
        dbc.Col([
            dbc.Label("Query Parameters"),
            dbc.Input(id="api-params", placeholder="e.g., category=eq.Electronics", type="text"),
        ], width=6),
        dbc.Col([
            dbc.Label("Request Body (JSON)"),
            dbc.Textarea(id="api-body", placeholder='{"name": "Product", "price": 99.99}', rows=4),
        ], width=6),
    ], className="mb-3"),

    dbc.Button("Send Request", id="send-api-request", color="primary", className="mb-4"),

    html.Div([
        html.H5("Response", className="mb-3"),
        html.Pre(id="api-response", className="bg-light p-3 rounded")
    ])
], className="animate-fade-in p-4")

# Main Layout
app.layout = html.Div([
    header,
    html.Div([
        tabs,
        html.Div(id="tab-content")
    ], className="main-container")
])

# ========================================
# Callbacks
# ========================================

# Tab content switcher
@app.callback(
    Output("tab-content", "children"),
    Input("tabs", "active_tab")
)
def render_tab_content(active_tab):
    if active_tab == "dashboard":
        return dashboard_content
    elif active_tab == "data-entry":
        return data_entry_content
    elif active_tab == "query-builder":
        return query_builder_content
    elif active_tab == "vector-search":
        return vector_search_content
    elif active_tab == "api-testing":
        return api_testing_content
    return html.Div("Tab not found")

# Data entry form switcher
@app.callback(
    Output("data-entry-form-container", "children"),
    Input("data-entry-tabs", "active_tab")
)
def render_data_entry_form(active_tab):
    if active_tab == "add-product":
        return product_form
    elif active_tab == "add-user":
        return user_form
    return html.Div()

# Update dashboard metrics
@app.callback(
    [Output("metric-users", "children"),
     Output("metric-products", "children"),
     Output("metric-orders", "children"),
     Output("metric-revenue", "children")],
    Input("interval-component", "n_intervals")
)
def update_metrics(n):
    try:
        with LakebaseConnection() as db:
            users = db.execute_query("SELECT COUNT(*) as count FROM ecommerce.users")[0]['count']
            products = db.execute_query("SELECT COUNT(*) as count FROM ecommerce.products")[0]['count']
            orders = db.execute_query("SELECT COUNT(*) as count FROM ecommerce.orders")[0]['count']
            revenue = db.execute_query(
                "SELECT COALESCE(SUM(total_amount), 0) as revenue FROM ecommerce.orders WHERE status='completed'"
            )[0]['revenue']

            return f"{users:,}", f"{products:,}", f"{orders:,}", f"${float(revenue):,.2f}"
    except Exception as e:
        return "Error", "Error", "Error", "Error"

# Update product inventory chart
@app.callback(
    Output("product-inventory-chart", "figure"),
    Input("interval-component", "n_intervals")
)
def update_inventory_chart(n):
    try:
        with LakebaseConnection() as db:
            results = db.execute_query("""
                SELECT name, stock_quantity, category
                FROM ecommerce.products
                ORDER BY stock_quantity DESC
                LIMIT 10
            """)

            if results:
                df = pd.DataFrame(results)
                fig = px.bar(
                    df,
                    x='name',
                    y='stock_quantity',
                    color='category',
                    title="",
                    labels={'stock_quantity': 'Stock Quantity', 'name': 'Product'},
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                fig.update_layout(
                    plot_bgcolor='white',
                    paper_bgcolor='white',
                    font=dict(family="Arial, sans-serif"),
                    xaxis=dict(showgrid=False),
                    yaxis=dict(showgrid=True, gridcolor='#f0f0f0')
                )
                return fig
    except Exception as e:
        pass

    return go.Figure()

# Update revenue trend chart
@app.callback(
    Output("revenue-trend-chart", "figure"),
    Input("interval-component", "n_intervals")
)
def update_revenue_chart(n):
    try:
        with LakebaseConnection() as db:
            results = db.execute_query("""
                SELECT
                    DATE(order_date) as date,
                    SUM(total_amount) as daily_revenue
                FROM ecommerce.orders
                WHERE status = 'completed'
                GROUP BY DATE(order_date)
                ORDER BY date DESC
                LIMIT 30
            """)

            if results:
                df = pd.DataFrame(results)
                fig = px.line(
                    df,
                    x='date',
                    y='daily_revenue',
                    title="",
                    labels={'daily_revenue': 'Revenue ($)', 'date': 'Date'},
                    line_shape='spline'
                )
                fig.update_traces(line_color='#667eea', line_width=3)
                fig.update_layout(
                    plot_bgcolor='white',
                    paper_bgcolor='white',
                    font=dict(family="Arial, sans-serif"),
                    xaxis=dict(showgrid=False),
                    yaxis=dict(showgrid=True, gridcolor='#f0f0f0')
                )
                return fig
    except Exception as e:
        pass

    return go.Figure()

# Update recent orders table
@app.callback(
    Output("recent-orders-table", "children"),
    Input("interval-component", "n_intervals")
)
def update_orders_table(n):
    try:
        with LakebaseConnection() as db:
            results = db.execute_query("""
                SELECT
                    o.order_id,
                    u.username,
                    o.order_date,
                    o.status,
                    o.total_amount
                FROM ecommerce.orders o
                JOIN ecommerce.users u ON o.user_id = u.user_id
                ORDER BY o.order_date DESC
                LIMIT 10
            """)

            if results:
                df = pd.DataFrame(results)
                df['order_date'] = pd.to_datetime(df['order_date']).dt.strftime('%Y-%m-%d %H:%M')
                df['total_amount'] = df['total_amount'].apply(lambda x: f"${float(x):.2f}")

                return dash_table.DataTable(
                    data=df.to_dict('records'),
                    columns=[{"name": i.replace('_', ' ').title(), "id": i} for i in df.columns],
                    style_cell={'textAlign': 'left', 'padding': '12px'},
                    style_header={
                        'backgroundColor': '#667eea',
                        'color': 'white',
                        'fontWeight': 'bold'
                    },
                    style_data_conditional=[
                        {
                            'if': {'row_index': 'odd'},
                            'backgroundColor': '#f9f9f9'
                        }
                    ]
                )
    except Exception as e:
        pass

    return html.Div("No orders found", className="text-muted")

# Add product callback
@app.callback(
    Output("product-form-feedback", "children"),
    Input("submit-product", "n_clicks"),
    [State("product-name", "value"),
     State("product-description", "value"),
     State("product-price", "value"),
     State("product-stock", "value"),
     State("product-category", "value"),
     State("product-tags", "value")],
    prevent_initial_call=True
)
def add_product(n_clicks, name, description, price, stock, category, tags):
    if not name or not price:
        return dbc.Alert("Please fill in required fields (Name and Price)", color="danger")

    try:
        tags_array = [tag.strip() for tag in tags.split(',')] if tags else []

        with LakebaseConnection() as db:
            db.execute_query("""
                INSERT INTO ecommerce.products
                (name, description, price, stock_quantity, category, tags)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (name, description, price, stock, category, tags_array))

        return dbc.Alert("✅ Product added successfully!", color="success")
    except Exception as e:
        return dbc.Alert(f"Error: {str(e)}", color="danger")

# Add user callback
@app.callback(
    Output("user-form-feedback", "children"),
    Input("submit-user", "n_clicks"),
    [State("user-email", "value"),
     State("user-username", "value"),
     State("user-fullname", "value"),
     State("user-role", "value")],
    prevent_initial_call=True
)
def add_user(n_clicks, email, username, fullname, role):
    if not email or not username:
        return dbc.Alert("Please fill in required fields (Email and Username)", color="danger")

    try:
        metadata = json.dumps({"role": role})

        with LakebaseConnection() as db:
            db.execute_query("""
                INSERT INTO ecommerce.users
                (email, username, full_name, metadata)
                VALUES (%s, %s, %s, %s::jsonb)
            """, (email, username, fullname, metadata))

        return dbc.Alert("✅ User added successfully!", color="success")
    except Exception as e:
        return dbc.Alert(f"Error: {str(e)}", color="danger")

# ========================================
# Run the app
# ========================================
if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=8080)
