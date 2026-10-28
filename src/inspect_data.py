from pathlib import Path
import pandas as pd

# --- Config ---
DATA_PATH = Path("data/raw/olist_order_items_dataset.csv")


def section(title: str) -> None:
    print(f"\n{'=' * 60}\n{title}\n{'=' * 60}")


def main() -> None:
    # 1. Load
    df = pd.read_csv(DATA_PATH)

    # 2. First five rows
    section("FIRST 5 ROWS")
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 200)
    print(df.head())

    # 3. Shape
    section("SHAPE")
    rows, cols = df.shape
    print(f"Rows: {rows:,}\nColumns: {cols}")

    # 4. Column names
    section("COLUMN NAMES")
    for name in df.columns:
        print(f"- {name}")

    # 5. Data types
    section("DATA TYPES")
    print(df.dtypes)

    # 6. Missing values
    section("MISSING VALUES")
    missing = pd.DataFrame({
        "missing": df.isna().sum(),
        "percent": (df.isna().mean() * 100).round(2),
    })
    print(missing)

    # 7. Duplicates
    section("DUPLICATE CHECKS")
    print(f"Fully duplicated rows: {df.duplicated().sum():,}")
    print(f"Repeated order_id values: {df['order_id'].duplicated().sum():,}")
    print(f"Unique order_ids: {df['order_id'].nunique():,}")
    print(
        "Repeated (order_id, order_item_id) pairs: "
        f"{df.duplicated(subset=['order_id', 'order_item_id']).sum():,}"
    )

    # Helpful extras for answering the questions (read-only, nothing is changed)
    section("EXTRA CONTEXT")
    print(df.describe(include="all").T)


if __name__ == "__main__":
    main()