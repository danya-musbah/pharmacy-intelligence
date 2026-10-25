import pandas as pd
import numpy as np


def _avg_daily_sales(sales: pd.DataFrame, window_days=30):
    """Average units sold per day, per barcode, over the most recent window."""
    if sales.empty:
        return pd.Series(dtype=float)
    end = sales["date"].max()
    start = end - pd.Timedelta(days=window_days)
    recent = sales[sales["date"] >= start]
    daily = recent.groupby("barcode")["quantity"].sum() / window_days
    return daily


def low_stock(inventory: pd.DataFrame, sales: pd.DataFrame, threshold_days=7, n=50):
    avg_sales = _avg_daily_sales(sales)
    df = inventory.copy()
    df["avg_daily_sales"] = df["barcode"].map(avg_sales).fillna(0.0)
    df["days_of_stock_left"] = np.where(
        df["avg_daily_sales"] > 0, df["quantity_on_hand"] / df["avg_daily_sales"], np.inf
    )
    at_risk = df[(df["avg_daily_sales"] > 0) & (df["days_of_stock_left"] <= threshold_days)].copy()
    at_risk = at_risk.sort_values("days_of_stock_left")
    at_risk["avg_daily_sales"] = at_risk["avg_daily_sales"].round(2)
    at_risk["days_of_stock_left"] = at_risk["days_of_stock_left"].round(1)
    cols = ["barcode", "product_name", "category", "quantity_on_hand", "avg_daily_sales", "days_of_stock_left"]
    return at_risk[cols].head(n).to_dict(orient="records")


def reorder_suggestions(inventory: pd.DataFrame, sales: pd.DataFrame, lead_time_days=4,
                         safety_days=5, n=50):
    avg_sales = _avg_daily_sales(sales)
    df = inventory.copy()
    df["avg_daily_sales"] = df["barcode"].map(avg_sales).fillna(0.0)
    moving = df[df["avg_daily_sales"] > 0].copy()
    # target stock = demand over (lead time + safety buffer); suggested qty tops up to that
    moving["target_stock"] = moving["avg_daily_sales"] * (lead_time_days + safety_days)
    moving["suggested_qty"] = (moving["target_stock"] - moving["quantity_on_hand"]).clip(lower=0)
    moving = moving[moving["suggested_qty"] >= 1]
    moving["suggested_qty"] = moving["suggested_qty"].round(0).astype(int)
    moving = moving.sort_values("suggested_qty", ascending=False)
    moving["avg_daily_sales"] = moving["avg_daily_sales"].round(2)
    cols = ["barcode", "product_name", "category", "quantity_on_hand", "avg_daily_sales",
            "suggested_qty"]
    result = moving[cols].head(n).to_dict(orient="records")
    for r in result:
        r["lead_time_days"] = lead_time_days
    return result


def dead_stock(inventory: pd.DataFrame, sales: pd.DataFrame, idle_days=45, n=50):
    df = inventory.copy()
    today = sales["date"].max() if not sales.empty else pd.Timestamp.now()
    sold_barcodes = set(sales["barcode"].unique())

    def days_idle(row):
        if pd.isna(row["last_sale_date"]) or row["barcode"] not in sold_barcodes:
            return 999
        return (today - row["last_sale_date"]).days

    df["days_since_last_sale"] = df.apply(days_idle, axis=1)
    stale = df[df["days_since_last_sale"] >= idle_days].copy()
    stale = stale.sort_values("stock_value", ascending=False)
    cols = ["barcode", "product_name", "category", "quantity_on_hand", "stock_value",
            "days_since_last_sale"]
    return stale[cols].head(n).to_dict(orient="records")


def dead_stock_total_value(inventory: pd.DataFrame, sales: pd.DataFrame, idle_days=45):
    rows = dead_stock(inventory, sales, idle_days=idle_days, n=100000)
    return round(sum(r["stock_value"] for r in rows), 2), len(rows)


def stock_summary(inventory: pd.DataFrame):
    return {
        "total_products": int(inventory["barcode"].nunique()),
        "total_stock_value": round(float(inventory["stock_value"].sum()), 2),
        "total_units": int(inventory["quantity_on_hand"].sum()),
    }
