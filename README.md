# Price Intel

Price Intel is a Chrome extension plus FastAPI backend that analyzes marketplace listings in real time. It started as a scraping engine, but the current project is an extension-driven workflow: when you open an eBay search page or item page, the extension captures listing data, sends it to the backend, and shows a compact resale snapshot in the popup.

## What It Does

The current flow answers a simple question:

If I am looking at this listing right now, how does it compare to the market?

For item pages, Price Intel:

1. Reads the listing title, price, condition, and category from the page.
2. Saves the observed listing to the backend.
3. Calls `/analyze` to get a market snapshot.
4. Shows the result in the popup with deal score, average, median, comparable count, range, and short insights.

For search pages, Price Intel:

1. Extracts multiple visible listings from the results page.
2. Sends them to `/collect_bulk`.
3. Stores a lightweight summary for the popup and history.

## Current Features

- Chrome extension content script for eBay item and search pages
- Popup UI that renders the latest captured product and analysis
- Backend `/collect`, `/collect_bulk`, and `/analyze` endpoints
- Cached market snapshots in the database
- Product normalization so title variations map to the same snapshot
- Simple insight generation from the market statistics

## Architecture

### Extension

- `backend/chrome_extension/content.js`
  - Detects eBay search pages and item pages
  - Extracts listing data from the DOM
  - Posts listings to the backend
  - Stores the latest analysis in Chrome local storage

- `backend/chrome_extension/popup.js`
  - Reads the latest stored data
  - Renders deal score and market metrics
  - Falls back to a lighter summary when analysis is not available yet

- `backend/chrome_extension/popup.html`
  - Popup layout and styles

- `backend/chrome_extension/manifest.json`
  - Chrome extension manifest and host permissions

### Backend

- `backend/main.py`
  - FastAPI app
  - `/collect` saves one observed listing
  - `/collect_bulk` saves search result listings
  - `/analyze` normalizes the product name, checks the cache, queries comparables, computes metrics, and returns the analysis payload

- `backend/db/models.py`
  - ORM models for observed listings and market snapshots

- `backend/schemas/`
  - Request payload definitions for the endpoints

- `backend/providers/`
  - eBay and Best Buy provider logic

- `backend/services/`
  - Scoring and opportunity helpers

## How The Analysis Flow Works

1. The extension extracts a listing from eBay.
2. It sends the listing to `/collect` so the observation is stored.
3. It sends the same listing to `/analyze`.
4. The backend normalizes the product name so similar titles share the same cache key.
5. If there is a fresh market snapshot, the backend returns it immediately.
6. If not, the backend queries eBay comparables, calculates market stats, saves a new snapshot, and returns the result.
7. The popup reads the saved response from `chrome.storage.local` and renders the result.

## Analysis Output

The `/analyze` response now includes:

- `average_price`
- `median_price`
- `lowest_price`
- `highest_price`
- `listing_count`
- `comparable_count`
- `deal_score`
- `price_delta`
- `percent_delta`
- `cached`
- `normalized_name`
- `insights`
- `comparables`

Example insight strings:

- `This listing is 5.8% below the market average.`
- `Based on 38 comparable listings, this appears to be a fair deal.`
- `Prices for this product are tightly clustered, increasing confidence in the estimate.`

## Product Normalization

The backend uses normalization so titles like these land on the same cache key:

- `RTX 4070 FE 12GB`
- `NVIDIA GeForce RTX 4070 Founders Edition`

Both normalize to:

```text
rtx 4070 founders edition
```

That keeps the cached snapshot stable even when sellers phrase the product differently.

## Local Development

### Backend

Run the API with:

```bash
uvicorn backend.main:app --reload
```

The backend expects a database URL in the environment and creates tables on startup.

### Extension

Load `backend/chrome_extension/` as an unpacked extension in Chrome.

The extension expects the backend to be running locally on port `8000`.

## Project Status

The project is no longer just a scraper. It is now a browser extension that captures live listings, asks the backend for market analysis, and shows the result in the popup.

The original scraping and provider logic still matters, but it now supports the extension experience instead of being the whole product.

## Notes

- The popup currently focuses on eBay listings.
- The backend keeps cached market snapshots so repeat lookups are cheaper and faster.
- The insight generation is intentionally simple and deterministic for now.
