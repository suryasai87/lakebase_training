# Databricks Lakebase Training Application

A comprehensive training application demonstrating how to build and deploy applications using **Databricks Lakebase** (PostgreSQL) as a backend. This repository serves as an end-to-end guide for learning Lakebase features and deploying applications on the Databricks platform.

**Live Demo:** [https://lakebase-training-app-1602460480284688.aws.databricksapps.com](https://lakebase-training-app-1602460480284688.aws.databricksapps.com)

---

## Table of Contents

1. [Overview](#overview)
2. [Key Lakebase Features Demonstrated](#key-lakebase-features-demonstrated)
3. [Architecture](#architecture)
4. [Prerequisites](#prerequisites)
5. [End-to-End Training Guide](#end-to-end-training-guide)
   - [Module 1: Setting Up Lakebase](#module-1-setting-up-lakebase)
   - [Module 2: Database Schema Design](#module-2-database-schema-design)
   - [Module 3: Building the Application](#module-3-building-the-application)
   - [Module 4: Deploying to Databricks Apps](#module-4-deploying-to-databricks-apps)
6. [Application Features](#application-features)
7. [File Structure](#file-structure)
8. [Local Development](#local-development)
9. [Troubleshooting](#troubleshooting)
10. [Additional Resources](#additional-resources)

---

## Overview

This training application showcases a modern e-commerce dashboard built with:

- **Backend:** Databricks Lakebase (PostgreSQL-compatible database)
- **Frontend:** Dash (Python web framework) with Bootstrap components
- **Visualization:** Plotly for interactive charts
- **Authentication:** Databricks OAuth token management
- **Deployment:** Databricks Apps with DAB (Databricks Asset Bundles)

---

## Key Lakebase Features Demonstrated

This application demonstrates the following Lakebase/PostgreSQL capabilities:

### 1. **PostgreSQL-Compatible Database Operations**
```python
# Standard psycopg3 connection with SSL
conn_string = (
    f"dbname={os.getenv('PGDATABASE')} "
    f"user={os.getenv('PGUSER')} "
    f"password={postgres_password} "
    f"host={os.getenv('PGHOST')} "
    f"sslmode=require"
)
```

### 2. **OAuth Token Authentication**
```python
from databricks import sdk

workspace_client = sdk.WorkspaceClient()
postgres_password = workspace_client.config.oauth_token().access_token
```
- Automatic token refresh every 15 minutes
- Secure authentication without hardcoded credentials

### 3. **Connection Pooling**
```python
from psycopg_pool import ConnectionPool

connection_pool = ConnectionPool(conn_string, min_size=2, max_size=10)
```
- Efficient database connection management
- Automatic connection recycling

### 4. **Advanced Data Types**
- **JSONB:** For storing user metadata and shipping addresses
- **TEXT[]:** Array types for product tags
- **SERIAL:** Auto-incrementing primary keys
- **DECIMAL:** Precise financial calculations
- **TIMESTAMP WITH TIME ZONE:** Timezone-aware datetime

### 5. **Schema Organization**
```sql
CREATE SCHEMA IF NOT EXISTS ecommerce;
```
- Logical grouping of related tables
- Clean namespace management

### 6. **Constraints and Data Integrity**
```sql
price DECIMAL(10, 2) NOT NULL CHECK (price >= 0),
stock_quantity INTEGER DEFAULT 0 CHECK (stock_quantity >= 0),
REFERENCES ecommerce.users(user_id) ON DELETE CASCADE
```
- CHECK constraints for data validation
- Foreign key relationships
- Cascading deletes

### 7. **Computed/Generated Columns**
```sql
subtotal DECIMAL(10, 2) GENERATED ALWAYS AS (quantity * unit_price) STORED
```
- Automatic calculation of derived values

### 8. **Indexing Strategies**
```sql
CREATE INDEX idx_users_email ON ecommerce.users(email);
CREATE INDEX idx_users_metadata ON ecommerce.users USING GIN(metadata);
```
- B-tree indexes for standard columns
- GIN indexes for JSONB queries

### 9. **Transaction Management**
```python
def execute_query(self, query, params=None):
    try:
        self.cursor.execute(query, params)
        self.connection.commit()
    except Exception as e:
        self.connection.rollback()
        raise e
```
- ACID-compliant transactions
- Proper rollback on errors

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Databricks Apps Platform                      │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────┐ │
│  │   Dash App      │    │   OAuth Token   │    │  Lakebase   │ │
│  │  (dash_app.py)  │───▶│   Management    │───▶│  PostgreSQL │ │
│  │                 │    │                 │    │             │ │
│  │  - Dashboard    │    │  - Auto-refresh │    │  - ecommerce│ │
│  │  - Data Entry   │    │  - SDK Client   │    │    schema   │ │
│  │  - Query Builder│    │                 │    │  - users    │ │
│  │  - Vector Search│    │                 │    │  - products │ │
│  │  - API Testing  │    │                 │    │  - orders   │ │
│  └─────────────────┘    └─────────────────┘    └─────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

Before starting the training, ensure you have:

1. **Databricks Workspace Access** with Lakebase enabled
2. **Databricks CLI** installed and configured
3. **Python 3.9+** installed locally
4. **Git** for version control

### Install Databricks CLI
```bash
# macOS
brew install databricks/tap/databricks

# Or using pip
pip install databricks-cli
```

### Configure Databricks CLI
```bash
databricks configure
# Enter your workspace URL and personal access token
```

---

## End-to-End Training Guide

### Module 1: Setting Up Lakebase

#### Step 1.1: Create a Lakebase Database Instance

1. Navigate to your Databricks workspace
2. Go to **SQL > Endpoints** or **Compute > Create**
3. Create a new Lakebase (PostgreSQL) instance
4. Note the connection details:
   - Host: `instance-XXXXX.database.cloud.databricks.com`
   - Port: `5432`
   - Database: `databricks_postgres`

#### Step 1.2: Test Connection

```bash
# Clone this repository
git clone https://github.com/suryasai87/lakebase_training.git
cd lakebase_training

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export PGHOST="your-lakebase-host"
export PGDATABASE="databricks_postgres"
export PGPORT="5432"
export PGSSLMODE="require"
```

#### Step 1.3: Authenticate with Lakebase

Lakebase uses OAuth tokens for authentication:

```python
from databricks import sdk

# Initialize workspace client
workspace_client = sdk.WorkspaceClient()

# Get OAuth token (valid for 1 hour)
token = workspace_client.config.oauth_token().access_token

# Use token as password
PGUSER = "token"
PGPASSWORD = token
```

---

### Module 2: Database Schema Design

#### Step 2.1: Create the E-commerce Schema

Run the setup script or execute SQL manually:

```bash
# Option 1: Run setup script
python setup_and_deploy.py

# Option 2: Connect via psql and run SQL
psql "postgresql://token:$TOKEN@$PGHOST:5432/databricks_postgres?sslmode=require" -f setup_database.sql
```

#### Step 2.2: Understand the Schema

The application uses four main tables:

**Users Table:**
```sql
CREATE TABLE ecommerce.users (
    user_id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    full_name VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB,              -- Flexible user attributes
    preferences JSONB DEFAULT '{}'::jsonb
);
```

**Products Table:**
```sql
CREATE TABLE ecommerce.products (
    product_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL CHECK (price >= 0),
    stock_quantity INTEGER DEFAULT 0,
    category VARCHAR(100),
    tags TEXT[],                 -- Array of tags
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

**Orders Table:**
```sql
CREATE TABLE ecommerce.orders (
    order_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES ecommerce.users(user_id),
    status VARCHAR(50) DEFAULT 'pending',
    total_amount DECIMAL(10, 2),
    shipping_address JSONB,      -- Structured address data
    payment_method VARCHAR(50)
);
```

**Order Items Table:**
```sql
CREATE TABLE ecommerce.order_items (
    order_item_id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES ecommerce.orders(order_id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES ecommerce.products(product_id),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price DECIMAL(10, 2) NOT NULL,
    subtotal DECIMAL(10, 2) GENERATED ALWAYS AS (quantity * unit_price) STORED
);
```

#### Step 2.3: Sample Queries

Practice with these queries to understand Lakebase capabilities:

```sql
-- Query with JSONB filtering
SELECT * FROM ecommerce.users
WHERE metadata->>'role' = 'customer';

-- Query with array operations
SELECT * FROM ecommerce.products
WHERE 'ai' = ANY(tags);

-- Aggregation with JOINs
SELECT
    u.username,
    COUNT(o.order_id) as total_orders,
    SUM(o.total_amount) as lifetime_value
FROM ecommerce.users u
LEFT JOIN ecommerce.orders o ON u.user_id = o.user_id
GROUP BY u.user_id, u.username
ORDER BY lifetime_value DESC;
```

---

### Module 3: Building the Application

#### Step 3.1: Application Structure

```
lakebase_training/
├── dash_app.py          # Main Dash application
├── app.py               # Streamlit version (alternative)
├── setup_database.sql   # Database schema and sample data
├── requirements.txt     # Python dependencies
├── app.yaml             # Databricks App configuration
├── databricks.yml       # DAB bundle configuration
└── README.md            # This file
```

#### Step 3.2: Key Code Components

**Database Connection Manager (`dash_app.py:80-122`):**
```python
class LakebaseConnection:
    """Manage Lakebase database connections with OAuth token refresh"""

    def __init__(self):
        self.connection = None
        self.cursor = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def connect(self):
        """Establish connection to Lakebase"""
        self.connection = get_connection()
        self.cursor = self.connection.cursor(row_factory=dict_row)
        return True

    def execute_query(self, query, params=None):
        """Execute a query and return results"""
        self.cursor.execute(query, params)
        if query.strip().upper().startswith('SELECT'):
            return self.cursor.fetchall()
        else:
            self.connection.commit()
            return self.cursor.rowcount
```

**OAuth Token Management (`dash_app.py:26-42`):**
```python
def refresh_oauth_token():
    """Refresh OAuth token if expired."""
    global postgres_password, last_password_refresh
    if postgres_password is None or time.time() - last_password_refresh > 900:
        postgres_password = workspace_client.config.oauth_token().access_token
        last_password_refresh = time.time()
```

#### Step 3.3: Run Locally

```bash
# Set required environment variables
export PGHOST="your-lakebase-host"
export PGDATABASE="databricks_postgres"
export PGUSER="token"
export PGPORT="5432"
export PGSSLMODE="require"

# Run the Dash app
python dash_app.py

# Access at http://localhost:8080
```

---

### Module 4: Deploying to Databricks Apps

#### Step 4.1: Configure DAB Bundle

**databricks.yml:**
```yaml
bundle:
  name: lakebase-training-app

resources:
  apps:
    lakebase_training_dashboard:
      name: lakebase-training-app
      description: "Interactive Lakebase Training Dashboard"
      source_code_path: .
```

**app.yaml:**
```yaml
command:
  - python
  - dash_app.py
```

#### Step 4.2: Deploy Using DAB

```bash
# Validate the bundle
databricks bundle validate

# Deploy to workspace
databricks bundle deploy

# Run the app
databricks bundle run lakebase_training_dashboard

# Check app status
databricks apps list
```

#### Step 4.3: Alternative Deployment Methods

**Method 1: Direct CLI deployment**
```bash
databricks apps create lakebase-training-app \
  --source-code-path /Workspace/Users/your.email/lakebase-training-app
```

**Method 2: Using the deployment script**
```bash
python deploy.py
```

**Method 3: Manual deployment via UI**
1. Navigate to Databricks workspace
2. Go to **Apps** section
3. Click **Create App**
4. Point to the source code location

---

## Application Features

### 1. Dashboard
- Real-time metrics (users, products, orders, revenue)
- Interactive bar charts for product inventory
- Revenue trend line charts
- Recent orders table with auto-refresh

### 2. Data Entry
- Add new products with categories and tags
- Add new users with role metadata
- Form validation and error handling

### 3. Query Builder
- Pre-built sample queries
- Custom SQL query execution
- CSV export functionality

### 4. Vector Search (Demo)
- Semantic search interface
- Hybrid search options
- Demonstrates pg_vector capabilities

### 5. API Testing
- PostgREST endpoint testing
- HTTP method selection (GET, POST, PATCH, DELETE)
- Request/response visualization

---

## File Structure

| File | Description |
|------|-------------|
| `dash_app.py` | Main Dash application with full UI |
| `app.py` | Streamlit version (alternative) |
| `setup_database.sql` | Complete database schema with sample data |
| `requirements.txt` | Python package dependencies |
| `app.yaml` | Databricks App entry point configuration |
| `databricks.yml` | DAB bundle definition |
| `deploy.py` | Deployment automation script |
| `setup_and_deploy.py` | Database setup and verification |

---

## Local Development

### Setup Virtual Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file:
```env
PGHOST=your-lakebase-instance.database.cloud.databricks.com
PGDATABASE=databricks_postgres
PGUSER=token
PGPORT=5432
PGSSLMODE=require
PGAPPNAME=lakebase-training-app
```

### Running Tests

```bash
# Test database connection
python -c "from dash_app import test_connection; test_connection()"

# Run the application
python dash_app.py
```

---

## Troubleshooting

### Common Issues

**1. Connection Refused**
```
Error: could not connect to server: Connection refused
```
**Solution:** Verify your `PGHOST` is correct and the Lakebase instance is running.

**2. Authentication Failed**
```
Error: password authentication failed
```
**Solution:** Ensure you're using a fresh OAuth token. Tokens expire after 1 hour.

**3. SSL Certificate Error**
```
Error: SSL SYSCALL error
```
**Solution:** Set `PGSSLMODE=require` in your environment.

**4. Schema Not Found**
```
Error: relation "ecommerce.users" does not exist
```
**Solution:** Run `setup_database.sql` to create the schema and tables.

**5. 502 Bad Gateway on Databricks Apps**
```
Error: 502 Bad Gateway
```
**Solution:**
- Check the app.yaml command is correct
- Verify the port matches `DATABRICKS_APP_PORT`
- Check app logs: `databricks apps logs lakebase-training-app`

### Debugging Commands

```bash
# Check app status
databricks apps get lakebase-training-app

# View app logs
databricks apps logs lakebase-training-app

# List all apps
databricks apps list

# Delete and recreate app
databricks apps delete lakebase-training-app
databricks bundle deploy
```

---

## Additional Resources

### Documentation
- [Databricks Lakebase Documentation](https://docs.databricks.com/en/lakebase/index.html)
- [Databricks Apps Documentation](https://docs.databricks.com/en/apps/index.html)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [psycopg3 Documentation](https://www.psycopg.org/psycopg3/docs/)
- [Dash Documentation](https://dash.plotly.com/)

### Related Repositories
- [pg_vector for Vector Search](https://github.com/pgvector/pgvector)
- [PostgREST for REST APIs](https://postgrest.org/)

### Training Videos
- [Databricks Lakebase Introduction](https://www.databricks.com/resources)
- [Building Apps on Databricks](https://www.databricks.com/learn)

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit changes (`git commit -am 'Add your feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Create a Pull Request

---

## License

This training material is provided for educational purposes. See [LICENSE](LICENSE) for details.

---

**Training Version:** 2.0
**Last Updated:** December 2024
**Target Audience:** Developers learning Databricks Lakebase
**Estimated Duration:** 4-8 hours (self-paced)

---

*Built with Databricks Lakebase and Dash*
