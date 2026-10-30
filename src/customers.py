from pathlib import Path
import numpy as np
import pandas as pd

from config import INCLUDED_STATUSES, START, END
from load_data import load_merged

REF = pd.Timestamp(END)
EXPECTED_TOTAL = 13_181_027.13          # verified in verify_claims.py
OUT = Path("outputs")
OUT.mkdir(exist_ok=True)


def section(title: str) -> None:
    print(f"\n{'=' * 60}\n{title}\n{'=' * 60}")


def order_level(df, statuses, start=START, end=END):
    """One row per order: who bought, when, and the order's item value."""
    w = df[df["order_status"].isin(statuses)
           & (df["order_purchase_timestamp"] >= start)
           & (df["order_purchase_timestamp"] < end)]
    lvl = (w.groupby(["order_id", "customer_unique_id"], as_index=False)
             .agg(order_value=("price", "sum"),
                  purchased=("order_purchase_timestamp", "first")))
    assert lvl["order_id"].is_unique, "An order maps to two people!"
    assert lvl["customer_unique_id"].notna().all()
    return lvl


def people_table(lvl):
    lvl = lvl.sort_values(["customer_unique_id", "purchased", "order_id"])
    lvl = lvl.assign(n=lvl.groupby("customer_unique_id").cumcount())
    p = lvl.groupby("customer_unique_id").agg(
        orders=("order_id", "nunique"),
        spend=("order_value", "sum"),
        first_order=("purchased", "min"),
        last_order=("purchased", "max"),
    )
    second = lvl[lvl["n"] == 1].set_index("customer_unique_id")["purchased"]
    p["second_order"] = second
    p["days_to_second"] = (p["second_order"] - p["first_order"]).dt.total_seconds() / 86400
    return p


def main() -> None:
    pd.set_option("display.width", 200)
    pd.set_option("display.max_columns", None)
    pd.set_option("display.float_format", "{:,.2f}".format)

    df = load_merged()

    # ---------- Base definition: delivered, 2017-01 to 2018-08 ----------
    lvl = order_level(df, INCLUDED_STATUSES)
    p = people_table(lvl)
    total = lvl["order_value"].sum()
    assert abs(total - EXPECTED_TOTAL) < 0.005, f"Total changed: {total:,.2f}"
    assert abs(p["spend"].sum() - total) < 1e-6

    section("BASE DEFINITION (delivered, purchases 2017-01 to 2018-08)")
    print(f"Orders:                {len(lvl):,}")
    print(f"Unique customers:      {len(p):,}   (customer_unique_id, not customer_id)")
    print(f"Orders per customer:   {len(lvl) / len(p):.4f}")
    print(f"Item value:            {total:,.2f}  (reconciles with verified total)")

    section("ORDERS PER CUSTOMER")
    dist = p["orders"].clip(upper=5).value_counts().sort_index()
    dist.index = [f"{i}" if i < 5 else "5+" for i in dist.index]
    print(pd.DataFrame({"customers": dist, "% of customers": dist / len(p) * 100}))
    print(f"Max orders by one customer: {p['orders'].max()}")

    # ---------- Repeat share + sensitivity ----------
    section("REPEAT-CUSTOMER SHARE UNDER DIFFERENT DEFINITIONS")
    variants = {
        "Base: delivered, 2017-01..2018-08": lvl,
        "Delivered, ALL dates (adds 2016)":
            order_level(df, INCLUDED_STATUSES, "2016-01-01", "2019-01-01"),
        "Non-canceled orders, 2017-01..2018-08":
            order_level(df, [s for s in df["order_status"].unique()
                             if s not in ("canceled", "unavailable")]),
    }
    rows = []
    for name, v in variants.items():
        pv = people_table(v)
        rows.append({"definition": name, "customers": len(pv),
                     "repeat customers": int((pv["orders"] >= 2).sum()),
                     "repeat %": (pv["orders"] >= 2).mean() * 100})
    print(pd.DataFrame(rows).to_string(index=False))

    # ---------- One-time vs repeat ----------
    section("ONE-TIME VS REPEAT CUSTOMERS")
    p["type"] = np.where(p["orders"] >= 2, "repeat (2+ orders)", "one-time")
    g = p.groupby("type").agg(customers=("spend", "size"),
                              orders=("orders", "sum"),
                              item_value=("spend", "sum"),
                              avg_spend_per_customer=("spend", "mean"))
    g["% of customers"] = g["customers"] / len(p) * 100
    g["% of item value"] = g["item_value"] / total * 100
    print(g)
    one_time_orders = lvl[lvl["customer_unique_id"].isin(p.index[p["orders"] == 1])]
    rep_orders = lvl[lvl["customer_unique_id"].isin(p.index[p["orders"] >= 2])]
    print(f"\nAverage ORDER value: one-time {one_time_orders['order_value'].mean():,.2f}"
          f" vs repeat {rep_orders['order_value'].mean():,.2f}")

    # ---------- Spend distribution ----------
    section("SPEND PER CUSTOMER")
    print(p["spend"].describe(percentiles=[0.25, 0.5, 0.75, 0.9, 0.99]))

    section("CONCENTRATION OF SPEND (ties broken by customer_unique_id)")
    ranked = (p["spend"].rename("spend").reset_index()
                .sort_values(["spend", "customer_unique_id"], ascending=[False, True])
                .reset_index(drop=True))
    ranked["cum_share"] = ranked["spend"].cumsum() / total * 100
    N = len(ranked)
    print(f"Denominator: all {N:,} customers; shares of {total:,.2f}")
    for pct in (1, 10, 20):
        k = int(round(N * pct / 100))
        tie = ranked.loc[k - 1, "spend"] == ranked.loc[k, "spend"]
        print(f"Top {pct:>2}% = {k:>6,} customers -> "
              f"{ranked.loc[k - 1, 'cum_share']:5.1f}% (tie at cut-off: {tie})")

    section("TOP 10 CUSTOMERS BY ITEM VALUE")
    top = p.sort_values("spend", ascending=False).head(10)
    print(top[["orders", "spend", "first_order", "last_order"]])

    # ---------- Right-censoring: repeat within 90 days, by first-order month ----------
    section("REPEAT WITHIN 90 DAYS, BY FIRST-ORDER MONTH")
    cutoff = REF - pd.Timedelta(days=90)
    p["cohort"] = p["first_order"].dt.to_period("M")
    p["repeat_90d"] = p["days_to_second"] <= 90          # NaN -> False
    eligible = p[p["first_order"] <= cutoff]
    cohort = eligible.groupby("cohort").agg(customers=("repeat_90d", "size"),
                                            repeat_90d=("repeat_90d", "sum"))
    cohort["repeat_90d_%"] = cohort["repeat_90d"] / cohort["customers"] * 100
    print(cohort)
    print(f"\nEligible (first order on/before {cutoff.date()}): {len(eligible):,} of {len(p):,}")
    print(f"Repeat within 90 days, eligible customers: "
          f"{eligible['repeat_90d'].mean() * 100:.2f}%")
    print(f"Repeat EVER within window, eligible customers: "
          f"{(eligible['orders'] >= 2).mean() * 100:.2f}%")
    print("Customers with a first order after the cut-off are excluded: "
          "they had under 90 days to return.")

    p.to_csv(OUT / "customers.csv")
    print(f"\nSaved to {OUT.resolve()}")


if __name__ == "__main__":
    main()