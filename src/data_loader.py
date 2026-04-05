"""
Data loading and cleaning pipeline for Olist E-Commerce dataset.
Uses DuckDB in-memory engine; queries written in PostgreSQL dialect.
"""

import os
from pathlib import Path
import duckdb
import pandas as pd
import numpy as np

# Project root relative to this file
PROJECT_ROOT = Path(__file__).parent.parent
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"

# Map CSV filenames to table names
CSV_TABLE_MAP = {
    "olist_customers_dataset.csv": "customers",
    "olist_sellers_dataset.csv": "sellers",
    "product_category_name_translation.csv": "product_category_name_translation",
    "olist_products_dataset.csv": "products",
    "olist_geolocation_dataset.csv": "geolocation",
    "olist_orders_dataset.csv": "orders",
    "olist_order_items_dataset.csv": "order_items",
    "olist_order_payments_dataset.csv": "order_payments",
    "olist_order_reviews_dataset.csv": "order_reviews",
}


def get_connection() -> duckdb.DuckDBPyConnection:
    """Return a new in-memory DuckDB connection."""
    return duckdb.connect(":memory:")


def load_all_tables(con: duckdb.DuckDBPyConnection = None) -> duckdb.DuckDBPyConnection:
    """
    Load all 9 Olist CSVs into DuckDB tables.
    Returns the connection so callers can run queries immediately.
    """
    if con is None:
        con = get_connection()

    missing = []
    for csv_file, table_name in CSV_TABLE_MAP.items():
        csv_path = DATA_RAW / csv_file
        if not csv_path.exists():
            missing.append(csv_file)
            continue
        con.execute(
            f"CREATE OR REPLACE TABLE {table_name} AS "
            f"SELECT * FROM read_csv_auto('{csv_path}')"
        )

    if missing:
        print(f"WARNING: Missing CSVs (download from Kaggle): {missing}")
    else:
        tables = con.execute("SHOW TABLES").fetchdf()
        print(f"Loaded {len(tables)} tables: {', '.join(tables['name'].tolist())}")

    return con


def clean_and_export(con: duckdb.DuckDBPyConnection = None) -> pd.DataFrame:
    """
    Build master orders dataframe with all relevant fields joined.
    Applies cleaning decisions documented in docs/DATA_QUALITY.md.
    Exports to data/processed/olist_master.parquet.
    """
    if con is None:
        con = load_all_tables()

    query = """
    WITH base AS (
        SELECT
            o.order_id,
            o.order_status,
            o.order_purchase_timestamp,
            o.order_approved_at,
            o.order_delivered_carrier_date,
            o.order_delivered_customer_date,
            o.order_estimated_delivery_date,

            -- Customer identity (use unique_id for cohort/RFM analysis)
            c.customer_id,
            c.customer_unique_id,
            c.customer_state,
            c.customer_city,

            -- Order financials
            oi.order_item_id,
            oi.price,
            oi.freight_value,
            (oi.price + oi.freight_value) AS item_total,

            -- Product
            p.product_id,
            COALESCE(t.product_category_name_english, 'other') AS product_category,

            -- Seller
            s.seller_id,
            s.seller_state,

            -- Review
            r.review_score,

            -- Payment
            pay.payment_type,
            pay.payment_installments,
            pay.payment_value

        FROM orders o
        JOIN customers c USING (customer_id)
        JOIN order_items oi USING (order_id)
        JOIN products p USING (product_id)
        LEFT JOIN product_category_name_translation t
            ON p.product_category_name = t.product_category_name
        JOIN sellers s USING (seller_id)
        LEFT JOIN order_reviews r USING (order_id)
        LEFT JOIN order_payments pay
            ON o.order_id = pay.order_id AND pay.payment_sequential = 1
    )
    SELECT *,
        -- Derived delivery metrics
        DATEDIFF('day', order_purchase_timestamp, order_delivered_customer_date)
            AS days_to_deliver,
        DATEDIFF('day', order_delivered_customer_date, order_estimated_delivery_date)
            AS days_early_late,  -- positive = early, negative = late
        CASE
            WHEN order_delivered_customer_date > order_estimated_delivery_date THEN 1
            ELSE 0
        END AS is_late_delivery

    FROM base
    -- Only keep delivered orders for most analyses
    WHERE order_status = 'delivered'
      AND order_delivered_customer_date IS NOT NULL
      AND order_purchase_timestamp IS NOT NULL
    """

    df = con.execute(query).df()

    # Type conversions
    ts_cols = [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ]
    for col in ts_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    # Export
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    out_path = DATA_PROCESSED / "olist_master.parquet"
    df.to_parquet(out_path, index=False)
    print(f"Exported {len(df):,} rows to {out_path}")

    return df


def load_master() -> pd.DataFrame:
    """Load the pre-processed master parquet. Build it first with clean_and_export()."""
    path = DATA_PROCESSED / "olist_master.parquet"
    if not path.exists():
        raise FileNotFoundError(
            f"Master parquet not found at {path}. "
            "Run: python -c 'from src.data_loader import clean_and_export; clean_and_export()'"
        )
    return pd.read_parquet(path)


if __name__ == "__main__":
    con = load_all_tables()
    df = clean_and_export(con)
    print(df.head())
    print(df.dtypes)
