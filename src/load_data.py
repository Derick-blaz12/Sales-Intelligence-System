from pathlib import Path
import pandas as pd

RAW = Path("data/raw")

REQUIRED_FILES = [
    "olist_order_items_dataset.csv",
    "olist_products_dataset.csv",
    "olist_orders_dataset.csv",
    "product_category_name_translation.csv",
]

DATE_COLS = [
    "order_purchase_timestamp",
    "order_approved_at",
    "order_delivered_carrier_date",
    "order_delivered_customer_date",
    "order_estimated_delivery_date",
]

# Categories missing from the translation file (English wording is ours)
MANUAL_TRANSLATIONS = {
    "pc_gamer": "pc_gamer",
    "portateis_cozinha_e_preparadores_de_alimentos":
        "portable_kitchen_and_food_preparers",
}


def load_merged(raw_dir: Path = RAW) -> pd.DataFrame:
    """Order items enriched with product, order and category-translation info.
    One row = one item within an order (same grain as the raw items file)."""
    raw_dir = Path(raw_dir)

    missing = [f for f in REQUIRED_FILES if not (raw_dir / f).exists()]
    if missing:
        raise FileNotFoundError(f"Missing in {raw_dir}: {', '.join(missing)}")

    items = pd.read_csv(raw_dir / "olist_order_items_dataset.csv")
    products = pd.read_csv(raw_dir / "olist_products_dataset.csv")
    orders = pd.read_csv(raw_dir / "olist_orders_dataset.csv")
    translation = pd.read_csv(raw_dir / "product_category_name_translation.csv")

    merged = (
        items.merge(products, on="product_id", how="left", validate="many_to_one")
             .merge(orders, on="order_id", how="left", validate="many_to_one")
             .merge(translation, on="product_category_name", how="left",
                    validate="many_to_one")
    )

    # Fill categories missing from the translation file
    fill = merged["product_category_name"].map(MANUAL_TRANSLATIONS)
    merged["product_category_name_english"] = (
        merged["product_category_name_english"].fillna(fill)
    )

    # Items whose product has no category at all stay visible as "unknown"
    merged["product_category_name_english"] = (
        merged["product_category_name_english"].fillna("unknown")
    )

    # Parse timestamps (unparseable values become NaT so we can count them)
    for col in DATE_COLS:
        merged[col] = pd.to_datetime(merged[col], errors="coerce")

    assert len(merged) == len(items), "Merge changed the row count!"
    return merged