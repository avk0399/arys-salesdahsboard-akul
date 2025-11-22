from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
import pandas as pd
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

DB_PATH = 'sales_data.db'

def get_db_connection():
    """Create database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def query_to_dict(query, params=()):
    """Execute query and return results as list of dicts"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    columns = [description[0] for description in cursor.description]
    results = [dict(zip(columns, row)) for row in cursor.fetchall()]
    conn.close()
    return results

# API 1: Sales Over Time
@app.route('/api/sales-over-time', methods=['GET'])
def sales_over_time():
    """Get sales aggregated by time period"""
    period = request.args.get('period', 'month')  # day, month, quarter, year
    
    if period == 'day':
        query = """
            SELECT ORDERDATE as date, SUM(SALES) as total_sales, COUNT(*) as order_count
            FROM sales
            GROUP BY ORDERDATE
            ORDER BY ORDERDATE
        """
    elif period == 'month':
        query = """
            SELECT YEAR_ID || '-' || printf('%02d', MONTH_ID) as date, 
                   SUM(SALES) as total_sales, COUNT(*) as order_count
            FROM sales
            GROUP BY YEAR_ID, MONTH_ID
            ORDER BY YEAR_ID, MONTH_ID
        """
    elif period == 'quarter':
        query = """
            SELECT YEAR_ID || '-Q' || QTR_ID as date, 
                   SUM(SALES) as total_sales, COUNT(*) as order_count
            FROM sales
            GROUP BY YEAR_ID, QTR_ID
            ORDER BY YEAR_ID, QTR_ID
        """
    else:  # year
        query = """
            SELECT YEAR_ID as date, SUM(SALES) as total_sales, COUNT(*) as order_count
            FROM sales
            GROUP BY YEAR_ID
            ORDER BY YEAR_ID
        """
    
    results = query_to_dict(query)
    return jsonify(results)

# API 2: Sales by Category (Status)
@app.route('/api/sales-by-category', methods=['GET'])
def sales_by_category():
    """Get sales by status/category"""
    query = """
        SELECT STATUS as category, 
               SUM(SALES) as total_sales,
               COUNT(*) as order_count,
               AVG(SALES) as avg_sales
        FROM sales
        GROUP BY STATUS
        ORDER BY total_sales DESC
    """
    results = query_to_dict(query)
    return jsonify(results)

# API 3: Sales by Country (if available)
@app.route('/api/sales-by-country', methods=['GET'])
def sales_by_country():
    """Get sales by country - check if COUNTRY column exists"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if COUNTRY column exists
    cursor.execute("PRAGMA table_info(sales)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if 'COUNTRY' in columns:
        query = """
            SELECT COUNTRY, 
                   SUM(SALES) as total_sales,
                   COUNT(*) as order_count
            FROM sales
            GROUP BY COUNTRY
            ORDER BY total_sales DESC
            LIMIT 10
        """
        results = query_to_dict(query)
    else:
        # Return mock data or empty if no country column
        results = [{"message": "Country data not available in dataset"}]
    
    conn.close()
    return jsonify(results)

# API 4: KPIs (Key Performance Indicators)
@app.route('/api/kpis', methods=['GET'])
def get_kpis():
    """Get key performance indicators"""
    query = """
        SELECT 
            SUM(SALES) as total_revenue,
            COUNT(DISTINCT ORDERNUMBER) as total_orders,
            AVG(SALES) as avg_order_value,
            SUM(QUANTITYORDERED) as total_quantity
        FROM sales
    """
    results = query_to_dict(query)
    
    # Get status breakdown
    status_query = """
        SELECT STATUS, COUNT(*) as count
        FROM sales
        GROUP BY STATUS
    """
    status_results = query_to_dict(status_query)
    
    kpis = results[0] if results else {}
    kpis['status_breakdown'] = status_results
    
    return jsonify(kpis)

# API 5: Top Customers
@app.route('/api/top-customers', methods=['GET'])
def top_customers():
    """Get top customers by sales"""
    limit = request.args.get('limit', 10, type=int)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if CUSTOMERNAME column exists
    cursor.execute("PRAGMA table_info(sales)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if 'CUSTOMERNAME' in columns:
        query = f"""
            SELECT CUSTOMERNAME as customer_name,
                   SUM(SALES) as total_sales,
                   COUNT(DISTINCT ORDERNUMBER) as order_count,
                   AVG(SALES) as avg_order_value
            FROM sales
            GROUP BY CUSTOMERNAME
            ORDER BY total_sales DESC
            LIMIT {limit}
        """
        results = query_to_dict(query)
    else:
        # Group by order number if customer name not available
        query = f"""
            SELECT ORDERNUMBER as order_id,
                   SUM(SALES) as total_sales,
                   COUNT(*) as line_items
            FROM sales
            GROUP BY ORDERNUMBER
            ORDER BY total_sales DESC
            LIMIT {limit}
        """
        results = query_to_dict(query)
    
    conn.close()
    return jsonify(results)

# API 6: Sales Trends
@app.route('/api/sales-trends', methods=['GET'])
def sales_trends():
    """Get sales trends with growth calculations"""
    query = """
        SELECT YEAR_ID, MONTH_ID,
               SUM(SALES) as monthly_sales
        FROM sales
        GROUP BY YEAR_ID, MONTH_ID
        ORDER BY YEAR_ID, MONTH_ID
    """
    results = query_to_dict(query)
    
    # Calculate month-over-month growth
    for i in range(1, len(results)):
        prev_sales = results[i-1]['monthly_sales']
        curr_sales = results[i]['monthly_sales']
        if prev_sales > 0:
            growth = ((curr_sales - prev_sales) / prev_sales) * 100
            results[i]['growth_rate'] = round(growth, 2)
        else:
            results[i]['growth_rate'] = 0
    
    if results:
        results[0]['growth_rate'] = 0
    
    return jsonify(results)

# API 7: Product Performance
@app.route('/api/product-performance', methods=['GET'])
def product_performance():
    """Get product line performance if available"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("PRAGMA table_info(sales)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if 'PRODUCTLINE' in columns:
        query = """
            SELECT PRODUCTLINE as product,
                   SUM(SALES) as total_sales,
                   SUM(QUANTITYORDERED) as total_quantity,
                   COUNT(DISTINCT ORDERNUMBER) as order_count
            FROM sales
            GROUP BY PRODUCTLINE
            ORDER BY total_sales DESC
        """
        results = query_to_dict(query)
    else:
        results = [{"message": "Product line data not available"}]
    
    conn.close()
    return jsonify(results)

# Health check endpoint
@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "message": "API is running"})

# Get database schema
@app.route('/api/schema', methods=['GET'])
def get_schema():
    """Get database schema information"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(sales)")
    columns = cursor.fetchall()
    conn.close()
    
    schema = [{"name": col[1], "type": col[2]} for col in columns]
    return jsonify(schema)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)