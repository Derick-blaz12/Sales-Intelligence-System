1. What does one row represent?
One item within an order, not an entire order. There are 112,650 rows but only 98,666 unique order_ids, so about 14,000 orders span multiple rows. order_item_id is a counter (1, 2, 3...) within an order, and its max of 21 means one order has 21 items.

2. Which columns identify a product and give sales value?
product_id identifies the product (32,951 unique). price is the item’s selling price. freight_value is shipping. For sales value, price is the revenue figure. Freight is a separate charge and shouldn’t be silently mixed in. Whether to include it is a business decision we’ll make deliberately. seller_id tells you who sold it (3,095 sellers), which is a useful extra dimension.

3. Missing data?
None in this file. Every column shows 0 missing. But that only means nothing is blank. Look at the extremes: price ranges from 0.85 to 6,735, and freight_value has a minimum of 0.0. Free shipping is plausible, and a 6,735 price might be a genuine expensive item or an outlier. Neither is an error yet; both are things to investigate in Milestone 3.

4. Duplicates?
This is the subtle one. Your three checks tell different stories:

Fully duplicated rows: 0. No exact copies.
Repeated order_id: 13,984. Not errors. A customer buying several items creates several rows with the same order_id.
Repeated (order_id, order_item_id) pairs: 0. This is the real uniqueness test. The combination is the true row key, and it’s never violated.

One more nuance: if a customer buys three of the same product, you’ll see three rows with the same order_id and product_id but different order_item_id. Those are three units, not duplicates. So “repeated identifier” is not the same as “data error.”

5. What do we need from other files?

olist_products_dataset.csv for product category (join on product_id)
olist_orders_dataset.csv for the purchase date and order status (join on order_id)
product_category_name_translation.csv to turn Portuguese category names into English

Note that shipping_limit_date is the seller’s shipping deadline, not the purchase date. Don’t use it as the sales date. Also, it’s loaded as a string (str), not a datetime, so it’ll need converting when we get to cleaning.

Two things worth noticing
The str dtype for text columns (instead of object) means you’re on a recent pandas version. That’s fine, just don’t be surprised when tutorials show object.
Order status matters. The orders file includes cancelled and unavailable orders, and those rows in this file may not represent real revenue. That’s a key reason we need the join before calculating any metrics.