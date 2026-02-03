from bs4 import BeautifulSoup
from backend.providers.buy_provider import BuyPriceProvider
from backend.domain.product_query import ProductQuery
import requests
import statistics

class EbayPriceProvider(BuyPriceProvider):

    SEARCH_URL = "https://www.ebay.com/sch/i.html"
    PRICE_SELECTORS = [
        ".s-item__price",
        ".s-card__price"
    ]

    def get_buy_price(self, product_query: ProductQuery) -> dict | None:

        #set parameters for search
        params = {
            "_nkw": product_query.name
        }

        #if product query object has a category we can set the search specific to product category
        if product_query.category:
            category = product_query.get_category_id
            if category:
                params["_sacat"] = category

        headers = { "User-Agent": "ResellIntel/1.0 (price intel)" }

        #get the page response
        response = requests.get(self.SEARCH_URL, params=params, headers=headers)

        if response.status_code != 200:
            print(f"There was a problem getting the page. Status Code: {response.status_code}")
            return None

        #get soup
        soup = BeautifulSoup(response.text, 'lxml')

        #array to hold the prices
        prices = []

        for selector in self.PRICE_SELECTORS:
            for tag in soup.select(selector):

                #get text for price 
                text = tag.text.replace("$", "").replace(",", "").strip()

                #skip if the listing is not a fixed price
                if "to" in text.lower():
                    continue
                    
                try:
                    prices.append(float(text))
                except:
                    print(f"could not parse: {text}")

        return {"price": statistics.median(prices)}
    
