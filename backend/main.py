
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

models.Base.metadata.create_all(bind=engine)
app = FastAPI()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/test-insert")
def test_insert(db: Session = Depends(get_db)):
    record = models.EbayBuyPrice(
        product_name="RTX 4070",
        price=289.99
    )

    db.add(record)
    db.commit()
    db.refresh(record)

    return record


@app.get("/analyze")
def analyze(category: str, name: str):
    product_query = ProductQuery(name=name, category=category)

    ebay_sell_provider = EbayScrapeSellProvider()
    ebay_buy_provider = EbayPriceProvider()

    sell_data = ebay_sell_provider.get_sell_metrics(product_query)
    buy_data = ebay_buy_provider.get_buy_price(product_query)

    return {
        "buy": buy_data,
        "sell": sell_data,
        "opportunity": get_opportunity_index(
            buy_price=buy_data["price"],
            sell_price=sell_data["median_price"],
            sold_count=sell_data["sold_count"],
            category=category
        )
    }
    

    