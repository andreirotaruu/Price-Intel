const url = window.location.href;

if (url.includes("/sch/")) {
    collectSearchResults();
}
else if (url.includes("/itm/")) {
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

async function collectSearchResults() {
  const listings = extractSearchListings().map((listing) => ({
    ...listing,
    category: "General",
    condition: "Unknown",
  }));

  if (!listings.length) {
    console.log("Price Intel: no listings found on search page");
    return;
  }

  console.log("Price Intel: sending bulk →", listings.length, "listings");

  try {
    const response = await fetch("http://localhost:8000/collect_bulk", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ listings }),
    });

    const result = await response.json();
    console.log("Price Intel: bulk result →", result);

    chrome.storage.local.set({ lastBulkAnalysis: result, lastBulkListings: listings });
  } catch (err) {
    console.error("Price Intel: bulk upload failed", err);
    chrome.storage.local.set({ lastBulkAnalysis: null, lastBulkListings: listings });
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
