-- Create sample tables for analytics

-- Sales table
CREATE TABLE IF NOT EXISTS sales (
    id SERIAL PRIMARY KEY,
    order_id VARCHAR(50) UNIQUE NOT NULL,
    customer_name VARCHAR(255),
    product_name VARCHAR(255),
    category VARCHAR(100),
    quantity INTEGER,
    unit_price DECIMAL(10, 2),
    total_amount DECIMAL(10, 2),
    order_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Customers table
CREATE TABLE IF NOT EXISTS customers (
    id SERIAL PRIMARY KEY,
    customer_id VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255),
    email VARCHAR(255),
    country VARCHAR(100),
    city VARCHAR(100),
    signup_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Products table
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    product_id VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255),
    category VARCHAR(100),
    price DECIMAL(10, 2),
    stock_quantity INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert sample sales data
INSERT INTO sales (order_id, customer_name, product_name, category, quantity, unit_price, total_amount, order_date)
VALUES
    ('ORD001', 'John Doe', 'Laptop', 'Electronics', 1, 1200.00, 1200.00, '2024-01-15'),
    ('ORD002', 'Jane Smith', 'Mouse', 'Electronics', 2, 25.00, 50.00, '2024-01-16'),
    ('ORD003', 'Bob Johnson', 'Keyboard', 'Electronics', 1, 75.00, 75.00, '2024-01-17'),
    ('ORD004', 'Alice Brown', 'Monitor', 'Electronics', 1, 350.00, 350.00, '2024-01-18'),
    ('ORD005', 'Charlie Davis', 'Webcam', 'Electronics', 1, 120.00, 120.00, '2024-01-19'),
    ('ORD006', 'Eva Wilson', 'Headphones', 'Electronics', 3, 60.00, 180.00, '2024-01-20'),
    ('ORD007', 'Frank Miller', 'USB Cable', 'Accessories', 5, 10.00, 50.00, '2024-01-21'),
    ('ORD008', 'Grace Lee', 'Laptop Stand', 'Accessories', 1, 45.00, 45.00, '2024-01-22'),
    ('ORD009', 'Henry Taylor', 'Desk Lamp', 'Furniture', 2, 35.00, 70.00, '2024-01-23'),
    ('ORD010', 'Ivy Anderson', 'Office Chair', 'Furniture', 1, 250.00, 250.00, '2024-01-24')
ON CONFLICT (order_id) DO NOTHING;

-- Insert sample customer data
INSERT INTO customers (customer_id, name, email, country, city, signup_date)
VALUES
    ('CUST001', 'John Doe', 'john@example.com', 'USA', 'New York', '2023-12-01'),
    ('CUST002', 'Jane Smith', 'jane@example.com', 'USA', 'Los Angeles', '2023-12-05'),
    ('CUST003', 'Bob Johnson', 'bob@example.com', 'UK', 'London', '2023-12-10'),
    ('CUST004', 'Alice Brown', 'alice@example.com', 'Canada', 'Toronto', '2023-12-15'),
    ('CUST005', 'Charlie Davis', 'charlie@example.com', 'USA', 'Chicago', '2023-12-20')
ON CONFLICT (customer_id) DO NOTHING;

-- Insert sample product data
INSERT INTO products (product_id, name, category, price, stock_quantity)
VALUES
    ('PROD001', 'Laptop', 'Electronics', 1200.00, 50),
    ('PROD002', 'Mouse', 'Electronics', 25.00, 200),
    ('PROD003', 'Keyboard', 'Electronics', 75.00, 150),
    ('PROD004', 'Monitor', 'Electronics', 350.00, 75),
    ('PROD005', 'Webcam', 'Electronics', 120.00, 100),
    ('PROD006', 'Headphones', 'Electronics', 60.00, 180),
    ('PROD007', 'USB Cable', 'Accessories', 10.00, 500),
    ('PROD008', 'Laptop Stand', 'Accessories', 45.00, 120),
    ('PROD009', 'Desk Lamp', 'Furniture', 35.00, 90),
    ('PROD010', 'Office Chair', 'Furniture', 250.00, 40)
ON CONFLICT (product_id) DO NOTHING;

-- Create some views for easier querying
CREATE OR REPLACE VIEW sales_summary AS
SELECT
    category,
    COUNT(*) as order_count,
    SUM(quantity) as total_quantity,
    SUM(total_amount) as total_revenue,
    AVG(total_amount) as avg_order_value
FROM sales
GROUP BY category;

CREATE OR REPLACE VIEW monthly_sales AS
SELECT
    DATE_TRUNC('month', order_date) as month,
    COUNT(*) as order_count,
    SUM(total_amount) as total_revenue
FROM sales
GROUP BY DATE_TRUNC('month', order_date)
ORDER BY month;

-- Grant permissions (if needed)
GRANT SELECT ON ALL TABLES IN SCHEMA public TO analytics_user;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO analytics_user;