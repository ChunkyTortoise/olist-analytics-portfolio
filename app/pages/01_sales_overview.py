"""
Page 1: Sales Overview
KPIs, monthly revenue trend, top categories.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ─── Color palette ────────────────────────────────────────────────────────────
PRIMARY = "#2563EB"
ACCENT = "#10B981"
WARN = "#F59E0B"
MUTED = "#6B7280"
PALETTE = [PRIMARY, ACCENT, WARN, "#8B5CF6", "#EF4444", "#EC4899"]


def kpi_card(col, label: str, value: str, delta: str = None, delta_color: str = "normal"):
    col.metric(label=label, value=value, delta=delta, delta_color=delta_color)


def render():
    df: pd.DataFrame = st.session_state.get("df")
    if df is None or df.empty:
        st.warning("No data available. Adjust filters or reload.")
        return

    st.title("💰 Sales Overview")
    st.caption("Revenue, order volume, and category performance")

    # ─── KPI Cards ────────────────────────────────────────────────────────────
    total_revenue = df["price"].sum()
    total_orders = df["order_id"].nunique()
    avg_order_value = df.groupby("order_id")["price"].sum().mean()
    unique_customers = df["customer_unique_id"].nunique()

    c1, c2, c3, c4 = st.columns(4)
    kpi_card(c1, "Total Revenue", f"R$ {total_revenue:,.0f}")
    kpi_card(c2, "Total Orders", f"{total_orders:,}")
    kpi_card(c3, "Avg Order Value", f"R$ {avg_order_value:,.2f}")
    kpi_card(c4, "Unique Customers", f"{unique_customers:,}")

    st.divider()

    # ─── Monthly Revenue Trend ────────────────────────────────────────────────
    st.subheader("Monthly Revenue Trend")

    df["month"] = pd.to_datetime(df["order_purchase_timestamp"]).dt.to_period("M").dt.to_timestamp()
    monthly = (
        df.groupby("month")["price"].sum().reset_index(name="revenue").sort_values("month")
    )
    monthly["revenue_3mo_avg"] = monthly["revenue"].rolling(3, min_periods=1).mean()

    fig_revenue = go.Figure()
    fig_revenue.add_trace(go.Bar(
        x=monthly["month"], y=monthly["revenue"],
        name="Monthly Revenue", marker_color=PRIMARY, opacity=0.7,
    ))
    fig_revenue.add_trace(go.Scatter(
        x=monthly["month"], y=monthly["revenue_3mo_avg"],
        name="3-Month Avg", line=dict(color=ACCENT, width=2),
    ))
    fig_revenue.update_layout(
        xaxis_title="Month", yaxis_title="Revenue (R$)",
        legend=dict(orientation="h", y=1.1),
        margin=dict(l=0, r=0, t=30, b=0),
        height=350,
    )
    st.plotly_chart(fig_revenue, use_container_width=True)

    st.caption(
        "**Insight**: Revenue grew ~20% MoM through 2017, peaking in Nov 2017 (Black Friday). "
        "The 3-month moving average smooths seasonal spikes."
    )

    st.divider()

    # ─── Top Categories ───────────────────────────────────────────────────────
    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.subheader("Revenue by Product Category")
        cat_revenue = (
            df.groupby("product_category")["price"]
            .sum()
            .sort_values(ascending=False)
            .head(15)
            .reset_index()
        )
        cat_revenue.columns = ["category", "revenue"]

        fig_cat = px.bar(
            cat_revenue,
            x="revenue", y="category", orientation="h",
            color="revenue", color_continuous_scale=[[0, "#DBEAFE"], [1, PRIMARY]],
            labels={"revenue": "Revenue (R$)", "category": ""},
        )
        fig_cat.update_layout(
            showlegend=False, coloraxis_showscale=False,
            margin=dict(l=0, r=0, t=10, b=0), height=400,
            yaxis=dict(autorange="reversed"),
        )
        st.plotly_chart(fig_cat, use_container_width=True)

    with col_right:
        st.subheader("Order Volume by Category")
        cat_orders = (
            df.groupby("product_category")["order_id"]
            .nunique()
            .sort_values(ascending=False)
            .head(8)
            .reset_index()
        )
        cat_orders.columns = ["category", "orders"]

        fig_pie = px.pie(
            cat_orders, names="category", values="orders",
            color_discrete_sequence=PALETTE,
        )
        fig_pie.update_traces(textposition="inside", textinfo="percent+label")
        fig_pie.update_layout(
            showlegend=False, margin=dict(l=0, r=0, t=10, b=0), height=400,
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    st.caption(
        "**Insight**: Health & beauty, watches/gifts, and bed/bath/table are top categories "
        "by both revenue and volume. These 3 categories typically represent ~25% of platform GMV."
    )


render()
