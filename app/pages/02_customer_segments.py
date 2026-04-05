"""
Page 2: Customer Segments
RFM + K-Means segmentation results, cluster profiles, segment KPIs.
"""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from sklearn.decomposition import PCA

PRIMARY = "#2563EB"
SEGMENT_COLORS = {
    "Champions": "#10B981",
    "Loyal Customers": "#2563EB",
    "At-Risk": "#F59E0B",
    "Hibernating": "#EF4444",
}


def render():
    rfm: pd.DataFrame = st.session_state.get("rfm")
    if rfm is None or rfm.empty:
        st.warning("Segmentation data unavailable.")
        return

    st.title("👥 Customer Segments")
    st.caption("RFM-based customer segmentation using K-Means clustering (k=4)")

    # ─── Segment Summary KPIs ─────────────────────────────────────────────────
    segment_summary = (
        rfm.groupby("segment")
        .agg(
            customers=("customer_unique_id", "count"),
            avg_recency=("recency_days", "mean"),
            avg_frequency=("frequency", "mean"),
            avg_monetary=("monetary", "mean"),
        )
        .reset_index()
    )

    cols = st.columns(4)
    for i, row in segment_summary.iterrows():
        with cols[i % 4]:
            color = SEGMENT_COLORS.get(row["segment"], PRIMARY)
            st.markdown(
                f"<div style='border-left: 4px solid {color}; padding: 8px 12px; "
                f"border-radius: 4px; background: #F9FAFB;'>"
                f"<b style='color:{color}'>{row['segment']}</b><br>"
                f"<span style='font-size:1.4em;font-weight:bold'>{row['customers']:,}</span> customers<br>"
                f"<span style='color:#6B7280;font-size:0.85em'>"
                f"Avg R: {row['avg_recency']:.0f}d · "
                f"F: {row['avg_frequency']:.1f}x · "
                f"M: R${row['avg_monetary']:,.0f}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )

    st.divider()

    col_left, col_right = st.columns([3, 2])

    # ─── PCA Scatter ──────────────────────────────────────────────────────────
    with col_left:
        st.subheader("Customer Clusters (PCA 2D Projection)")

        from sklearn.preprocessing import StandardScaler
        features = ["recency_days", "frequency", "monetary"]
        rfm_log = np.log1p(rfm[features])
        scaled = StandardScaler().fit_transform(rfm_log)
        pca = PCA(n_components=2, random_state=42)
        coords = pca.fit_transform(scaled)
        rfm_plot = rfm.copy()
        rfm_plot["PC1"] = coords[:, 0]
        rfm_plot["PC2"] = coords[:, 1]

        # Sample for performance
        sample = rfm_plot.sample(min(3000, len(rfm_plot)), random_state=42)

        fig_scatter = px.scatter(
            sample, x="PC1", y="PC2", color="segment",
            color_discrete_map=SEGMENT_COLORS,
            opacity=0.5, size_max=4,
            labels={"PC1": f"PC1 ({pca.explained_variance_ratio_[0]:.1%} variance)",
                    "PC2": f"PC2 ({pca.explained_variance_ratio_[1]:.1%} variance)"},
        )
        fig_scatter.update_traces(marker=dict(size=3))
        fig_scatter.update_layout(
            legend=dict(orientation="h", y=1.05),
            margin=dict(l=0, r=0, t=30, b=0), height=380,
        )
        st.plotly_chart(fig_scatter, use_container_width=True)
        st.caption(
            f"PCA captures {sum(pca.explained_variance_ratio_[:2]):.1%} of variance. "
            "Cluster separation confirms distinct behavioral segments."
        )

    # ─── Segment Distribution ─────────────────────────────────────────────────
    with col_right:
        st.subheader("Segment Distribution")
        dist = rfm["segment"].value_counts().reset_index()
        dist.columns = ["segment", "count"]

        fig_pie = px.pie(
            dist, names="segment", values="count",
            color="segment", color_discrete_map=SEGMENT_COLORS,
        )
        fig_pie.update_traces(textposition="inside", textinfo="percent+label")
        fig_pie.update_layout(
            showlegend=False, margin=dict(l=0, r=0, t=10, b=0), height=380,
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    st.divider()

    # ─── Segment Profile (Grouped Bar) ────────────────────────────────────────
    st.subheader("Segment Profiles (Normalized RFM)")

    normalized = segment_summary.copy()
    for col in ["avg_recency", "avg_frequency", "avg_monetary"]:
        col_min = normalized[col].min()
        col_max = normalized[col].max()
        normalized[col] = (normalized[col] - col_min) / (col_max - col_min + 1e-9)
    # Invert recency (lower = better)
    normalized["avg_recency"] = 1 - normalized["avg_recency"]

    melted = normalized.melt(
        id_vars="segment",
        value_vars=["avg_recency", "avg_frequency", "avg_monetary"],
        var_name="metric",
        value_name="score",
    )
    melted["metric"] = melted["metric"].map({
        "avg_recency": "Recency (lower days = higher score)",
        "avg_frequency": "Frequency",
        "avg_monetary": "Monetary Value",
    })

    fig_bar = px.bar(
        melted, x="metric", y="score", color="segment", barmode="group",
        color_discrete_map=SEGMENT_COLORS,
        labels={"score": "Normalized Score (0-1)", "metric": ""},
    )
    fig_bar.update_layout(
        legend=dict(orientation="h", y=1.1),
        margin=dict(l=0, r=0, t=30, b=0), height=320,
        yaxis_range=[0, 1.1],
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    # ─── Business Implications ────────────────────────────────────────────────
    st.subheader("Business Implications")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
**Champions** -- Reward & leverage
- VIP program, early access to new products
- Ask for reviews and referrals
- Upsell premium categories

**Loyal Customers** -- Nurture retention
- Loyalty rewards for repeat purchases
- Personalized category recommendations
- Prevent downgrade to At-Risk
""")
    with col2:
        st.markdown("""
**At-Risk** -- Win-back campaigns
- Time-sensitive discount offers
- Survey to understand churn reasons
- Highlight new products in purchased categories

**Hibernating** -- Re-engagement or sunset
- One-time win-back email with strong incentive
- If no response in 90 days, remove from active marketing
- Reduce CAC spend on this group
""")


render()
