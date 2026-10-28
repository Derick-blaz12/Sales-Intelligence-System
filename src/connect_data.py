from pathlib import Path
import pandas as pd

RAW = Path("data/raw")


def section(title: str) -> None:
    print(f"\n{'=' * 60}\n{title}\n{'=' * 60}")


def main() -> None:
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 200)

    items = pd.read_csv(RAW / "olist_order_items_dataset.csv")
    products = pd.read_csv(RAW / "olist_products_dataset.csv")
    orders = pd.read_csv(RAW / "olist_orders_dataset.csv")

    # --- 1. Inspect each table ---
    section("TABLE SHAPES")
    print(f"items:    {items.shape}")
    print(f"products: {products.shape}")
    print(f"orders:   {orders.shape}")

    section("PRODUCTS: columns and dtypes")
    print(products.dtypes)

    section("ORDERS: columns and dtypes")
    print(orders.dtypes)

    # --- 2. Key uniqueness ---
    section("KEY UNIQUENESS")
    print(f"products.product_id unique? {products['product_id'].is_unique}")
    print(f"  repeated product_ids: {products['product_id'].duplicated().sum():,}")
    print(f"orders.order_id unique?     {orders['order_id'].is_unique}")
    print(f"  repeated order_ids: {orders['order_id'].duplicated().sum():,}")

    # --- 3. Merge 1: items + products ---
    section("MERGE 1: items + products (left join on product_id)")
    rows_before = len(items)
    merged1 = items.merge(
        products,
        on="product_id",
        how="left",
        indicator=True,
        validate="many_to_one",
    )
    print(f"Rows before: {rows_before:,}")
    print(f"Rows after:  {len(merged1):,}")
    print(merged1["_merge"].value_counts())
    print(f"Items with no matching product: {(merged1['_merge'] == 'left_only').sum():,}")
    merged1 = merged1.drop(columns="_merge")

    # --- 4. Merge 2: result + orders ---
    section("MERGE 2: + orders (left join on order_id)")
    rows_before = len(merged1)
    merged2 = merged1.merge(
        orders,
        on="order_id",
        how="left",
        indicator=True,
        validate="many_to_one",
    )
    print(f"Rows before: {rows_before:,}")
    print(f"Rows after:  {len(merged2):,}")
    print(merged2["_merge"].value_counts())
    print(f"Items with no matching order: {(merged2['_merge'] == 'left_only').sum():,}")
    merged2 = merged2.drop(columns="_merge")

    # --- 5. Final check ---
    section("FINAL TABLE")
    print(f"Shape: {merged2.shape}")
    print(f"Matches original item count? {len(merged2) == len(items)}")
    print("\nColumns:")
    for name in merged2.columns:
        print(f"- {name}")

    section("FINAL TABLE: first 3 rows")
    print(merged2.head(3).T)

    section("EXTRA: order status breakdown (read-only)")
    print(merged2["order_status"].value_counts())

    section("EXTRA: missing values after merge")
    print(merged2.isna().sum()[merged2.isna().sum() > 0])


if __name__ == "__main__":
    main()