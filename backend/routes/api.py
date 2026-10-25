import math
from datetime import timedelta

import pandas as pd
from flask import Blueprint, jsonify, request

from backend.data_processing import loader
from backend.data_processing.normalizer import detect_mapping, apply_mapping
from backend.data_processing.validator import validate
from backend.importers.file_importer import read_file, guess_table_type
from backend.analytics import (
    sales_analysis, inventory_analysis, expiry_analysis,
    profit_analysis, demand_forecast, association_rules,
)

api = Blueprint("api", __name__, url_prefix="/api")


# ---------------------------------------------------------------- helpers --
def _paginate(records, page, page_size):
    total = len(records)
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "rows": records[start:end],
        "page": page,
        "page_size": page_size,
        "total_rows": total,
        "total_pages": max(1, math.ceil(total / page_size)),
    }


def _table_frame(name):
    df = loader.get(name)
    return df.copy()


# ------------------------------------------------------------- demo data --
@api.get("/demo/summary")
def demo_summary():
    sales = loader.get("sales")
    purchases = loader.get("purchases")
    inventory = loader.get("inventory")
    products = loader.get("products")

    return jsonify({
        "period_start": sales["date"].min().strftime("%Y-%m-%d") if not sales.empty else None,
        "period_end": sales["date"].max().strftime("%Y-%m-%d") if not sales.empty else None,
        "product_count": int(products["barcode"].nunique()),
        "sales_invoice_count": int(sales["invoice_no"].nunique()),
        "purchase_invoice_count": int(purchases["po_no"].nunique()),
        "total_units_sold": int(sales["quantity"].sum()),
        "supplier_count": int(purchases["supplier"].nunique()),
        "stock_value": round(float(inventory["stock_value"].sum()), 2),
    })


@api.get("/demo/table/<table>")
def demo_table(table):
    if table not in ("sales", "purchases", "inventory", "products"):
        return jsonify({"error": "unknown table"}), 404

    df = _table_frame(table)
    search = request.args.get("search", "").strip().lower()
    if search:
        text_cols = [c for c in ("product_name", "supplier", "category", "manufacturer") if c in df.columns]
        if text_cols:
            mask = False
            for c in text_cols:
                mask = mask | df[c].astype(str).str.lower().str.contains(search, na=False)
            df = df[mask]

    sort_by = request.args.get("sort_by")
    if sort_by and sort_by in df.columns:
        ascending = request.args.get("sort_dir", "asc") == "asc"
        df = df.sort_values(sort_by, ascending=ascending)

    for date_col in ("date", "expiry_date", "last_sale_date"):
        if date_col in df.columns:
            df[date_col] = df[date_col].dt.strftime("%Y-%m-%d")

    page = int(request.args.get("page", 1))
    page_size = min(int(request.args.get("page_size", 20)), 100)
    records = df.to_dict(orient="records")
    return jsonify(_paginate(records, page, page_size))


@api.post("/analyze")
def analyze():
    # In the demo, all analytics are computed on demand from the dataset already
    # in memory -- this endpoint exists to drive the "processing" UI sequence.
    sales = loader.get("sales")
    return jsonify({
        "status": "ok",
        "rows_analyzed": int(len(sales)),
    })


# --------------------------------------------------------------- dashboard --
def _period_bounds(range_key, sales):
    end = sales["date"].max()
    if pd.isna(end):
        end = pd.Timestamp.now()
    ranges = {
        "7d": 7, "30d": 30, "90d": 90, "6m": 182,
    }
    days = ranges.get(range_key, 30)
    start = end - timedelta(days=days)
    prev_end = start - timedelta(days=1)
    prev_start = prev_end - timedelta(days=days)
    return start, end, prev_start, prev_end


@api.get("/dashboard")
def dashboard():
    sales = loader.get("sales")
    inventory = loader.get("inventory")

    start, end, prev_start, prev_end = _period_bounds("30d", sales)
    comparison = sales_analysis.compare_periods(sales, start, end, prev_start, prev_end)

    low_stock = inventory_analysis.low_stock(inventory, sales, threshold_days=7, n=1000)
    expiry = expiry_analysis.expiry_report(inventory, sales)
    dead_value, dead_count = inventory_analysis.dead_stock_total_value(inventory, sales)

    return jsonify({
        "period": comparison,
        "attention": {
            "low_stock_count": len(low_stock),
            "expiry_7_days_count": expiry["counts"]["7_days"] + expiry["counts"]["expired"],
            "dead_stock_count": dead_count,
            "dead_stock_value": dead_value,
        },
        "top_products": sales_analysis.top_products(sales, by="revenue", n=5),
    })


# ------------------------------------------------------------------ sales --
@api.get("/sales")
def sales_endpoint():
    sales = loader.get("sales")
    range_key = request.args.get("range", "30d")
    start, end, prev_start, prev_end = _period_bounds(range_key, sales)
    comparison = sales_analysis.compare_periods(sales, start, end, prev_start, prev_end)
    freq = "W" if range_key in ("90d", "6m") else "D"
    trend = sales_analysis.trend_over_time(sales, freq=freq, start=start, end=end)

    return jsonify({
        "comparison": comparison,
        "trend": trend,
        "top_products": sales_analysis.top_products(sales, by="revenue", n=10, ascending=False)[:10],
        "bottom_products": [p for p in sales_analysis.top_products(sales, by="revenue", n=2000, ascending=False)][-10:],
        "top_categories": sales_analysis.top_categories(sales),
        "weekday": sales_analysis.sales_by_weekday(sales),
        "peak_hours": sales_analysis.peak_hours(sales),
    })


# -------------------------------------------------------------- inventory --
@api.get("/inventory/low-stock")
def low_stock_endpoint():
    inventory, sales = loader.get("inventory"), loader.get("sales")
    return jsonify(inventory_analysis.low_stock(inventory, sales))


@api.get("/inventory/reorder")
def reorder_endpoint():
    inventory, sales = loader.get("inventory"), loader.get("sales")
    return jsonify(inventory_analysis.reorder_suggestions(inventory, sales))


@api.get("/inventory/dead-stock")
def dead_stock_endpoint():
    inventory, sales = loader.get("inventory"), loader.get("sales")
    rows = inventory_analysis.dead_stock(inventory, sales)
    value, count = inventory_analysis.dead_stock_total_value(inventory, sales)
    return jsonify({"rows": rows, "total_value": value, "total_count": count})


@api.get("/inventory/summary")
def inventory_summary_endpoint():
    return jsonify(inventory_analysis.stock_summary(loader.get("inventory")))


@api.get("/expiry")
def expiry_endpoint():
    inventory, sales = loader.get("inventory"), loader.get("sales")
    return jsonify(expiry_analysis.expiry_report(inventory, sales))


# ----------------------------------------------------------------- profit --
@api.get("/profit")
def profit_endpoint():
    sales = loader.get("sales")
    return jsonify(profit_analysis.profit_report(sales))


@api.get("/profit/matrix")
def profit_matrix_endpoint():
    sales = loader.get("sales")
    return jsonify(profit_analysis.profit_matrix(sales))


# ------------------------------------------------------------ associations --
@api.get("/associations")
def associations_endpoint():
    sales = loader.get("sales")
    return jsonify(association_rules.association_rules(sales))


# --------------------------------------------------------------- forecast --
@api.get("/forecast")
def forecast_endpoint():
    sales = loader.get("sales")
    horizon = int(request.args.get("days", 14))
    return jsonify(demand_forecast.forecast_overall_demand(sales, horizon_days=horizon))


# ------------------------------------------------------------- categories --
@api.get("/categories")
def categories_endpoint():
    sales = loader.get("sales")
    inventory = loader.get("inventory")
    cats = sales_analysis.top_categories(sales, n=20)
    stock_by_cat = inventory.groupby("category")["stock_value"].sum().round(2).to_dict()
    for c in cats:
        c["stock_value"] = stock_by_cat.get(c["category"], 0)
    return jsonify(cats)


# ------------------------------------------------------- executive summary --
@api.get("/executive-summary")
def executive_summary_endpoint():
    sales = loader.get("sales")
    inventory = loader.get("inventory")

    start, end, prev_start, prev_end = _period_bounds("30d", sales)
    comparison = sales_analysis.compare_periods(sales, start, end, prev_start, prev_end)
    low_stock = inventory_analysis.low_stock(inventory, sales, threshold_days=7, n=1000)
    dead_value, dead_count = inventory_analysis.dead_stock_total_value(inventory, sales)
    expiry = expiry_analysis.expiry_report(inventory, sales)
    cats = sales_analysis.top_categories(sales, n=3)

    highlights = []
    rev_change = comparison["change_pct"]["revenue"]
    if rev_change is not None:
        direction = "ارتفعت" if rev_change >= 0 else "انخفضت"
        highlights.append(f"المبيعات {direction} {abs(rev_change)}% خلال آخر 30 يومًا مقارنة بالفترة السابقة.")

    risks = []
    if low_stock:
        risks.append(f"{len(low_stock)} صنفًا قد يصل إلى مستوى مخزون حرج خلال أسبوع.")
    if expiry["counts"]["7_days"] + expiry["counts"]["expired"]:
        risks.append(f"{expiry['counts']['7_days'] + expiry['counts']['expired']} صنفًا قريب من انتهاء الصلاحية خلال أسبوع.")
    if dead_count:
        risks.append(f"قيمة المخزون الراكد تقدر بـ {dead_value:,.0f} د.ل عبر {dead_count} صنفًا.")

    opportunities = []
    if cats:
        opportunities.append(f"فئة {cats[0]['category']} هي الأعلى مبيعًا خلال الفترة الحالية.")

    actions = []
    if low_stock:
        actions.append("مراجعة قائمة اقتراحات إعادة الطلب لتفادي نفاد المخزون.")
    if dead_count:
        actions.append("التفكير في عروض تصريف للأصناف الراكدة لتحرير السيولة.")

    return jsonify({
        "highlights": highlights,
        "risks": risks,
        "opportunities": opportunities,
        "actions": actions,
        "comparison": comparison,
    })


# --------------------------------------------------------------- data quality --
@api.get("/data-quality")
def data_quality_endpoint():
    sales = loader.get("sales")
    report = validate(sales, required_fields=["product_name", "quantity", "date", "selling_price"])
    return jsonify(report)


@api.post("/reset")
def reset_endpoint():
    loader.reset_to_demo()
    return jsonify({"status": "reset"})


# --------------------------------------------------------------- import ---
@api.post("/import/detect")
def import_detect():
    if "file" not in request.files:
        return jsonify({"error": "لم يتم إرفاق أي ملف."}), 400
    df, error = read_file(request.files["file"])
    if error:
        return jsonify({"error": error}), 400

    table_type = request.form.get("table_type") or guess_table_type(request.files["file"].filename, df.columns)
    mapping = detect_mapping(df.columns, table_type)
    preview = df.head(10).fillna("").to_dict(orient="records")

    return jsonify({
        "table_type": table_type,
        "columns": list(df.columns),
        "suggested_mapping": mapping,
        "preview": preview,
        "row_count": len(df),
    })


@api.post("/import/apply")
def import_apply():
    """
    Expects multipart form: file + table_type + mapping (JSON string of
    {raw_column: standard_field}). Validates, normalizes, and swaps the
    in-memory dataset used by every other endpoint.
    """
    import json

    if "file" not in request.files:
        return jsonify({"error": "لم يتم إرفاق أي ملف."}), 400
    df, error = read_file(request.files["file"])
    if error:
        return jsonify({"error": error}), 400

    table_type = request.form.get("table_type", "sales")
    try:
        mapping = json.loads(request.form.get("mapping", "{}"))
    except json.JSONDecodeError:
        return jsonify({"error": "تنسيق mapping غير صالح."}), 400

    normalized = apply_mapping(df, mapping)
    required = {
        "sales": ["product_name", "quantity", "date", "selling_price"],
        "purchases": ["product_name", "quantity", "date", "purchase_price"],
        "inventory": ["product_name", "quantity_on_hand"],
    }.get(table_type, ["product_name"])

    report = validate(normalized, required_fields=required)
    if report["quality_score"] == 0:
        return jsonify({"error": "بيانات غير صالحة للتحليل.", "report": report}), 400

    # best-effort type coercion before swapping into memory
    if "date" in normalized.columns:
        normalized["date"] = pd.to_datetime(normalized["date"], errors="coerce")
    for numeric_col in ("quantity", "quantity_on_hand", "selling_price", "purchase_price"):
        if numeric_col in normalized.columns:
            normalized[numeric_col] = pd.to_numeric(normalized[numeric_col], errors="coerce")

    loader.set_frame(table_type, normalized)
    return jsonify({"status": "ok", "table_type": table_type, "report": report})
