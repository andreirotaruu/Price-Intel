from providers.mock_buy_provider import MockBuyProvider
from providers.mock_sell_provider import MockSellProvider
from services.opportunity import get_opportunity_index
from providers.ebay_scrape_sell_provider import EbayScrapeSellProvider
from domain.product_query import ProductQuery

def analyze_product(upc: str, category: str):
    buy_provider = MockBuyProvider()
    sell_provider = MockSellProvider()

    buy_price = buy_provider.get_buy_price(upc)
    sell_data = sell_provider.get_sell_metrics(upc)

    ebay_sell_provider = EbayScrapeSellProvider()
    product_query = ProductQuery(
        name = 'RTX 4070',
        category = 'gpu'
    )
    ebay_sell_data = ebay_sell_provider.get_sell_metrics(product_query)

    print()
    print(ebay_sell_data)

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

    