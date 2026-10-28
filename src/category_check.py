import pandas as pd
from load_data import load_merged

df = load_merged()

print(f"Rows: {len(df):,} (should still be 112,650)")

missing_pt = df["product_category_name"].isna()
missing_en = df["product_category_name_english"].isna()

print(f"\nItems with no Portuguese category: {missing_pt.sum():,}")
print(f"Items with no English category:    {missing_en.sum():,}")
print(f"Items with a Portuguese name but no translation: {(missing_en & ~missing_pt).sum():,}")

print("\nPortuguese names lacking a translation:")
print(df.loc[missing_en & ~missing_pt, "product_category_name"].value_counts())

print(f"\nDistinct English categories: {df['product_category_name_english'].nunique()}")

print("\n--- After fixes ---")
print(df["product_category_name_english"].isna().sum())            # expect 0
print((df["product_category_name_english"] == "unknown").sum())    # expect 1,603
print(df["product_category_name_english"].nunique())               # expect 74

blank = df[df["product_category_name"].isna()]
print(f"Distinct products with no category: {blank['product_id'].nunique():,}")
print(f"Their item value: {blank['price'].sum():,.2f}")