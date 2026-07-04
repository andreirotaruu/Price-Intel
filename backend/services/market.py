import math
from backend.schemas.analyze_request import AnalyzeRequest

def calculate_deal_score(current_price: float | None, market_price: float | None, comparable_count: int = 0):
    if (
        current_price is None
        or market_price is None
        or current_price <= 0
        or market_price <= 0
    ):
        return None

    upside_ratio = (market_price - current_price) / market_price
    confidence = min(max(comparable_count, 0) / 20, 1)
    confidence_weight = 0.65 + confidence * 0.35

    if upside_ratio <= -0.1:
        base_score = 10
    elif upside_ratio < 0:
        base_score = 25 + ((upside_ratio + 0.1) / 0.1) * 20
    elif upside_ratio < 0.1:
        base_score = 45 + (upside_ratio / 0.1) * 20
    elif upside_ratio < 0.2:
        base_score = 65 + ((upside_ratio - 0.1) / 0.1) * 17
    elif upside_ratio < 0.35:
        base_score = 82 + ((upside_ratio - 0.2) / 0.15) * 13
    else:
        base_score = 95 + min((upside_ratio - 0.35) / 0.25, 1) * 3

    score = 50 + (base_score - 50) * confidence_weight
    return round(max(1, min(98, score)))


def generate_insights(current_price, average_price, lowest_price, highest_price, comparable_count):
    insights = []

    if current_price and average_price:
        percent_delta = (average_price - current_price) / average_price * 100
        direction = "below" if percent_delta >= 0 else "above"
        insights.append(
            f"This listing is {abs(percent_delta):.1f}% {direction} the market average."
        )

    if comparable_count:
        if current_price and average_price:
            percent_delta = (average_price - current_price) / average_price * 100
            if percent_delta >= 10:
                deal_read = "strong deal"
            elif percent_delta >= 0:
                deal_read = "fair deal"
            else:
                deal_read = "high-priced listing"
            insights.append(
                f"Based on {comparable_count} comparable listings, this appears to be a {deal_read}."
            )
        elif comparable_count >= 30:
            insights.append(
                f"Based on {comparable_count} comparable listings, this appears to be a strong estimate."
            )
        else:
            insights.append(
                f"Based on {comparable_count} comparable listings, this appears to be an early estimate."
            )

    if average_price and lowest_price is not None and highest_price is not None:
        spread_pct = (highest_price - lowest_price) / average_price * 100
        if spread_pct <= 20:
            insights.append(
                "Prices for this product are tightly clustered, increasing confidence in the estimate."
            )
        elif spread_pct >= 60:
            insights.append(
                "Comparable prices vary widely, so condition and seller details matter more here."
            )

    return insights


def build_analysis_response(
    *,
    request: AnalyzeRequest,
    normalized_name: str,
    average_price: float,
    median_price: float,
    lowest_price: float,
    highest_price: float,
    listing_count: int,
    cached: bool,
    comparables=None,
):
    current_price = request.current_price
    price_delta = None
    percent_delta = None

    if current_price and average_price:
        price_delta = average_price - current_price
        percent_delta = price_delta / average_price * 100

    return {
        "product_name": request.name,
        "normalized_name": normalized_name,
        "current_price": current_price,
        "average_price": average_price,
        "median_price": median_price,
        "lowest_price": lowest_price,
        "highest_price": highest_price,
        "listing_count": listing_count,
        "comparable_count": listing_count,
        "deal_score": calculate_deal_score(current_price, average_price, listing_count),
        "price_delta": price_delta,
        "percent_delta": percent_delta,
        "cached": cached,
        "insights": generate_insights(
            current_price,
            average_price,
            lowest_price,
            highest_price,
            listing_count,
        ),
        "comparables": comparables or [],
    }