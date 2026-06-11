from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime, timezone, UTC
from backend.db.database import Base

class EbayBuyPrice(Base):
    __tablename__ = "ebay_buy_prices"

    id = Column(Integer, primary_key=True, index=True)
    product_name = Column(String, index=True)
    price = Column(Float)
    source = Column(String, default="ebay")
    created_at = Column(DateTime, default=datetime.now(timezone.utc))


class PriceCache(Base):
    __tablename__ = "price_cache"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    category = Column(String, index=True)
    buy_price = Column(Float)
    sell_price = Column(Float)
    sold_count = Column(Float)

    created_at = Column(DateTime, default=datetime.now)


class ObservedListing(Base):
    __tablename__ = "observed_listings"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, index=True)
    category = Column(String)
    marketplace = Column(String)

    condition = Column(String)

    observed_price = Column(Float)

    created_at = Column(DateTime, default=datetime.now(UTC))