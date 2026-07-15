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

const formatNumber = (value) =>
  typeof value === "number" ? new Intl.NumberFormat("en-US").format(value) : "—";

const formatPercent = (value) =>
  typeof value === "number" ? `${Math.abs(value).toFixed(1)}%` : "—";

const formatSellerFeedback = (seller) => {
  if (!seller) return "—";

  const username = seller.username || "Seller";
  const score =
    typeof seller.feedback_score === "number"
      ? ` (${formatNumber(seller.feedback_score)})`
      : "";
  const percentage =
    typeof seller.feedback_percentage === "number"
      ? ` · ${seller.feedback_percentage.toFixed(1)}%`
      : "";

  return `${username}${score}${percentage}`;
};

const formatListingMeta = (listing) => {
  const parts = [
    listing.condition,
    listing.seller_username,
  ].filter(Boolean);

  if (typeof listing.seller_feedback === "number") {
    parts.push(`${formatPercent(listing.seller_feedback)} positive`);
  }

  return parts.join(" · ");
};

function getFeedbackKey(product, analysis) {
  return (
    product.item_id ||
    product.source ||
    product.url ||
    product.name ||
    analysis?.normalized_name ||
    "latest-analysis"
  );
}

function getScoreClass(score) {
  if (typeof score !== "number") return "neutral";
  if (score >= 80) return "good";
  if (score >= 50) return "neutral";
  return "bad";
}

function calculateDealScore(currentPrice, marketEstimate, listingCount = 0) {
  if (
    !Number.isFinite(currentPrice) ||
    !Number.isFinite(marketEstimate) ||
    currentPrice <= 0 ||
    marketEstimate <= 0 ||
    listingCount < 3
  ) {
    return null;
  }

  const upsideRatio = (marketEstimate - currentPrice) / marketEstimate;
  const confidence = Math.min(Math.max(listingCount, 0) / 20, 1);
  const confidenceWeight = 0.65 + confidence * 0.35;
  let baseScore;

  if (upsideRatio <= -0.1) {
    baseScore = 10;
  } else if (upsideRatio < 0) {
    baseScore = 25 + ((upsideRatio + 0.1) / 0.1) * 20;
  } else if (upsideRatio < 0.1) {
    baseScore = 45 + (upsideRatio / 0.1) * 20;
  } else if (upsideRatio < 0.2) {
    baseScore = 65 + ((upsideRatio - 0.1) / 0.1) * 17;
  } else if (upsideRatio < 0.35) {
    baseScore = 82 + ((upsideRatio - 0.2) / 0.15) * 13;
  } else {
    baseScore = 95 + Math.min((upsideRatio - 0.35) / 0.25, 1) * 3;
  }

  const score = 50 + (baseScore - 50) * confidenceWeight;
  return Math.round(Math.max(1, Math.min(98, score)));
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

  if (data.lastAnalysisError) {
    renderEmptyState("Analysis unavailable", data.lastAnalysisError);
    return;
  }

  const product = data.lastProduct;
  const analysis = data.lastAnalysis;
  const feedbackKey = getFeedbackKey(product, analysis);
  const savedFeedback = data.analysisFeedback?.[feedbackKey] || {};
  const summary = data.lastBulkSummary;
  const title = product.name || product.title || "Unknown";
  const currentPrice = analysis?.current_price ?? product.current_price ?? product.price;
  const average = analysis?.average_price;
  const median = analysis?.median_price ?? summary?.quickMarketEstimate;
  const estimate = average ?? median;
  const difference =
    typeof analysis?.price_delta === "number"
      ? analysis.price_delta
      : typeof estimate === "number" && typeof currentPrice === "number"
      ? estimate - currentPrice
      : null;
  const percentDelta =
    typeof analysis?.percent_delta === "number"
      ? analysis.percent_delta
      : typeof difference === "number" && typeof estimate === "number" && estimate > 0
      ? (difference / estimate) * 100
      : null;
  const comparableCount = analysis?.comparable_count ?? analysis?.listing_count ?? summary?.listingCount;
  const condition = product.condition || "Unknown condition";

  const dealScore = analysis
    ? analysis.deal_score ?? calculateDealScore(currentPrice, estimate, comparableCount)
    : summary?.dealScore;
  const scoreClass = getScoreClass(dealScore);
  const scoreWidth =
    typeof dealScore === "number" ? Math.max(0, Math.min(100, dealScore)) : 0;
  const differenceClass =
    typeof difference === "number"
      ? difference >= 0
        ? "good"
        : "bad"
      : "";
  const deltaCopy =
    typeof difference === "number"
      ? `${formatCurrency(difference)} (${formatPercent(percentDelta)})`
      : "—";
  const rangeCopy =
    typeof analysis?.lowest_price === "number" && typeof analysis?.highest_price === "number"
      ? `${formatCurrency(analysis.lowest_price)} - ${formatCurrency(analysis.highest_price)}`
      : "—";
  const sellerSummary = analysis?.seller_summary;
  const topSeller = sellerSummary?.top_seller;
  const marketConfidence = analysis?.market_confidence;
  const insights = Array.isArray(analysis?.insights) ? analysis.insights : [];
  const recommendedListings = Array.isArray(analysis?.recommended_listings)
    ? analysis.recommended_listings
    : [];
  const confidenceHtml = marketConfidence
    ? `
      <section class="confidence">
        <div class="confidence-header">
          <span class="confidence-label">Confidence</span>
          <span class="confidence-level">${escapeHtml(marketConfidence.level || "Low")}</span>
        </div>
        <div class="confidence-signals">
          ${(Array.isArray(marketConfidence.signals) ? marketConfidence.signals : [])
            .map((signal) => `<span>${escapeHtml(signal)}</span>`)
            .join("")}
        </div>
      </section>
    `
    : "";
  const insightHtml = insights.length
    ? `
      <div class="insights">
        ${insights
          .map((insight) => `<p>${escapeHtml(insight)}</p>`)
          .join("")}
      </div>
    `
    : "";
  const recommendationsHtml = recommendedListings.length
    ? `
      <section class="recommendations">
        <h2>Good similar listings</h2>
        <div class="listing-list">
          ${recommendedListings
            .map(
              (listing) => `
                <a class="listing" href="${escapeHtml(listing.item_url)}" target="_blank" rel="noopener noreferrer">
                  <div class="listing-copy">
                    <span class="listing-title">${escapeHtml(listing.title)}</span>
                    <span class="listing-meta">${escapeHtml(formatListingMeta(listing))}</span>
                  </div>
                  <span class="listing-price">${formatCurrency(listing.total_price)}</span>
                </a>
              `
            )
            .join("")}
        </div>
      </section>
    `
    : "";
  const helpfulChoice = savedFeedback.helpful;
  const hasReportedComparables = Boolean(savedFeedback.incorrectComparables);
  const feedbackNote = hasReportedComparables
    ? "Thanks. This report is saved in this browser for review."
    : helpfulChoice
    ? "Thanks for the feedback."
    : "Your feedback helps tune future scoring.";
  const feedbackHtml = analysis
    ? `
      <section class="feedback" data-feedback-key="${escapeHtml(feedbackKey)}">
        <div class="feedback-row">
          <span class="feedback-question">Was this analysis helpful?</span>
          <div class="feedback-actions" role="group" aria-label="Analysis feedback">
            <button class="feedback-button ${helpfulChoice === "up" ? "selected" : ""}" type="button" data-feedback-choice="up" aria-label="Yes, this analysis was helpful">👍</button>
            <button class="feedback-button ${helpfulChoice === "down" ? "selected" : ""}" type="button" data-feedback-choice="down" aria-label="No, this analysis was not helpful">👎</button>
          </div>
        </div>
        <button class="report-button ${hasReportedComparables ? "reported" : ""}" type="button" data-report-comparables="true">
          ${hasReportedComparables ? "Incorrect comparables reported" : "Report incorrect comparables"}
        </button>
        <div class="feedback-note">${escapeHtml(feedbackNote)}</div>
      </section>
    `
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
        <span class="label">Market average</span>
        <span class="value">${formatCurrency(average)}</span>
      </div>
      <div class="stat">
        <span class="label">Median price</span>
        <span class="value">${formatCurrency(median)}</span>
      </div>
      <div class="stat">
        <span class="label">Vs. average</span>
        <span class="value ${differenceClass}">${deltaCopy}</span>
      </div>
      <div class="stat">
        <span class="label">Comparable range</span>
        <span class="value">${rangeCopy}</span>
      </div>
      <div class="stat">
        <span class="label">Comparables</span>
        <span class="value">${formatNumber(comparableCount)}</span>
      </div>
      <div class="stat">
        <span class="label">Seller signal</span>
        <span class="value compact" title="${escapeHtml(formatSellerFeedback(topSeller))}">${escapeHtml(formatSellerFeedback(topSeller))}</span>
      </div>
      <div class="stat">
        <span class="label">Updated</span>
        <span class="value">${analysis ? (analysis.cached ? "Cached" : "Just Now") : "Pending"}</span>
      </div>
    </div>
    ${confidenceHtml}
    ${insightHtml}
    ${recommendationsHtml}
    <div class="meter" aria-hidden="true">
      <div class="meter-fill" style="width: ${scoreWidth}%"></div>
    </div>
    ${feedbackHtml}
  `;

  content.innerHTML = html;
}

function refreshPopup() {
  chrome.storage.local.get(
    [
      "lastAnalysis",
      "lastAnalysisError",
      "lastProduct",
      "lastBulkSummary",
      "lastPageType",
      "analysisFeedback",
    ],
    renderPopup
  );
}

refreshPopup();

content.addEventListener("click", (event) => {
  const feedbackButton = event.target.closest("[data-feedback-choice]");
  const reportButton = event.target.closest("[data-report-comparables]");

  if (!feedbackButton && !reportButton) return;

  const feedbackSection = event.target.closest("[data-feedback-key]");
  if (!feedbackSection) return;

  const feedbackKey = feedbackSection.dataset.feedbackKey;
  chrome.storage.local.get(["analysisFeedback"], ({ analysisFeedback = {} }) => {
    const currentFeedback = analysisFeedback[feedbackKey] || {};
    const nextFeedback = {
      ...currentFeedback,
      updatedAt: new Date().toISOString(),
    };

    if (feedbackButton) {
      nextFeedback.helpful = feedbackButton.dataset.feedbackChoice;
    }

    if (reportButton) {
      nextFeedback.incorrectComparables = true;
    }

    chrome.storage.local.set({
      analysisFeedback: {
        ...analysisFeedback,
        [feedbackKey]: nextFeedback,
      },
    });
  });
});

chrome.storage.onChanged.addListener((changes, areaName) => {
  if (areaName !== "local") return;

  if (
    changes.lastAnalysis ||
    changes.lastAnalysisError ||
    changes.lastProduct ||
    changes.lastBulkSummary ||
    changes.lastPageType ||
    changes.analysisFeedback
  ) {
    refreshPopup();
  }
});
