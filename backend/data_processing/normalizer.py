"""
Maps loosely-named source columns (Arabic or English, varying naming
conventions) to the platform's standard schema. Never assumes a fixed
column order or exact names -- see README "Import Architecture".
"""

# candidate source header -> standard field, per table type
COLUMN_ALIASES = {
    "sales": {
        "product_name": ["اسم الصنف", "اسم المنتج", "الصنف", "product name", "item name", "product", "name"],
        "quantity": ["الكمية", "qty", "quantity", "units"],
        "date": ["التاريخ", "تاريخ البيع", "date", "sale date", "invoice date"],
        "selling_price": ["سعر البيع", "selling price", "sale price", "price"],
        "purchase_price": ["سعر الشراء", "cost price", "purchase price", "cost"],
        "barcode": ["الباركود", "barcode", "sku"],
        "invoice_no": ["رقم الفاتورة", "invoice", "invoice no", "invoice_number"],
        "category": ["الفئة", "category"],
    },
    "purchases": {
        "product_name": ["اسم الصنف", "product name", "item name", "product"],
        "quantity": ["الكمية", "qty", "quantity"],
        "date": ["التاريخ", "date"],
        "purchase_price": ["سعر الشراء", "cost price", "purchase price", "cost"],
        "supplier": ["المورد", "supplier", "vendor"],
        "barcode": ["الباركود", "barcode", "sku"],
        "po_no": ["رقم فاتورة الشراء", "po", "po no", "purchase order"],
    },
    "inventory": {
        "product_name": ["اسم الصنف", "product name", "item name", "product"],
        "quantity_on_hand": ["الكمية الحالية", "quantity", "qty", "stock", "on hand"],
        "purchase_price": ["سعر الشراء", "cost price"],
        "selling_price": ["سعر البيع", "selling price"],
        "expiry_date": ["تاريخ الصلاحية", "expiry", "expiry date", "exp date"],
        "barcode": ["الباركود", "barcode", "sku"],
        "category": ["الفئة", "category"],
    },
}


def normalize(value: str) -> str:
    return value.strip().lower()


def detect_mapping(columns, table_type):
    """
    For each raw column header, suggest the standard field it most likely maps to.
    Returns {raw_column: suggested_standard_field | None}.
    """
    aliases = COLUMN_ALIASES.get(table_type, {})
    suggestions = {}
    for raw_col in columns:
        norm = normalize(str(raw_col))
        match = None
        for standard_field, candidates in aliases.items():
            if norm in [normalize(c) for c in candidates] or norm == standard_field:
                match = standard_field
                break
        suggestions[raw_col] = match
    return suggestions


def apply_mapping(df, mapping):
    """mapping: {raw_column: standard_field}. Drops unmapped columns, renames the rest."""
    keep = {raw: std for raw, std in mapping.items() if std and raw in df.columns}
    return df[list(keep.keys())].rename(columns=keep)
