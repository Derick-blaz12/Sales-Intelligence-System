Milestone 5 review: all assertions passed, and the data tells a clear story

Every check passed, and the reconciliation holds: category value and records sum back to 13,181,027.13 and 109,880. One bookkeeping point first: this window total is below the Milestone 3 delivered total (13,221,498.11) by about 40k. That is expected, since the window drops the 2016 delivered orders (about 40.4k), but state it in your notes so the two figures aren’t mistaken for a discrepancy.

Categories: rank disagreement is the insight
Category	Value rank	Records rank	Reading
watches_gifts	2	7	High-ticket: 5.3% of records but 8.8% of value
cool_stuff	8	12	Also higher-priced per item
bed_bath_table	3	1	Volume leader, lower price per item
telephony	14	8	Frequent, cheap
electronics	22	15	Frequent, cheap (value is 155k from 2,728 records)
computers	17	46	Only 199 records, yet 218k value (about 1,100 per record)

The top seven categories hold roughly half of item value. Wording to use: health_beauty leads on value, bed_bath_table leads on reach. Check the 50% claim by summing value_share_% for the top seven yourself, since I’m reading it from the table (about 49.7% by my arithmetic).

unknown is 1.29% of window value, so it’s a footnote as predicted.

Products: best-selling and highest-earning are different lists
Only a handful of products appear in both top-15 lists (e.g. 99a4..., d1c4..., 53b3..., bb50...).
The top-by-orders list is full of cheap garden tools (about 54 each) and one health_beauty item at 22.53. They reach many customers but contribute modest value.
The top-by-value list includes high-ticket products with few orders: d6160... (computers) is 3rd by value with only 33 orders at about 1,392 each, and 25c3... (baby) has 38 orders at about 1,024.
records_per_order > 1 for 4,242 products, max 20. That is the closest the data gets to multiple units per order, but still not verified quantity.
The long tail: large, but not obviously “failures”
Concentration: top 1% of products (321) produce 24.5% of value; top 10% produce 60.9%; top 20% produce 74.8%.
Thin reach: 59.3% of products (19,028) have exactly one order, and 75.8% have two or fewer. Together the 2-or-fewer group still carries 35.5% of item value, so the tail is collectively material, not dead weight.
2x2: 15,014 products are low-reach and low-value (the true quiet tail), but 9,310 are low-reach yet above the median value. Many of the top niche items are single sales at 4,799 to 6,735, which look like high-ticket one-offs. A single order of 6,735 is also the maximum price we saw in Milestone 1, so one outlier-sized sale can top a list.
Launch-timing check: 22.9% of low-reach products first sold on or after 2018-06-01, versus 18.7% of all products. The difference is only about 4 points, so recent launches explain a small part of the tail. Most low-reach products are not simply new. That slightly supports “genuinely low reach”, but the data can’t say why (niche, seasonal, poorly marketed, or a long-tail catalogue by design). Also note one limitation: a product can only be “first sold on or after June” within the window, so products that sold earlier but not recently aren’t distinguished from ones that are still active. A last_order check would address this.
Claims you can and can’t make

Can: value is concentrated in a minority of products; the best sellers by reach and by value differ; several categories are high-ticket and others are high-frequency.

Can’t: call low-order products failures, or call any single product a bestseller on the strength of item value alone. A high-value product with 33 orders is a different business story from one with 456.