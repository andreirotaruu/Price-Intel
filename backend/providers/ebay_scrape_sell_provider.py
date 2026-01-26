from bs4 import BeautifulSoup
import requests
from backend.providers.sell_provider import SellPriceProvider
from backend.domain.product_query import ProductQuery
import statistics

class EbayScrapeSellProvider(SellPriceProvider):

    SELL_URL = "https://www.ebay.com/sch/i.html"
    PRICE_SELECTORS = [
        ".s-item__price",
        ".s-card__price"
    ]

    def get_sell_metrics(self, product_query: ProductQuery) -> dict | None:
        
        #load url parameters to search for specific product and get on that page
        params = {
            "_nkw": product_query.name,
            "LH_Sold": "1",
            "LH_Complete": "1"
        }

        #if a sacat # is present we can look up the specific category of that product
        if product_query.category:
            ebay_category = product_query.get_category_id()
            if ebay_category:
                params["_sacat"] = ebay_category

        #user agent so we not sus
        headers = { "User-Agent": "ResellIntel/1.0 (price intel)" }

        #open page
        response = requests.get(self.SELL_URL, params=params, headers=headers)

        #handle error response
        if response.status_code != 200:

            print("There was an error when getting the page for EBay")
            return None
        
        #get desired page html
        soup = BeautifulSoup(response.text, "lxml")

        #all the prices on the page will go in here
        prices = []

        #iterate over all the html tags on the page that have the prices 
        for selector in self.PRICE_SELECTORS:
            for tag in soup.select(selector):
                
                #get the text for the price html element
                text = (tag.text.replace("$","").replace(",", "").strip())
                
                if "to" in text.lower():
                    continue

                try:
                    prices.append(float(text))
                except:
                    continue

        
        if not prices:
            return None
        
        #calculate median and count being sold and return them
        return{
            "median_price": statistics.median(prices),
            "sold_count": len(prices)
        }
