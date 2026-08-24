-- Supply chain case: schema
-- Star-schema-ish layout: one wide staging table, then dims + fact
-- built from it. Keeping the staging table lets you re-derive the
-- model without re-parsing the raw CSV every time.

DROP TABLE IF EXISTS stg_orders CASCADE;
CREATE TABLE stg_orders (
    row_id                    INT,
    order_id                  INT,
    order_item_id             INT,
    order_date                DATE,
    shipping_date             DATE,
    shipping_mode             TEXT,
    days_for_shipping_real    INT,
    days_for_shipment_sched   INT,
    late_delivery_risk        INT,
    delivery_status           TEXT,
    order_status              TEXT,
    payment_type              TEXT,
    

    -- customer
    customer_id               INT,
    order_customer_id           INT,
    customer_segment          TEXT,
    customer_city             TEXT,
    customer_state            TEXT,
    customer_country          TEXT,
   

    -- product
    product_card_id           INT,
    product_name              TEXT,
    product_price             NUMERIC,
    product_status            INT,
    category_id               INT,
    category_name             TEXT,
    department_id             INT,
    department_name           TEXT,

    -- order geography
    order_city                TEXT,
    order_state                TEXT,
    order_country              TEXT,
    order_region                TEXT,
    market                      TEXT,

    -- order-item facts
    sales                     NUMERIC,
    sales_per_customer        NUMERIC,
    order_item_quantity        INT,
    order_item_discount        NUMERIC,
    order_item_discount_rate   NUMERIC,
    order_item_product_price   NUMERIC,
    order_item_profit_ratio    NUMERIC,
    order_item_total           NUMERIC,
    order_profit_per_order     NUMERIC,
    benefit_per_order          NUMERIC
);

DROP TABLE IF EXISTS dim_customer CASCADE;
CREATE TABLE dim_customer(
    customer_id  INT PRIMARY KEY,
    customer_segment TEXT,
    customer_city TEXT,
    customer_state TEXT,
    customer_country TEXT
);

DROP TABLE IF EXISTS dim_product CASCADE;
CREATE TABLE dim_product(
    product_card_id INT PRIMARY KEY,
    product_price NUMERIC,
    product_name TEXT,
    product_status INT,
    category_id INT,
    category_name TEXT,
    department_id INT,
    department_name TEXT
);

DROP TABLE IF EXISTS dim_geography CASCADE;
CREATE TABLE dim_geography(
    geography_id SERIAL PRIMARY KEY,
    order_city TEXT,
    order_state TEXT,
    order_country TEXT,
    order_region TEXT,
    market TEXT,
    UNIQUE (order_city, order_state, order_country, order_region, market)
);

DROP TABLE IF EXISTS dim_shipping_mode CASCADE;
CREATE TABLE dim_shipping_mode(
    shipping_mode_id SERIAL PRIMARY KEY,
    shipping_mode TEXT UNIQUE
);


DROP TABLE IF EXISTS dim_date CASCADE;
CREATE TABLE dim_date(
    date_id SERIAL PRIMARY KEY,
    full_date DATE UNIQUE,
    year INT,
    month INT,
    day INT,
    weekday TEXT
);

DROP TABLE IF EXISTS fact_order_items CASCADE;
CREATE TABLE fact_order_items(
    order_item_id           INT PRIMARY KEY,
    order_id                INT,

    -- foreign keys to dimensions
    customer_id             INT REFERENCES dim_customer(customer_id),
    product_card_id         INT REFERENCES dim_product(product_card_id),
    geography_id            INT REFERENCES dim_geography(geography_id),
    shipping_mode_id        INT REFERENCES dim_shipping_mode(shipping_mode_id),
    order_date_id           INT REFERENCES dim_date(date_id),
    shipping_date_id        INT REFERENCES dim_date(date_id),

    -- shipping / delivery facts
    days_for_shipping_real  INT,
    days_for_shipment_sched INT,
    late_delivery_risk      INT,
    delivery_status         TEXT,
    order_status            TEXT,

    -- numeric measures 
    sales                   NUMERIC,
    sales_per_customer      NUMERIC,
    order_item_quantity     INT,
    order_item_discount     NUMERIC,
    order_item_discount_rate NUMERIC,
    order_item_product_price NUMERIC,
    order_item_profit_ratio NUMERIC,
    order_item_total        NUMERIC,
    order_profit_per_order  NUMERIC,
    benefit_per_order       NUMERIC,
    payment_type TEXT
);

CREATE INDEX idx_fact_customer ON fact_order_items(customer_id);
CREATE INDEX idx_fact_product ON fact_order_items(product_card_id);
CREATE INDEX idx_fact_geography ON fact_order_items(geography_id);
CREATE INDEX idx_fact_shipping_mode ON fact_order_items(shipping_mode_id);
CREATE INDEX idx_fact_late_delivery ON fact_order_items(late_delivery_risk);
