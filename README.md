#### Resell Price Intel Engine

This is a price intel engine that will gather data for popular items that are resold and give valuable insights on reselling opportunity for the specific product

## Question we will answer

"If I buy this item today, is it likely to flip for a profit soon?"

### V1 focus 

## Products Covered

1. GPUs
2. Gaming Consoles

## Data Sources

1. Buy Side: Best Buy scraping

2. Sell Side: Ebay sold listings scraping

## V1 Data contract

# Input:

1. Product identifier (name or UPC)
2. Category

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

1. Python

2. FastAPI

3. PostgreSQL

# Frontend

1. React (states updated by FastAPI backend)

# Data access:

1. Ebay Scraping

V1 products are identified by UPC when available.

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

### To Add in V2

- Need to get access to APIs for seamless and more accurate data

## Data access

# Need to get approved for
1. Best Buy API
2. EBay API
3. Alibaba API