### Resell Price Intel Engine

This is a price intel engine that will gather data for popular items that are resold and give valuable insights on reselling opportunity for the specific product

## Question we will answer

"If I buy this item today, is it likely to flip for a profit soon?"

## V1 focus 

# Products Covered

1. GPUs
2. Gaming Consoles

# Data Sources

1. Buy Side: ShopSavvy API

2. Sell Side: Ebay sold listings API

## V1 Data contract

# Input:

Product identifier (name or UPC)

# Output:

{
  "buy_price": 519.99,
  "sell_price": 649.99,
  "fees": 92.00,
  "estimated_profit": 38.00,
  "roi_percent": 7.3,
  "velocity": "FAST",
  "recommendation": "BUY"
}

Velocity is determined by the number of sold listings within the last 7–14 days.

## Data Needed:

1. Retail price

2. eBay median sold price

3. eBay sold count (7–14 days)

4. Estimated fees


## Tech Stack

# Backend:

Python

FastAPI

SQLite

# Data access:

Shopsavvy API

eBay API

## Opportunity Logic

Opportunity is calculated using:
- Estimated resale fees (category-based)
- Net profit
- ROI threshold
- Recent sales velocity (7–14 days)

Recommendations are conservative by design to avoid false positives.

## Opportunity Scoring

Opportunity scores are computed using a weighted heuristic combining:
- ROI (capital efficiency)
- Recent sales velocity (liquidity)
- Estimated profit (absolute return)

Weights are chosen to normalize these signals onto a comparable scale and reflect typical reseller decision-making priorities.

## Out of Scope for v1:

1. Price forecasting

2. Multiple buy-side retailers

3. User accounts

4. Inventory management