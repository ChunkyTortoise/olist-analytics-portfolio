-- ============================================================
-- Business Question: What percentage of customers return to buy again?
-- How does retention curve look at 1, 3, 6, and 12 months?
--
-- Key: Uses customer_unique_id (NOT customer_id) because customer_id
-- is per-order in Olist. customer_unique_id tracks the same person
-- across multiple purchases.
--
-- Insight target: Typical Olist retention is <15% repeat rate --
-- context benchmark for a Brazilian marketplace (2016-2018).
-- ============================================================

WITH first_purchase AS (
    -- Assign each unique customer to their first purchase month (cohort)
    SELECT
        c.customer_unique_id,
        DATE_TRUNC('month', MIN(o.order_purchase_timestamp)) AS cohort_month
    FROM orders o
    JOIN customers c USING (customer_id)
    WHERE o.order_status = 'delivered'
    GROUP BY 1
),
cohort_sizes AS (
    SELECT cohort_month, COUNT(*) AS cohort_size
    FROM first_purchase
    GROUP BY 1
),
customer_activity AS (
    -- Every purchase a unique customer made, tagged with their cohort
    SELECT
        fp.customer_unique_id,
        fp.cohort_month,
        DATE_TRUNC('month', o.order_purchase_timestamp) AS activity_month
    FROM orders o
    JOIN customers c USING (customer_id)
    JOIN first_purchase fp USING (customer_unique_id)
    WHERE o.order_status = 'delivered'
),
retention_counts AS (
    SELECT
        cohort_month,
        -- Months elapsed since cohort acquisition (0 = first month)
        CAST(
            (EXTRACT(YEAR FROM activity_month) - EXTRACT(YEAR FROM cohort_month)) * 12
            + (EXTRACT(MONTH FROM activity_month) - EXTRACT(MONTH FROM cohort_month))
        AS INTEGER)                                AS months_since_first_purchase,
        COUNT(DISTINCT customer_unique_id)         AS active_customers
    FROM customer_activity
    GROUP BY 1, 2
)
SELECT
    rc.cohort_month,
    cs.cohort_size,
    rc.months_since_first_purchase,
    rc.active_customers,
    ROUND(rc.active_customers::FLOAT / cs.cohort_size * 100, 1) AS retention_pct
FROM retention_counts rc
JOIN cohort_sizes cs USING (cohort_month)
WHERE rc.months_since_first_purchase <= 12
ORDER BY rc.cohort_month, rc.months_since_first_purchase;
