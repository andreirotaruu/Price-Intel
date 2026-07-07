"""Daily job to gather listings from eBay API and store them."""

from datetime import datetime, timezone

from backend.db.database import SessionLocal
from backend.db.models import ObservedListing
from backend.providers.ebay_api import EbayAPIProvider
from backend.services.normalize import build_product_profile


SEED_PRODUCTS = [
    "RTX 4070",
    "RTX 4070 Super",
    "RTX 4070 Ti Super",
    "RTX 4080 Super",
    "RTX 4090",
    "RX 7800 XT",
    "RX 7900 XT",
    "RX 7900 XTX",
    "PlayStation 5 Slim",
    "PlayStation 5 Pro",
    "Xbox Series X",
    "Nintendo Switch OLED",
    "Steam Deck OLED",
    "iPhone 16 Pro",
    "iPhone 16 Pro Max",
    "Samsung Galaxy S25 Ultra",
    "Ryzen 7 9800X3D",
    "Ryzen 9 9950X",
    "MacBook Air M4",
    "MacBook Pro M4",
]


def parse_shipping(item: dict) -> float:
    shipping_options = item.get("shippingOptions", [])

    if not shipping_options:
        return 0.0

    shipping_cost = shipping_options[0].get("shippingCost", {})

    return float(shipping_cost.get("value", 0))


def save_listing(db, listing: dict):
    existing = (
        db.query(ObservedListing)
        .filter(ObservedListing.item_id == listing["item_id"])
        .first()
    )

    now = datetime.now(timezone.utc)

    if existing:
        existing.observed_price = listing["price"]
        existing.shipping = listing["shipping"]
        existing.condition = listing["condition"]
        existing.seller_feedback = listing["seller_feedback"]
        existing.seller_score = listing["seller_score"]
        existing.seller_username = listing["seller_username"]
        existing.seller_type = listing["seller_type"]
        existing.created_at = now
        return

    observed = ObservedListing(
        normalized_name=listing["normalized_name"],
        title=listing["title"],
        category=listing["category"],
        marketplace="ebay",
        item_id=listing["item_id"],
        condition=listing["condition"],
        observed_price=listing["price"],
        shipping=listing["shipping"],
        seller_feedback=listing["seller_feedback"],
        seller_score=listing["seller_score"],
        seller_username=listing["seller_username"],
        seller_type=listing["seller_type"],
        source="scheduled_api",
        created_at=now,
    )

    db.add(observed)


def main():
    db = SessionLocal()
    ebay = EbayAPIProvider()

    try:
        for product in SEED_PRODUCTS:
            print(f"Fetching: {product}")

            response = ebay.search(product)
            print(f"response code: {response}")
            items = response.get("itemSummaries", [])

            for item in items:
                item_profile = build_product_profile(item["title"])
                seller = item.get("seller", {})

                listing = {
                    "title": item.get("title", ""),
                    "normalized_name": item_profile["match_key"],
                    "category": product,
                    "price": float(item["price"]["value"]),
                    "condition": item.get("condition"),
                    "shipping": parse_shipping(item),
                    "seller_feedback": float(seller.get("feedbackPercentage", 0)),
                    "seller_score": seller.get("feedbackScore", 0),
                    "seller_username": seller.get("username", ""),
                    "seller_type": seller.get("sellerAccountType", ""),
                    "item_id": item["itemId"],
                }

                save_listing(db, listing)

            db.commit()
            print(f"Saved {len(items)} listings for {product}")

    except Exception as e:
        db.rollback()
        print("Error running daily market refresh:", e)
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()