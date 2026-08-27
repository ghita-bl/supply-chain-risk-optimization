# Supply Chain Risk & Delivery Optimization

A self-contained analytics case:
SQL data modeling → statistical analysis → predictive modeling → optimization →
dashboard MVP → client-ready synthesis.

## Business framing

**Client:** a multi-region retailer/distributor (DataCo).
**Problem:** a meaningful share of orders arrive late, hurting customer
satisfaction and cost. The client wants to know (1) where and why late
deliveries happen, (2) which orders are at risk, and (3) how to reallocate
shipping modes to cut late-delivery risk without blowing the shipping budget.

## Dataset

[DataCo Smart Supply Chain for Big Data Analysis](https://www.kaggle.com/datasets/shashwatwork/dataco-smart-supply-chain-for-big-data-analysis)
(Kaggle, public, ~180k orders, ~53 columns: order dates, shipping mode,
region, category, late-delivery-risk flag, sales, profit, etc.)

Steps to get it:
1. Create a free Kaggle account if you don't have one.
2. `pip install kaggle --break-system-packages`, then place your
   `kaggle.json` API token in `~/.kaggle/`.
3. `kaggle datasets download -d shashwatwork/dataco-smart-supply-chain-for-big-data-analysis -p data/raw --unzip`

(If Kaggle CLI access is awkward in your environment, download the CSV
manually from the link above and drop it in `data/raw/`.)

## Project roadmap (5 modules → 5 deliverables)

| # | Module | Tools | Deliverable |
|---|--------|-------|-------------|
| 1 | Data layer | PostgreSQL, SQL | Clean fact/dim tables, exploratory SQL queries |
| 2 | Statistical analysis | Python (pandas, scipy, statsmodels) | Notebook: what drives late delivery |
| 3 | Predictive model | Python (scikit-learn / xgboost) | Late-delivery-risk classifier + evaluation |
| 4 | Optimization | Python (PuLP) | Shipping-mode reallocation recommendation |
| 5 | Dashboard | Streamlit | Interactive MVP for the "client" |
| 6 | Synthesis | PPTX | 5-7 slide client-ready deck |

## Folder structure

```
supply-chain-case/
├── data/
│   ├── raw/              # original Kaggle CSV goes here
│   └── processed/        # cleaned parquet/csv outputs
├── sql/                  # schema + analysis queries
├── src/                  # loading, cleaning, modeling, optimization scripts
├── notebooks/            # exploratory analysis
├── dashboard/            # Streamlit app
├── reports/              # final PPT / exported charts
└── README.md
```

## Status
- [x] Repo scaffolded
- [x] Data downloaded
- [x] Schema created, data loaded into Postgres
- [x] Exploratory SQL done
- [x] Statistical analysis notebook
- [x] Classifier trained + evaluated
- [x] Optimization module
- [x] Dashboard
- [ ] Client deck
