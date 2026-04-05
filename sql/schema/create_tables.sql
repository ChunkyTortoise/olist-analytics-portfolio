-- ============================================================
-- Olist E-Commerce Schema
-- PostgreSQL dialect (compatible with DuckDB)
-- ============================================================

CREATE TABLE IF NOT EXISTS customers (
    customer_id           VARCHAR PRIMARY KEY,
    customer_unique_id    VARCHAR NOT NULL,
    customer_zip_code_prefix INTEGER,
    customer_city         TEXT,
    customer_state        CHAR(2)
);

CREATE TABLE IF NOT EXISTS sellers (
    seller_id             VARCHAR PRIMARY KEY,
    seller_zip_code_prefix INTEGER,
    seller_city           TEXT,
    seller_state          CHAR(2)
);

CREATE TABLE IF NOT EXISTS product_category_name_translation (
    product_category_name         TEXT PRIMARY KEY,
    product_category_name_english TEXT
);

CREATE TABLE IF NOT EXISTS products (
    product_id                   VARCHAR PRIMARY KEY,
    product_category_name        TEXT REFERENCES product_category_name_translation(product_category_name),
    product_name_length          INTEGER,
    product_description_length   INTEGER,
    product_photos_qty           INTEGER,
    product_weight_g             DECIMAL(10,2),
    product_length_cm            DECIMAL(10,2),
    product_height_cm            DECIMAL(10,2),
    product_width_cm             DECIMAL(10,2)
);

CREATE TABLE IF NOT EXISTS geolocation (
    geolocation_zip_code_prefix  INTEGER,
    geolocation_lat              DECIMAL(10,6),
    geolocation_lng              DECIMAL(10,6),
    geolocation_city             TEXT,
    geolocation_state            CHAR(2)
);

CREATE TABLE IF NOT EXISTS orders (
    order_id                          VARCHAR PRIMARY KEY,
    customer_id                       VARCHAR REFERENCES customers(customer_id),
    order_status                      TEXT,
    order_purchase_timestamp          TIMESTAMP,
    order_approved_at                 TIMESTAMP,
    order_delivered_carrier_date      TIMESTAMP,
    order_delivered_customer_date     TIMESTAMP,
    order_estimated_delivery_date     TIMESTAMP
);

CREATE TABLE IF NOT EXISTS order_items (
    order_id             VARCHAR REFERENCES orders(order_id),
    order_item_id        INTEGER,
    product_id           VARCHAR REFERENCES products(product_id),
    seller_id            VARCHAR REFERENCES sellers(seller_id),
    shipping_limit_date  TIMESTAMP,
    price                DECIMAL(10,2),
    freight_value        DECIMAL(10,2),
    PRIMARY KEY (order_id, order_item_id)
);

CREATE TABLE IF NOT EXISTS order_payments (
    order_id              VARCHAR REFERENCES orders(order_id),
    payment_sequential    INTEGER,
    payment_type          TEXT,
    payment_installments  INTEGER,
    payment_value         DECIMAL(10,2),
    PRIMARY KEY (order_id, payment_sequential)
);

CREATE TABLE IF NOT EXISTS order_reviews (
    review_id              VARCHAR,
    order_id               VARCHAR REFERENCES orders(order_id),
    review_score           INTEGER,
    review_comment_title   TEXT,
    review_comment_message TEXT,
    review_creation_date   TIMESTAMP,
    review_answer_timestamp TIMESTAMP,
    PRIMARY KEY (review_id, order_id)
);
