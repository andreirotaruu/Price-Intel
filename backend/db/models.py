from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime, timezone, UTC
from backend.db.database import Base

class EbayBuyPrice(Base):
    __tablename__ = "ebay_buy_prices"

    id = Column(Integer, primary_key=True, index=True)
    product_name = Column(String, index=True)
    price = Column(Float)
    source = Column(String, default="ebay")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class ObservedListing(Base):
    __tablename__ = "observed_listings"

    __tablename__ = "observed_listings"

    id = Column(Integer, primary_key=True)

    normalized_name = Column(String, index=True)

    title = Column(String)

    category = Column(String)

    marketplace = Column(String)

    item_id = Column(String)

    condition = Column(String)

    observed_price = Column(Float)

    shipping = Column(Float)

    seller_feedback = Column(Float)

    seller_score = Column(Integer)

    source = Column(String)      

    created_at = Column(DateTime)


class MarketSnapshot(Base):
    __tablename__ = "market_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)

    average = Column(Float)
    median = Column(Float)
    lowest_price = Column(Float)
    highest_price = Column(Float)
    count = Column(Integer)
    last_updated = Column(DateTime)
