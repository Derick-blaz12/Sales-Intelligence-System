from pathlib import Path
import numpy as np
import pandas as pd
from config import INCLUDED_STATUSES, START, END, CATEGORY_COL
from load_data import load_merged

REF = pd.Timestamp(END)          # observation reference: end of analysis window
OUT = Path("outputs")
OUT.mkdir(exist_ok=True)


def section(title: str) -> None:
    print(f"\n{'=' * 60}\n{title}\n{'=' * 60}")


def classify(prod: pd.DataFrame, recent: int, dormant: int) -> pd.Series:
    return pd.Series(
        np.select(
            [prod["days_since_first"] <= recent,
             prod["days_since_last"] <= recent,
             prod["days_since_last"] <= dormant],
            ["1 new", "2 older, still selling", "3 quiet"],
            default="4 not seen for a long time",
        ),
        index=prod.index,
    )


def main() -> None:
    pd.set_option("display.width", 220)
    pd.set_option("display.max_columns", None)
    pd.set_option("display.float_format", "{:,.1f}".format)

    df = load_merged()
    w = df[
        df["order_status"].isin(INCLUDED_STATUSES)
        & (df["order_purchase_timestamp"] >= START)
        & (df["order_purchase_timestamp"] < END)
    ]
    total = w["price"].sum()

    prod = w.groupby("product_id").agg(
        category=(CATEGORY_COL, "first"),
        orders_containing=("order_id", "nunique"),
        item_records=("order_id", "size"),
        item_value=("price", "sum"),
        first_order=("order_purchase_timestamp", "min"),
        last_order=("order_purchase_timestamp", "max"),
    )
    prod["days_since_first"] = (REF - prod["first_order"]).dt.total_seconds() / 86400
    prod["days_since_last"] = (REF - prod["last_order"]).dt.total_seconds() / 86400
    prod["span_days"] = prod["days_since_first"] - prod["days_since_last"]

    section("SETUP")
    print(f"Reference date: {REF}   Products: {len(prod):,}")
    print(f"Item value check: {prod['item_value'].sum():,.2f} vs {total:,.2f}")
    assert abs(prod["item_value"].sum() - total) < 1e-6
    assert (prod["days_since_last"] > 0).all()

    section("RECENCY OF ALL PRODUCTS (days since last order)")
    print(prod["days_since_last"].describe(percentiles=[0.25, 0.5, 0.75, 0.9]))

    prod["reach_tier"] = pd.cut(
        prod["orders_containing"], [0, 1, 2, 5, 10, np.inf],
        labels=["1 order", "2 orders", "3-5", "6-10", "11+"])
    prod["status"] = classify(prod, 90, 180)

    section("STATUS BY ORDER-REACH TIER (count of products)")
    counts = pd.crosstab(prod["reach_tier"], prod["status"], margins=True)
    print(counts)

    section("STATUS BY ORDER-REACH TIER (% of products in tier)")
    print(pd.crosstab(prod["reach_tier"], prod["status"], normalize="index") * 100)

    section("ITEM VALUE BY STATUS (% of window item value)")
    by_status = prod.groupby("status").agg(
        products=("item_value", "size"), item_value=("item_value", "sum"))
    by_status["% of value"] = by_status["item_value"] / total * 100
    print(by_status)

    section("LOW-ORDER PRODUCTS (<= 2 orders): status, two price tiers")
    low = prod[prod["orders_containing"] <= 2].copy()
    med = prod["item_value"].median()
    low["value_group"] = np.where(low["item_value"] > med,
                                  "above-median item value", "at/below-median item value")
    print(f"Median product item value (all products): {med:,.2f}")
    print(pd.crosstab(low["status"], low["value_group"], margins=True))

    section("SENSITIVITY: low-order products by status under different thresholds")
    rows = {}
    for recent, dormant in [(60, 120), (90, 180), (120, 240)]:
        s = classify(low, recent, dormant)
        rows[f"{recent}/{dormant} days"] = s.value_counts(normalize=True).mul(100)
    print(pd.DataFrame(rows).sort_index())

    section("HIGH-ORDER PRODUCTS (11+) NOT SEEN FOR A LONG TIME")
    stale = prod[(prod["orders_containing"] >= 11)
                 & (prod["status"] == "4 not seen for a long time")]
    print(f"{len(stale):,} products, {stale['item_value'].sum():,.2f} item value "
          f"({stale['item_value'].sum() / total * 100:.2f}% of window)")
    print(stale.sort_values("item_value", ascending=False).head(10)
               [["category", "orders_containing", "item_value", "first_order", "last_order"]])

    prod.to_csv(OUT / "product_recency.csv")
    print(f"\nSaved to {OUT.resolve()}")


if __name__ == "__main__":
    main()