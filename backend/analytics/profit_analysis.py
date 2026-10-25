import pandas as pd


def profit_report(sales: pd.DataFrame, n=15):
    grouped = sales.groupby(["barcode", "product_name", "category"]).agg(
        revenue=("revenue", "sum"), profit=("profit", "sum"), units=("quantity", "sum")
    ).reset_index()
    grouped["margin_pct"] = (grouped["profit"] / grouped["revenue"] * 100).round(1)
    grouped["revenue"] = grouped["revenue"].round(2)
    grouped["profit"] = grouped["profit"].round(2)

    top_profit = grouped.sort_values("profit", ascending=False).head(n).to_dict(orient="records")
    top_revenue = grouped.sort_values("revenue", ascending=False).head(n).to_dict(orient="records")
    top_margin = grouped[grouped["revenue"] > 100].sort_values("margin_pct", ascending=False).head(n).to_dict(orient="records")
    # high sales volume but low margin -- worth the pharmacy owner's attention
    high_vol_low_margin = grouped[grouped["units"] >= grouped["units"].quantile(0.7)]
    high_vol_low_margin = high_vol_low_margin.sort_values("margin_pct").head(n).to_dict(orient="records")

    return {
        "top_profit": top_profit,
        "top_revenue": top_revenue,
        "top_margin": top_margin,
        "high_volume_low_margin": high_vol_low_margin,
    }


def profit_matrix(sales: pd.DataFrame, n=60):
    """Sales-volume vs profit quadrant data for the stars/winners/dead-stock/low-volume chart."""
    grouped = sales.groupby(["barcode", "product_name", "category"]).agg(
        revenue=("revenue", "sum"), profit=("profit", "sum"), units=("quantity", "sum")
    ).reset_index()
    if grouped.empty:
        return {"points": [], "median_units": 0, "median_profit": 0}
    median_units = float(grouped["units"].median())
    median_profit = float(grouped["profit"].median())

    def quadrant(row):
        high_sales = row["units"] >= median_units
        high_profit = row["profit"] >= median_profit
        if high_sales and high_profit:
            return "stars"
        if high_sales and not high_profit:
            return "winners"
        if not high_sales and high_profit:
            return "low_volume"
        return "dead_stock"

    grouped["quadrant"] = grouped.apply(quadrant, axis=1)
    top = grouped.sort_values("revenue", ascending=False).head(n).copy()
    top["profit"] = top["profit"].round(2)
    top["revenue"] = top["revenue"].round(2)
    return {
        "points": top[["product_name", "category", "units", "profit", "revenue", "quadrant"]].to_dict(orient="records"),
        "median_units": round(median_units, 1),
        "median_profit": round(median_profit, 2),
    }
