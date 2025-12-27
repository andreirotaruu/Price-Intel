from providers.buy_provider import BuyPriceProvider

class MockBuyProvider(BuyPriceProvider):

    def get_buy_price(self, upc: str) -> float:
        return 519.99
