-- Exploratory SQL: "where and why are deliveries late?"
--
-- Grain matters here: fact_order_items has one row per order ITEM.
-- late_delivery_risk (and other order-level fields) is constant across
-- all items in the same order, so aggregating it directly at item-grain
-- double/triple-counts multi-item orders and skews the rate.
-- Queries measuring order-level facts (late rate, delivery status) use
-- v_orders (one row per order, from 03_order_view.sql -- run that first).
-- Queries measuring item-level facts (sales, product, discount) correctly
-- use fact_order_items directly, since those DO vary per item.

-- Q1. Late-delivery rate by region [ORDER-GRAIN]
SELECT
    g.order_region,
    COUNT(*)                                     AS n_orders,
    ROUND(AVG(v.late_delivery_risk)::numeric, 3) AS late_rate
FROM v_orders v
JOIN dim_geography g ON g.geography_id = v.geography_id
GROUP BY g.order_region
ORDER BY late_rate DESC;

-- Q2. Late-delivery rate by shipping mode [ORDER-GRAIN]
SELECT
    sm.shipping_mode,
    COUNT(*)                                     AS n_orders,
    ROUND(AVG(v.late_delivery_risk)::numeric, 3) AS late_rate
FROM v_orders v
JOIN dim_shipping_mode sm ON sm.shipping_mode_id = v.shipping_mode_id
GROUP BY sm.shipping_mode
ORDER BY late_rate DESC;

-- Q3. Region x shipping mode cross-tab [ORDER-GRAIN]
SELECT
    g.order_region,
    sm.shipping_mode,
    COUNT(*)                                     AS n_orders,
    ROUND(AVG(v.late_delivery_risk)::numeric, 3) AS late_rate
FROM v_orders v
JOIN dim_geography g      ON g.geography_id = v.geography_id
JOIN dim_shipping_mode sm ON sm.shipping_mode_id = v.shipping_mode_id
GROUP BY g.order_region, sm.shipping_mode
ORDER BY g.order_region, late_rate DESC;

-- Q3b. Average order value by region x shipping mode [ITEM-GRAIN,
-- summed to order level first, since "order value" = sum of its items]
SELECT
    g.order_region,
    sm.shipping_mode,
    ROUND(AVG(order_totals.total_sales)::numeric, 2) AS avg_order_value
FROM (
    SELECT order_id, geography_id, shipping_mode_id, SUM(sales) AS total_sales
    FROM fact_order_items
    GROUP BY order_id, geography_id, shipping_mode_id
) order_totals
JOIN dim_geography g      ON g.geography_id = order_totals.geography_id
JOIN dim_shipping_mode sm ON sm.shipping_mode_id = order_totals.shipping_mode_id
GROUP BY g.order_region, sm.shipping_mode
ORDER BY g.order_region;

-- Q4. Does order size correlate with late risk? [ORDER-GRAIN]
SELECT
    CASE
        WHEN total_sales < 100 THEN '<100'
        WHEN total_sales < 300 THEN '100-300'
        WHEN total_sales < 600 THEN '300-600'
        ELSE '600+'
    END AS sales_bucket,
    COUNT(*)                                    AS n_orders,
    ROUND(AVG(late_delivery_risk)::numeric, 3)  AS late_rate
FROM (
    SELECT f.order_id, SUM(f.sales) AS total_sales, v.late_delivery_risk
    FROM fact_order_items f
    JOIN v_orders v ON v.order_id = f.order_id
    GROUP BY f.order_id, v.late_delivery_risk
) order_sales
GROUP BY sales_bucket
ORDER BY MIN(total_sales);

-- Q5. Product category worst offenders [ITEM-GRAIN -- correct as-is]
SELECT
    p.category_name,
    COUNT(*)                                     AS n_order_items,
    ROUND(AVG(f.late_delivery_risk)::numeric, 3) AS late_rate
FROM fact_order_items f
JOIN dim_product p ON p.product_card_id = f.product_card_id
GROUP BY p.category_name
HAVING COUNT(*) >= 200
ORDER BY late_rate DESC
LIMIT 10;

-- Q6. Late-delivery rate by weekday shipped [ORDER-GRAIN]
SELECT
    d.weekday,
    COUNT(*)                                     AS n_orders,
    ROUND(AVG(v.late_delivery_risk)::numeric, 3) AS late_rate
FROM v_orders v
JOIN dim_date d ON d.date_id = v.shipping_date_id
GROUP BY d.weekday
ORDER BY late_rate DESC;











