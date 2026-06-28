from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime, timezone, UTC
from db.database import Base

class EbayBuyPrice(Base):
    __tablename__ = "ebay_buy_prices"

    id = Column(Integer, primary_key=True, index=True)
    product_name = Column(String, index=True)
    price = Column(Float)
    source = Column(String, default="ebay")
    created_at = Column(DateTime, default=datetime.now(timezone.utc))


class ObservedListing(Base):
    __tablename__ = "observed_listings"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, index=True)
    category = Column(String)
    marketplace = Column(String)

    condition = Column(String)

    observed_price = Column(Float)

    created_at = Column(DateTime, default=datetime.now(UTC))


class MarketSnapshot(Base):
    name = Column(String, index=True)

    average = Column(Float)
    median = Column(Float)
    lowest_price = Column(Float)
    highest_price = Column(Float)
    count = Column(Integer)
    last_updated = Column(DateTime)