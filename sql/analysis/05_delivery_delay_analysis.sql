-- ============================================================
-- Business Question: Where do deliveries fail, and why?
-- Which states have the worst on-time delivery performance?
--
-- Insight target: Late deliveries correlate with lower review scores
-- (~0.7 points lower on average). Fixing logistics in the worst
-- states is the highest-ROI improvement.
-- ============================================================

WITH delivery_metrics AS (
    SELECT
        c.customer_state,
        o.order_id,
        DATEDIFF('day', o.order_purchase_timestamp,
                 o.order_delivered_customer_date)                   AS actual_days,
        DATEDIFF('day', o.order_purchase_timestamp,
                 o.order_estimated_delivery_date)                   AS promised_days,
        DATEDIFF('day', o.order_delivered_customer_date,
                 o.order_estimated_delivery_date)                   AS days_early_late,
        CASE
            WHEN o.order_delivered_customer_date > o.order_estimated_delivery_date
            THEN 1 ELSE 0
        END                                                         AS is_late,
        CASE
            WHEN DATEDIFF('day', o.order_purchase_timestamp,
                          o.order_delivered_customer_date) > 20
            THEN 'Very Slow (>20 days)'
            WHEN DATEDIFF('day', o.order_purchase_timestamp,
                          o.order_delivered_customer_date) > 14
            THEN 'Slow (14-20 days)'
            WHEN DATEDIFF('day', o.order_purchase_timestamp,
                          o.order_delivered_customer_date) > 7
            THEN 'Standard (7-14 days)'
            ELSE 'Fast (≤7 days)'
        END                                                         AS delivery_speed_bucket,
        r.review_score
    FROM orders o
    JOIN customers c USING (customer_id)
    LEFT JOIN order_reviews r USING (order_id)
    WHERE o.order_status = 'delivered'
      AND o.order_delivered_customer_date IS NOT NULL
      AND o.order_purchase_timestamp IS NOT NULL
)
SELECT
    customer_state,
    COUNT(order_id)                                    AS total_orders,
    ROUND(AVG(actual_days), 1)                         AS avg_delivery_days,
    ROUND(AVG(promised_days), 1)                       AS avg_promised_days,
    ROUND(AVG(days_early_late), 1)                     AS avg_days_early_late,
    ROUND(SUM(is_late)::FLOAT / COUNT(*) * 100, 1)     AS late_rate_pct,
    ROUND(AVG(review_score), 2)                        AS avg_review_score,
    ROUND(AVG(CASE WHEN is_late = 1 THEN review_score END), 2)
                                                       AS avg_review_when_late,
    ROUND(AVG(CASE WHEN is_late = 0 THEN review_score END), 2)
                                                       AS avg_review_when_ontime,
    -- Distribution of delivery speed buckets
    COUNT(CASE WHEN delivery_speed_bucket = 'Fast (≤7 days)' THEN 1 END)    AS fast_orders,
    COUNT(CASE WHEN delivery_speed_bucket = 'Standard (7-14 days)' THEN 1 END) AS standard_orders,
    COUNT(CASE WHEN delivery_speed_bucket = 'Slow (14-20 days)' THEN 1 END) AS slow_orders,
    COUNT(CASE WHEN delivery_speed_bucket = 'Very Slow (>20 days)' THEN 1 END) AS very_slow_orders
FROM delivery_metrics
GROUP BY 1
ORDER BY late_rate_pct DESC;
