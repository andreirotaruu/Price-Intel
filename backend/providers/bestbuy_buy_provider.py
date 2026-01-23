from bs4 import BeautifulSoup
import re
import requests
from providers.buy_provider import BuyPriceProvider
from domain.product_query import ProductQuery
from typing import Optional
import statistics


class BestBuyProvider(BuyPriceProvider):

    SEARCH_URL = "https://www.bestbuy.com/site/searchpage.jsp?id=pcat17071&"

    def get_buy_price(self, product_query: ProductQuery) -> Optional[float]:
        """Search BestBuy for product_query and return the median price or None.

        Notes:
        - Returns None if the HTTP request fails or no prices are found.
        - Uses a tolerant price parser to strip currency symbols and commas.
        """

        params = {"st": product_query.name}
        headers = {"User-Agent": "ResellIntel/1.0 (price intel)"}

        try:
            response = requests.get(self.SEARCH_URL, params=params, headers=headers, timeout=10)
            print(response.status_code)
        except Exception as e:
            print("Best Buy Request Failed: ", e)

        #get response
        if response.status_code != 200:
            print("There was an error when getting BestBuy's page: ", response.status_code)
            return None

        soup = BeautifulSoup(response.text, "lxml")

        prices: list[float] = []

        #loop over all product blocks (use find_all, not find)
        for item_div in soup.find_all("div", attrs={"class": "sku-block"}):
            if item_div is None:
                continue

            #get the title of the product on the page
            title_element = item_div.find("a", attrs={"class": "product-title"})
            if not title_element:
                # try alternative class names used on the site
                title_element = item_div.find("h4", attrs={"class": "sku-header"})
            if not title_element:
                continue

            title = title_element.get_text(strip=True)

            #get the price element (correct attrs dict usage)
            price_div = item_div.find("div", attrs={"data-testid": "price-block-customer-price"})
            if not price_div:
                #some pages embed price in span or strong tags — try permissive search
                price_div = item_div.find(attrs={"class": re.compile(r"price", re.I)})
            if not price_div:
                continue

            price_text = price_div.get_text(strip=True)

            #clean the price text (remove currency symbols, commas, non-numeric chars)
            #allow numbers like "$1,234.56" or "1,234.56"
            m = re.search(r"([0-9]+[0-9,]*\.?[0-9]*)", price_text)
            if not m:
                continue

            try:
                normalized = m.group(1).replace(",", "")
                price = float(normalized)
            except Exception:
                continue

            prices.append(price)

        if not prices:
            return None

        median_price = statistics.median(prices)
        return median_price



        

