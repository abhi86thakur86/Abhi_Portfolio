-- SQLite dialect. All amounts NZD, GST exclusive. Synthetic CY2025 data.
-- One row per month x sales channel x product category.
WITH monthly AS (
 SELECT month,
 ROUND(SUM(units*unit_price),2) AS revenue,
 ROUND(SUM(units*unit_food_cost),2) AS food_cost,
 -- Rates use integer basis points before cent rounding (1.5% = 150 bp).
 ROUND(SUM(ROUND(units*unit_price*ROUND(fee_rate*10000,0)/100,0)/100),2) AS channel_fees
 FROM sales GROUP BY month
)
SELECT m.*, ROUND(revenue-food_cost,2) AS gross_profit,
 ROUND(revenue-food_cost-channel_fees,2) AS contribution,
 ROUND(1.0*(revenue-food_cost-channel_fees)/NULLIF(revenue,0),4) AS contribution_margin,
 o.overhead,
 ROUND(revenue-food_cost-channel_fees-o.overhead,2) AS operating_surplus
FROM monthly m JOIN overheads o ON m.month=o.month ORDER BY m.month;
