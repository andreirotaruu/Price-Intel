const content = document.getElementById("content");

const escapeHtml = (value) =>
  String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");

const formatCurrency = (value) =>
  typeof value === "number"
    ? new Intl.NumberFormat("en-US", {
        style: "currency",
        currency: "USD",
        maximumFractionDigits: 0,
      }).format(value)
    : "—";

function getScoreClass(score) {
  if (typeof score !== "number") return "neutral";
  if (score >= 80) return "good";
  if (score >= 50) return "neutral";
  return "bad";
}

function renderEmptyState(title, copy) {
  content.innerHTML = `
    <div class="empty-state">
      <div class="empty-icon" aria-hidden="true">
        <svg width="19" height="19" viewBox="0 0 24 24" fill="none">
          <path d="M21 21L16.7 16.7" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          <circle cx="11" cy="11" r="7" stroke="currentColor" stroke-width="2"/>
        </svg>
      </div>
      <p class="empty-title">${escapeHtml(title)}</p>
      <p class="empty-copy">${escapeHtml(copy)}</p>
    </div>
  `;
}

function renderPopup(data) {
  if (data.lastPageType === "search") {
    renderEmptyState(
      "Open a listing",
      "Search results are captured. Pick a product page to see the resale snapshot."
    );
    return;
  }

  if (!data.lastProduct) {
    renderEmptyState(
      "No product detected",
      "Navigate to an eBay listing or search page and Price Intel will summarize it here."
    );
    return;
  }

  const product = data.lastProduct;
  const summary = data.lastBulkSummary;
  const title = product.name || product.title || "Unknown";
  const currentPrice = product.current_price ?? product.price;
  const estimate = summary?.quickMarketEstimate;
  const difference =
    typeof estimate === "number" && typeof currentPrice === "number"
      ? estimate - currentPrice
      : null;
  const condition = product.condition || "Unknown condition";

  const dealScore = summary?.dealScore;
  const scoreClass = getScoreClass(dealScore);
  const scoreWidth =
    typeof dealScore === "number" ? Math.max(0, Math.min(100, dealScore)) : 0;
  const differenceClass =
    typeof difference === "number"
      ? difference >= 0
        ? "good"
        : "bad"
      : "";

  const html = `
    <section class="summary">
      <div>
        <div class="product-title" title="${escapeHtml(title)}">${escapeHtml(title)}</div>
        <div class="product-meta">
          <span>${escapeHtml(product.marketplace || "eBay")}</span>
          <span aria-hidden="true">&middot;</span>
          <span>${escapeHtml(condition)}</span>
        </div>
      </div>
      <div class="score ${scoreClass}" title="Deal score">${dealScore ?? "—"}</div>
    </section>
    <div class="stats">
      <div class="stat">
        <span class="label">Current price</span>
        <span class="value">${formatCurrency(currentPrice)}</span>
      </div>
      <div class="stat">
        <span class="label">Market estimate</span>
        <span class="value">${formatCurrency(estimate)}</span>
      </div>
      <div class="stat">
        <span class="label">Upside</span>
        <span class="value ${differenceClass}">${formatCurrency(difference)}</span>
      </div>
    </div>
    <div class="meter" aria-hidden="true">
      <div class="meter-fill" style="width: ${scoreWidth}%"></div>
    </div>
  `;

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
