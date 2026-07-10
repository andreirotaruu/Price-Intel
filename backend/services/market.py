import math
from backend.schemas.analyze_request import AnalyzeRequest


def _as_number(value):
    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def calculate_deal_score(current_price: float | None, market_price: float | None, comparable_count: int = 0):
    if (
        current_price is None
        or market_price is None
        or current_price <= 0
        or market_price <= 0
        or comparable_count < 3
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


def build_seller_summary(comparables):
    seller_rows = []

    for listing in comparables or []:
        username = listing.get("seller_username") or ""
        feedback_percentage = _as_number(listing.get("seller_feedback"))
        feedback_score = _as_number(listing.get("seller_score"))
        seller_type = listing.get("seller_type") or ""

        if not username and feedback_percentage is None and feedback_score is None:
            continue

        seller_rows.append(
            {
                "username": username,
                "feedback_percentage": feedback_percentage,
                "feedback_score": int(feedback_score or 0),
                "seller_type": seller_type,
            }
        )

    if not seller_rows:
        return None

    feedback_values = [
        seller["feedback_percentage"]
        for seller in seller_rows
        if seller["feedback_percentage"] is not None
    ]
    average_feedback = (
        sum(feedback_values) / len(feedback_values)
        if feedback_values
        else None
    )
    low_feedback_count = sum(
        1
        for seller in seller_rows
        if (
            seller["feedback_percentage"] is not None
            and seller["feedback_percentage"] < 95
        )
        or seller["feedback_score"] < 10
    )
    top_seller = max(
        seller_rows,
        key=lambda seller: (
            seller["feedback_score"],
            seller["feedback_percentage"] or 0,
        ),
    )

    return {
        "seller_count": len(seller_rows),
        "average_feedback": average_feedback,
        "low_feedback_count": low_feedback_count,
        "top_seller": top_seller,
    }


def build_recommended_listings(comparables, median_price, limit=3):
    recommendations = []
    fallback_recommendations = []

    for listing in comparables or []:
        price = _as_number(listing.get("price"))
        shipping = _as_number(listing.get("shipping")) or 0
        feedback_percentage = _as_number(listing.get("seller_feedback"))
        feedback_score = _as_number(listing.get("seller_score")) or 0
        item_url = listing.get("item_url") or ""

        if price is not None and item_url.startswith(("https://", "http://")):
            total_price = price + shipping
            fallback_recommendations.append(
                {
                    "title": listing.get("title") or "Similar listing",
                    "similarity_score": _as_number(listing.get("similarity_score")) or 0,
                    "condition": listing.get("condition") or "Unknown condition",
                    "price": price,
                    "shipping": shipping,
                    "total_price": total_price,
                    "item_url": item_url,
                    "seller_username": listing.get("seller_username") or "Seller",
                    "seller_feedback": feedback_percentage,
                    "seller_score": int(feedback_score),
                }
            )

        if (
            price is None
            or not item_url.startswith(("https://", "http://"))
            or feedback_percentage is None
            or feedback_percentage < 98
            or feedback_score < 10
        ):
            continue

        total_price = price + shipping
        if median_price and total_price > median_price:
            continue

        recommendations.append(
            {
                "title": listing.get("title") or "Similar listing",
                "similarity_score": _as_number(listing.get("similarity_score")) or 0,
                "condition": listing.get("condition") or "Unknown condition",
                "price": price,
                "shipping": shipping,
                "total_price": total_price,
                "item_url": item_url,
                "seller_username": listing.get("seller_username") or "Seller",
                "seller_feedback": feedback_percentage,
                "seller_score": int(feedback_score),
            }
        )

    recommendations.sort(
        key=lambda listing: (
            -listing["similarity_score"],
            listing["total_price"],
            -listing["seller_feedback"],
            -listing["seller_score"],
        )
    )
    recommendations = recommendations[:limit]

    if len(recommendations) >= limit:
        return recommendations

    recommendation_urls = {
        recommendation["item_url"]
        for recommendation in recommendations
    }
    fallback_recommendations.sort(
        key=lambda listing: (
            -listing["similarity_score"],
            listing["total_price"],
            -(listing["seller_feedback"] or 0),
            -listing["seller_score"],
        )
    )

    for listing in fallback_recommendations:
        if listing["item_url"] in recommendation_urls:
            continue

        recommendations.append(listing)
        recommendation_urls.add(listing["item_url"])

        if len(recommendations) >= limit:
            break

    return recommendations


def generate_seller_insights(seller_summary):
    if not seller_summary:
        return []

    insights = []
    seller_count = seller_summary["seller_count"]
    average_feedback = seller_summary["average_feedback"]
    low_feedback_count = seller_summary["low_feedback_count"]
    top_seller = seller_summary["top_seller"]

    if average_feedback is not None:
        insights.append(
            f"API seller data covers {seller_count} comparable sellers with {average_feedback:.1f}% average positive feedback."
        )

    if top_seller.get("username"):
        insights.append(
            f"Most established comparable seller: {top_seller['username']} with {top_seller['feedback_score']:,} feedback score."
        )

    if low_feedback_count:
        verb = "shows" if low_feedback_count == 1 else "show"
        insights.append(
            f"{low_feedback_count} comparable seller{'s' if low_feedback_count != 1 else ''} {verb} low feedback history, so seller reputation should be checked before buying."
        )

    return insights


def generate_insights(
    current_price,
    average_price,
    lowest_price,
    highest_price,
    comparable_count,
    seller_summary=None,
):
    insights = []

    if comparable_count >= 3 and current_price and average_price:
        percent_delta = (average_price - current_price) / average_price * 100
        direction = "below" if percent_delta >= 0 else "above"
        insights.append(
            f"This listing is {abs(percent_delta):.1f}% {direction} the market average."
        )

    if 0 < comparable_count < 3:
        insights.append(
            f"Only {comparable_count} comparable listing{'s' if comparable_count != 1 else ''} matched, which is not enough for a reliable deal estimate."
        )
    elif comparable_count:
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

    if (
        comparable_count >= 3
        and average_price
        and lowest_price is not None
        and highest_price is not None
    ):
        spread_pct = (highest_price - lowest_price) / average_price * 100
        if spread_pct <= 20:
            insights.append(
                "Prices for this product are tightly clustered, increasing confidence in the estimate."
            )
        elif spread_pct >= 60:
            insights.append(
                "Comparable prices vary widely, so condition and seller details matter more here."
            )

    insights.extend(generate_seller_insights(seller_summary))

    return insights


def build_analysis_response(
    *,
    request: AnalyzeRequest,
    normalized_name: str,
    product_attributes: dict | None = None,
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
    seller_summary = build_seller_summary(comparables)
    recommended_listings = build_recommended_listings(comparables, median_price)

    if current_price and average_price:
        price_delta = average_price - current_price
        percent_delta = price_delta / average_price * 100

    return {
        "product_name": request.name,
        "normalized_name": normalized_name,
        "product_attributes": product_attributes or {},
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
            seller_summary,
        ),
        "seller_summary": seller_summary,
        "recommended_listings": recommended_listings,
        "comparables": comparables or [],
    }
