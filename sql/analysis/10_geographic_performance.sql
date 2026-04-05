-- ============================================================
-- Business Question: How does performance vary across Brazilian states?
-- Are there geographic markets that are underserved or high-potential?
--
-- Insight target: SP (São Paulo) typically dominates volume (40%+)
-- but emerging states may show faster growth and less competition.
-- ============================================================

WITH state_metrics AS (
    SELECT
        c.customer_state,
        DATE_TRUNC('year', o.order_purchase_timestamp) AS year,
        COUNT(DISTINCT o.order_id)                     AS order_count,
        COUNT(DISTINCT c.customer_unique_id)           AS unique_customers,
        ROUND(SUM(oi.price), 2)                        AS revenue,
        ROUND(AVG(oi.price), 2)                        AS avg_order_value,
        ROUND(AVG(r.review_score), 2)                  AS avg_review_score,
        ROUND(
            AVG(DATEDIFF('day', o.order_purchase_timestamp,
                         o.order_delivered_customer_date)), 1
        )                                              AS avg_delivery_days,
        ROUND(
            SUM(CASE WHEN o.order_delivered_customer_date
                          > o.order_estimated_delivery_date THEN 1 ELSE 0 END)::FLOAT
            / COUNT(*) * 100, 1
        )                                              AS late_rate_pct
    FROM orders o
    JOIN customers c USING (customer_id)
    JOIN order_items oi USING (order_id)
    LEFT JOIN order_reviews r USING (order_id)
    WHERE o.order_status = 'delivered'
      AND o.order_delivered_customer_date IS NOT NULL
    GROUP BY 1, 2
)
SELECT
    customer_state,
    SUM(order_count)          AS total_orders,
    SUM(unique_customers)     AS total_customers,
    ROUND(SUM(revenue), 2)    AS total_revenue,
    ROUND(AVG(avg_order_value), 2)   AS avg_order_value,
    ROUND(AVG(avg_review_score), 2)  AS avg_review_score,
    ROUND(AVG(avg_delivery_days), 1) AS avg_delivery_days,
    ROUND(AVG(late_rate_pct), 1)     AS avg_late_rate_pct,
    ROUND(SUM(revenue) / SUM(SUM(revenue)) OVER () * 100, 2) AS revenue_share_pct,
    DENSE_RANK() OVER (ORDER BY SUM(revenue) DESC) AS revenue_rank
FROM state_metrics
GROUP BY 1
ORDER BY total_revenue DESC;
