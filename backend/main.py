from providers.mock_buy_provider import MockBuyProvider
from providers.mock_sell_provider import MockSellProvider
from services.opportunity import get_opportunity_index

def analyze_product(upc: str, category: str):
    buy_provider = MockBuyProvider()
    sell_provider = MockSellProvider()

    buy_price = buy_provider.get_buy_price(upc)
    sell_data = sell_provider.get_sell_metrics(upc)

    return get_opportunity_index(
        buy_price=buy_price,
        sell_price=sell_data["median_price"],
        sold_count=sell_data["sold_count"],
        category=category
    )

if __name__ == "__main__":
    result = analyze_product(
        upc="711719556047",
        category="console"
    )

    print(result)
