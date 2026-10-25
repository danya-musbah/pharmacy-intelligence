import itertools
from collections import Counter
import pandas as pd


def association_rules(sales: pd.DataFrame, min_support_count=15, top_n=20):
    """
    Simple co-occurrence based market-basket analysis (no external ML lib needed):
    support = P(A and B), confidence = P(B | A), lift = confidence / P(B).
    """
    baskets = sales.groupby("invoice_no")["product_name"].apply(lambda s: sorted(set(s)))
    baskets = baskets[baskets.apply(len) >= 2]
    total_baskets = sales["invoice_no"].nunique()

    pair_counts = Counter()
    item_counts = Counter()
    for basket in baskets:
        for item in basket:
            item_counts[item] += 1
        for a, b in itertools.combinations(basket, 2):
            pair_counts[(a, b)] += 1

    rows = []
    for (a, b), count in pair_counts.items():
        if count < min_support_count:
            continue
        support = count / total_baskets
        conf_a_to_b = count / item_counts[a]
        conf_b_to_a = count / item_counts[b]
        p_b = item_counts[b] / total_baskets
        lift = (conf_a_to_b / p_b) if p_b else 0
        rows.append({
            "product_a": a, "product_b": b, "frequency": count,
            "support": round(support, 4), "confidence": round(max(conf_a_to_b, conf_b_to_a), 3),
            "lift": round(lift, 2),
        })

    rows.sort(key=lambda r: r["frequency"], reverse=True)
    return rows[:top_n]
