
"""
Optimization module: given real region x shipping-mode late-rate and
cost data, recommend which shipping mode each region should default
to, minimizing expected late orders subject to a shipping-cost budget.

Framing note (from 03_statistical_analysis.py): lateness is driven
almost entirely by the promised-vs-actual delivery window per shipping
mode (e.g. First Class: 1 day promised, ~2 actual -> ~95% late), not
by region. So this optimizer is really answering: "given that reality,
which mix of shipping-mode assignments minimizes expected late orders
without blowing the cost budget" -- a lever the business can actually
pull (SLA/mode assignment), rather than something regional operations
can fix on their own.

Shrinkage note: some (region, mode) combinations have very few
historical orders (e.g. Canada + Same Day: only 12 orders). Their raw
late_rate is unreliable -- with that little data, the observed rate
could easily be far from the true rate just by chance. Before those
numbers feed the optimizer, we pull each rate toward the global
average late rate, weighted by how much data that combination has
(empirical-Bayes-style shrinkage / Beta-Binomial posterior mean):

    adjusted_rate = (n * raw_rate + k * global_rate) / (n + k)

Combinations with lots of data (n >> k) barely move; combinations with
little data (n << k) get pulled strongly toward the global average.
k is a modeling choice, not something derived from the data -- it
represents how many "pretend" global-average orders we blend in
before trusting a group's own numbers. k=100 here is a reasonable
default for the sample sizes seen in this dataset (regions range from
~200 to several thousand orders); it can be tuned via cross-validation
in a more rigorous version.

Cost index per shipping mode is a documented assumption (no real client
cost data available for this portfolio project) -- replace with actual
figures if you have them.

Usage:
    python src/05_optimization.py
"""
import os
import sys
import pandas as pd
import pulp

sys.path.insert(0, os.path.dirname(__file__))
from db import get_engine

# Assumed relative cost index per shipping mode (documented assumption).
# Ordered roughly by speed -- faster modes cost more to fulfill.
SHIPPING_COST_INDEX = {
    "Same Day": 4.0,
    "First Class": 3.0,
    "Second Class": 2.0,
    "Standard Class": 1.0,
}

# Shrinkage strength: how many "pretend" global-average orders to blend
# into each (region, mode) combination before trusting its raw rate.
SHRINKAGE_K = 100


def load_region_mode_stats(engine):
    query = """
        SELECT
            g.order_region,
            sm.shipping_mode,
            COUNT(*) AS n_orders,
            AVG(v.late_delivery_risk::numeric) AS late_rate
        FROM v_orders v
        JOIN dim_geography g      ON g.geography_id = v.geography_id
        JOIN dim_shipping_mode sm ON sm.shipping_mode_id = v.shipping_mode_id
        GROUP BY g.order_region, sm.shipping_mode
    """
    return pd.read_sql(query, engine)


def apply_shrinkage(df: pd.DataFrame, k: float = SHRINKAGE_K) -> pd.DataFrame:
    """
    Add a `late_rate_adjusted` column: each (region, mode)'s raw
    late_rate pulled toward the global average, weighted by its own
    order count vs. k. See module docstring for the formula and
    rationale.
    """
    global_rate = (df["n_orders"] * df["late_rate"]).sum() / df["n_orders"].sum()
    df = df.copy()
    df["late_rate_adjusted"] = (
        df["n_orders"] * df["late_rate"] + k * global_rate
    ) / (df["n_orders"] + k)
    return df, global_rate


def optimize(df: pd.DataFrame, budget_index_per_order: float, rate_col: str):
    """
    Decision variable: x[region, mode] = 1 if `region` is assigned
    `mode` as its default shipping mode, 0 otherwise.

    Objective: minimize total expected late orders, using `rate_col`
    (either the raw or shrinkage-adjusted late rate) as the per-group
    late-rate estimate.

    Constraints:
      - exactly one mode chosen per region
      - weighted average cost index per order <= budget_index_per_order
    """
    regions = df["order_region"].unique()
    modes = [m for m in df["shipping_mode"].unique() if m in SHIPPING_COST_INDEX]

    prob = pulp.LpProblem("shipping_mode_allocation", pulp.LpMinimize)
    x = {
        (r, m): pulp.LpVariable(f"x_{r}_{m}", cat="Binary")
        for r in regions for m in modes
    }

    stats = df.set_index(["order_region", "shipping_mode"])

    # Use each region's TOTAL order volume (all modes combined), not the
    # historical n_orders for that specific (region, mode) pair -- see
    # earlier bug note: the decision being modeled is "what if ALL of
    # this region's orders used mode m."
    total_orders = df.groupby("order_region")["n_orders"].sum()

    prob += pulp.lpSum(
        x[r, m] * total_orders[r] * stats.loc[(r, m), rate_col]
        for r in regions for m in modes
        if (r, m) in stats.index
    )

    for r in regions:
        prob += pulp.lpSum(x[r, m] for m in modes) == 1

    prob += pulp.lpSum(
        x[r, m] * total_orders[r] * SHIPPING_COST_INDEX[m]
        for r in regions for m in modes
        if (r, m) in stats.index
    ) <= budget_index_per_order * total_orders.sum()

    prob.solve(pulp.PULP_CBC_CMD(msg=0))

    assignment = []
    for r in regions:
        chosen = [m for m in modes if pulp.value(x[r, m]) == 1]
        if chosen:
            assignment.append({"order_region": r, "recommended_mode": chosen[0]})
    return pd.DataFrame(assignment), pulp.value(prob.objective)


if __name__ == "__main__":
    engine = get_engine()
    df = load_region_mode_stats(engine)
    df, global_rate = apply_shrinkage(df, k=SHRINKAGE_K)

    print(f"Global late rate: {global_rate:.3f}  (shrinkage k={SHRINKAGE_K})\n")

    # Show which combinations moved the most under shrinkage -- the
    # ones with the smallest n_orders should show the biggest shift.
    df["shift"] = (df["late_rate_adjusted"] - df["late_rate"]).abs()
    print("Combinations most affected by shrinkage (smallest samples):")
    print(
        df.sort_values("shift", ascending=False)
          .head(8)[["order_region", "shipping_mode", "n_orders",
                     "late_rate", "late_rate_adjusted"]]
          .to_string(index=False)
    )
    print()

    total_orders = df.groupby("order_region")["n_orders"].sum().sum()
    baseline_late = (df["n_orders"] * df["late_rate"]).sum()
    print(f"Baseline (current mix): ~{baseline_late:.0f} expected late orders "
          f"out of {total_orders} total\n")

    for budget in [1.5, 2.0, 2.5, 3.0]:
        assignment, expected_late = optimize(
            df, budget_index_per_order=budget, rate_col="late_rate_adjusted"
        )
        pct_of_baseline = 100 * expected_late / baseline_late
        print(f"Budget index/order <= {budget}: "
              f"expected late orders = {expected_late:.0f} "
              f"({pct_of_baseline:.0f}% of baseline)")
        print(assignment.to_string(index=False))
        print()
