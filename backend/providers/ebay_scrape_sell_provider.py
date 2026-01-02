from bs4 import BeautifulSoup
import requests
from providers.sell_provider import SellPriceProvider
from domain.product_query import ProductQuery
import statistics

class EbayScrapeSellProvider(SellPriceProvider):

    SELL_URL = "https://www.ebay.com/sch/i.html"
    PRICE_SELECTORS = [
        ".s-item__price",
        ".s-card__price"
    ]

    def get_sell_metrics(self, product_query: ProductQuery) -> dict | None:
        
        params = {
            "_nkw": product_query,
            "LH_Sold": "1",
            "LH_Complete": "1"
        }

        headers = { "User-Agent": "ResellIntel/1.0 (price intel)" }

        response = requests.get(self.SELL_URL, params=params, headers=headers)

        if response.status_code != 200:

            return None
        
        soup = BeautifulSoup(response.text, "lxml")

        prices = []

        for selector in self.PRICE_SELECTORS:
            for tag in soup.select(selector):

                text = (tag.text.replace("$","").replace(",", "").strip())
                
                if "to" in text.lower():
                    continue

                try:
                    prices.append(float(text))
                except:
                    continue

        
        if not prices:
            return None
        
        return{
            "median_price": statistics.median(prices),
            "sold_count": len(prices)
        }
