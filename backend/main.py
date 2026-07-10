from pathlib import Path
import sys

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.services.market import build_analysis_response
from backend.services.normalize import (
    build_market_search_query,
    build_product_profile,
    enrich_product_profile,
    normalize_name,
    products_are_comparable,
    token_similarity_score,
)
from backend.providers.ebay_api import EbayAPIError, EbayAPIProvider
from backend.schemas.collect_request import CollectRequest, CollectBulkRequest
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.db.database import SessionLocal
from backend.db import models
from backend.db.models import MarketSnapshot
from backend.db.database import engine
from backend.schemas.analyze_request import AnalyzeRequest
from fastapi.middleware.cors import CORSMiddleware
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone


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


def _get_item_details(provider, item_id):
    try:
        return provider.get_item(item_id)
    except Exception:
        return {}


def _snapshot_is_usable(snapshot):
    if not snapshot or not snapshot.count or snapshot.count < 3:
        return False

    prices = (
        snapshot.average,
        snapshot.median,
        snapshot.lowest_price,
        snapshot.highest_price,
    )
    if any(price is None or price <= 0 for price in prices):
        return False

    # Reject legacy snapshots whose range strongly suggests accessories or bad matches.
    return (
        snapshot.lowest_price >= snapshot.median * 0.25
        and snapshot.highest_price <= snapshot.median * 3
    )


def _build_listing_from_item(item, request_profile):
    item_profile = build_product_profile(item["title"])
    item_profile = enrich_product_profile(item_profile, item)

    return {
        "title": item["title"],
        "normalized_name": item_profile["match_key"],
        "attributes": item_profile,
        "similarity_score": token_similarity_score(request_profile, item_profile),
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
        "item_id": item.get("itemId"),
        "legacy_item_id": item.get("legacyItemId", ""),
        "item_url": item.get("itemWebUrl") or item.get("itemAffiliateWebUrl", ""),
    }


def _snapshot_response_kwargs(snapshot):
    return {
        "average_price": snapshot.average,
        "median_price": snapshot.median,
        "lowest_price": snapshot.lowest_price,
        "highest_price": snapshot.highest_price,
        "listing_count": snapshot.count,
        "cached": True,
    }


def _save_observed_listings(db, listings, category):
    for listing in listings:
        item_id = listing.get("item_id")
        observed = None

        if item_id:
            observed = (
                db.query(models.ObservedListing)
                .filter(models.ObservedListing.item_id == item_id)
                .first()
            )

        if not observed:
            observed = models.ObservedListing(item_id=item_id)
            db.add(observed)

        observed.normalized_name = listing["normalized_name"]
        observed.title = listing.get("title")
        observed.category = listing.get("category", category)
        observed.marketplace = listing.get("marketplace", "ebay")
        observed.condition = listing.get("condition", "Unknown")
        observed.observed_price = listing["price"] + listing["shipping"]
        observed.shipping = listing.get("shipping")
        observed.seller_feedback = listing.get("seller_feedback")
        observed.seller_score = listing.get("seller_score")
        observed.seller_username = listing.get("seller_username")
        observed.seller_type = listing.get("seller_type")
        observed.source = listing.get("item_url")

    db.commit()


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
    
    ebay = EbayAPIProvider()
    request_profile = enrich_product_profile(
        request_profile,
        {"condition": request.condition} if request.condition else None,
    )
    if request.item_id:
        try:
            request_profile = enrich_product_profile(
                request_profile,
                ebay.get_item_by_legacy_id(request.item_id),
            )
        except Exception:
            pass

    try:
        response = ebay.search(name)
    except EbayAPIError as exc:
        if _snapshot_is_usable(snapshot):
            return build_analysis_response(
                request=request,
                normalized_name=normalized_name,
                product_attributes=request_profile,
                **_snapshot_response_kwargs(snapshot),
            )
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    items = response.get("itemSummaries", [])
    market_query = build_market_search_query(request_profile, name)
    if market_query.lower() != name.lower():
        try:
            broad_response = ebay.search(market_query)
            items.extend(broad_response.get("itemSummaries", []))
        except EbayAPIError:
            pass

    items = list(
        {
            item.get("itemId") or item.get("itemWebUrl"): item
            for item in items
            if item.get("itemId") or item.get("itemWebUrl")
        }.values()
    )

    listings = [_build_listing_from_item(item, request_profile) for item in items]

    detail_candidates = sorted(
        (
            listing
            for listing in listings
            if (
                listing["item_id"]
                and
                (not request.item_id or listing["legacy_item_id"] != request.item_id)
                and products_are_comparable(request_profile, listing["attributes"])
            )
        ),
        key=lambda listing: listing["similarity_score"],
        reverse=True,
    )[:12]
    with ThreadPoolExecutor(max_workers=6) as executor:
        future_to_listing = {
            executor.submit(_get_item_details, ebay, listing["item_id"]): listing
            for listing in detail_candidates
        }
        for future in as_completed(future_to_listing):
            listing = future_to_listing[future]
            listing["attributes"] = enrich_product_profile(
                listing["attributes"],
                future.result(),
            )
    
    _save_observed_listings(db, listings, category)
    
    #to-do change to HTTP exception
    if not listings:
        print("No listings found")
        print(response)
        if _snapshot_is_usable(snapshot):
            return build_analysis_response(
                request=request,
                normalized_name=normalized_name,
                product_attributes=request_profile,
                **_snapshot_response_kwargs(snapshot),
            )
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
        if (
            (not request.item_id or listing["legacy_item_id"] != request.item_id)
            and products_are_comparable(request_profile, listing["attributes"])
        ):
            comparables.append(listing)

    if not comparables:
        if _snapshot_is_usable(snapshot):
            return build_analysis_response(
                request=request,
                normalized_name=normalized_name,
                product_attributes=request_profile,
                comparables=[],
                **_snapshot_response_kwargs(snapshot),
            )
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
            comparables=[],
        )

    prices = [
        listing["price"] + listing["shipping"]
        for listing in comparables
    ]

    if _snapshot_is_usable(snapshot):
        average_price = snapshot.average
        median_price = snapshot.median
        lowest_price = snapshot.lowest_price
        highest_price = snapshot.highest_price
        listing_count = snapshot.count
        cached = True
    else:
        average_price = statistics.mean(prices)
        median_price = statistics.median(prices)
        lowest_price = min(prices)
        highest_price = max(prices)
        listing_count = len(prices)
        cached = False

    if not snapshot:
        snapshot = MarketSnapshot(name=normalized_name)

    if not cached:
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
        cached=cached,
        comparables=comparables,
    )

if __name__ == "__main__":
    main()
