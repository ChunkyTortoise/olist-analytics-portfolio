"""
Page 3: Delivery Performance
Delivery time trends, late delivery by state, review score correlation.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

PRIMARY = "#2563EB"
WARN = "#F59E0B"
DANGER = "#EF4444"
SUCCESS = "#10B981"


def render():
    df: pd.DataFrame = st.session_state.get("df")
    if df is None or df.empty:
        st.warning("No data available.")
        return

    df = df.copy()
    df["order_purchase_timestamp"] = pd.to_datetime(df["order_purchase_timestamp"])
    df = df.dropna(subset=["days_to_deliver", "customer_state"])

    st.title("🚚 Delivery Performance")
    st.caption("On-time delivery rates, delivery time by state, and review score impact")

    # ─── KPI Cards ────────────────────────────────────────────────────────────
    avg_days = df["days_to_deliver"].mean()
    late_rate = df["is_late_delivery"].mean() * 100
    avg_review_ontime = df[df["is_late_delivery"] == 0]["review_score"].mean()
    avg_review_late = df[df["is_late_delivery"] == 1]["review_score"].mean()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Avg Delivery Days", f"{avg_days:.1f} days")
    c2.metric("Late Delivery Rate", f"{late_rate:.1f}%", delta=f"-{late_rate:.1f}% target: 0%", delta_color="inverse")
    c3.metric("Avg Review (On-Time)", f"{avg_review_ontime:.2f} / 5")
    c4.metric(
        "Avg Review (Late)",
        f"{avg_review_late:.2f} / 5",
        delta=f"{avg_review_late - avg_review_ontime:.2f} vs on-time",
        delta_color="inverse",
    )

    st.divider()

    col_left, col_right = st.columns([3, 2])

    # ─── Delivery Days Distribution ───────────────────────────────────────────
    with col_left:
        st.subheader("Delivery Time Distribution")

        fig_hist = px.histogram(
            df[df["days_to_deliver"].between(0, 60)],
            x="days_to_deliver",
            nbins=60,
            color="is_late_delivery",
            color_discrete_map={0: SUCCESS, 1: DANGER},
            labels={"days_to_deliver": "Days to Deliver", "is_late_delivery": "Late?",
                    "count": "Orders"},
            barmode="overlay",
        )
        fig_hist.update_traces(opacity=0.75)
        fig_hist.update_layout(
            legend=dict(
                title="Delivery Status",
                orientation="h", y=1.1,
            ),
            margin=dict(l=0, r=0, t=30, b=0), height=320,
        )
        # Remap legend labels
        for trace in fig_hist.data:
            trace.name = "On-Time" if trace.name == "0" else "Late"
        st.plotly_chart(fig_hist, use_container_width=True)
        st.caption(
            "**Insight**: Most deliveries complete in 7-14 days. "
            "The tail beyond 20 days represents logistics failures concentrated in specific states."
        )

    # ─── Review Score by Delivery Status ─────────────────────────────────────
    with col_right:
        st.subheader("Review Score vs Delivery")

        review_by_status = (
            df.groupby("is_late_delivery")["review_score"]
            .value_counts(normalize=True)
            .mul(100)
            .rename("pct")
            .reset_index()
        )
        review_by_status["delivery_status"] = review_by_status["is_late_delivery"].map(
            {0: "On-Time", 1: "Late"}
        )

        fig_review = px.bar(
            review_by_status,
            x="review_score", y="pct", color="delivery_status",
            barmode="group",
            color_discrete_map={"On-Time": SUCCESS, "Late": DANGER},
            labels={"review_score": "Review Score (1-5)", "pct": "% of Orders"},
        )
        fig_review.update_layout(
            legend=dict(title="", orientation="h", y=1.1),
            margin=dict(l=0, r=0, t=30, b=0), height=320,
        )
        st.plotly_chart(fig_review, use_container_width=True)

    st.divider()

    # ─── Late Rate by State (Bar Chart) ───────────────────────────────────────
    st.subheader("Delivery Performance by State")

    state_metrics = (
        df.groupby("customer_state")
        .agg(
            total_orders=("order_id", "nunique"),
            late_rate=("is_late_delivery", "mean"),
            avg_delivery_days=("days_to_deliver", "mean"),
            avg_review=("review_score", "mean"),
        )
        .reset_index()
        .assign(late_rate=lambda x: x["late_rate"] * 100)
        .sort_values("late_rate", ascending=False)
    )

    col_a, col_b = st.columns(2)

    with col_a:
        fig_state_late = px.bar(
            state_metrics.head(20),
            x="customer_state", y="late_rate",
            color="late_rate",
            color_continuous_scale=[[0, "#FEF3C7"], [0.5, WARN], [1, DANGER]],
            labels={"customer_state": "State", "late_rate": "Late Delivery Rate (%)"},
        )
        fig_state_late.update_layout(
            coloraxis_showscale=False,
            margin=dict(l=0, r=0, t=10, b=0), height=320,
        )
        st.plotly_chart(fig_state_late, use_container_width=True)
        st.caption("States with highest late delivery rates. Target logistics investment here first.")

    with col_b:
        fig_state_review = px.scatter(
            state_metrics,
            x="late_rate", y="avg_review",
            size="total_orders", hover_name="customer_state",
            color="avg_delivery_days",
            color_continuous_scale=[[0, SUCCESS], [0.5, WARN], [1, DANGER]],
            labels={
                "late_rate": "Late Rate (%)",
                "avg_review": "Avg Review Score",
                "avg_delivery_days": "Avg Delivery Days",
            },
        )
        fig_state_review.update_layout(
            margin=dict(l=0, r=0, t=10, b=0), height=320,
        )
        st.plotly_chart(fig_state_review, use_container_width=True)
        st.caption(
            "States with higher late rates consistently show lower review scores. "
            "Each point = one state; size = order volume."
        )

    # ─── Key Finding ──────────────────────────────────────────────────────────
    delta = avg_review_ontime - avg_review_late
    st.info(
        f"**Key Finding**: On-time deliveries score {avg_review_ontime:.2f}/5 vs {avg_review_late:.2f}/5 for late deliveries "
        f"-- a {delta:.2f} point gap. Reducing late deliveries by 10% would improve platform-wide review scores and drive repeat purchases."
    )


render()
