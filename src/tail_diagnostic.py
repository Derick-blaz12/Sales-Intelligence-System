import pandas as pd
from load_data import load_merged

ORDER_COLS = [
    "order_id", "order_status", "order_purchase_timestamp",
    "order_approved_at", "order_delivered_carrier_date",
    "order_delivered_customer_date", "order_estimated_delivery_date",
]
OBSERVED_EVENT_COLS = [
    "order_purchase_timestamp", "order_approved_at",
    "order_delivered_carrier_date", "order_delivered_customer_date",
]


def section(title: str) -> None:
    print(f"\n{'=' * 60}\n{title}\n{'=' * 60}")


def main() -> None:
    pd.set_option("display.width", 200)
    pd.set_option("display.max_rows", 100)
    pd.set_option("display.max_columns", None)
    pd.set_option("display.float_format", "{:,.1f}".format)

    df = load_merged()

    # Item rows -> one row per order (order columns repeat across items)
    orders = df.drop_duplicates("order_id")[ORDER_COLS].copy()
    assert orders["order_id"].is_unique
    orders["month"] = orders["order_purchase_timestamp"].dt.to_period("M")
    orders["week"] = orders["order_purchase_timestamp"].dt.to_period("W")
    print(f"Orders (all statuses): {len(orders):,}")

    # ---- 1. Latest timestamp in each column ----
    section("1. EARLIEST / LATEST / MISSING PER TIMESTAMP COLUMN")
    for col in ORDER_COLS[2:] + ["order_purchase_timestamp"]:
        s = orders[col]
        print(f"{col:32s} {s.min()} -> {s.max()}   missing: {s.isna().sum():,}")

    obs_end = orders[OBSERVED_EVENT_COLS].max().max()
    print(f"\nObservation-end proxy (latest actual event): {obs_end}")
    print(f"Latest purchase:                              "
          f"{orders['order_purchase_timestamp'].max()}")

    # ---- 2. How long deliveries normally take ----
    section("2. PURCHASE -> CUSTOMER DELIVERY TIME (delivered orders, days)")
    deliv = orders[orders["order_status"] == "delivered"].dropna(
        subset=["order_delivered_customer_date"])
    days = (deliv["order_delivered_customer_date"]
            - deliv["order_purchase_timestamp"]).dt.total_seconds() / 86400
    print(days.describe(percentiles=[0.5, 0.9, 0.95, 0.99]))
    print(f"\n'delivered' status but no delivery date: "
          f"{((orders['order_status'] == 'delivered') & orders['order_delivered_customer_date'].isna()).sum():,}")

    # ---- 3. Volume and status mix by purchase month ----
    section("3. ORDERS AND STATUS MIX BY PURCHASE MONTH (% of that month's orders)")
    counts = pd.crosstab(orders["month"], orders["order_status"])
    mix = counts.div(counts.sum(axis=1), axis=0) * 100
    mix.insert(0, "orders_total", counts.sum(axis=1))
    print(mix.tail(8))

    # ---- 4. Weekly view of the final stretch ----
    section("4. WEEKLY VIEW SINCE JULY 2018 (all statuses)")
    recent = orders[orders["order_purchase_timestamp"] >= "2018-07-01"]
    weekly = recent.groupby("week").agg(
        orders=("order_id", "size"),
        delivered_pct=("order_status", lambda s: (s == "delivered").mean() * 100),
        canceled_pct=("order_status", lambda s: (s == "canceled").mean() * 100),
    )
    print(weekly)

    # ---- 5. Unfinished orders: still in transit, or overdue? ----
    section("5. UNFINISHED ORDERS: estimate in future vs already passed")
    unfinished = orders[~orders["order_status"].isin(
        ["delivered", "canceled", "unavailable"])].copy()
    unfinished["estimate"] = (
        (unfinished["order_estimated_delivery_date"] > obs_end)
        .map({True: "est_in_future", False: "est_passed"})
    )
    print(pd.crosstab(unfinished["month"], unfinished["estimate"]).tail(8))


if __name__ == "__main__":
    main()