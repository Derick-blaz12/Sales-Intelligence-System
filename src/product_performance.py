from pathlib import Path
import pandas as pd
from load_data import load_merged

INCLUDED_STATUSES = ["delivered"]
START, END = "2017-01-01", "2018-09-01"   # END is exclusive
CAT = "product_category_name_english"
OUT = Path("outputs")
OUT.mkdir(exist_ok=True)


def section(title: str) -> None:
    print(f"\n{'=' * 60}\n{title}\n{'=' * 60}")


def summarise(df: pd.DataFrame, key: str) -> pd.DataFrame:
    """Three metrics side by side, grouped by `key`."""
    return df.groupby(key).agg(
        order_count=("order_id", "nunique"),     # distinct orders containing it
        item_record_count=("order_id", "size"),  # rows, not verified quantity
        item_value=("price", "sum"),
    )


def main() -> None:
    pd.set_option("display.width", 220)
    pd.set_option("display.max_columns", None)
    pd.set_option("display.max_colwidth", 40)
    pd.set_option("display.float_format", "{:,.2f}".format)

    df = load_merged()

    # ---------- Requirement 6: checks BEFORE interpreting anything ----------
    section("PRE-ANALYSIS CHECKS (all rows)")
    print(f"Missing product_id:            {df['product_id'].isna().sum():,}")
    print(f"Raw category missing:          {df['product_category_name'].isna().sum():,}")
    print(f"Items labelled 'unknown':      {(df[CAT] == 'unknown').sum():,}")
    print(f"Missing English label:         {df[CAT].isna().sum():,}")

    window = df[
        df["order_status"].isin(INCLUDED_STATUSES)
        & (df["order_purchase_timestamp"] >= START)
        & (df["order_purchase_timestamp"] < END)
    ].copy()
    assert window["product_id"].notna().all()
    assert window[CAT].notna().all()
    # each product must have exactly one category, or product->category is ambiguous
    assert window.groupby("product_id")[CAT].nunique().max() == 1

    total_value = window["price"].sum()
    section("ANALYSIS WINDOW")
    print(f"Item records:   {len(window):,}")
    print(f"Distinct orders:{window['order_id'].nunique():>10,}")
    print(f"Item value:     {total_value:,.2f}")
    print(f"Date range:     {window['order_purchase_timestamp'].min()} -> "
          f"{window['order_purchase_timestamp'].max()}")
    print(f"'unknown' share of item value: "
          f"{window.loc[window[CAT] == 'unknown', 'price'].sum() / total_value * 100:.2f}%")

    # ---------- Requirements 1 & 2: categories ----------
    cat = summarise(window, CAT)
    cat["value_share_%"] = cat["item_value"] / total_value * 100
    cat["records_share_%"] = cat["item_record_count"] / len(window) * 100
    cat["value_rank"] = cat["item_value"].rank(ascending=False, method="min").astype(int)
    cat["records_rank"] = cat["item_record_count"].rank(ascending=False, method="min").astype(int)
    cat["orders_rank"] = cat["order_count"].rank(ascending=False, method="min").astype(int)

    section("CATEGORY RECONCILIATION")
    assert abs(cat["item_value"].sum() - total_value) < 1e-6
    assert cat["item_record_count"].sum() == len(window)
    print("Category item value and records sum back to the window totals: OK")
    print(f"Sum of category order_counts: {cat['order_count'].sum():,} "
          f"vs distinct orders {window['order_id'].nunique():,}")
    print("  -> larger because one order can contain several categories")

    section("TOP 15 CATEGORIES BY ITEM VALUE (with all three ranks)")
    print(cat.sort_values("item_value", ascending=False).head(15))

    section("TOP 15 CATEGORIES BY ITEM-RECORD COUNT")
    print(cat.sort_values("item_record_count", ascending=False).head(15)
             [["item_record_count", "records_share_%", "item_value", "value_rank"]])

    section("CATEGORIES WHERE VALUE RANK AND RECORD RANK DIFFER MOST")
    cat["rank_gap"] = (cat["value_rank"] - cat["records_rank"]).abs()
    print(cat.sort_values("rank_gap", ascending=False).head(8)
             [["value_rank", "records_rank", "orders_rank", "item_value", "item_record_count"]])

    # ---------- Requirements 3 & 4: products ----------
    prod = summarise(window, "product_id")
    prod["category"] = window.drop_duplicates("product_id").set_index("product_id")[CAT]
    prod["avg_price"] = prod["item_value"] / prod["item_record_count"]
    prod["records_per_order"] = prod["item_record_count"] / prod["order_count"]
    dates = window.groupby("product_id")["order_purchase_timestamp"].agg(
        first_order="min", last_order="max")
    prod = prod.join(dates)

    section(f"PRODUCT TABLE: {len(prod):,} products sold in the window")
    section("TOP 15 PRODUCTS BY ITEM VALUE")
    print(prod.sort_values("item_value", ascending=False).head(15)
              [["category", "order_count", "item_record_count", "item_value", "avg_price"]])

    section("TOP 15 PRODUCTS BY DISTINCT ORDER COUNT")
    print(prod.sort_values("order_count", ascending=False).head(15)
              [["category", "order_count", "item_record_count", "item_value", "avg_price"]])

    section("PRODUCTS WHERE records_per_order > 1 (same product, several rows per order)")
    print(f"{(prod['records_per_order'] > 1).sum():,} products; "
          f"max records_per_order = {prod['records_per_order'].max():.1f}")

    # ---------- Requirement 5: the long tail ----------
    section("LONG TAIL: how concentrated is item value?")
    ranked = prod.sort_values("item_value", ascending=False)
    cum_share = ranked["item_value"].cumsum() / total_value * 100
    for pct in (1, 5, 10, 20, 50):
        n = int(round(len(ranked) * pct / 100))
        print(f"Top {pct:>2}% of products ({n:>6,}) -> {cum_share.iloc[n - 1]:5.1f}% of item value")

    section("LONG TAIL: products by order-count threshold")
    rows = []
    for t in (1, 2, 3, 5, 10):
        low = prod[prod["order_count"] <= t]
        rows.append({
            "orders <=": t,
            "products": len(low),
            "% of products": len(low) / len(prod) * 100,
            "item_value": low["item_value"].sum(),
            "% of value": low["item_value"].sum() / total_value * 100,
        })
    print(pd.DataFrame(rows).to_string(index=False))

    section("LOW REACH (<= 2 orders) x VALUE (above / below median product value)")
    median_value = prod["item_value"].median()
    prod["low_reach"] = prod["order_count"] <= 2
    prod["low_value"] = prod["item_value"] <= median_value
    print(f"Median product item value: {median_value:,.2f}")
    print(pd.crosstab(prod["low_reach"], prod["low_value"],
                      rownames=["low_reach"], colnames=["low_value"]))

    section("LOW REACH BUT HIGH VALUE: top 10 (niche, high-ticket?)")
    niche = prod[prod["low_reach"]].sort_values("item_value", ascending=False).head(10)
    print(niche[["category", "order_count", "item_value", "avg_price"]])

    section("HIGH REACH BUT LOW VALUE PER ORDER: top 10 by orders, avg_price below median")
    cheap = prod[prod["avg_price"] < prod["avg_price"].median()]
    print(cheap.sort_values("order_count", ascending=False).head(10)
              [["category", "order_count", "item_value", "avg_price"]])

    section("TAIL CAVEAT: are low-reach products just recent launches?")
    low = prod[prod["low_reach"]]
    recent = (low["first_order"] >= "2018-06-01").mean() * 100
    print(f"Low-reach products whose first order was on/after 2018-06-01: {recent:.1f}%")
    print(f"Same share across ALL products: "
          f"{(prod['first_order'] >= '2018-06-01').mean() * 100:.1f}%")

    # ---------- Save tables ----------
    cat.to_csv(OUT / "category_performance.csv")
    prod.to_csv(OUT / "product_performance.csv")
    print(f"\nSaved tables to {OUT.resolve()}")


if __name__ == "__main__":
    main()