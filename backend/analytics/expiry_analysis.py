import pandas as pd
from backend.analytics.inventory_analysis import _avg_daily_sales


def expiry_report(inventory: pd.DataFrame, sales: pd.DataFrame, reference_date=None, n=200):
    if reference_date is None:
        reference_date = sales["date"].max() if not sales.empty else pd.Timestamp.now()
    avg_sales = _avg_daily_sales(sales)

    df = inventory.copy()
    df["days_to_expiry"] = (df["expiry_date"] - reference_date).dt.days
    df["avg_daily_sales"] = df["barcode"].map(avg_sales).fillna(0.0)

    df["estimated_units_sold_before_expiry"] = (df["avg_daily_sales"] * df["days_to_expiry"]).clip(lower=0)
    df["estimated_units_sold_before_expiry"] = df[["estimated_units_sold_before_expiry", "quantity_on_hand"]].min(axis=1)
    df["estimated_units_at_risk"] = (df["quantity_on_hand"] - df["estimated_units_sold_before_expiry"]).clip(lower=0)

    def bucket(days):
        if days < 0:
            return "expired"
        if days <= 7:
            return "7_days"
        if days <= 30:
            return "30_days"
        if days <= 90:
            return "90_days"
        return "safe"

    df["bucket"] = df["days_to_expiry"].apply(bucket)

    result = {}
    for b in ("expired", "7_days", "30_days", "90_days"):
        sub = df[df["bucket"] == b].sort_values("days_to_expiry")
        sub = sub.head(n).copy()
        sub["estimated_units_sold_before_expiry"] = sub["estimated_units_sold_before_expiry"].round(0).astype(int)
        sub["estimated_units_at_risk"] = sub["estimated_units_at_risk"].round(0).astype(int)
        sub["avg_daily_sales"] = sub["avg_daily_sales"].round(2)
        cols = ["barcode", "product_name", "category", "quantity_on_hand", "expiry_date",
                "days_to_expiry", "avg_daily_sales", "estimated_units_sold_before_expiry",
                "estimated_units_at_risk", "stock_value"]
        sub = sub.copy()
        sub["expiry_date"] = sub["expiry_date"].dt.strftime("%Y-%m-%d")
        result[b] = sub[cols].to_dict(orient="records")

    counts = df["bucket"].value_counts().to_dict()
    value_at_risk = float(df[df["bucket"].isin(["expired", "7_days", "30_days"])]["stock_value"].sum())

    return {
        "buckets": result,
        "counts": {k: int(counts.get(k, 0)) for k in ("expired", "7_days", "30_days", "90_days", "safe")},
        "value_at_risk": round(value_at_risk, 2),
    }
