import pandas as pd
from config import INCLUDED_STATUSES, START, END, CATEGORY_COL
from load_data import load_merged

pd.set_option("display.width", 200)
pd.set_option("display.float_format", "{:,.2f}".format)

df = load_merged()
delivered = df[df["order_status"].isin(INCLUDED_STATUSES)]
in_window = (delivered["order_purchase_timestamp"] >= START) & \
            (delivered["order_purchase_timestamp"] < END)
w = delivered[in_window]
outside = delivered[~in_window]
total = w["price"].sum()

print("=== RECONCILIATION WITH MILESTONE 3 ===")
print(f"Window item value:                {total:,.2f}")
print(f"Delivered, outside window:        {outside['price'].sum():,.2f}")
print(f"  earliest/latest outside:        {outside['order_purchase_timestamp'].min()} / "
      f"{outside['order_purchase_timestamp'].max()}")
print(f"Sum:                              {total + outside['price'].sum():,.2f}")
print(f"Milestone 3 delivered total:      {delivered['price'].sum():,.2f}")

print("\n=== TOP 7 CATEGORIES (denominator = window item value) ===")
cat = w.groupby(CATEGORY_COL)["price"].sum().sort_values(ascending=False)
top7 = cat.head(7)
print(top7)
print(f"Top 7 combined: {top7.sum():,.2f} = {top7.sum() / total * 100:.2f}% of {total:,.2f}")
print(f"Tie at the 7th/8th boundary? {cat.iloc[6] == cat.iloc[7]}")

print("\n=== PRODUCT CONCENTRATION ===")
prod = (w.groupby("product_id")["price"].sum().rename("item_value").reset_index()
          .sort_values(["item_value", "product_id"], ascending=[False, True])
          .reset_index(drop=True))               # product_id breaks ties deterministically
N = len(prod)
prod["cum_share"] = prod["item_value"].cumsum() / total * 100
print(f"Denominator: all {N:,} products sold in the window; shares are of {total:,.2f}")
for pct in (1, 5, 10, 20, 50):
    n = int(round(N * pct / 100))
    tie = prod.loc[n - 1, "item_value"] == prod.loc[n, "item_value"]
    print(f"Top {pct:>2}% = first {n:>6,} products -> {prod.loc[n - 1, 'cum_share']:5.1f}% "
          f"(tie at cut-off: {tie})")

print("\n=== DISTRIBUTION OF PRODUCT ITEM VALUE ===")
print(prod["item_value"].describe(percentiles=[0.25, 0.5, 0.75, 0.9, 0.99]))
print(f"Mean / median ratio: {prod['item_value'].mean() / prod['item_value'].median():.1f}")