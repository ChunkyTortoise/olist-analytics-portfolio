-- ============================================================
-- Business Question: Which product categories drive the most revenue?
-- Are high-revenue categories also high-volume, or are there niche
-- high-value categories?
--
-- Insight target: Identify the 80/20 -- typically 3-5 categories
-- drive 50%+ of revenue in e-commerce marketplaces.
-- ============================================================

WITH category_metrics AS (
    SELECT
        COALESCE(t.product_category_name_english, 'other') AS category,
        COUNT(DISTINCT o.order_id)                          AS order_count,
        COUNT(DISTINCT c.customer_unique_id)                AS unique_customers,
        ROUND(SUM(oi.price), 2)                             AS revenue,
        ROUND(AVG(oi.price), 2)                             AS avg_item_price,
        ROUND(AVG(r.review_score), 2)                       AS avg_review_score
    FROM order_items oi
    JOIN orders o USING (order_id)
    JOIN customers c USING (customer_id)
    JOIN products p USING (product_id)
    LEFT JOIN product_category_name_translation t
        ON p.product_category_name = t.product_category_name
    LEFT JOIN order_reviews r USING (order_id)
    WHERE o.order_status = 'delivered'
    GROUP BY 1
)
SELECT
    category,
    order_count,
    unique_customers,
    revenue,
    avg_item_price,
    avg_review_score,
    DENSE_RANK() OVER (ORDER BY revenue DESC)           AS revenue_rank,
    ROUND(revenue / SUM(revenue) OVER () * 100, 2)     AS revenue_share_pct,
    ROUND(SUM(revenue) OVER (
        ORDER BY revenue DESC
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) / SUM(revenue) OVER () * 100, 1)                 AS cumulative_revenue_pct
FROM category_metrics
ORDER BY revenue_rank;
