"""
Loads the CSV dataset into pandas DataFrames and caches it in memory.
In this demo, "uploaded" data replaces the in-memory frames for the
current server process (no database — intentional, see README).
"""
import os
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(ROOT, "data")

_cache = {}


def _read(name):
    path = os.path.join(DATA_DIR, f"{name}.csv")
    df = pd.read_csv(path)
    return df


def load_all(force=False):
    global _cache
    if _cache and not force:
        return _cache

    products = _read("products")
    sales = _read("sales")
    purchases = _read("purchases")
    inventory = _read("inventory")

    sales["date"] = pd.to_datetime(sales["date"])
    purchases["date"] = pd.to_datetime(purchases["date"])
    inventory["expiry_date"] = pd.to_datetime(inventory["expiry_date"])
    inventory["last_sale_date"] = pd.to_datetime(inventory["last_sale_date"], errors="coerce")

    _cache = {
        "products": products,
        "sales": sales,
        "purchases": purchases,
        "inventory": inventory,
    }
    return _cache


def get(name):
    return load_all()[name]


def set_frame(name, df):
    """Used by the CSV/Excel import flow to swap in a customer's normalized data."""
    load_all()
    _cache[name] = df


def reset_to_demo():
    load_all(force=True)
