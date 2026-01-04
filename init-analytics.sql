CREATE TABLE IF NOT EXISTS sales (
    id SERIAL PRIMARY KEY,
    product_name VARCHAR(255),
    quantity INTEGER,
    price DECIMAL(10, 2),
    sale_date DATE,
    customer_name VARCHAR(255),
    region VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS users_analytics (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    action VARCHAR(100),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

INSERT INTO sales (product_name, quantity, price, sale_date, customer_name, region) VALUES
    ('Laptop', 2, 1200.00, '2024-01-15', 'John Doe', 'North'),
    ('Mouse', 5, 25.00, '2024-01-16', 'Jane Smith', 'South'),
    ('Keyboard', 3, 75.00, '2024-01-17', 'Bob Johnson', 'East'),
    ('Monitor', 1, 350.00, '2024-01-18', 'Alice Brown', 'West'),
    ('Headphones', 4, 50.00, '2024-01-19', 'Charlie Wilson', 'North');

INSERT INTO users_analytics (user_id, action, metadata) VALUES
    (1, 'login', '{"ip": "192.168.1.1", "device": "desktop"}'),
    (2, 'signup', '{"referrer": "google", "device": "mobile"}'),
    (1, 'view_page', '{"page": "/dashboard", "duration": 45}'),
    (3, 'login', '{"ip": "192.168.1.2", "device": "tablet"}'),
    (2, 'purchase', '{"amount": 99.99, "product_id": 123}');