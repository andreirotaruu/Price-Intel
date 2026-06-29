from backend.services.opportunity import get_opportunity_index
from backend.services.market import get_deal_score
from backend.providers.ebay_api import EbayAPIProvider
from backend.schemas.collect_request import CollectRequest, CollectBulkRequest
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from backend.db.database import SessionLocal
from backend.db import models
from backend.db.models import MarketSnapshot
from backend.db.database import engine
from backend.schemas.analyze_request import AnalyzeRequest
from fastapi.middleware.cors import CORSMiddleware
import statistics
import datetime
import re
from datetime import timedelta, timezone


#create models
models.Base.metadata.create_all(bind=engine)
#initialize fastAPI
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def main():
    provider = EbayAPIProvider()

    response = provider.search("RTX 4070")
    print(response)


def get_db():

    #creating the db session
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

#setting the endpoint to call this function
@app.post("/test-insert")
def test_insert(db: Session = Depends(get_db)):
    
    #creating a record
    record = models.EbayBuyPrice(
        product_name="RTX 4070",
        price=289.99
    )

    #adding the record to db
    db.add(record)
    db.commit()
    db.refresh(record)

    return record

@app.post("/collect")
def collect(request: CollectRequest, db: Session = Depends(get_db)):
    
    listing = models.ObservedListing(
        name=request.name,
        category=request.category,
        marketplace=request.marketplace,
        condition=request.condition,
        observed_price=request.current_price,
    )

    db.add(listing)
    db.commit()

    return {
        "status": "saved"
    }

@app.post("/collect_bulk")
def collect_bulk(request: CollectBulkRequest, db: Session = Depends(get_db)):
    if not request.listings:
        return {
            "status": "saved",
            "inserted": 0
        }

    records = [
        models.ObservedListing(
            name=listing.name,
            category=listing.category,
            marketplace=listing.marketplace,
            condition=listing.condition,
            observed_price=listing.current_price,
        )
        for listing in request.listings
    ]

    db.add_all(records)
    db.commit()

    return {
        "status": "saved",
        "inserted": len(records)
    }

def normalize_name(name: str) -> str:
    text = name.lower()
    text = re.sub(r"[^a-z0-9+\s-]", " ", text)
    text = re.sub(r"\bfe\b", " founders edition ", text)
    text = re.sub(r"\bfounders?\s+editions?\b", " founders edition ", text)
    text = re.sub(r"\b(\d+)\s*gb\b", r"\1gb", text)

    tokens = text.replace("-", " ").split()
    token_set = set(tokens)

    gpu_match = re.search(r"\brtx\s*(\d{4})\b", text)
    if gpu_match:
        parts = ["rtx", gpu_match.group(1)]
        if "ti" in token_set:
            parts.append("ti")
        if "super" in token_set:
            parts.append("super")
        if "founders" in token_set and "edition" in token_set:
            parts.extend(["founders", "edition"])
        return " ".join(parts)

    stop_words = {
        "excellent",
        "condition",
        "used",
        "new",
        "tested",
        "working",
        "nvidia",
        "geforce",
        "graphics",
        "graphic",
        "card",
        "gddr6",
        "gddr6x",
    }

    words = [word for word in tokens if word not in stop_words]
    return " ".join(words)


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

#setting this endpoint to call this function
@app.post("/analyze")
def analyze(request: AnalyzeRequest, db: Session = Depends(get_db)):


    name = request.name
    normalized_name = normalize_name(name)
    category = request.category

    snapshot = (db.query(MarketSnapshot)
                .filter(
                    MarketSnapshot.name == normalized_name
                )
                .first()
            )
    
    if snapshot:
        last_updated = snapshot.last_updated
        if last_updated.tzinfo is None:
            last_updated = last_updated.replace(tzinfo=timezone.utc)

        age = datetime.now(timezone.utc) - last_updated

        if age < timedelta(hours=1):
            return build_analysis_response(
                request=request,
                normalized_name=normalized_name,
                average_price=snapshot.average,
                median_price=snapshot.median,
                lowest_price=snapshot.lowest_price,
                highest_price=snapshot.highest_price,
                listing_count=snapshot.count,
                cached=True,
            )

    ebay = EbayAPIProvider()
    response = ebay.search(name)

    items = response.get("itemSummaries", [])

    listings = []
    
    for item in items:
        listings.append({
            "title": item["title"],
            "price": float(item["price"]["value"]),
            "condition": item.get("condition"),
            "shipping": float(
                item.get("shippingOptions", [{}])[0]
                    .get("shippingCost", {})
                    .get("value", 0)
            ),
            "seller_feedback": float(
                item.get("seller", {})
                    .get("feedbackPercentage", 0)
            ),
            "seller_score": item.get("seller", {})
                            .get("feedbackScore", 0),
            "item_id": item["itemId"]
        })
    

    #to-do change to HTTP exception
    if not listings:
        print("No listings found")
        return build_analysis_response(
            request=request,
            normalized_name=normalized_name,
            average_price=0,
            median_price=0,
            lowest_price=0,
            highest_price=0,
            listing_count=0,
            cached=False,
        )
    #compare price + shipping
    prices = [l["price"] + l["shipping"] for l in listings]


    average_price = statistics.mean(prices)
    median_price = statistics.median(prices)
    lowest_price = min(prices)
    highest_price = max(prices)
    listing_count = len(prices)

    if not snapshot:
        snapshot = MarketSnapshot(name=normalized_name)

    snapshot.average = average_price
    snapshot.median = median_price
    snapshot.lowest_price = lowest_price
    snapshot.highest_price = highest_price
    snapshot.count = listing_count
    snapshot.last_updated = datetime.now(timezone.utc)

    db.add(snapshot)
    db.commit()
    
    #store in DB
    #to-do change db column names for min and max price


    return build_analysis_response(
        request=request,
        normalized_name=normalized_name,
        average_price=average_price,
        median_price=median_price,
        lowest_price=lowest_price,
        highest_price=highest_price,
        listing_count=listing_count,
        cached=False,
        comparables=listings,
    )

if __name__ == "__main__":
    main()
