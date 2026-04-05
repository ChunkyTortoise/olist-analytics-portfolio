-- ============================================================
-- Business Question: Which sellers drive the most revenue?
-- How do the top 10% of sellers compare to the bottom 50%?
--
-- Insight target: Identify platform's revenue concentration risk --
-- if top 10 sellers drive 40%+ of GMV, churn of key sellers is
-- a significant business risk.
-- ============================================================

WITH seller_metrics AS (
    SELECT
        s.seller_id,
        s.seller_state,
        COUNT(DISTINCT o.order_id)          AS total_orders,
        COUNT(DISTINCT c.customer_unique_id) AS unique_customers,
        ROUND(SUM(oi.price), 2)             AS total_revenue,
        ROUND(AVG(oi.price), 2)             AS avg_order_value,
        ROUND(AVG(r.review_score), 2)       AS avg_review_score,
        COUNT(DISTINCT
            CASE WHEN o.order_delivered_customer_date > o.order_estimated_delivery_date
                 THEN o.order_id END
        )::FLOAT / NULLIF(COUNT(DISTINCT o.order_id), 0) * 100
                                            AS late_delivery_rate_pct
    FROM sellers s
    JOIN order_items oi USING (seller_id)
    JOIN orders o USING (order_id)
    JOIN customers c USING (customer_id)
    LEFT JOIN order_reviews r USING (order_id)
    WHERE o.order_status = 'delivered'
    GROUP BY 1, 2
),
ranked AS (
    SELECT
        *,
        DENSE_RANK() OVER (ORDER BY total_revenue DESC) AS revenue_rank,
        NTILE(10) OVER (ORDER BY total_revenue DESC)    AS revenue_decile,
        SUM(total_revenue) OVER (
            ORDER BY total_revenue DESC
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        )                                               AS cumulative_revenue,
        SUM(total_revenue) OVER ()                      AS platform_total_revenue
    FROM seller_metrics
)
SELECT
    seller_id,
    seller_state,
    revenue_rank,
    revenue_decile,
    total_orders,
    unique_customers,
    total_revenue,
    avg_order_value,
    ROUND(avg_review_score, 2)                                            AS avg_review_score,
    ROUND(late_delivery_rate_pct, 1)                                      AS late_delivery_pct,
    ROUND(cumulative_revenue, 2)                                          AS cumulative_revenue,
    ROUND(cumulative_revenue / platform_total_revenue * 100, 1)          AS cumulative_revenue_pct
FROM ranked
ORDER BY revenue_rank
LIMIT 100;
