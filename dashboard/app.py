"""
Streamlit MVP: Diagnose / Predict / Optimize.

Run with:
    streamlit run dashboard/app.py
"""
import os
import sys
import pandas as pd
import streamlit as st
import plotly.express as px

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from db import get_engine  # noqa: E402

st.set_page_config(page_title="Supply Chain Delivery Risk", layout="wide")
st.title("Supply Chain Delivery Risk — Case Dashboard")

engine = get_engine()

tab_diagnose, tab_predict, tab_optimize = st.tabs(
    ["Diagnose", "Predict", "Optimize"]
)

# ---------------------------------------------------------------- Diagnose
with tab_diagnose:
    st.subheader("Where is late delivery happening?")

    query = """
        SELECT g.order_region, sm.shipping_mode,
               COUNT(*) AS n_orders,
               AVG(v.late_delivery_risk::numeric) AS late_rate
        FROM v_orders v
        JOIN dim_geography g      ON g.geography_id = v.geography_id
        JOIN dim_shipping_mode sm ON sm.shipping_mode_id = v.shipping_mode_id
        GROUP BY g.order_region, sm.shipping_mode
    """
    df = pd.read_sql(query, engine)

    region_filter = st.multiselect(
        "Filter by region", options=sorted(df["order_region"].unique())
    )
    if region_filter:
        df = df[df["order_region"].isin(region_filter)]

    fig = px.bar(
        df, x="order_region", y="late_rate", color="shipping_mode",
        barmode="group", title="Late-delivery rate by region and shipping mode",
        labels={"late_rate": "Late-delivery rate", "order_region": "Region"},
    )
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(df.sort_values("late_rate", ascending=False), use_container_width=True)

# ----------------------------------------------------------------- Predict
with tab_predict:
    st.subheader("Risk score for a hypothetical order")

    model_path = os.path.join(os.path.dirname(__file__), "model.joblib")
    if not os.path.exists(model_path):
        st.warning(
            "No trained model found. Run `python src/04_predictive_model.py` "
            "first to generate dashboard/model.joblib."
        )
    else:
        import joblib
        model = joblib.load(model_path)

        regions = pd.read_sql(
            "SELECT DISTINCT order_region FROM dim_geography ORDER BY 1", engine
        )["order_region"].tolist()
        modes = pd.read_sql(
            "SELECT DISTINCT shipping_mode FROM dim_shipping_mode ORDER BY 1", engine
        )["shipping_mode"].tolist()

        col1, col2 = st.columns(2)
        with col1:
            region = st.selectbox("Region", regions)
            mode = st.selectbox("Shipping mode", modes)
        with col2:
            sales = st.number_input("Order value (total sales)", min_value=0.0, value=150.0)

        if st.button("Score this order"):
            X_new = pd.DataFrame([{
                "shipping_mode": mode,
                "order_region": region,
                "total_sales": sales,
            }])
            proba = model.predict_proba(X_new)[0, 1]
            st.metric("Predicted probability of late delivery", f"{proba:.1%}")
            if proba > 0.6:
                st.error("High risk — consider flagging for proactive customer communication.")
            elif proba > 0.4:
                st.warning("Moderate risk.")
            else:
                st.success("Low risk.")

# ---------------------------------------------------------------- Optimize
with tab_optimize:
    st.subheader("Recommended shipping-mode allocation")

    from importlib import import_module
    opt_module = import_module("05_optimization")

    budget = st.slider(
        "Cost budget index per order", min_value=1.0, max_value=4.0,
        value=1.5, step=0.1,
    )

    df_stats = opt_module.load_region_mode_stats(engine)
    df_stats, global_rate = opt_module.apply_shrinkage(df_stats)

    baseline_late = (df_stats["n_orders"] * df_stats["late_rate"]).sum()

    assignment, expected_late = opt_module.optimize(
        df_stats, budget_index_per_order=budget, rate_col="late_rate_adjusted"
    )
    pct = 100 * expected_late / baseline_late

    col1, col2 = st.columns(2)
    col1.metric("Baseline expected late orders", f"{baseline_late:.0f}")
    col2.metric(
        "With this budget", f"{expected_late:.0f}",
        delta=f"{pct - 100:.0f}% vs baseline", delta_color="inverse",
    )

    st.dataframe(assignment, use_container_width=True)