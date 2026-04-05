-- ============================================================
-- Business Question: How do customers pay, and does payment method
-- affect order value or customer behavior?
--
-- Brazil context: "parcelamento" (installment) culture is dominant.
-- High installment use signals customers are credit-constrained --
-- relevant for pricing and promotional strategy.
-- ============================================================

SELECT
    payment_type,
    COUNT(DISTINCT order_id)                            AS order_count,
    ROUND(SUM(payment_value), 2)                        AS total_revenue,
    ROUND(AVG(payment_value), 2)                        AS avg_payment_value,
    ROUND(AVG(payment_installments), 1)                 AS avg_installments,
    COUNT(CASE WHEN payment_installments > 1 THEN 1 END) AS installment_orders,
    ROUND(
        COUNT(CASE WHEN payment_installments > 1 THEN 1 END)::FLOAT
        / COUNT(*) * 100, 1
    )                                                   AS installment_rate_pct,
    MAX(payment_installments)                           AS max_installments,
    -- Installment distribution
    COUNT(CASE WHEN payment_installments = 1  THEN 1 END) AS single_payment,
    COUNT(CASE WHEN payment_installments BETWEEN 2 AND 6  THEN 1 END) AS short_term_2_6,
    COUNT(CASE WHEN payment_installments > 6 THEN 1 END) AS long_term_7_plus
FROM order_payments
GROUP BY 1
ORDER BY order_count DESC;
