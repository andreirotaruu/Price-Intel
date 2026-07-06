from backend.services.market import build_analysis_response
from backend.services.normalize import (
    build_product_profile,
    normalize_name,
    products_are_comparable,
)
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
from datetime import datetime, timedelta, timezone


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


@app.post("/collect")
def collect(request: CollectRequest, db: Session = Depends(get_db)):
    product_profile = build_product_profile(request.name)
    
    listing = models.ObservedListing(
        normalized_name=product_profile["match_key"],
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
            normalized_name=build_product_profile(listing.name)["match_key"],
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


#setting this endpoint to call this function
@app.post("/analyze")
def analyze(request: AnalyzeRequest, db: Session = Depends(get_db)):
    request_profile = build_product_profile(request.name)
    name = request.name
    normalized_name = request_profile["match_key"]
    legacy_normalized_name = normalize_name(name)
    category = request.category

    snapshot = (db.query(MarketSnapshot)
                .filter(
                    MarketSnapshot.name.in_([normalized_name, legacy_normalized_name])
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
                product_attributes=request_profile,
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
        item_profile = build_product_profile(item["title"])
        listings.append({
            "title": item["title"],
            "normalized_name": item_profile["match_key"],
            "attributes": item_profile,
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
            "seller_username": item.get("seller", {})
                            .get("username", ""), 
            "seller_type": item.get("seller", {})
                            .get("sellerAccountType", ""),
            "item_id": item["itemId"]
        })
    
    records = [
        models.ObservedListing(
            normalized_name=listing["normalized_name"],
            category=listing.get("category", category),
            marketplace=listing.get("marketplace", "ebay"),
            condition=listing.get("condition", "Unknown"),
            observed_price=listing["price"] + listing["shipping"],
        )
        for listing in listings
    ]

    db.add_all(records)
    db.commit()
    
    #to-do change to HTTP exception
    if not listings:
        print("No listings found")
        print(response)
        return build_analysis_response(
            request=request,
            normalized_name=normalized_name,
            product_attributes=request_profile,
            average_price=0,
            median_price=0,
            lowest_price=0,
            highest_price=0,
            listing_count=0,
            cached=False,
        )
    
    comparables = []

    for listing in listings:
        if products_are_comparable(request_profile, listing["attributes"]):
            comparables.append(listing)

    if not comparables:
        comparables = listings

    prices = [
        listing["price"] + listing["shipping"]
        for listing in comparables
    ]

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
        product_attributes=request_profile,
        average_price=average_price,
        median_price=median_price,
        lowest_price=lowest_price,
        highest_price=highest_price,
        listing_count=listing_count,
        cached=False,
        comparables=comparables,
    )

if __name__ == "__main__":
    main()
