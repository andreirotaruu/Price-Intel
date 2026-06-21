const content = document.getElementById("content");

const formatCurrency = (value) =>
  typeof value === "number"
    ? new Intl.NumberFormat("en-US", {
        style: "currency",
        currency: "USD",
        maximumFractionDigits: 0,
      }).format(value)
    : "—";

function renderPopup(data) {
  if (data.lastPageType === "search") {
    content.innerHTML = '<div id="status">Navigate to a listing to view the price summary.</div>';
    return;
  }

  if (!data.lastProduct) {
    content.innerHTML = '<div id="status">No product detected.<br>Navigate to an eBay listing or search page.</div>';
    return;
  }

  const product = data.lastProduct;
  const summary = data.lastBulkSummary;
  const title = product.name || product.title || "Unknown";
  const currentPrice = product.current_price ?? product.price;

  let html = `<div class="product-title" title="${title}">${title}</div>`;

  html += `<div class="stat"><span class="label">Current Price</span><span class="value">${formatCurrency(currentPrice)}</span></div>`;
  html += `<div class="stat"><span class="label">Quick Market Estimate</span><span class="value">${formatCurrency(summary?.quickMarketEstimate)}</span></div>`;

  const dealScore = summary?.dealScore;
  const scoreClass = typeof dealScore === "number" ? (dealScore >= 80 ? "good" : dealScore >= 50 ? "neutral" : "bad") : "neutral";
  html += `<div class="stat"><span class="label">Deal Score</span><span class="value ${scoreClass}">${dealScore ?? "—"}</span></div>`;

  content.innerHTML = html;
}

function refreshPopup() {
  chrome.storage.local.get(["lastAnalysis", "lastProduct", "lastBulkSummary", "lastPageType"], renderPopup);
}

refreshPopup();

chrome.storage.onChanged.addListener((changes, areaName) => {
  if (areaName !== "local") return;

  if (
    changes.lastAnalysis ||
    changes.lastProduct ||
    changes.lastBulkSummary ||
    changes.lastPageType
  ) {
    refreshPopup();
  }
});
