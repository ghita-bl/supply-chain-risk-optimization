"""
Statistical analysis: is late delivery significantly associated with
shipping mode, region, or order size?

Grain note: uses v_orders (one row per order), not fact_order_items
directly, since late_delivery_risk is constant per order and averaging
it at item-grain would double/triple-count multi-item orders.

Usage:
    python src/03_statistical_analysis.py
"""
import os
import sys
import pandas as pd
from scipy.stats import chi2_contingency
import statsmodels.formula.api as smf
from scipy.stats import ttest_ind


sys.path.insert(0, os.path.dirname(__file__))
from db import get_engine


 # df["actually_late"] = df["late_delivery_risk"]  despite the column name, this is the observed 0/1 outcome, not a risk score !!!!!!!!!!!!


#late delivery x region x shipping mode
def load_orders(engine):
    query = """
        SELECT v.late_delivery_risk, v.order_id,
               g.order_region, sm.shipping_mode
        FROM v_orders v
        JOIN dim_geography g      ON g.geography_id = v.geography_id
        JOIN dim_shipping_mode sm ON sm.shipping_mode_id = v.shipping_mode_id
    """
    return pd.read_sql(query, engine)


def load_order_sales(engine):
    # order value isn't on v_orders (it's an item-level fact, summed here)
    query = """
        SELECT order_id, SUM(sales) AS total_sales
        FROM fact_order_items
        GROUP BY order_id
    """
    return pd.read_sql(query, engine)


def chi_square_test(df, col, label="late_delivery_risk"):
    """Is `col` significantly associated with the late-delivery flag?"""
    contingency = pd.crosstab(df[col], df[label])
    chi2, p, dof, _ = chi2_contingency(contingency)
    print(f"{col}: chi2={chi2:.2f}, dof={dof}, p-value={p:.4g}")
    return chi2, p

def sales_ttest(df):
    late = df[df["late_delivery_risk"] == 1]["total_sales"].dropna()
    on_time = df[df["late_delivery_risk"] == 0]["total_sales"].dropna()
    t_stat, p_value = ttest_ind(late, on_time, equal_var=False)  # Welch's t-test
    print(f"total_sales: t={t_stat:.2f}, p-value={p_value:.4g}")
    print(f"  mean sales (late): {late.mean():.2f}, mean sales (on-time): {on_time.mean():.2f}")


def logistic_regression(df):
    """
    Interpretable model: which factors move the odds of late delivery,
    holding others constant?
    """
    model = smf.logit(
        "late_delivery_risk ~ C(shipping_mode) + C(order_region) + total_sales",
        data=df,
    ).fit()
    print(model.summary())
    return model


if __name__ == "__main__":
    engine = get_engine()
    orders = load_orders(engine)
    sales = load_order_sales(engine)
    df = orders.merge(sales, on="order_id", how="left")

    print(f"\nLoaded {len(df)} orders. Late-delivery rate: {df['late_delivery_risk'].mean():.3f}\n")

    print("--- Chi-square tests: association with late_delivery_risk ---")
    for col in ["shipping_mode", "order_region"]:
        chi_square_test(df, col)


    print("\n--- Independent t-test two sample for order size x late delivery ---")
    sales_ttest(df)    

    print("\n--- Logistic regression ---")
    logistic_regression(df)
