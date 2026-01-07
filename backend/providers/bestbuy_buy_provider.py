from bs4 import BeautifulSoup
import requests
from providers.buy_provider import BuyPriceProvider
from domain.product_query import ProductQuery
from typing import Dict

class BestBuyProvider(BuyPriceProvider):

    SEARCH_URL = "https://www.bestbuy.com/site/searchpage.jsp"
    def get_buy_metrics(self, product_query: ProductQuery) -> Dict | None:

        #load url parameters for http request
        params = {

        }