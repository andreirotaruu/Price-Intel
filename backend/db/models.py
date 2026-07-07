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

    id = Column(Integer, primary_key=True, index=True)

    # Product information
    normalized_name = Column(String, index=True)
    title = Column(String)
    category = Column(String)
    marketplace = Column(String)

    # eBay listing information
    item_id = Column(String, unique=True, index=True)

    # Listing details
    condition = Column(String)
    observed_price = Column(Float)
    shipping = Column(Float)

    # Seller information
    seller_feedback = Column(Float)
    seller_score = Column(Integer)
    seller_username = Column(String)
    seller_type = Column(String)

    # Metadata
    source = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))


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
