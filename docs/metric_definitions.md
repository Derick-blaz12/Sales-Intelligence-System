Item revenue vs a freight-inclusive figure: the difference is exactly the freight total, which is a meaningful share of the combined number. Freight isn’t product revenue, so we keep price as the headline sales figure and report freight separately.

How multiple items in one order weren’t counted as multiple orders: orders are counted with nunique() on order_id, never len(). The script prints both so the gap is visible. AOV is calculated by summing price per order_id first, then averaging those totals.

Exactly which orders are included, and why: orders with status delivered only. Cancelled and unavailable orders never became sales, and in-progress orders may still fail, so excluding them avoids overstating revenue. The by-status table shows the money in each excluded group, so the choice is transparent and reversible.

Also record one caveat: these figures cover the whole 2016 to 2018 period. We haven’t filtered by date or looked at oddities in the early or late months yet, which belongs to the next milestone.