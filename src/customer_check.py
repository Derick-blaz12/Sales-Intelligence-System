import pandas as pd

pd.set_option("display.width", 200)

orders = pd.read_csv("data/raw/olist_orders_dataset.csv")
cust = pd.read_csv("data/raw/olist_customers_dataset.csv")

print(f"customers rows: {len(cust):,}")
print(f"customers columns: {list(cust.columns)}")
print(f"orders rows: {len(orders):,}")

print("\n--- Key uniqueness ---")
print(f"customer_id unique in customers?  {cust['customer_id'].is_unique}")
print(f"distinct customer_id:             {cust['customer_id'].nunique():,}")
print(f"distinct customer_unique_id:      {cust['customer_unique_id'].nunique():,}")

print("\n--- Join orders -> customers ---")
m = orders.merge(cust, on="customer_id", how="left",
                 validate="many_to_one", indicator=True)
print(f"rows before/after: {len(orders):,} / {len(m):,}")
print(f"orders with no customer record: {(m['_merge'] == 'left_only').sum():,}")

print("\n--- Does customer_id repeat across orders? ---")
print(f"orders per customer_id, max: {orders['customer_id'].value_counts().max()}")
per_person = m.groupby("customer_unique_id")["order_id"].nunique()
print(f"orders per customer_unique_id, max: {per_person.max()}")
print(f"people with 2+ orders (all statuses): {(per_person >= 2).sum():,} "
      f"of {len(per_person):,}")