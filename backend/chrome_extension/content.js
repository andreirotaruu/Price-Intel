const url = window.location.href;

if (url.includes("/sch/")) {
    chrome.storage.local.set({ lastPageType: "search" });
    collectSearchResults();
}
else if (url.includes("/itm/")) {
    chrome.storage.local.set({ lastPageType: "item" });
    analyzeProduct();
}


function extractEbayData() {
  // Title
  const titleEl = document.querySelector("h1.x-item-title__mainTitle span");
  const title = titleEl ? titleEl.innerText.trim() : null;

  // Price
  const priceEl =
    document.querySelector(".x-price-primary span.ux-textspans") ||
    document.querySelector("[data-testid='x-price-section'] .ux-textspans");
  const price = priceEl ? parseFloat(priceEl.innerText.replace(/[^0-9.]/g, "")) || null : null;

  // Condition
  const conditionEl = document.querySelector(".x-item-condition-value .ux-textspans");
  const condition = conditionEl ? conditionEl.innerText.trim() : "Unknown";

  // Category — eBay puts this in the breadcrumb nav
  const breadcrumbs = document.querySelectorAll(".seo-breadcrumb-text span");
  // Breadcrumb is usually: Home > Category > Subcategory > ...
  // Index 1 gives us the top-level category (skip "Home" at index 0)
  const category = breadcrumbs.length > 1 ? breadcrumbs[1].innerText.trim() : "General";

  return {
    name: title,
    category: category,
    current_price: price,
    marketplace: "ebay",
    condition: condition,
  };
}

function extractSearchListings() {
    const listings = [];
    const cardSelectors = [".s-card", ".s-item"];
    const titleSelectors = [
        ".su-styled-text.primary.default",
        ".s-card__title",
        ".s-item__title",
    ];
    const priceSelectors = [
        ".su-styled-text.primary.bold.large-1.s-card__price",
        ".s-card__price",
        ".s-item__price",
    ];

    for (const cardSelector of cardSelectors) {
        const cards = document.querySelectorAll(cardSelector);
        if (!cards.length) continue;

        cards.forEach((item) => {
            const titleEl = titleSelectors
                .map((selector) => item.querySelector(selector))
                .find(Boolean);
            const priceEl = priceSelectors
                .map((selector) => item.querySelector(selector))
                .find(Boolean);

            if (!titleEl || !priceEl) return;

            const title = titleEl.innerText.trim();
            const price = parseFloat(priceEl.innerText.replace(/[^0-9.]/g, ""));

            if (!title || !price) return;

            listings.push({
                name: title,
                current_price: price,
                marketplace: "ebay",
            });
        });

        if (listings.length) return listings;
    }

    return listings;
}

function buildSearchSummary(listings) {
  if (!listings.length) return null;

  const prices = listings
    .map((listing) => listing.current_price)
    .filter((price) => Number.isFinite(price) && price > 0)
    .sort((left, right) => left - right);

  if (!prices.length) return null;

  const middleIndex = Math.floor(prices.length / 2);
  const quickMarketEstimate =
    prices.length % 2 === 0
      ? (prices[middleIndex - 1] + prices[middleIndex]) / 2
      : prices[middleIndex];

  const currentPrice = listings[0].current_price;
  const discountRatio =
    quickMarketEstimate > 0
      ? (quickMarketEstimate - currentPrice) / quickMarketEstimate
      : 0;
  const confidence = Math.min(listings.length / 20, 1);
  const dealScore = Math.round(
    Math.max(0, Math.min(100, 50 + discountRatio * 250 + confidence * 20))
  );

  return {
    currentPrice,
    quickMarketEstimate,
    dealScore,
    listingCount: listings.length,
    productName: listings[0].name,
  };
}

async function collectSearchResults() {
  const listings = extractSearchListings().map((listing) => ({
    ...listing,
    category: "General",
    condition: "Unknown",
  }));
  const summary = buildSearchSummary(listings);

  if (!listings.length) {
    console.log("Price Intel: no listings found on search page");
    return;
  }

  console.log("Price Intel: sending bulk →", listings.length, "listings");
  chrome.storage.local.set({ lastBulkSummary: summary, lastBulkListings: listings });

  try {
    const response = await fetch("http://localhost:8000/collect_bulk", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ listings }),
    });

    const result = await response.json();
    console.log("Price Intel: bulk result →", result);

    chrome.storage.local.set({ lastBulkAnalysis: result, lastBulkListings: listings, lastBulkSummary: summary });
  } catch (err) {
    console.error("Price Intel: bulk upload failed", err);
    chrome.storage.local.set({ lastBulkAnalysis: null, lastBulkListings: listings, lastBulkSummary: summary });
  }
}



async function analyzeProduct() {

  const productData = extractEbayData();

  if (!productData.name || !productData.current_price) {
    console.log("Price Intel: could not extract required fields", productData);
    return;
  }

  console.log("Price Intel: sending →", productData);

  try {
    const response = await fetch("http://localhost:8000/collect", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(productData),
    });

    const result = await response.json();
    console.log("Price Intel: result →", result);

    chrome.storage.local.set({ lastAnalysis: result, lastProduct: productData });

  } catch (err) {
    console.error("Price Intel: backend unreachable", err);
    chrome.storage.local.set({ lastAnalysis: null, lastProduct: productData });
  }
}
