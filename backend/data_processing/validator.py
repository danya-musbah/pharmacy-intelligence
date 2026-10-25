import pandas as pd


def validate(df: pd.DataFrame, required_fields):
    issues = []
    n_rows = len(df)

    missing_fields = [f for f in required_fields if f not in df.columns]
    if missing_fields:
        issues.append({"level": "error", "message": f"Missing required columns: {', '.join(missing_fields)}"})
        return {"row_count": n_rows, "issues": issues, "quality_score": 0}

    n_missing_price = 0
    for price_col in ("selling_price", "purchase_price"):
        if price_col in df.columns:
            n_missing = df[price_col].isna().sum()
            n_missing_price += int(n_missing)
            if n_missing:
                issues.append({"level": "warning", "message": f"{n_missing} rows have missing {price_col}"})

    # Sales/purchases are line-item tables -- the same invoice legitimately repeats
    # across lines, so duplicates are only meaningful at the (invoice, product) level.
    n_duplicates = 0
    if "invoice_no" in df.columns and "barcode" in df.columns:
        n_duplicates = int(df.duplicated(subset=["invoice_no", "barcode"]).sum())
        if n_duplicates:
            issues.append({"level": "warning", "message": f"{n_duplicates} duplicate invoice/product lines"})
    elif "po_no" in df.columns and "barcode" in df.columns:
        n_duplicates = int(df.duplicated(subset=["po_no", "barcode"]).sum())
        if n_duplicates:
            issues.append({"level": "warning", "message": f"{n_duplicates} duplicate PO/product lines"})

    n_invalid_dates = 0
    if "date" in df.columns:
        parsed = pd.to_datetime(df["date"], errors="coerce")
        n_invalid_dates = int(parsed.isna().sum())
        if n_invalid_dates:
            issues.append({"level": "warning", "message": f"{n_invalid_dates} rows have an invalid date"})

    n_unknown_product = int(df["product_name"].isna().sum()) if "product_name" in df.columns else 0
    if n_unknown_product:
        issues.append({"level": "warning", "message": f"{n_unknown_product} rows have no product name"})

    # simple deduction-based score
    penalty = (n_missing_price + n_duplicates + n_invalid_dates + n_unknown_product)
    score = max(0, 100 - round((penalty / max(n_rows, 1)) * 100))

    return {
        "row_count": n_rows,
        "missing_prices": n_missing_price,
        "duplicates": n_duplicates,
        "invalid_dates": n_invalid_dates,
        "missing_products": n_unknown_product,
        "issues": issues,
        "quality_score": score,
    }
