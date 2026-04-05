-- ============================================================
-- Business Question: How is monthly revenue trending?
-- What is month-over-month and year-over-year growth?
--
-- Insight target: Identify peak months, growth inflection points,
-- and seasonal patterns to guide inventory and marketing planning.
-- ============================================================

WITH monthly_rev AS (
    SELECT
        DATE_TRUNC('month', o.order_purchase_timestamp) AS month,
        COUNT(DISTINCT o.order_id)                      AS order_count,
        SUM(oi.price)                                   AS revenue,
        SUM(oi.price + oi.freight_value)                AS gmv
    FROM orders o
    JOIN order_items oi USING (order_id)
    WHERE o.order_status = 'delivered'
    GROUP BY 1
)
SELECT
    month,
    order_count,
    ROUND(revenue, 2)                                                          AS revenue,
    ROUND(gmv, 2)                                                              AS gmv,
    LAG(revenue) OVER (ORDER BY month)                                         AS prev_month_revenue,
    ROUND(
        (revenue - LAG(revenue) OVER (ORDER BY month))
        / NULLIF(LAG(revenue) OVER (ORDER BY month), 0) * 100, 1
    )                                                                          AS mom_growth_pct,
    ROUND(
        (revenue - LAG(revenue, 12) OVER (ORDER BY month))
        / NULLIF(LAG(revenue, 12) OVER (ORDER BY month), 0) * 100, 1
    )                                                                          AS yoy_growth_pct,
    ROUND(AVG(revenue) OVER (
        ORDER BY month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ), 2)                                                                      AS revenue_3mo_avg
FROM monthly_rev
ORDER BY month;
