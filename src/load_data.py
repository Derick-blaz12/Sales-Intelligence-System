from pathlib import Path
import pandas as pd

RAW = Path("data/raw")


def load_merged() -> pd.DataFrame:
    """Order items enriched with product and order info.
    One row = one item within an order (same grain as the raw items file)."""
    items = pd.read_csv(RAW / "olist_order_items_dataset.csv")
    products = pd.read_csv(RAW / "olist_products_dataset.csv")
    orders = pd.read_csv(RAW / "olist_orders_dataset.csv")

    translation = pd.read_csv(RAW / "product_category_name_translation.csv")

    merged = (
        items.merge(products, on="product_id", how="left", validate="many_to_one")
             .merge(orders, on="order_id", how="left", validate="many_to_one")
             .merge(translation, on="product_category_name", how="left", validate="many_to_one")
    )

    # Parse timestamps (errors="coerce" turns unparseable values into NaT
    # instead of crashing, so we can count them rather than miss them)
    date_cols = [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ]
    for col in date_cols:
        merged[col] = pd.to_datetime(merged[col], errors="coerce")
    assert len(merged) == len(items), "Merge changed the row count!"
    return merged