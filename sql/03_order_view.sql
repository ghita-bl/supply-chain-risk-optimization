-- One row per order (not per order item), for questions where
-- double-counting multi-item orders would skew the answer
-- (e.g. late-delivery rate, since late_delivery_risk is constant
-- across all items in the same order).
--
-- Uses DISTINCT ON, which keeps the first row per order_id based
-- on the ORDER BY that follows it -- here we just need any one row
-- since late_delivery_risk/region/etc. are identical across an
-- order's items anyway.

CREATE OR REPLACE VIEW v_orders AS
SELECT DISTINCT ON (order_id)
    order_id,
    geography_id,
    shipping_mode_id,
    order_date_id,
    shipping_date_id,
    late_delivery_risk,
    delivery_status,
    order_status,
    payment_type
FROM fact_order_items
ORDER BY order_id;