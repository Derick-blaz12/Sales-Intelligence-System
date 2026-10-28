import pandas as pd
from config import INCLUDED_STATUSES, START, END
from load_data import load_merged

REF = pd.Timestamp(END)

df = load_merged()
w = df[
    df["order_status"].isin(INCLUDED_STATUSES)
    & (df["order_purchase_timestamp"] >= START)
    & (df["order_purchase_timestamp"] < END)
].copy()
w["days_before_ref"] = (REF - w["order_purchase_timestamp"]).dt.total_seconds() / 86400

# 1. Baseline: where in time do ALL window orders fall?
orders = w.drop_duplicates("order_id")
print("ALL window orders purchased within the last N days:")
for n in (90, 180):
    print(f"  last {n} days: {(orders['days_before_ref'] <= n).mean() * 100:.1f}%")

# 2. Where does the single order of a one-order product fall?
n_orders = w.groupby("product_id")["order_id"].nunique()
single_ids = n_orders[n_orders == 1].index
single = w[w["product_id"].isin(single_ids)].drop_duplicates("product_id")
print(f"\nProducts with exactly 1 order: {len(single):,}")
for n in (90, 180):
    print(f"  sole order within last {n} days: "
          f"{(single['days_before_ref'] <= n).mean() * 100:.1f}%")

# 3. Is the computers cluster a single seller?
cluster = ["d6160fb7873f184099d9bc95e30376af", "588531f8ec37e7d5ff5b7b22ea0488f8",
           "a5215a7a9f46c4185b12f38e9ddf2abc", "bc4cd4da98dd128c39bf0b8c2674032f"]
print("\nSellers of the four computers products (rows per product/seller):")
print(w[w["product_id"].isin(cluster)].groupby(["product_id", "seller_id"]).size())

# 4. How concentrated are the 270 stale high-order products by seller?
rec = pd.read_csv("outputs/product_recency.csv", index_col=0)
stale = rec[(rec["orders_containing"] >= 11)
            & (rec["status"] == "4 not seen for a long time")]
by_seller = (w[w["product_id"].isin(stale.index)]
             .groupby("seller_id")["price"].sum().sort_values(ascending=False))
print(f"\nStale 11+ products: {len(stale)}; distinct sellers: {len(by_seller)}")
print(f"Top 5 sellers' share of their item value: "
      f"{by_seller.head(5).sum() / by_seller.sum() * 100:.1f}%")