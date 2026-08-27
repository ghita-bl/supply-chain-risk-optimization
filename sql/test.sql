SELECT
    sm.shipping_mode,
    COUNT(*)                                     AS n_orders,
    ROUND(AVG(v.late_delivery_risk)::numeric, 3) AS late_rate
FROM v_orders v
JOIN dim_shipping_mode sm ON sm.shipping_mode_id = v.shipping_mode_id
GROUP BY sm.shipping_mode
ORDER BY late_rate DESC;

-- shipping_mode  | n_orders | late_rate 
----------------+----------+-----------
   --  First Class    |    10079 |     0.953
   -- Second Class   |    12778 |     0.767
   -- Same Day       |     3571 |     0.461
   -- Standard Class |    39324 |     0.381
    --(4 rows) 

-- why first class is the highest ???

SELECT sm.shipping_mode,
       ROUND(AVG(order_days.days_real)::numeric, 2) AS avg_actual_days,
       ROUND(AVG(order_days.days_sched)::numeric, 2) AS avg_scheduled_days
FROM (
    SELECT DISTINCT ON (order_id)
        order_id,
        shipping_mode_id,
        days_for_shipping_real AS days_real,
        days_for_shipment_sched AS days_sched
    FROM fact_order_items
    ORDER BY order_id
) order_days
JOIN dim_shipping_mode sm ON sm.shipping_mode_id = order_days.shipping_mode_id
GROUP BY sm.shipping_mode;


SELECT
    g.order_region,
    sm.shipping_mode,
    COUNT(*) AS n_orders,
    ROUND(AVG(v.late_delivery_risk)::numeric, 3) AS late_rate
FROM v_orders v
JOIN dim_geography g      ON g.geography_id = v.geography_id
JOIN dim_shipping_mode sm ON sm.shipping_mode_id = v.shipping_mode_id
WHERE g.order_region IN (
    'Canada', 'Central Africa', 'Central Asia', 'Eastern Europe', 'South of  USA '
)
GROUP BY g.order_region, sm.shipping_mode
ORDER BY g.order_region, sm.shipping_mode;

--Same Day is used rarely enough everywhere 
--that we don't have strong statistical confidence in its true late rate for any single region — the current apparent regional advantages are more likely small-sample variation than a genuine pattern.