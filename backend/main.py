from services.opportunity import get_opportunity_index
from services.market import get_deal_score
from providers.ebay_api import EbayAPIProvider
from schemas.collect_request import CollectRequest, CollectBulkRequest
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from db.database import SessionLocal
from db import models
from db.database import engine
from schemas.analyze_request import AnalyzeRequest
from fastapi.middleware.cors import CORSMiddleware
from numpy import average, median

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
    import re

    name = name.lower()

    name = re.sub(r'[^a-z0-9\s]', '', name)

    stop_words = {
        "excellent",
        "condition",
        "used",
        "new",
        "tested",
        "working"
    }

    words = [
        word
        for word in name.split()
        if word not in stop_words
    ]

    return " ".join(words)

#setting this endpoint to call this function
@app.post("/analyze")
def analyze(request: AnalyzeRequest, db: Session = Depends(get_db)):

    name = request.name
    category = request.category
    ebay = EbayAPIProvider()
    response = ebay.search(name)

    items = response["itemSummaries"]

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
                

    prices = [l.price for l in listings]

    #make this the 10th percentile in the future
    min_price = min(prices)
    #make this the 90th percentile in the future
    max_price = max(prices)
    sold_count = len(prices)
    average_price = average(prices)
    median_price = median(prices)
    
    #store in DB
    #to-do change db column names for min and max price
    cache_entry = models.PriceCache(
        name=name,
        category=category,
        buy_price=min_price,
        sell_price=max_price,
        sold_count=sold_count
    )

    db.add(cache_entry)
    db.commit()

    return {
        "source": "fresh",
        "min_price": min_price,
        "max_price": max_price,
        "sold_count": sold_count,
    }

if __name__ == "__main__":
    main()