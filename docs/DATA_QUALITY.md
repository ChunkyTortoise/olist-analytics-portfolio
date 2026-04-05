# Data Quality Documentation

Follows the PMC three-phase framework (pre-cleaning, operations, post-cleaning).

---

## Phase 1: Pre-Cleaning Assessment

Raw CSV row counts and null rates as loaded from Kaggle:

| Table | Raw Rows | Null Rate (key cols) | Notes |
|-------|----------|---------------------|-------|
| orders | 99,441 | 3.8% (delivered_date) | Expected: non-delivered orders have no delivery date |
| customers | 99,441 | 0% | Clean |
| order_items | 112,650 | 0% | Multiple items per order |
| order_payments | 103,886 | 0% | Multiple payments per order |
| order_reviews | 98,410 | 58% (comment_message) | Expected: reviews without comments |
| products | 32,951 | 1.2% (product_weight_g) | Physical attribute missings |
| sellers | 3,095 | 0% | Clean |
| geolocation | 1,000,163 | 0% | ~2.4M rows, many duplicates per zip prefix |
| product_category_name_translation | 71 | 0% | 3 categories in products table NOT in translation table |

### Known Issues Identified Pre-Cleaning

1. **3 untranslatable product categories**: `pc_gamer`, `portateis_cozinha_e_preparadores_de_alimentos`, and 1 null record not present in translation table.
2. **Geolocation duplicates**: Multiple lat/lng entries per zip code prefix (~14 per prefix on average).
3. **Order status variety**: 8 distinct statuses (`delivered`, `shipped`, `canceled`, `unavailable`, `invoiced`, `processing`, `created`, `approved`) -- most analyses should filter to `delivered` only.
4. **Order reviews with no corresponding delivery**: Some reviews exist for non-delivered orders; join carefully.

---

## Phase 2: Cleaning Operations

### 2.1 Orders Filtered

| Decision | Rows Affected | Criterion | Rationale |
|----------|--------------|-----------|-----------|
| Keep only `delivered` status | ~2,800 removed | order_status != 'delivered' | Undelivered orders have no delivery metrics; including them would distort RFM and delivery analysis |
| Remove null delivery timestamps | ~1,100 removed | order_delivered_customer_date IS NULL | Cannot compute delivery_days without delivery date |
| Remove null purchase timestamps | <50 removed | order_purchase_timestamp IS NULL | Data integrity check |

**Net effect**: ~96,478 orders retained from 99,441 raw orders.

### 2.2 Product Category Translation

| Decision | Rows Affected | Method | Rationale |
|----------|--------------|--------|-----------|
| Fill untranslatable categories | 3 categories | Replace with 'other' | Categories `pc_gamer` and kitchen-prep category have no English translation; negligible volume (~200 orders total) |
| Fill null product_category_name | ~6 products | Replace with 'other' | Products with no category assigned |

### 2.3 Geolocation Deduplication

| Decision | Rows Affected | Method | Rationale |
|----------|--------------|--------|-----------|
| Deduplicate geolocation by zip prefix | ~986,000 removed | Keep first occurrence per geolocation_zip_code_prefix | Geolocation table is used only for geographic visualization; exact coordinate precision is not required |

### 2.4 Product Physical Attributes

| Decision | Rows Affected | Method | Rationale |
|----------|--------------|--------|-----------|
| Fill null product_weight_g | ~361 rows (1.1%) | Impute with category-level median | Weight needed for freight analysis; category-median is a reasonable proxy |

### 2.5 Review Join

| Decision | Rationale |
|----------|-----------|
| LEFT JOIN on order_reviews | Some delivered orders have no review (~1,031 = 1.1%). These are retained in the master table with NULL review_score. Review analysis excludes NULLs. |

---

## Phase 3: Post-Cleaning State

### Final Row Counts

| File | Rows | Notes |
|------|------|-------|
| `olist_master.parquet` | ~112,000 | Line-item level (one row per order_item, not per order) |
| Unique order IDs | ~96,478 | Delivered orders with complete timestamps |
| Unique customer_unique_ids | ~95,000 | For RFM/cohort analysis |

### Validated Ranges

| Column | Expected Range | Validated |
|--------|----------------|-----------|
| price | R$0.85 – R$6,735 | Yes; outliers retained (legitimate high-value items) |
| days_to_deliver | 0 – 209 days | Values >60 days are extreme but valid (remote regions) |
| review_score | 1 – 5 | Yes |
| is_late_delivery | 0 or 1 | Yes |
| customer_state | 27 Brazilian states | Yes |

### Known Residual Issues

1. **Some orders show 0-day delivery** (same-day): 47 orders with `days_to_deliver = 0`. Likely data entry issues. Retained but flagged; exclude from delivery time analysis if computing minimum benchmarks.
2. **Review score lag**: Some reviews submitted weeks after delivery may not reflect delivery experience. Cannot isolate this without review timestamp join in analysis.
3. **Geolocation is approximate**: Using first-occurrence of zip prefix for lat/lng introduces coordinate imprecision of ~1-5km. Sufficient for state-level analysis; not suitable for hyper-local routing analysis.
