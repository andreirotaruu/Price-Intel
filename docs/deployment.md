# Price Intel Deployment

Use this for a small friends-and-family test on Render plus an unpacked Chrome extension.

## 1. Confirm prerequisites

- Push the latest repo to GitHub.
- Make sure `requirements.txt` and `render.yaml` are committed.
- Have your eBay production `Client ID` and `Client Secret` ready.

## 2. Create Render resources

1. In Render, create a new Blueprint from this GitHub repo.
2. Render will read `render.yaml` and create:
   - `price-intel-db`
   - `price-intel-api`
   - `price-intel-daily-market-refresh`
3. When Render asks for secret values, enter:
   - `EBAY_CLIENT_ID`
   - `EBAY_CLIENT_SECRET`

The FastAPI service uses:

```bash
uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```

The cron job runs daily at 08:00 UTC:

```bash
python -m backend.jobs.market_refresh
```

## 3. Test the deployed API

Replace the URL with your Render service URL.

```bash
curl https://price-intel-api.onrender.com/health
```

Expected shape:

```json
{
  "status": "ok",
  "database": "ok",
  "ebay_credentials_configured": true
}
```

Test analysis:

```bash
curl -X POST https://price-intel-api.onrender.com/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "name": "NVIDIA RTX 4070 Founders Edition 12GB",
    "category": "Graphics Cards",
    "current_price": 499.99,
    "condition": "Used",
    "item_id": "1234567890"
  }'
```

## 4. Point the extension at Render

In `backend/chrome_extension/content.js`, change:

```js
const API_BASE_URL = "http://localhost:8000";
```

to your Render URL:

```js
const API_BASE_URL = "https://price-intel-api.onrender.com";
```

Then reload the unpacked extension in `chrome://extensions`.

## 5. Give the extension to testers

1. Zip `backend/chrome_extension`.
2. Send testers the zip plus these steps:
   - Unzip it.
   - Open `chrome://extensions`.
   - Enable Developer Mode.
   - Click **Load unpacked**.
   - Select the unzipped `chrome_extension` folder.
   - Open an eBay listing and click the Price Intel extension icon.

Ask testers to send:

- listing URL
- screenshot of the popup
- whether the comparison looked right
- any visible error text

## 6. Triage comparison failures

Track failures by product category and cause:

- wrong product family
- accessory/parts listing included
- condition mismatch
- bundle included
- eBay API failure
- no comparables found

For each bad comparison, save the eBay URL and the returned `comparables` from `/analyze`.

## 7. Chrome Web Store later

After tester feedback is stable:

1. Replace broad test host permissions with the exact production API URL.
2. Add extension icons.
3. Bump `manifest.json` version.
4. Create a privacy policy.
5. Zip only the extension folder contents.
6. Submit in the Chrome Web Store Developer Dashboard.
