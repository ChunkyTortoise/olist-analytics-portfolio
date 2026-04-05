-- ============================================================
-- Business Question: What share of customers buy more than once?
-- How does revenue differ between one-time and repeat buyers?
--
-- Uses anti-join pattern to cleanly separate one-time vs repeat buyers.
-- Insight target: Repeat customers typically generate 3-5x the LTV
-- of one-time buyers in e-commerce.
-- ============================================================

WITH customer_purchase_counts AS (
    SELECT
        c.customer_unique_id,
        COUNT(DISTINCT o.order_id)  AS purchase_count,
        ROUND(SUM(oi.price), 2)     AS total_spent,
        MIN(o.order_purchase_timestamp) AS first_purchase,
        MAX(o.order_purchase_timestamp) AS last_purchase
    FROM orders o
    JOIN customers c USING (customer_id)
    JOIN order_items oi USING (order_id)
    WHERE o.order_status = 'delivered'
    GROUP BY 1
),
segmented AS (
    SELECT
        customer_unique_id,
        purchase_count,
        total_spent,
        first_purchase,
        last_purchase,
        DATEDIFF('day', first_purchase, last_purchase) AS days_active,
        CASE
            WHEN purchase_count = 1  THEN 'One-Time Buyer'
            WHEN purchase_count = 2  THEN 'Second Purchase'
            WHEN purchase_count <= 5 THEN 'Regular (3-5x)'
            ELSE 'Power Buyer (6+)'
        END AS buyer_segment
    FROM customer_purchase_counts
)
SELECT
    buyer_segment,
    COUNT(*)                                AS customer_count,
    ROUND(COUNT(*)::FLOAT / SUM(COUNT(*)) OVER () * 100, 1) AS pct_of_customers,
    ROUND(AVG(total_spent), 2)              AS avg_lifetime_value,
    ROUND(AVG(purchase_count), 1)           AS avg_purchase_count,
    ROUND(AVG(days_active), 0)              AS avg_days_active,
    ROUND(SUM(total_spent), 2)              AS segment_total_revenue,
    ROUND(SUM(total_spent) / SUM(SUM(total_spent)) OVER () * 100, 1) AS pct_of_revenue
FROM segmented
GROUP BY 1
ORDER BY avg_lifetime_value DESC;
