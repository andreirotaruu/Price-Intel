from providers.sell_provider import SellPriceProvider

class MockSellProvider(SellPriceProvider):

    def get_sell_metrics(self, upc: str):
        return {
            "median_price": 649.99,
            "sold_count": 42
        }
