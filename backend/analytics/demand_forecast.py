import numpy as np
import pandas as pd


def forecast_overall_demand(sales: pd.DataFrame, horizon_days=14):
    """
    Forecasts total daily units sold using a simple linear-trend model fit on the
    last 60 days, with a naive confidence band derived from residual std-dev.
    This is intentionally simple and explainable rather than a black-box model —
    appropriate for a demo, not a production forecasting system (see README).
    """
    daily = sales.groupby("date")["quantity"].sum().sort_index()
    daily = daily.tail(60)
    if len(daily) < 7:
        return {"history": [], "forecast": []}

    x = np.arange(len(daily))
    y = daily.values.astype(float)
    coeffs = np.polyfit(x, y, 1)
    trend = np.poly1d(coeffs)
    residuals = y - trend(x)
    std = float(np.std(residuals))

    last_date = daily.index.max()
    future_x = np.arange(len(daily), len(daily) + horizon_days)
    future_dates = [last_date + pd.Timedelta(days=i + 1) for i in range(horizon_days)]
    forecast_values = trend(future_x)

    history = [{"date": d.strftime("%Y-%m-%d"), "actual": round(float(v), 1)}
               for d, v in zip(daily.index, y)]
    forecast = [{
        "date": d.strftime("%Y-%m-%d"),
        "forecast": round(max(0, float(v)), 1),
        "low": round(max(0, float(v) - 1.28 * std), 1),
        "high": round(float(v) + 1.28 * std, 1),
    } for d, v in zip(future_dates, forecast_values)]

    return {"history": history, "forecast": forecast}


def product_reorder_forecast(inventory_row: dict, avg_daily_sales: float, lead_time_days=4):
    """Per-product stockout estimate used by the low-stock / reorder views."""
    qty = inventory_row.get("quantity_on_hand", 0)
    if avg_daily_sales <= 0:
        return {"days_until_stockout": None}
    days_left = qty / avg_daily_sales
    return {
        "days_until_stockout": round(days_left, 1),
        "expected_stockout_within_lead_time": days_left <= lead_time_days,
    }
