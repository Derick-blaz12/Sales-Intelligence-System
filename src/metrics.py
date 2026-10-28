import pandas as pd
from load_data import load_merged

# Business decision: which order statuses count as recognised sales.
# Documented in docs/metric_definitions.md
INCLUDED_STATUSES = ["delivered"]


def section(title: str) -> None:
    print(f"\n{'=' * 60}\n{title}\n{'=' * 60}")


def main() -> None:
    pd.set_option("display.width", 200)
    pd.set_option("display.float_format", "{:,.2f}".format)

    df = load_merged()

    # ---------- Part C (1): structure still holds ----------
    section("STRUCTURE CHECKS")
    print(f"Rows: {len(df):,}")
    print(f"(order_id, order_item_id) unique? "
          f"{not df.duplicated(subset=['order_id', 'order_item_id']).any()}")
    print(f"Items with no order status: {df['order_status'].isna().sum():,}")

    # ---------- What is at stake in the status decision ----------
    section("BY ORDER STATUS (all rows, nothing excluded)")
    by_status = (
        df.groupby("order_status")
          .agg(
              orders=("order_id", "nunique"),
              units=("order_id", "size"),
              item_revenue=("price", "sum"),
              freight=("freight_value", "sum"),
          )
          .sort_values("item_revenue", ascending=False)
    )
    print(by_status)
    print(f"\nTotal price across ALL statuses: {df['price'].sum():,.2f}")

    # ---------- Part B: metrics on included orders ----------
    included = df[df["order_status"].isin(INCLUDED_STATUSES)]

    item_revenue = included["price"].sum()
    freight = included["freight_value"].sum()
    unique_orders = included["order_id"].nunique()
    units_sold = len(included)

    order_totals = included.groupby("order_id")["price"].sum()
    aov = order_totals.mean()

    section(f"METRICS (statuses included: {INCLUDED_STATUSES})")
    print(f"Item sales revenue:    {item_revenue:>15,.2f}")
    print(f"Freight charges:       {freight:>15,.2f}")
    print(f"Unique orders:         {unique_orders:>15,}")
    print(f"Units sold:            {units_sold:>15,}")
    print(f"Average order value:   {aov:>15,.2f}")

    # ---------- Part C: verification ----------
    section("VERIFICATION")

    # Orders: rows vs distinct IDs
    print(f"Included rows: {len(included):,} vs unique orders: {unique_orders:,}")
    print(f"  -> counting rows as orders would overstate orders by "
          f"{len(included) - unique_orders:,}")

    # AOV: two routes must agree
    print(f"\nAOV via revenue / orders:     {item_revenue / unique_orders:,.4f}")
    print(f"AOV via mean of order totals: {aov:,.4f}")
    assert abs(item_revenue / unique_orders - aov) < 1e-9

    # AOV is NOT the average item price
    print(f"Average ITEM price (not AOV): {included['price'].mean():,.4f}")

    # Price vs price + freight
    with_freight = item_revenue + freight
    print(f"\nItem revenue (price only):    {item_revenue:,.2f}")
    print(f"Price + freight:              {with_freight:,.2f}")
    print(f"Freight as % of price + freight: {freight / with_freight * 100:.1f}%")

    # Order totals sanity
    print(f"\nOrder totals: min {order_totals.min():,.2f}, "
          f"median {order_totals.median():,.2f}, max {order_totals.max():,.2f}")


if __name__ == "__main__":
    main()