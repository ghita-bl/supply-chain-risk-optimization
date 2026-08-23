import os
import sys
from sqlalchemy import text

sys.path.insert(0,os.path.dirname(__file__))
from db import get_engine

def main():
    engine=get_engine()
    with engine.begin() as connection:
        connection.execute(text("""
               INSERT INTO dim_customer (customer_id, customer_segment, customer_city,
                                       customer_state, customer_country)
            SELECT DISTINCT customer_id, customer_segment, customer_city,
                             customer_state, customer_country
            FROM stg_orders
            WHERE customer_id IS NOT NULL
            ON CONFLICT (customer_id) DO NOTHING;
        """))
        print("dim_customer populated.")

        connection.execute(text("""
                    INSERT INTO dim_product (product_card_id, product_price, product_name,
                                      product_status, category_id, category_name,
                                      department_id, department_name)
            SELECT DISTINCT product_card_id, product_price, product_name,
                             product_status, category_id, category_name,
                             department_id, department_name
            FROM stg_orders
            WHERE product_card_id IS NOT NULL
            ON CONFLICT (product_card_id) DO NOTHING;
        """))
        print("dim_product populated")

        connection.execute(text("""
        INSERT INTO dim_geography (order_city, order_state, order_country, order_region, market )
        SELECT DISTINCT order_city, order_state, order_country, order_region, market
        FROM stg_orders
        ON CONFLICT (order_city, order_state, order_country, order_region, market) DO NOTHING;
        """))
        print("dim_geography populated")

        connection.execute(text("""
        INSERT INTO dim_shipping_mode (shipping_mode)
        SELECT DISTINCT shipping_mode
        FROM stg_orders
        WHERE shipping_mode IS NOT NULL
        ON CONFLICT (shipping_mode) DO NOTHING;
        """))
        print("dim_shipping_mode populated.")

        connection.execute(text("""
            INSERT INTO dim_date (full_date, year, month, day, weekday)
            SELECT DISTINCT d::date AS full_date,
                   EXTRACT(YEAR FROM d)::int AS year,
                   EXTRACT(MONTH FROM d)::int AS month,
                   EXTRACT(DAY FROM d)::int AS day,
                   TO_CHAR(d, 'FMDay') AS weekday
            FROM (
                SELECT order_date AS d FROM stg_orders WHERE order_date IS NOT NULL
                UNION
                SELECT shipping_date AS d FROM stg_orders WHERE shipping_date IS NOT NULL
            ) all_dates
            ON CONFLICT (full_date) DO NOTHING;
        """))
        print("dim_date populated.")

        connection.execute(text("""
            INSERT INTO fact_order_items (
                order_item_id, order_id, customer_id, product_card_id,
                geography_id, shipping_mode_id, order_date_id, shipping_date_id,
                days_for_shipping_real, days_for_shipment_sched, late_delivery_risk,
                delivery_status, order_status, sales, sales_per_customer,
                order_item_quantity, order_item_discount, order_item_discount_rate,
                order_item_product_price, order_item_profit_ratio, order_item_total,
                order_profit_per_order, benefit_per_order, payment_type
            )
            SELECT
                s.order_item_id,
                s.order_id,
                s.customer_id,
                s.product_card_id,
                g.geography_id,
                sm.shipping_mode_id,
                od.date_id AS order_date_id,
                sd.date_id AS shipping_date_id,
                s.days_for_shipping_real,
                s.days_for_shipment_sched,
                s.late_delivery_risk,
                s.delivery_status,
                s.order_status,
                s.sales,
                s.sales_per_customer,
                s.order_item_quantity,
                s.order_item_discount,
                s.order_item_discount_rate,
                s.order_item_product_price,
                s.order_item_profit_ratio,
                s.order_item_total,
                s.order_profit_per_order,
                s.benefit_per_order,
                s.payment_type
            FROM stg_orders s
            LEFT JOIN dim_geography g
                ON g.order_city = s.order_city
               AND g.order_state = s.order_state
               AND g.order_country = s.order_country
               AND g.order_region = s.order_region
               AND g.market = s.market
            LEFT JOIN dim_shipping_mode sm ON sm.shipping_mode = s.shipping_mode
            LEFT JOIN dim_date od ON od.full_date = s.order_date::date
            LEFT JOIN dim_date sd ON sd.full_date = s.shipping_date::date
            ON CONFLICT (order_item_id) DO NOTHING;
        """))
        print("fact_order_items populated.")
 
    print("Done.")
 
 
if __name__ == "__main__":
    main()
 





