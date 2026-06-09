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

analyzeProduct();