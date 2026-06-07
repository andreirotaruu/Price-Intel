from backend.services.opportunity import get_opportunity_index
from backend.providers.ebay_scrape_sell_provider import EbayScrapeSellProvider
from backend.domain.product_query import ProductQuery
from backend.providers.bestbuy_buy_provider import BestBuyProvider
from backend.providers.ebay_scrape_buy_provider import EbayPriceProvider
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from backend.db.database import SessionLocal
from backend.db import models
from backend.db.database import engine
from backend.schemas.analyze_request import AnalyzeRequest
from fastapi.middleware.cors import CORSMiddleware

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

#setting this endpoint to call this function
@app.post("/analyze")
def analyze(request: AnalyzeRequest, db: Session = Depends(get_db)):

    name = request.name
    category = request.category

    #check cache
    cached = db.query(models.PriceCache).filter(
        models.PriceCache.name == name,
        models.PriceCache.category == category
    ).first()

    if cached:
        opportunity = get_opportunity_index(
            buy_price=cached.buy_price,
            sell_price=cached.sell_price,
            sold_count=cached.sold_count,
            category=category
        )

        return {
            "source": "cache",
            "buy_price": cached.buy_price,
            "sell_price": cached.sell_price,
            "sold_count": cached.sold_count,
            "opportunity": opportunity
        }

    #replace scraping with request data
    buy_price = request.current_price

    # TODO: replace this later with real provider
    sell_price = 500  # mock
    sold_count = 20   # mock

    opportunity = get_opportunity_index(
        buy_price=buy_price,
        sell_price=sell_price,
        sold_count=sold_count,
        category=category
    )

    #store in DB
    cache_entry = models.PriceCache(
        name=name,
        category=category,
        buy_price=buy_price,
        sell_price=sell_price,
        sold_count=sold_count
    )

    db.add(cache_entry)
    db.commit()

    return {
        "source": "fresh",
        "buy_price": buy_price,
        "sell_price": sell_price,
        "sold_count": sold_count,
        "opportunity": opportunity
    }