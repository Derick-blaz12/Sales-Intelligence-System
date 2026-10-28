1. Why product_id for product info and order_id for order info?
Each key points at the entity the other table describes. Every row in products describes one product, and items.product_id says which product that item is. Every row in orders describes one order, and items.order_id says which order the item belongs to. You join on the column that names the thing you want more information about.

2. What does a row count increase tell you?
Some left-hand rows matched more than one right-hand row, so the right table’s key wasn’t unique. The result is a “fan-out”: one item row becomes several, and any later sum (like revenue) would be inflated. That’s why we check uniqueness first and use validate="many_to_one".

3. Inner vs left join here?
A left join keeps every order item and fills in blanks (NaN) where no match exists. An inner join keeps only items that matched in both tables, so unmatched items silently disappear.

4. Why is a left join safer during investigation?
Because nothing vanishes. With a left join, unmatched rows stay visible, so you can count and inspect them. With an inner join, the row count simply drops and you may never notice what was lost, which is dangerous when the lost rows might be real sales.

5. What does one row represent after the merges?
Still one item within an order. The final count equals the original 112,650, so the grain hasn’t changed. The new columns (category, product dimensions, order status, dates) just describe each item’s product and order more richly.