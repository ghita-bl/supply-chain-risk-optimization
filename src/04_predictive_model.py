import os
import sys
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import ( classification_report, roc_auc_score, precision_recall_curve, auc)
from xgboost import XGBClassifier


sys.path.insert(0, os.path.dirname(__file__))
from db import get_engine


LABEL="late_delivery_risk"

def load_data(engine):
    query="""
        SELECT
            v.order_id,
            v.late_delivery_risk,
            g.order_region,
            sm.shipping_mode,
            order_facts.total_sales,
            order_facts.days_for_shipment_sched
        FROM v_orders v
        JOIN dim_geography g      ON g.geography_id = v.geography_id
        JOIN dim_shipping_mode sm ON sm.shipping_mode_id = v.shipping_mode_id
        JOIN (
            SELECT order_id,
                   SUM(sales) AS total_sales,
                   MAX(days_for_shipment_sched) AS days_for_shipment_sched
            FROM fact_order_items
            GROUP BY order_id
        ) order_facts ON order_facts.order_id = v.order_id
    """

    return pd.read_sql(query,engine)

def build_preprocessor(categorical, numeric):
    return ColumnTransformer([("cat",OneHotEncoder(handle_unknown="ignore"),categorical),],remainder="passthrough")


def evaluate(name,y_test, y_pred, y_proba):
    print(f"\n=== {name} ===")
    print(classification_report(y_test, y_pred))
    print(f"ROC-AUC: {roc_auc_score(y_test, y_proba):.3f}")
    precision, recall, _ = precision_recall_curve(y_test, y_proba)
    print(f"PR-AUC:  {auc(recall, precision):.3f}")

def run_version(name,df, categorical,numeric):
    X=df[categorical+numeric]
    y=df[LABEL]
    X_train,X_test,y_train,y_test=train_test_split(X,y,test_size=0.2, random_state=42, stratify=y)
    logit_pipe=Pipeline([
        ("prep",build_preprocessor(categorical,numeric)),("clf",LogisticRegression(max_iter=1000)),
    ])
    logit_pipe.fit(X_train, y_train)
    y_pred=logit_pipe.predict(X_test)
    y_proba=logit_pipe.predict_proba(X_test)[:,1]
    evaluate(f"{name} - Logistic Regression", y_test,y_pred,y_proba)

    xgb_pipe= Pipeline([
        ("prep",build_preprocessor(categorical,numeric)),("clf",XGBClassifier(n_estimators=200, max_depth=4, learning_rate=0.1,eval_metric="logloss", random_state=42,)),
    ])
    xgb_pipe.fit(X_train,y_train)
    y_pred=xgb_pipe.predict(X_test)
    yh_proba=xgb_pipe.predict_proba(X_test)[:,1]
    evaluate(f"{name}- XGBoost", y_test, y_pred, y_proba )

   
    # --- persist the Version A model for the dashboard's Predict tab ---
def save_model_for_dashboard(df):
    import joblib
    categorical = ["shipping_mode", "order_region"]
    numeric = ["total_sales"]
    X = df[categorical + numeric]
    y = df[LABEL]
    pipe = Pipeline([
        ("prep", build_preprocessor(categorical, numeric)),
        ("clf", XGBClassifier(
            n_estimators=200, max_depth=4, learning_rate=0.1,
            eval_metric="logloss", random_state=42,
        )),
    ])
    pipe.fit(X, y)
    out_path = os.path.join(os.path.dirname(__file__), "..", "dashboard", "model.joblib")
    joblib.dump(pipe, out_path)
    print(f"Saved dashboard model to {out_path}")

def main():
    engine = get_engine()
    df = load_data(engine)
    print(f"Loaded {len(df)} orders. Late-delivery rate: {df[LABEL].mean():.3f}")

    print("\n" + "=" * 60)
    print("VERSION A (realistic): shipping_mode, order_region, total_sales")
    print("=" * 60)
    run_version(
        "Version A",
        df,
        categorical=["shipping_mode", "order_region"],
        numeric=["total_sales"],
    )

    print("\n" + "=" * 60)
    print("VERSION B (SLA-aware): + days_for_shipment_sched")
    print("=" * 60)
    run_version(
        "Version B",
        df,
        categorical=["shipping_mode", "order_region"],
        numeric=["total_sales", "days_for_shipment_sched"],
    )
    save_model_for_dashboard(df) 



if __name__ == "__main__":
    main()   
    