"""
K-Means RFM customer segmentation pipeline.
Follows academic best practices: log1p transform -> StandardScaler -> KMeans++.
"""

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score


# ─── RFM Computation ──────────────────────────────────────────────────────────

def compute_rfm(df: pd.DataFrame, reference_date: pd.Timestamp = None) -> pd.DataFrame:
    """
    Compute RFM metrics at the customer_unique_id level.

    Args:
        df: Master orders dataframe from data_loader.load_master()
        reference_date: Snapshot date (default: day after max order date)

    Returns:
        DataFrame with columns: customer_unique_id, recency_days, frequency, monetary
    """
    df = df.copy()
    df["order_purchase_timestamp"] = pd.to_datetime(df["order_purchase_timestamp"])

    if reference_date is None:
        reference_date = df["order_purchase_timestamp"].max() + pd.Timedelta(days=1)

    rfm = (
        df.groupby("customer_unique_id")
        .agg(
            last_purchase=("order_purchase_timestamp", "max"),
            frequency=("order_id", "nunique"),
            monetary=("price", "sum"),
        )
        .reset_index()
    )

    rfm["recency_days"] = (reference_date - rfm["last_purchase"]).dt.days
    rfm = rfm.drop(columns=["last_purchase"])
    rfm["monetary"] = rfm["monetary"].round(2)

    return rfm


# ─── Outlier Handling & Scaling ───────────────────────────────────────────────

def preprocess_rfm(rfm: pd.DataFrame) -> tuple[np.ndarray, pd.DataFrame]:
    """
    Apply log1p transform + StandardScaler to RFM values.
    Returns (scaled_array, rfm_log_df).

    Note: log1p handles frequency=0 edge case gracefully.
    Note: Recency is NOT inverted here -- KMeans operates on distance,
          and labeling is done post-hoc by inspecting cluster centers.
    """
    features = ["recency_days", "frequency", "monetary"]
    rfm_log = np.log1p(rfm[features])

    scaler = StandardScaler()
    scaled = scaler.fit_transform(rfm_log)

    return scaled, rfm_log


# ─── Cluster Selection ────────────────────────────────────────────────────────

def elbow_scores(scaled: np.ndarray, k_range: range = range(2, 9)) -> dict:
    """
    Compute inertia (WCSS) for each k. Used to plot the elbow curve.
    Returns {k: inertia}.
    """
    scores = {}
    for k in k_range:
        km = KMeans(n_clusters=k, init="k-means++", random_state=42, n_init=10)
        km.fit(scaled)
        scores[k] = km.inertia_
    return scores


def silhouette_scores(scaled: np.ndarray, k_range: range = range(2, 9)) -> dict:
    """
    Compute silhouette score for each k.
    Returns {k: silhouette_score}.
    Expect scores in 0.3-0.5 range for real customer data (normal).
    """
    scores = {}
    for k in k_range:
        km = KMeans(n_clusters=k, init="k-means++", random_state=42, n_init=10)
        labels = km.fit_predict(scaled)
        scores[k] = silhouette_score(scaled, labels)
    return scores


# ─── Clustering ───────────────────────────────────────────────────────────────

def run_clustering(scaled: np.ndarray, k: int = 4) -> tuple[KMeans, np.ndarray]:
    """
    Fit KMeans with k-means++ initialization.
    k=4 is validated as optimal for Olist by peer-reviewed study (Perplexity source).
    Returns (fitted_model, labels).
    """
    km = KMeans(n_clusters=k, init="k-means++", random_state=42, n_init=10)
    labels = km.fit_predict(scaled)
    return km, labels


def label_clusters(rfm: pd.DataFrame, labels: np.ndarray) -> pd.DataFrame:
    """
    Assign business-meaningful names to clusters based on cluster center profiles.

    Business logic:
      - Champions:    low recency (recent), high frequency, high monetary
      - Loyal:        medium recency, high frequency, medium monetary
      - At-Risk:      high recency (not recent), medium frequency, medium monetary
      - Hibernating:  high recency, low frequency, low monetary
    """
    rfm = rfm.copy()
    rfm["cluster"] = labels

    # Compute cluster means on original (non-scaled) RFM values
    cluster_means = rfm.groupby("cluster")[["recency_days", "frequency", "monetary"]].mean()

    # Rank clusters: recency LOWER = better, frequency/monetary HIGHER = better
    cluster_means["r_rank"] = cluster_means["recency_days"].rank(ascending=True)  # 1=best (recent)
    cluster_means["f_rank"] = cluster_means["frequency"].rank(ascending=False)
    cluster_means["m_rank"] = cluster_means["monetary"].rank(ascending=False)
    cluster_means["rfm_rank"] = (
        cluster_means["r_rank"] + cluster_means["f_rank"] + cluster_means["m_rank"]
    )

    label_map = {}
    sorted_clusters = cluster_means.sort_values("rfm_rank").index.tolist()
    segment_names = ["Champions", "Loyal Customers", "At-Risk", "Hibernating"]

    for cluster_id, name in zip(sorted_clusters, segment_names):
        label_map[cluster_id] = name

    rfm["segment"] = rfm["cluster"].map(label_map)
    return rfm


# ─── Convenience Runner ───────────────────────────────────────────────────────

def full_pipeline(df: pd.DataFrame, k: int = 4) -> pd.DataFrame:
    """
    Run the full RFM + K-Means pipeline end-to-end.
    Returns rfm dataframe with cluster and segment columns.
    """
    rfm = compute_rfm(df)
    scaled, _ = preprocess_rfm(rfm)
    _, labels = run_clustering(scaled, k=k)
    rfm_labeled = label_clusters(rfm, labels)
    return rfm_labeled
