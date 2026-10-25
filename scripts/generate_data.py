"""
generate_data.py
-----------------
Generates a large, statistically realistic SYNTHETIC dataset for the
Pharmacy Intelligence demo. Nothing here represents a real pharmacy,
real suppliers, or real people.

Run:
    python scripts/generate_data.py

Outputs CSV files into ../data/:
    products.csv
    sales.csv
    purchases.csv
    inventory.csv
"""

import csv
import os
import random
from datetime import datetime, timedelta

random.seed(42)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data")
os.makedirs(DATA_DIR, exist_ok=True)

PERIOD_START = datetime(2026, 1, 1)
PERIOD_END = datetime(2026, 6, 30)
TOTAL_DAYS = (PERIOD_END - PERIOD_START).days + 1

CATEGORIES = [
    "painkillers", "vitamins", "antibiotics", "cold_flu", "dermatology",
    "digestive", "baby_care", "personal_care", "medical_supplies", "diabetes_care",
]

MANUFACTURERS = [
    "MedLibya Labs", "Atlas Pharma", "NorthShore Pharmaceuticals", "Nile Health",
    "Sahara Bio", "Green Crescent Pharma", "Tripoli Pharma Group", "Coral Health Co",
]

UNITS = ["box", "strip", "bottle", "tube", "piece"]

PRODUCT_NAME_ROOTS = {
    "painkillers": ["Panadol", "Panadol Extra", "Algex", "Reliva", "Feverex", "Nurofen", "Doloran"],
    "vitamins": ["Vitamin C 1000", "Multivit Daily", "Zinc Plus", "Vitamin D3", "Omega Gold", "B-Complex", "Calcimax"],
    "antibiotics": ["Amoxiclav", "Zithrocin", "Ciprovex", "Cefanox", "Augmex", "Clarithin"],
    "cold_flu": ["Coldrex", "Fluvex Syrup", "Nasocare Spray", "Coughlin Syrup", "Throat Ease Lozenge", "Bronchicare"],
    "dermatology": ["Dermazin Cream", "Sunblock 50", "Acnex Gel", "Hydraline Lotion", "Calamine Plus"],
    "digestive": ["Gastrol", "Antacid Fast", "Digezyme", "Rehydrex ORS", "Probiotix"],
    "baby_care": ["BabySoft Diapers", "Infacare Formula", "Gripe Water", "Baby Lotion", "Colic Ease Drops"],
    "personal_care": ["Sensiderm Soap", "Oral Fresh Mouthwash", "HandCare Sanitizer", "ShampooPlus", "SunCare Balm"],
    "medical_supplies": ["Sterile Gauze", "Elastic Bandage", "Digital Thermometer", "BP Monitor", "Glucose Strips", "Nebulizer Mask"],
    "diabetes_care": ["Glucosafe Strips", "InsulEase Pen Needles", "Diabetic Foot Cream", "Metglu Support"],
}

STRENGTHS = ["", "250mg", "500mg", "10mg", "20mg", "5%", "1%", "60ml", "100ml", "30 tabs", "20 caps"]


def money(v):
    return round(v, 2)


class ProductProfile:
    ARCHETYPES = [
        ("fast_mover", 0.10),
        ("medium_mover", 0.32),
        ("slow_mover", 0.30),
        ("dead_stock", 0.14),
        ("seasonal", 0.08),
        ("sudden_spike", 0.06),
    ]

    @staticmethod
    def pick():
        r = random.random()
        cum = 0
        for name, weight in ProductProfile.ARCHETYPES:
            cum += weight
            if r <= cum:
                return name
        return "medium_mover"


def generate_products(n=3200):
    products = []
    barcode_start = 622100000000
    for i in range(n):
        cat = random.choice(CATEGORIES)
        root = random.choice(PRODUCT_NAME_ROOTS[cat])
        strength = random.choice(STRENGTHS)
        name = f"{root} {strength}".strip()
        manufacturer = random.choice(MANUFACTURERS)
        unit = random.choice(UNITS)

        base_price_ranges = {
            "painkillers": (2, 8), "vitamins": (4, 15), "antibiotics": (8, 35),
            "cold_flu": (3, 12), "dermatology": (6, 22), "digestive": (3, 10),
            "baby_care": (5, 25), "personal_care": (3, 14), "medical_supplies": (5, 60),
            "diabetes_care": (10, 45),
        }
        lo, hi = base_price_ranges[cat]
        purchase_price = money(random.uniform(lo, hi))

        margin_roll = random.random()
        if margin_roll < 0.15:
            margin = random.uniform(0.55, 0.9)
        elif margin_roll < 0.75:
            margin = random.uniform(0.22, 0.45)
        else:
            margin = random.uniform(0.05, 0.15)
        selling_price = money(purchase_price * (1 + margin))

        archetype = ProductProfile.pick()

        products.append({
            "barcode": str(barcode_start + i),
            "product_name": name,
            "category": cat,
            "manufacturer": manufacturer,
            "unit": unit,
            "purchase_price": purchase_price,
            "selling_price": selling_price,
            "archetype": archetype,
        })
    return products


def daily_demand_multiplier(day_index, archetype, category):
    day = PERIOD_START + timedelta(days=day_index)
    weekday = day.weekday()
    weekday_factor = {0: 0.9, 1: 0.9, 2: 0.95, 3: 1.05, 4: 1.25, 5: 1.2, 6: 0.85}[weekday]

    month = day.month
    seasonal_factor = 1.0
    if category == "cold_flu":
        seasonal_factor = {1: 1.6, 2: 1.5, 3: 1.1, 4: 0.8, 5: 0.6, 6: 0.55}[month]
    elif category == "vitamins":
        seasonal_factor = {1: 1.2, 2: 1.15, 3: 1.05, 4: 1.0, 5: 1.05, 6: 1.1}[month]
    elif category == "dermatology":
        seasonal_factor = {1: 0.7, 2: 0.75, 3: 0.9, 4: 1.1, 5: 1.35, 6: 1.5}[month]

    if archetype == "seasonal":
        seasonal_factor *= {1: 0.6, 2: 0.7, 3: 0.9, 4: 1.2, 5: 1.5, 6: 1.6}[month]

    growth_factor = 1.0 + (day_index / TOTAL_DAYS) * 0.12
    return weekday_factor * seasonal_factor * growth_factor


PEAK_HOUR_WEIGHTS = {
    9: 0.9, 10: 1.1, 11: 1.2, 12: 1.0, 13: 0.7, 14: 0.6, 15: 0.8,
    16: 1.0, 17: 1.3, 18: 1.8, 19: 1.9, 20: 1.6, 21: 1.0, 22: 0.5,
}


def pick_hour():
    hours = list(PEAK_HOUR_WEIGHTS.keys())
    weights = list(PEAK_HOUR_WEIGHTS.values())
    return random.choices(hours, weights=weights, k=1)[0]


def generate_sales(products, target_invoices=19500):
    base_rate = {
        "fast_mover": 3.2, "medium_mover": 1.1, "slow_mover": 0.35,
        "dead_stock": 0.0, "seasonal": 0.9, "sudden_spike": 0.5,
    }

    by_category = {}
    for p in products:
        by_category.setdefault(p["category"], []).append(p)

    association_pairs = []
    assoc_categories = ["cold_flu", "vitamins", "painkillers", "digestive"]
    for cat in assoc_categories:
        pool = [p for p in by_category[cat] if p["archetype"] in ("fast_mover", "medium_mover")]
        random.shuffle(pool)
        for i in range(0, min(len(pool) - 1, 10), 2):
            association_pairs.append((pool[i], pool[i + 1]))

    spike_windows = {}
    for p in products:
        if p["archetype"] == "sudden_spike":
            start = random.randint(TOTAL_DAYS - 60, TOTAL_DAYS - 20)
            spike_windows[p["barcode"]] = (start, start + random.randint(10, 18))

    sales_rows = []
    invoice_no = 100000
    invoices_per_day_base = target_invoices / TOTAL_DAYS

    for day_index in range(TOTAL_DAYS):
        day = PERIOD_START + timedelta(days=day_index)
        weekday = day.weekday()
        weekday_factor = {0: 0.9, 1: 0.9, 2: 0.95, 3: 1.05, 4: 1.25, 5: 1.2, 6: 0.85}[weekday]
        n_invoices_today = max(1, int(round(invoices_per_day_base * weekday_factor * random.uniform(0.85, 1.15))))

        for _ in range(n_invoices_today):
            invoice_no += 1
            hour = pick_hour()
            minute = random.randint(0, 59)
            n_items = random.choices([1, 2, 3, 4, 5], weights=[45, 27, 16, 8, 4], k=1)[0]

            basket = []
            if random.random() < 0.20 and association_pairs:
                pair = random.choice(association_pairs)
                basket.extend(pair)
                n_items = max(n_items, 2)

            attempts = 0
            while len(basket) < n_items and attempts < 20:
                attempts += 1
                cand = random.choice(products)
                if cand["archetype"] == "dead_stock":
                    continue
                basket.append(cand)

            for prod in basket[:n_items]:
                rate = base_rate[prod["archetype"]]
                if prod["barcode"] in spike_windows:
                    s, e = spike_windows[prod["barcode"]]
                    if s <= day_index <= e:
                        rate = rate + 4.0
                if rate <= 0:
                    continue
                qty = max(1, int(round(random.gauss(1.4, 0.8))))
                qty = min(qty, 6)

                revenue = money(qty * prod["selling_price"])
                cost = money(qty * prod["purchase_price"])
                profit = money(revenue - cost)

                sales_rows.append({
                    "invoice_no": invoice_no,
                    "date": day.strftime("%Y-%m-%d"),
                    "time": f"{hour:02d}:{minute:02d}",
                    "barcode": prod["barcode"],
                    "product_name": prod["product_name"],
                    "category": prod["category"],
                    "quantity": qty,
                    "selling_price": prod["selling_price"],
                    "purchase_price": prod["purchase_price"],
                    "revenue": revenue,
                    "profit": profit,
                })

        if len(sales_rows) > 45000:
            break

    return sales_rows


SUPPLIERS = [
    "Al-Nahda Medical Distribution", "Libya Pharma Trading", "Green Crescent Distributors",
    "Mediterranean Health Supplies", "Tripoli Wholesale Pharma", "Sahara Medical Import Co",
]


def generate_purchases(products, target=1300):
    rows = []
    po_no = 500000
    for _ in range(target):
        po_no += 1
        day_index = random.randint(0, TOTAL_DAYS - 1)
        day = PERIOD_START + timedelta(days=day_index)
        prod = random.choice(products)
        qty = random.randint(20, 400)
        total = money(qty * prod["purchase_price"])
        rows.append({
            "po_no": po_no,
            "date": day.strftime("%Y-%m-%d"),
            "supplier": random.choice(SUPPLIERS),
            "barcode": prod["barcode"],
            "product_name": prod["product_name"],
            "quantity": qty,
            "purchase_price": prod["purchase_price"],
            "total": total,
        })
    rows.sort(key=lambda r: r["date"])
    return rows


def compute_units_sold(sales_rows):
    sold = {}
    last_sale_date = {}
    for r in sales_rows:
        sold[r["barcode"]] = sold.get(r["barcode"], 0) + r["quantity"]
        d = r["date"]
        if r["barcode"] not in last_sale_date or d > last_sale_date[r["barcode"]]:
            last_sale_date[r["barcode"]] = d
    return sold, last_sale_date


def generate_inventory(products, sales_rows, purchases_rows):
    total_sold, last_sale_date = compute_units_sold(sales_rows)
    total_purchased = {}
    for r in purchases_rows:
        total_purchased[r["barcode"]] = total_purchased.get(r["barcode"], 0) + r["quantity"]

    rows = []
    for p in products:
        archetype = p["archetype"]
        purchased = total_purchased.get(p["barcode"], random.randint(50, 300))
        sold = total_sold.get(p["barcode"], 0)

        if archetype == "dead_stock":
            qty_on_hand = random.randint(15, 120)
        elif archetype == "fast_mover":
            qty_on_hand = max(0, random.randint(0, 40))
        elif archetype == "slow_mover":
            qty_on_hand = random.randint(20, 90)
        else:
            qty_on_hand = max(0, purchased - sold + random.randint(-10, 30))
            qty_on_hand = max(0, min(qty_on_hand, 400))

        stock_value = money(qty_on_hand * p["purchase_price"])

        r = random.random()
        if r < 0.05:
            expiry_days = random.randint(3, 7)
        elif r < 0.15:
            expiry_days = random.randint(8, 30)
        elif r < 0.30:
            expiry_days = random.randint(31, 90)
        else:
            expiry_days = random.randint(120, 720)
        expiry_date = (PERIOD_END + timedelta(days=expiry_days)).strftime("%Y-%m-%d")

        rows.append({
            "barcode": p["barcode"],
            "product_name": p["product_name"],
            "category": p["category"],
            "quantity_on_hand": qty_on_hand,
            "purchase_price": p["purchase_price"],
            "selling_price": p["selling_price"],
            "stock_value": stock_value,
            "expiry_date": expiry_date,
            "supplier": random.choice(SUPPLIERS),
            "last_sale_date": last_sale_date.get(p["barcode"], ""),
            "archetype": archetype,
        })
    return rows


def write_csv(path, rows, fieldnames):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {len(rows):>7,} rows -> {os.path.relpath(path, ROOT)}")


def main():
    print("Generating synthetic Pharmacy Intelligence dataset...")
    products = generate_products(3200)
    sales_rows = generate_sales(products, target_invoices=19500)
    purchases_rows = generate_purchases(products, target=1300)
    inventory_rows = generate_inventory(products, sales_rows, purchases_rows)

    write_csv(
        os.path.join(DATA_DIR, "products.csv"), products,
        ["barcode", "product_name", "category", "manufacturer", "unit",
         "purchase_price", "selling_price", "archetype"],
    )
    write_csv(
        os.path.join(DATA_DIR, "sales.csv"), sales_rows,
        ["invoice_no", "date", "time", "barcode", "product_name", "category",
         "quantity", "selling_price", "purchase_price", "revenue", "profit"],
    )
    write_csv(
        os.path.join(DATA_DIR, "purchases.csv"), purchases_rows,
        ["po_no", "date", "supplier", "barcode", "product_name", "quantity",
         "purchase_price", "total"],
    )
    write_csv(
        os.path.join(DATA_DIR, "inventory.csv"), inventory_rows,
        ["barcode", "product_name", "category", "quantity_on_hand", "purchase_price",
         "selling_price", "stock_value", "expiry_date", "supplier", "last_sale_date", "archetype"],
    )

    n_invoices = len(set(r["invoice_no"] for r in sales_rows))
    print(f"\nSummary: {len(products):,} products | {n_invoices:,} sales invoices | "
          f"{len(sales_rows):,} sale line items | {len(purchases_rows):,} purchase orders")


if __name__ == "__main__":
    main()
