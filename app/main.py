"""
Olist E-Commerce Analytics Dashboard
Multi-page Streamlit app using st.navigation (Streamlit 1.36+)
"""

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

# Ensure src/ is importable from app/
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_loader import load_master
from src.ml_pipeline import full_pipeline

st.set_page_config(
    page_title="Olist E-Commerce Analytics",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ─── Data Loading (cached, shared across pages) ───────────────────────────────

@st.cache_data(show_spinner="Loading Olist data...")
def get_master_data() -> pd.DataFrame:
    return load_master()


@st.cache_data(show_spinner="Running customer segmentation...")
def get_rfm_data(data_hash: str) -> pd.DataFrame:
    df = get_master_data()
    return full_pipeline(df, k=4)


# ─── Sidebar Filters ──────────────────────────────────────────────────────────

def render_sidebar(df: pd.DataFrame) -> dict:
    """Render global sidebar filters and return filter values."""
    st.sidebar.title("🛒 Olist Analytics")
    st.sidebar.markdown("**Filters**")

    # Date range
    min_date = df["order_purchase_timestamp"].min().date()
    max_date = df["order_purchase_timestamp"].max().date()
    date_range = st.sidebar.date_input(
        "Order Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
        key="date_range",
    )

    # Product category
    all_categories = sorted(df["product_category"].dropna().unique().tolist())
    selected_categories = st.sidebar.multiselect(
        "Product Category",
        options=all_categories,
        default=[],
        placeholder="All categories",
        key="categories",
    )

    # State
    all_states = sorted(df["customer_state"].dropna().unique().tolist())
    selected_states = st.sidebar.multiselect(
        "Customer State",
        options=all_states,
        default=[],
        placeholder="All states",
        key="states",
    )

    st.sidebar.markdown("---")
    st.sidebar.caption(
        "**Dataset**: Olist Brazilian E-Commerce  \n"
        "100K orders · 2016–2018  \n"
        "[GitHub Repo](#) · [Live Dashboard](#)"
    )

    return {
        "date_range": date_range,
        "categories": selected_categories,
        "states": selected_states,
    }


def apply_filters(df: pd.DataFrame, filters: dict) -> pd.DataFrame:
    """Apply sidebar filter selections to master dataframe."""
    df = df.copy()
    df["order_purchase_timestamp"] = pd.to_datetime(df["order_purchase_timestamp"])

    if len(filters["date_range"]) == 2:
        start, end = filters["date_range"]
        df = df[
            (df["order_purchase_timestamp"].dt.date >= start)
            & (df["order_purchase_timestamp"].dt.date <= end)
        ]

    if filters["categories"]:
        df = df[df["product_category"].isin(filters["categories"])]

    if filters["states"]:
        df = df[df["customer_state"].isin(filters["states"])]

    return df


# ─── Navigation ───────────────────────────────────────────────────────────────

def main():
    # Load data
    try:
        df = get_master_data()
    except FileNotFoundError:
        st.error(
            "**Data not found.** Please build the master parquet first:\n\n"
            "```bash\n"
            "python -c 'from src.data_loader import clean_and_export; clean_and_export()'\n"
            "```"
        )
        st.stop()

    # Sidebar filters (persisted via session_state keys)
    filters = render_sidebar(df)
    filtered_df = apply_filters(df, filters)

    # Store in session state for pages to access
    st.session_state["df"] = filtered_df
    st.session_state["df_full"] = df
    st.session_state["rfm"] = get_rfm_data(str(df.shape))

    # Page definitions
    pages = [
        st.Page("pages/01_sales_overview.py", title="Sales Overview", icon="💰"),
        st.Page("pages/02_customer_segments.py", title="Customer Segments", icon="👥"),
        st.Page("pages/03_delivery_performance.py", title="Delivery Performance", icon="🚚"),
    ]

    pg = st.navigation(pages)
    pg.run()


if __name__ == "__main__":
    main()
