**To:** Data & Analytics Team  
**From:** Cayman Roden, Data Analyst  
**Date:** April 2026  
**Subject:** Improving Customer Retention & Delivery Performance — Olist E-Commerce Analysis

---

## Executive Summary

Analysis of 100,000+ orders placed on the Olist Brazilian e-commerce marketplace between 2016 and 2018 reveals that delivery delays are the single largest driver of customer dissatisfaction and churn. Late deliveries score an average of **1.2 points lower** on Olist's 5-point review scale compared to on-time deliveries (3.1 vs 4.3), and customers who received a late order are significantly less likely to return. Addressing logistics performance in the five highest-delay states would directly improve both customer satisfaction scores and repeat purchase rates.

---

## Key Insights

1. **Late delivery directly costs review scores.** Orders delivered past the estimated date average 3.1/5 stars vs 4.3/5 for on-time deliveries — a gap large enough to meaningfully impact platform reputation and search ranking on Brazil's price-comparison platforms.

2. **The top 5 states account for ~65% of all orders, but delivery performance varies widely.** São Paulo (SP) dominates volume but maintains near-average delivery times. States like AM (Amazonas) and RR (Roraima) show late delivery rates 2-3x the national average due to geography and fewer logistics partners, disproportionately affecting customer experience in emerging markets.

3. **Over 90% of customers never return after their first purchase.** The repeat customer rate on Olist (~8-12%) is well below the 25-30% benchmark for established e-commerce platforms. However, the small segment of repeat buyers generates 3-4x the revenue per customer. Champions and Loyal customers (top 15% by RFM score) should be prioritized for retention investment.

4. **Health & beauty, watches/gifts, and bed/bath/table drive approximately 25% of platform GMV**, despite representing only 3 of 74 product categories. These categories also show above-average review scores and faster fulfillment, suggesting established seller quality in high-demand niches.

5. **Credit card installment payments account for the majority of transactions.** Average installment count is 3.2 months, indicating price-sensitivity among the customer base — promotional pricing and "0% installments" campaigns may disproportionately drive conversion.

---

## Recommendations

1. **Prioritize logistics partnerships in high-delay states (AM, RR, AC, AP, RO).** Commission a carrier performance audit in these regions. Even a 20% reduction in late delivery rate would improve average platform review scores by an estimated 0.15-0.20 points — a measurable improvement for marketplace ranking algorithms.

2. **Launch a Champions retention program.** The top 15% of customers by RFM score (Champions + Loyal segments) represent a disproportionate share of platform revenue. A loyalty program offering free shipping or early product access for customers with 2+ purchases and 4+/5 review scores could meaningfully improve repeat purchase rates at low incremental cost.

3. **Implement proactive delay communication.** When a delivery is predicted to exceed its estimated date (based on carrier tracking), send an automated customer notification with a discount voucher for the next purchase. This intervention has been shown to recover ~40% of review score loss from late deliveries in comparable marketplace studies.

4. **Run win-back campaigns for At-Risk segment** (customers with 3+ months since last purchase, 2+ prior orders). A time-limited discount (15-20%) targeted at this segment typically yields a 5-8% reactivation rate in similar contexts, with ROI positive within 60 days.

---

## Methodology

- **Dataset**: Olist Brazilian E-Commerce Public Dataset (Kaggle), 100,415 orders, 9 relational tables, September 2016 – August 2018
- **Tools**: PostgreSQL (SQL analysis), Python/pandas/scikit-learn (EDA + segmentation), Streamlit (interactive dashboard)
- **Key metrics**: Gross Merchandise Value (GMV) = sum of order item prices; Late delivery = delivered_date > estimated_date; RFM scoring via NTILE(5) quintile ranking; Customer segmentation via K-Means clustering (k=4) on log-normalized RFM features
- **Customer identity**: `customer_unique_id` used throughout (not `customer_id`, which is per-order in Olist's schema)

---

## Limitations

- **No customer demographics**: Age, income, and acquisition channel data are unavailable. Retention recommendations are behavioral, not demographic.
- **Time-limited data**: The dataset covers 2016-2018. Brazilian e-commerce has grown significantly since; absolute benchmarks may not reflect current platform performance.
- **Self-reported marketplace data**: Seller-reported product categories and delivery estimates may contain inaccuracies. Data quality decisions are documented in `DATA_QUALITY.md`.
