from pathlib import Path
import pandas as pd

RAW = Path("data/raw")


def load_merged() -> pd.DataFrame:
    """Order items enriched with product and order info.
    One row = one item within an order (same grain as the raw items file)."""
    items = pd.read_csv(RAW / "olist_order_items_dataset.csv")
    products = pd.read_csv(RAW / "olist_products_dataset.csv")
    orders = pd.read_csv(RAW / "olist_orders_dataset.csv")

    merged = (
        items.merge(products, on="product_id", how="left", validate="many_to_one")
             .merge(orders, on="order_id", how="left", validate="many_to_one")
    )
    assert len(merged) == len(items), "Merge changed the row count!"
    return merged