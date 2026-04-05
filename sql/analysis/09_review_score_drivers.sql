-- ============================================================
-- Business Question: What drives customer satisfaction?
-- Does delivery speed predict review scores?
--
-- Insight target: Late deliveries typically score 2.5-3.0 vs 4.2-4.5
-- for on-time orders. This quantifies the business cost of logistics
-- failure in terms of customer satisfaction.
-- ============================================================

WITH order_features AS (
    SELECT
        o.order_id,
        r.review_score,
        DATEDIFF('day', o.order_purchase_timestamp,
                 o.order_delivered_customer_date)      AS actual_delivery_days,
        DATEDIFF('day', o.order_delivered_customer_date,
                 o.order_estimated_delivery_date)      AS days_vs_estimate,
        CASE
            WHEN o.order_delivered_customer_date > o.order_estimated_delivery_date
            THEN 'Late' ELSE 'On-Time or Early'
        END                                            AS delivery_status,
        c.customer_state,
        COALESCE(t.product_category_name_english, 'other') AS category,
        oi.price
    FROM orders o
    JOIN customers c USING (customer_id)
    JOIN order_items oi USING (order_id)
    JOIN products p USING (product_id)
    LEFT JOIN product_category_name_translation t
        ON p.product_category_name = t.product_category_name
    JOIN order_reviews r USING (order_id)
    WHERE o.order_status = 'delivered'
      AND r.review_score IS NOT NULL
      AND o.order_delivered_customer_date IS NOT NULL
)
SELECT
    delivery_status,
    COUNT(*)                                AS order_count,
    ROUND(AVG(review_score), 2)             AS avg_review_score,
    ROUND(AVG(actual_delivery_days), 1)     AS avg_delivery_days,
    ROUND(AVG(days_vs_estimate), 1)         AS avg_days_vs_estimate,
    -- Review score distribution
    COUNT(CASE WHEN review_score = 5 THEN 1 END)  AS score_5,
    COUNT(CASE WHEN review_score = 4 THEN 1 END)  AS score_4,
    COUNT(CASE WHEN review_score = 3 THEN 1 END)  AS score_3,
    COUNT(CASE WHEN review_score = 2 THEN 1 END)  AS score_2,
    COUNT(CASE WHEN review_score = 1 THEN 1 END)  AS score_1,
    ROUND(
        COUNT(CASE WHEN review_score >= 4 THEN 1 END)::FLOAT
        / COUNT(*) * 100, 1
    )                                       AS positive_review_pct
FROM order_features
GROUP BY 1
ORDER BY avg_review_score DESC;
