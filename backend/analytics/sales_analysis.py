import pandas as pd


def _filter(sales, start, end):
    df = sales
    if start is not None:
        df = df[df["date"] >= pd.to_datetime(start)]
    if end is not None:
        df = df[df["date"] <= pd.to_datetime(end)]
    return df


def summary(sales: pd.DataFrame, start=None, end=None):
    df = _filter(sales, start, end)
    invoices = df["invoice_no"].nunique()
    revenue = float(df["revenue"].sum())
    profit = float(df["profit"].sum())
    units = int(df["quantity"].sum())
    avg_invoice = round(revenue / invoices, 2) if invoices else 0
    return {
        "revenue": round(revenue, 2),
        "profit": round(profit, 2),
        "invoices": int(invoices),
        "units_sold": units,
        "avg_invoice_value": avg_invoice,
    }


def compare_periods(sales, current_start, current_end, previous_start, previous_end):
    cur = summary(sales, current_start, current_end)
    prev = summary(sales, previous_start, previous_end)

    def pct(a, b):
        if not b:
            return None
        return round(((a - b) / b) * 100, 1)

    return {
        "current": cur,
        "previous": prev,
        "change_pct": {
            "revenue": pct(cur["revenue"], prev["revenue"]),
            "profit": pct(cur["profit"], prev["profit"]),
            "invoices": pct(cur["invoices"], prev["invoices"]),
            "units_sold": pct(cur["units_sold"], prev["units_sold"]),
        },
    }


def trend_over_time(sales: pd.DataFrame, freq="D", start=None, end=None):
    df = _filter(sales, start, end)
    grouped = df.groupby(pd.Grouper(key="date", freq=freq)).agg(
        revenue=("revenue", "sum"), profit=("profit", "sum"), invoices=("invoice_no", "nunique")
    ).reset_index()
    grouped["date"] = grouped["date"].dt.strftime("%Y-%m-%d")
    grouped["revenue"] = grouped["revenue"].round(2)
    grouped["profit"] = grouped["profit"].round(2)
    return grouped.to_dict(orient="records")


def sales_by_weekday(sales: pd.DataFrame):
    df = sales.copy()
    df["weekday"] = df["date"].dt.dayofweek
    names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    grouped = df.groupby("weekday").agg(
        revenue=("revenue", "sum"), invoices=("invoice_no", "nunique")
    ).reindex(range(7), fill_value=0)
    return [
        {"weekday": names[i], "revenue": round(float(grouped.loc[i, "revenue"]), 2),
         "invoices": int(grouped.loc[i, "invoices"])}
        for i in range(7)
    ]


def peak_hours(sales: pd.DataFrame, top_n=5):
    df = sales.copy()
    df["hour"] = df["time"].str.slice(0, 2).astype(int)
    grouped = df.groupby("hour").agg(
        revenue=("revenue", "sum"), invoices=("invoice_no", "nunique")
    ).reset_index()
    grouped["revenue"] = grouped["revenue"].round(2)
    top = grouped.sort_values("revenue", ascending=False).head(top_n).to_dict(orient="records")
    for r in top:
        r["hour_label"] = f"{r['hour']:02d}:00 — {(r['hour'] + 1) % 24:02d}:00"
    full = grouped.sort_values("hour").to_dict(orient="records")
    return {"top": top, "all_hours": full}


def top_products(sales: pd.DataFrame, by="revenue", n=10, ascending=False):
    grouped = sales.groupby(["barcode", "product_name", "category"]).agg(
        revenue=("revenue", "sum"), profit=("profit", "sum"),
        units=("quantity", "sum"), invoices=("invoice_no", "nunique")
    ).reset_index()
    grouped = grouped.sort_values(by, ascending=ascending).head(n)
    grouped["revenue"] = grouped["revenue"].round(2)
    grouped["profit"] = grouped["profit"].round(2)
    return grouped.to_dict(orient="records")


def top_categories(sales: pd.DataFrame, n=10):
    grouped = sales.groupby("category").agg(
        revenue=("revenue", "sum"), profit=("profit", "sum"), units=("quantity", "sum")
    ).reset_index().sort_values("revenue", ascending=False).head(n)
    grouped["revenue"] = grouped["revenue"].round(2)
    grouped["profit"] = grouped["profit"].round(2)
    return grouped.to_dict(orient="records")
