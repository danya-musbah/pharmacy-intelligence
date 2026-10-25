import io
import pandas as pd


def read_file(file_storage):
    """file_storage: a Flask FileStorage object. Returns (DataFrame, error|None)."""
    filename = file_storage.filename or ""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    raw = file_storage.read()
    if not raw:
        return None, "الملف فارغ."
    try:
        if ext == "csv":
            df = pd.read_csv(io.BytesIO(raw), encoding_errors="replace")
        elif ext in ("xlsx", "xls"):
            df = pd.read_excel(io.BytesIO(raw))
        else:
            return None, "نوع الملف غير مدعوم. الرجاء رفع CSV أو Excel."
    except Exception as exc:  # noqa: BLE001 - surfaced to the user as a friendly message
        return None, f"تعذّرت قراءة الملف: {exc}"

    if df.empty:
        return None, "الملف لا يحتوي على بيانات."
    return df, None


def guess_table_type(filename: str, columns) -> str:
    name = (filename or "").lower()
    cols_joined = " ".join(str(c).lower() for c in columns)
    if "purchase" in name or "شراء" in name or "supplier" in cols_joined or "مورد" in cols_joined:
        return "purchases"
    if "inventory" in name or "stock" in name or "مخزون" in name or "expiry" in cols_joined or "صلاحية" in cols_joined:
        return "inventory"
    return "sales"
