chrome.storage.local.get(["lastAnalysis", "lastProduct", "lastBulkSummary", "lastPageType"], (data) => {
  const content = document.getElementById("content");
  const formatCurrency = (value) =>
    typeof value === "number"
      ? new Intl.NumberFormat("en-US", {
          style: "currency",
          currency: "USD",
          maximumFractionDigits: 0,
        }).format(value)
      : "—";

  if (data.lastPageType === "search") {
    content.innerHTML = '<div id="status">Navigate to a listing to view the price summary.</div>';
    return;
  }

  if (data.lastBulkSummary) {
    const summary = data.lastBulkSummary;

    content.innerHTML = `
      <div class="stat"><span class="label">Current Price:</span><span class="value">${
        formatCurrency(summary.currentPrice)
      }</span></div>
      <div class="stat"><span class="label">Quick Market Estimate:</span><span class="value">${formatCurrency(
        summary.quickMarketEstimate
      )}</span></div>
      <div class="stat"><span class="label">Deal Score:</span><span class="value ${summary.dealScore >= 80 ? "good" : summary.dealScore >= 50 ? "neutral" : "bad"}">${
        summary.dealScore ?? "—"
      }</span></div>
    `;
    return;
  }

  if (!data.lastProduct) {
    content.innerHTML = '<div id="status">No product detected.<br>Navigate to an eBay listing or search page.</div>';
    return;
  }

  const p = data.lastProduct;
  const a = data.lastAnalysis;

  let html = `<div class="product-title" title="${p.title}">${p.title || "Unknown"}</div>`;

  html += `<div class="stat"><span class="label">Listed price</span><span class="value">$${p.price?.toFixed(2) ?? "—"}</span></div>`;
  html += `<div class="stat"><span class="label">Condition</span><span class="value neutral">${p.condition ?? "—"}</span></div>`;

  if (a) {
    const profitClass = a.profit > 0 ? "good" : "bad";
    html += `<div class="stat"><span class="label">Est. profit</span><span class="value ${profitClass}">$${a.profit?.toFixed(2) ?? "—"}</span></div>`;
    html += `<div class="stat"><span class="label">ROI</span><span class="value ${profitClass}">${a.roi ?? "—"}%</span></div>`;
    html += `<div class="stat"><span class="label">Confidence</span><span class="value neutral">${a.confidence ?? "—"}%</span></div>`;
  } else {
    html += `<div id="status">Backend offline — showing raw data only.</div>`;
  }

  content.innerHTML = html;
});
