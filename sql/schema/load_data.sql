-- ============================================================
-- DuckDB CSV Loading Commands
-- Run via: duckdb -c ".read sql/schema/load_data.sql"
-- Or use src/data_loader.py (recommended)
-- ============================================================

-- Customers
INSERT INTO customers
SELECT * FROM read_csv_auto('data/raw/olist_customers_dataset.csv');

-- Sellers
INSERT INTO sellers
SELECT * FROM read_csv_auto('data/raw/olist_sellers_dataset.csv');

-- Product category translations
INSERT INTO product_category_name_translation
SELECT * FROM read_csv_auto('data/raw/product_category_name_translation.csv');

-- Products
INSERT INTO products
SELECT * FROM read_csv_auto('data/raw/olist_products_dataset.csv');

-- Geolocation (has duplicates by design)
INSERT INTO geolocation
SELECT * FROM read_csv_auto('data/raw/olist_geolocation_dataset.csv');

-- Orders
INSERT INTO orders
SELECT * FROM read_csv_auto('data/raw/olist_orders_dataset.csv');

-- Order items
INSERT INTO order_items
SELECT * FROM read_csv_auto('data/raw/olist_order_items_dataset.csv');

-- Order payments
INSERT INTO order_payments
SELECT * FROM read_csv_auto('data/raw/olist_order_payments_dataset.csv');

-- Order reviews
INSERT INTO order_reviews
SELECT * FROM read_csv_auto('data/raw/olist_order_reviews_dataset.csv');
