import pandas as pd
from load_data import load_merged

INCLUDED_STATUSES = ["delivered"]  # same decision as Milestone 3


def section(title: str) -> None:
    print(f"\n{'=' * 60}\n{title}\n{'=' * 60}")


def main() -> None:
    pd.set_option("display.width", 200)
    pd.set_option("display.max_rows", 100)
    pd.set_option("display.float_format", "{:,.2f}".format)

    df = load_merged()

    # ---------- Requirement 1 & 2: dtype, range, missing ----------
    section("PURCHASE TIMESTAMP CHECKS")
    ts = df["order_purchase_timestamp"]
    print(f"dtype: {ts.dtype}")
    print(f"Missing / unparseable (all rows): {ts.isna().sum():,}")
    print(f"Earliest (all statuses): {ts.min()}")
    print(f"Latest   (all statuses): {ts.max()}")

    included = df[df["order_status"].isin(INCLUDED_STATUSES)].copy()
    ts_inc = included["order_purchase_timestamp"]
    print(f"\nDelivered rows: {len(included):,}")
    print(f"Missing purchase date (delivered): {ts_inc.isna().sum():,}")
    print(f"Earliest (delivered): {ts_inc.min()}")
    print(f"Latest   (delivered): {ts_inc.max()}")

    # ---------- Requirements 3-5: monthly summary ----------
    included["month"] = included["order_purchase_timestamp"].dt.to_period("M")

    # Step A: one row per order (so AOV uses order totals, not item rows)
    order_level = (
        included.groupby(["order_id", "month"], as_index=False)
                .agg(order_total=("price", "sum"))
    )
    assert order_level["order_id"].is_unique, "An order landed in two months!"

    # Step B: monthly summary from order-level data
    monthly = (
        order_level.groupby("month")
                   .agg(orders=("order_id", "nunique"),
                        item_value=("order_total", "sum"),
                        aov=("order_total", "mean"))
    )

    # Units per month, from item rows
    monthly["units"] = included.groupby("month").size()

    section("MONTHLY SUMMARY (delivered only)")
    print(monthly)

    # ---------- Verification ----------
    section("VERIFICATION")
    print(f"Sum of monthly item value: {monthly['item_value'].sum():,.2f}")
    print(f"Milestone 3 delivered revenue: {included['price'].sum():,.2f}")
    print(f"Sum of monthly orders: {monthly['orders'].sum():,}")
    print(f"Unique delivered orders:  {included['order_id'].nunique():,}")

    # ---------- Requirement 6: edge months ----------
    section("EARLIEST AND LATEST MONTHS")
    print(monthly.head(4))
    print(monthly.tail(4))

    section("GAPS IN THE MONTH SEQUENCE")
    full = pd.period_range(monthly.index.min(), monthly.index.max(), freq="M")
    missing_months = full.difference(monthly.index)
    print(f"Months with no delivered orders: {list(missing_months)}")

    section("EARLIEST / LATEST DAYS PER EDGE MONTH")
    for label, month in [("first", monthly.index.min()), ("last", monthly.index.max())]:
        sub = included[included["month"] == month]["order_purchase_timestamp"]
        print(f"{label} month {month}: {sub.min()} -> {sub.max()}  "
              f"({sub.dt.normalize().nunique()} distinct days with orders)")


if __name__ == "__main__":
    main()