"""
Load the DataCo Smart Supply Chain CSV into a Postgres staging table.

Usage:
    python src/01_load_data.py --csv data/raw/DataCoSupplyChainDataset.csv

Env vars expected (or edit DB_URL below directly):
    PGHOST, PGPORT, PGDATABASE, PGUSER, PGPASSWORD
"""
import argparse
import os
import sys
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from db import get_engine

# The raw Kaggle file is usually latin-1 encoded, not utf-8 !!!
CSV_ENCODING = "latin-1"

# Map raw CSV column names -> our stg_orders schema.
# NOTE: verify these against your actual CSV header once downloaded —
# Kaggle versions of this dataset vary slightly in capitalization/spacing.
COLUMN_MAP = {
    "Days for shipping (real)":"days_for_shipping_real",
"Days for shipment (scheduled)"	:"days_for_shipment_sched",
"Benefit per order"	:"benefit_per_order",
"Sales per customer":	"sales_per_customer",
"Delivery Status":	"delivery_status",
"Late_delivery_risk":	"late_delivery_risk",
"Category Id":	"category_id",
"Category Name":	"category_name",
"Customer City":	"customer_city",
"Customer Country":	"customer_country",
"Customer Id":	"customer_id",
"Customer Segment":	"customer_segment",
"Customer State":	"customer_state",
"Department Id":	"department_id",
"Department Name":	"department_name",
"Market":	"market",
"Order City":	"order_city",
"Order Country":	"order_country",
"Order Customer Id":	"order_customer_id",
"order date (DateOrders)":	"order_date",
"Order Id":	"order_id",
"Order Item Discount":	"order_item_discount",
"Order Item Discount Rate":	"order_item_discount_rate",
"Order Item Id":	"order_item_id",
"Order Item Product Price":	"order_item_product_price",
"Order Item Profit Ratio":	"order_item_profit_ratio",
"Order Item Quantity":"order_item_quantity",
"Sales":"sales",
"Order Item Total":	"order_item_total",
"Order Profit Per Order":	"order_profit_per_order",
"Order Region":	"order_region",
"Order State":	"order_state",
"Order Status":	"order_status",
"Product Name":	"product_name",
"Product Price":	"product_price",
"Product Status":"product_status",
"shipping date (DateOrders)"	:"shipping_date",
"Shipping Mode":	"shipping_mode"

}


def main(csv_path: str):
    print(f"Reading {csv_path} ...")
    df = pd.read_csv(csv_path, encoding=CSV_ENCODING)

    missing = [c for c in COLUMN_MAP if c not in df.columns]
    if missing:
        print("WARNING - these expected columns were not found in the CSV:")
        for c in missing:
            print(f"  - {c}")
        print("Open the CSV header and fix COLUMN_MAP before continuing.")

    present_map = {k: v for k, v in COLUMN_MAP.items() if k in df.columns}
    df = df[list(present_map.keys())].rename(columns=present_map)

    df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")
    df["shipping_date"] = pd.to_datetime(df["shipping_date"], errors="coerce")

    engine = get_engine()
    print(f"Writing {len(df)} rows to stg_orders ...")
    df.to_sql("stg_orders", engine, if_exists="append", index=False, chunksize=5000)
    print("Done.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", required=True, help="Path to the raw CSV file")
    args = parser.parse_args()
    main(args.csv)
