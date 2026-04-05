-- ============================================================
-- Business Question: Who are our most valuable customers?
-- How do customers segment by Recency, Frequency, and Monetary value?
--
-- Uses NTILE(5) to assign quintile scores 1-5 per dimension.
-- Note: For RFM, Recency score is INVERTED (lower recency days = higher score).
--
-- Insight target: Identify Champions (555), At-Risk (low F+M),
-- and Hibernating segments for targeted marketing.
-- ============================================================

WITH reference_date AS (
    -- Day after the last recorded order (snapshot point)
    SELECT MAX(order_purchase_timestamp)::DATE + INTERVAL '1 day' AS ref_date
    FROM orders
    WHERE order_status = 'delivered'
),
customer_orders AS (
    SELECT
        c.customer_unique_id,
        MAX(o.order_purchase_timestamp)::DATE          AS last_purchase_date,
        COUNT(DISTINCT o.order_id)                     AS frequency,
        SUM(oi.price)                                  AS monetary
    FROM orders o
    JOIN customers c USING (customer_id)
    JOIN order_items oi USING (order_id)
    WHERE o.order_status = 'delivered'
    GROUP BY 1
),
rfm_raw AS (
    SELECT
        co.customer_unique_id,
        DATEDIFF('day', co.last_purchase_date, rd.ref_date) AS recency_days,
        co.frequency,
        ROUND(co.monetary, 2)                               AS monetary
    FROM customer_orders co
    CROSS JOIN reference_date rd
),
rfm_scored AS (
    SELECT
        customer_unique_id,
        recency_days,
        frequency,
        monetary,
        -- Recency: lower days = better = higher score (inverted NTILE)
        6 - NTILE(5) OVER (ORDER BY recency_days ASC)  AS r_score,
        NTILE(5) OVER (ORDER BY frequency ASC)         AS f_score,
        NTILE(5) OVER (ORDER BY monetary ASC)          AS m_score
    FROM rfm_raw
)
SELECT
    customer_unique_id,
    recency_days,
    frequency,
    monetary,
    r_score,
    f_score,
    m_score,
    CONCAT(r_score::TEXT, f_score::TEXT, m_score::TEXT) AS rfm_segment,
    (r_score + f_score + m_score)                       AS rfm_total_score,
    CASE
        WHEN r_score >= 4 AND f_score >= 4 AND m_score >= 4 THEN 'Champions'
        WHEN r_score >= 3 AND f_score >= 3                  THEN 'Loyal Customers'
        WHEN r_score >= 4 AND f_score <= 2                  THEN 'Recent New Customers'
        WHEN r_score <= 2 AND f_score >= 3 AND m_score >= 3 THEN 'At-Risk'
        WHEN r_score <= 2 AND f_score <= 2                  THEN 'Hibernating'
        ELSE 'Promising'
    END                                                 AS segment_label
FROM rfm_scored
ORDER BY rfm_total_score DESC;
